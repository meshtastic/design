#!/usr/bin/env python3
"""Generate the Chirpy notification sounds.

Each sound is defined by one RTTTL string. The string is parsed the way
firmware parses it, and the phone/desktop audio, the piezo preview, the
manifest and the generated parts of README.md and index.html all come
from that parse.

Python standard library only. Needs ffmpeg on PATH; uses afconvert for
CAF when present (macOS) and ffmpeg otherwise.

    python3 generate_sounds.py
"""

import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import wave

SAMPLE_RATE = 48000
TWO_PI = 2.0 * math.pi

RTTTL_MAX_BYTES = 230  # RTTTLConfig.ringtone max_size is 231 including the NUL
TARGET_LUFS = -16.0  # integrated
MAX_TRUE_PEAK = -1.0  # dBTP
NO_READING_LUFS = -70.0
TAIL_SILENCE_S = 0.050  # digital silence appended to every non-looping file

SEMITONE = {"c": 0, "c#": 1, "d": 2, "d#": 3, "e": 4, "f": 5, "f#": 6,
            "g": 7, "g#": 8, "a": 9, "a#": 10, "b": 11}

# Equal temperament from A4 = 440 Hz, for the octaves firmware can play.
NOTES = {
    f"{name}{octave}": 440.0 * 2.0 ** ((12 * (octave - 4) + semi - 9) / 12.0)
    for octave in range(4, 8)
    for name, semi in SEMITONE.items()
}

SUITE = [
    {
        "id": "chirpy",
        "title": "Chirpy",
        "use": "Message notification. Recommended device default.",
        "device": True,
        "loop": False,
        "bell_s": 0.55,
        "antenna": True,
        "syncword_alt": {
            "label": "Alternate: sync-word chirps",
            "note": (
                "Not the default. The rising strokes start 2/16 and 11/16 of the way up and wrap around, "
                "like a LoRa radio's sync word chirps, as a nod to Meshtastic's `0x2b` (it doesn't encode it). "
                "A wrapped stroke can't run into the fall, so it loses the logo's joined peak."
            ),
        },
        "rtttl": "Chirpy:d=32,o=5,b=150:f#,a#,c#6,f#6,p,f#,a#,c#6,f#6,c#6,a#,8f#,2p.",
    },
    {
        "id": "chirpy_ack",
        "title": "Chirpy Ack",
        "use": "Delivery receipt or reaction. Client apps only.",
        "device": False,
        "loop": False,
        "bell_s": 0.25,
        "rtttl": "ChirpyAck:d=32,o=5,b=150:a#,c#6,16f#6",
    },
    {
        "id": "chirpy_ringtone",
        "title": "Chirpy Ringtone",
        "use": "The long alert: a longer device ringtone, and the suggested sound for client alert channels. Loops.",
        "device": True,
        "loop": True,
        "bell_s": 0.55,
        "name": "ChirpyRing",
        "header": "d=32,o=5,b=150",
        # The parts of a LoRa frame, in order. Joined with commas into one string.
        "phrases": [
            ("Logo", "`chirpy`, note for note.",
             "f#,a#,c#6,f#6,p,f#,a#,c#6,f#6,c#6,a#,8f#,8p,p"),
            ("Preamble", "Four identical rising strokes, evenly spaced.",
             "f#,a#,c#6,f#6,16p,f#,a#,c#6,f#6,16p,f#,a#,c#6,f#6,16p,f#,a#,c#6,f#6,16p"),
            ("Sync word", "Two more rising strokes, spaced like the logo's. The second runs into the first fall.",
             "f#,a#,c#6,f#6,p,f#,a#,c#6,f#6"),
            ("Start of frame", "Two full falls and a quarter of one, which stops on D#6.",
             "c#6,a#,f#,16p,f#6,c#6,a#,f#,16p,f#6,d#6,8p"),
            ("Close", "F#5 held, then a rest before the loop repeats.",
             "4f#,2p"),
        ],
    },
]


for _item in SUITE:
    if "phrases" in _item:
        _item["rtttl"] = f"{_item['name']}:{_item['header']}:" + ",".join(p[2] for p in _item["phrases"])


# ----------------------------------------------------------------------------
# RTTTL
# ----------------------------------------------------------------------------

def parse_rtttl(text):
    """Parse an RTTTL string into note events.

    Follows NonBlockingRTTTL, which the PWM buzzer path uses, including its
    integer millisecond math. The string is also checked against the subset
    that the I2S players (ESP8266Audio, NRF52RtttlPlayer) read the same way.

    Returns (name, events, total_ms). Each event is a dict with start_ms,
    dur_ms, note (such as "f#6", or None for a rest) and freq.
    """
    if len(text.encode("ascii")) > RTTTL_MAX_BYTES:
        raise ValueError(f"RTTTL is over {RTTTL_MAX_BYTES} bytes: {text}")
    name, header, body = text.split(":")
    if not 0 < len(name) <= 10:
        raise ValueError(f"RTTTL name must be 1-10 characters: {name}")
    m = re.fullmatch(r"d=(\d+),o=(\d),b=(\d+)", header)
    if not m:
        raise ValueError(f"RTTTL header must be d=,o=,b= in that order: {header}")
    default_dur, default_oct, bpm = (int(g) for g in m.groups())
    if 60000 % bpm:
        # (60000 / bpm) * 4 and 240000 / bpm only agree when this divides.
        raise ValueError(f"bpm {bpm} gives different timing on different players")
    wholenote = (60000 // bpm) * 4

    events = []
    now = 0
    for token in body.split(","):
        # A dot before an octave digit is read differently by ESP8266Audio.
        m = re.fullmatch(r"(\d*)([a-gp]#?)(\.?)([4-7]?)(\.?)", token)
        if not m or (m.group(3) and m.group(4)) or (m.group(3) and m.group(5)):
            raise ValueError(f"unsupported RTTTL note: {token!r}")
        num, pitch, dot_a, octave, dot_b = m.groups()
        num = int(num) if num else default_dur
        if num not in (1, 2, 4, 8, 16, 32):
            raise ValueError(f"unsupported RTTTL duration: {token!r}")
        dur = wholenote // num
        if dot_a or dot_b:
            dur += dur // 2
        if pitch == "p":
            if octave:
                raise ValueError(f"rest with an octave: {token!r}")
            note, freq = None, 0.0
        else:
            note = f"{pitch}{octave or default_oct}"
            freq = NOTES[note]
        events.append({"start_ms": now, "dur_ms": dur, "note": note, "freq": freq})
        now += dur
    return name, events, now


def sounding_ms(events):
    """End of the last note, ignoring trailing rests."""
    return max(e["start_ms"] + e["dur_ms"] for e in events if e["note"])


def note_groups(events):
    """Runs of notes with no rest between them. Each run is one stroke."""
    groups, current = [], []
    for e in events:
        if e["note"]:
            current.append(e)
        elif current:
            groups.append(current)
            current = []
    if current:
        groups.append(current)
    return groups


# ----------------------------------------------------------------------------
# Synthesis
# ----------------------------------------------------------------------------

def raised_cosine(x):
    return 0.5 - 0.5 * math.cos(math.pi * max(0.0, min(1.0, x)))


def pan_gains(pan):
    angle = (pan + 1.0) * math.pi / 4.0
    return math.cos(angle), math.sin(angle)


STROKE_PAN = (-0.25, 0.20, 0.05)
STROKE_AMP = (0.55, 0.70, 0.60)
ANCHOR_S = 0.025  # a sweep reaches a note's pitch this far into the note
ATTACK_S = 0.008
RELEASE_S = 0.025
JUMP_FADE_S = 0.004
ANTENNA_CENTS = 6.0
ANTENNA_CYCLES = 3
# Where the two rising sweeps start in the sync-word variant, as a fraction
# of the sweep. 2/16 and 11/16 nod to the nibbles of sync word 0x2b. This is
# not a model of how a LoRa chip places its sync symbols.
SYNCWORD_OFFSETS = (2 / 16, 11 / 16)
BELL_PARTIALS = ((1.00, 1.00, 1.0), (2.00, 0.12, 0.6), (2.76, 0.05, 0.4))
REFLECTIONS = ((0.016, 0.14, 0.06), (0.034, 0.10, 0.12), (0.058, 0.05, 0.05))


def stroke_anchors(group, sixteenth):
    """The notes a run's sweep has to land on, as (time_s, freq).

    These are the first and last note, every turning point, and any note of
    a 16th or longer. A run of 32nds between two anchors is one straight
    sweep, the way a LoRa chirp is.
    """
    anchors = []
    for i, e in enumerate(group):
        ends = i == 0 or i == len(group) - 1
        turn = not ends and (group[i - 1]["freq"] < e["freq"]) != (e["freq"] < group[i + 1]["freq"])
        if ends or turn or e["dur_ms"] >= sixteenth:
            anchors.append((e["start_ms"] / 1000.0 + ANCHOR_S, e["freq"]))
    return anchors


def stroke_segments(group, anchors, wrap_offsets):
    """Frequency path of one run as (t0, t1, f0, f1), linear in Hz.

    wrap_offsets is consumed by rising sweeps: each one starts that fraction
    of the way up, runs to the top, drops to the bottom and finishes where it
    started, like a cyclically shifted chirp.
    """
    start = group[0]["start_ms"] / 1000.0
    end = (group[-1]["start_ms"] + group[-1]["dur_ms"]) / 1000.0
    sweeps = []
    for (t0, f0), (t1, f1) in zip(anchors, anchors[1:]):
        if f1 > f0 and wrap_offsets:
            off = wrap_offsets.pop(0)
            mid = f0 + off * (f1 - f0)
            turn = t0 + (1.0 - off) * (t1 - t0)
            sweeps += [(t0, turn, mid, f1), (turn, t1, f0, mid)]
        else:
            sweeps.append((t0, t1, f0, f1))
    if not sweeps:
        return [(start, end, anchors[0][1], anchors[0][1])]
    lead = (start, sweeps[0][0], sweeps[0][2], sweeps[0][2])
    hold = (sweeps[-1][1], end, sweeps[-1][3], sweeps[-1][3])
    return [lead] + sweeps + [hold]


def add_stroke(left, right, segments, pan, amp, antenna, sr):
    """One voice following a frequency path, with continuous phase."""
    start, end = segments[0][0], segments[-1][1]
    first = int(round(start * sr))
    n = int(round((end - start) * sr))
    att = int(ATTACK_S * sr)
    rel = int(RELEASE_S * sr)
    hold_t0, hold_t1 = segments[-1][0], segments[-1][1]
    gain_l, gain_r = pan_gains(pan)
    # A wrapped sweep jumps in frequency. Duck the level across the jump.
    jumps = [a[1] for a, b in zip(segments, segments[1:]) if abs(a[3] - b[2]) > 1.0]

    phase = 0.0
    seg = 0
    for i in range(n):
        t = start + i / sr
        while seg + 1 < len(segments) and t >= segments[seg][1]:
            seg += 1
        t0, t1, f0, f1 = segments[seg]
        freq = f0 + (f1 - f0) * (t - t0) / (t1 - t0) if t1 > t0 else f1
        env = raised_cosine(i / att) * raised_cosine((n - 1 - i) / rel)
        for jump in jumps:
            env *= raised_cosine(abs(t - jump) / JUMP_FADE_S)
        if t > hold_t0:
            if antenna:
                # A zigzag of a few cents on the last note, for the antenna.
                x = (t - hold_t0) / (hold_t1 - hold_t0) * ANTENNA_CYCLES % 1.0
                zigzag = 4.0 * x if x < 0.25 else (2.0 - 4.0 * x if x < 0.75 else 4.0 * x - 4.0)
                freq *= 2.0 ** (ANTENNA_CENTS * zigzag / 1200.0)
            if t > hold_t0 + 0.075:
                env *= math.exp(-(t - hold_t0 - 0.075) / 0.5)
        phase += TWO_PI * freq / sr
        val = (math.sin(phase) + 0.08 * math.sin(2.0 * phase)) * env * amp
        left[first + i] += val * gain_l
        right[first + i] += val * gain_r


def add_bell(left, right, start_s, freq, dur_s, pan, amp, sr):
    """A struck-bell layer. The last 40% fades to zero so it never truncates."""
    first = int(start_s * sr)
    n = int(dur_s * sr)
    att = int(0.004 * sr)
    rel = int(0.4 * n)
    tau = 0.25 * (1500.0 / freq) ** 0.3
    gain_l, gain_r = pan_gains(pan)
    incs = [TWO_PI * freq * mult / sr for mult, _, _ in BELL_PARTIALS]
    for i in range(n):
        t = i / sr
        val = 0.0
        for inc, (_, p_amp, d_mult) in zip(incs, BELL_PARTIALS):
            val += p_amp * math.exp(-t / (tau * d_mult)) * math.sin(inc * i)
        val *= raised_cosine(i / att) * raised_cosine((n - 1 - i) / rel) * amp * 0.40
        left[first + i] += val * gain_l
        right[first + i] += val * gain_r


def studio_paths(events, wrap_offsets=()):
    """Sweep path and bell strikes for each run of notes."""
    sixteenth = min(e["dur_ms"] for e in events) * 2
    if min(e["dur_ms"] for e in events if e["note"]) < 2000 * ANCHOR_S:
        raise ValueError("notes are too short for the sweep anchors")
    wrap = list(wrap_offsets)
    paths = []
    for group in note_groups(events):
        anchors = stroke_anchors(group, sixteenth)
        paths.append((stroke_segments(group, anchors, wrap), anchors[1:] or anchors))
    return paths


def render_studio(events, total_ms, bell_s, loop, antenna=False, wrap_offsets=(), sr=SAMPLE_RATE):
    """Phone and desktop rendering of the parsed RTTTL events.

    A looping sound is exactly as long as its RTTTL string, trailing rest
    included. A one-shot drops the trailing rest and ends when its tail does.
    """
    paths = studio_paths(events, wrap_offsets)
    bells = []
    for gi, (_, strikes) in enumerate(paths):
        for t, freq in strikes:
            amp = 0.45 if (t, freq) == strikes[-1] else 0.30
            bells.append((t, freq, bell_s, -STROKE_PAN[gi % 3], amp))

    content_end = max([sounding_ms(events) / 1000.0] + [b[0] + b[2] for b in bells])
    content_end += REFLECTIONS[-1][0]
    if loop:
        total = total_ms / 1000.0
        if content_end + TAIL_SILENCE_S > total:
            raise ValueError("loop needs a longer trailing rest for its tail")
    else:
        total = content_end + TAIL_SILENCE_S
    n = int(round(total * sr))
    dry_l = [0.0] * (n + 1)
    dry_r = [0.0] * (n + 1)

    for gi, (segments, _) in enumerate(paths):
        last = gi == len(paths) - 1
        add_stroke(dry_l, dry_r, segments, STROKE_PAN[gi % 3], STROKE_AMP[gi % 3], antenna and last, sr)
    for start_s, freq, dur_s, pan, amp in bells:
        add_bell(dry_l, dry_r, start_s, freq, dur_s, pan, amp, sr)

    out_l = list(dry_l[:n])
    out_r = list(dry_r[:n])
    for delay_s, g_dir, g_cross in REFLECTIONS:
        d = int(delay_s * sr)
        for i in range(d, n):
            out_l[i] += dry_l[i - d] * g_dir + dry_r[i - d] * g_cross
            out_r[i] += dry_r[i - d] * g_dir + dry_l[i - d] * g_cross
    return out_l, out_r


def render_piezo(events, total_ms, sr=SAMPLE_RATE):
    """Square-wave preview of the string as a buzzer plays it.

    Notes run their full length with no gap, as tone() does. The square is
    built from odd harmonics below 20 kHz so the preview has no aliasing.
    """
    has_trailing_rest = events[-1]["note"] is None
    total = total_ms / 1000.0 + (0.0 if has_trailing_rest else TAIL_SILENCE_S)
    n = int(round(total * sr))
    mix = [0.0] * n
    ramp = int(0.001 * sr)
    for e in events:
        if not e["note"]:
            continue
        first = int(e["start_ms"] * sr / 1000)
        length = int(e["dur_ms"] * sr / 1000)
        harmonics = [k for k in range(1, 40, 2) if k * e["freq"] < 20000.0]
        inc = TWO_PI * e["freq"] / sr
        for i in range(length):
            val = sum(math.sin(k * inc * i) / k for k in harmonics)
            env = min(1.0, i / ramp, (length - 1 - i) / ramp)
            mix[first + i] += val * env
    return mix, list(mix)


# ----------------------------------------------------------------------------
# Files, loudness
# ----------------------------------------------------------------------------

def write_wav(path, left, right, gain=1.0, sr=SAMPLE_RATE):
    frames = bytearray()
    for l, r in zip(left, right):
        lv = int(round(l * gain * 32767.0))
        rv = int(round(r * gain * 32767.0))
        if abs(lv) > 32767 or abs(rv) > 32767:
            raise ValueError(f"{path} would clip")
        frames.extend(struct.pack("<hh", lv, rv))
    with wave.open(path, "wb") as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(sr)
        f.writeframes(frames)


def run(cmd):
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)}\n{res.stderr[-2000:]}")
    return res.stderr


def measure(path):
    """EBU R128 numbers from ffmpeg.

    integrated and true_peak come from the file as it is. momentary_max is
    taken with 0.5 s of silence appended, so a sound shorter than the 400 ms
    momentary window still fills one.
    """
    plain = run(["ffmpeg", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"])
    summary = plain[plain.rindex("Summary:"):]
    integrated = float(re.search(r"I:\s+(-?[\d.]+) LUFS", summary).group(1))
    true_peak = float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", summary).group(1))
    padded = run(["ffmpeg", "-nostats", "-i", path, "-af", "apad=pad_dur=0.5,ebur128", "-f", "null", "-"])
    frames = [float(v) for v in re.findall(r"\bM:\s*(-?\d+\.\d+)", padded)]
    return {"integrated_lufs": integrated, "momentary_max_lufs": max(frames), "true_peak_dbtp": true_peak}


def wav_stats(path):
    with wave.open(path, "rb") as f:
        sr, n = f.getframerate(), f.getnframes()
        f.setpos(n - int(0.030 * sr))
        tail = struct.unpack(f"<{int(0.030 * sr) * 2}h", f.readframes(int(0.030 * sr)))
    peak = max(abs(v) for v in tail)
    tail_db = 20.0 * math.log10(peak / 32768.0) if peak else float("-inf")
    return n / sr, tail_db


def normalize(path, left, right, fallback_momentary=None):
    """Write the buffers at TARGET_LUFS integrated.

    ffmpeg reports -70 LUFS when a file is too short for one 400 ms gating
    block. Such a file is matched to fallback_momentary instead.
    """
    peak = max(max(abs(v) for v in left), max(abs(v) for v in right))
    gain = 0.5 / peak
    with tempfile.TemporaryDirectory() as tmp:
        probe = os.path.join(tmp, "probe.wav")
        write_wav(probe, left, right, gain)
        got = measure(probe)
    if got["integrated_lufs"] > NO_READING_LUFS:
        target, key = TARGET_LUFS, "integrated_lufs"
    elif fallback_momentary is not None:
        target, key = fallback_momentary, "momentary_max_lufs"
    else:
        raise RuntimeError(f"{path} is too short for an integrated reading")
    gain *= 10.0 ** ((target - got[key]) / 20.0)
    over = got["true_peak_dbtp"] + (target - got[key]) - MAX_TRUE_PEAK
    if over > 0.0:
        print(f"  {os.path.basename(path)}: held {over + 0.1:.1f} dB under target to keep true peak")
        gain *= 10.0 ** (-(over + 0.1) / 20.0)
    write_wav(path, left, right, gain)
    result = measure(path)
    if result["true_peak_dbtp"] > MAX_TRUE_PEAK:
        raise RuntimeError(f"{path} true peak {result['true_peak_dbtp']} dBTP")
    return result


def encode(wav_path, out_dir, base):
    """WAV to MP3, M4A, CAF and OGG. Returns {format: path}."""
    out = {ext: os.path.join(out_dir, f"{base}.{ext}") for ext in ("mp3", "m4a", "caf", "ogg")}
    # bitexact keeps the Ogg stream serial and the container tags fixed, so a
    # rerun with the same ffmpeg writes the same bytes.
    exact = ["-fflags", "+bitexact", "-flags:a", "+bitexact"]
    run(["ffmpeg", "-y", "-i", wav_path, "-codec:a", "libmp3lame", "-q:a", "2", *exact, out["mp3"]])
    run(["ffmpeg", "-y", "-i", wav_path, "-c:a", "aac", "-b:a", "192k", *exact, out["m4a"]])
    run(["ffmpeg", "-y", "-i", wav_path, "-c:a", "libopus", "-b:a", "128k", *exact, out["ogg"]])
    if shutil.which("afconvert"):
        run(["afconvert", "-f", "caff", "-d", "LEI16", wav_path, out["caf"]])
    else:
        run(["ffmpeg", "-y", "-i", wav_path, "-c:a", "pcm_s16le", out["caf"]])
    return out


# ----------------------------------------------------------------------------
# Generated documentation blocks
# ----------------------------------------------------------------------------

def replace_block(path, begin, end, body):
    with open(path) as f:
        text = f.read()
    if text.count(begin) != 1 or text.count(end) != 1:
        raise RuntimeError(f"{path} needs exactly one {begin} ... {end} block")
    head, rest = text.split(begin)
    _, tail = rest.split(end)
    with open(path, "w") as f:
        f.write(head + begin + "\n" + body + "\n" + end + tail)


def readme_block(manifest):
    lines = [
        "| Sound | Use | Phone file | Device RTTTL | RTTTL bytes |",
        "| --- | --- | --- | --- | --- |",
    ]
    for m in manifest:
        device = f"{m['rtttl_ms'] / 1000:.2f} s"
        if m["rtttl_ms"] != m["rtttl_sounding_ms"]:
            device = f"{m['rtttl_sounding_ms'] / 1000:.2f} s, then {(m['rtttl_ms'] - m['rtttl_sounding_ms']) / 1000:.2f} s rest"
        if not m["device"]:
            device += " (reference only)"
        lines.append(f"| `{m['id']}` | {m['use']} | {m['duration_s']:.2f} s | {device} | {m['rtttl_bytes']} |")
    for m in manifest:
        lines += ["", f"`{m['id']}`", "", "```text", m["rtttl"], "```"]
    for m in manifest:
        if "syncword_alt" in m:
            lines += ["", f"`{m['syncword_alt']['wav']}`: {m['syncword_alt']['note']}"]
    for m in manifest:
        if "phrases" in m:
            lines += ["", f"The parts of `{m['id']}`:", "",
                      "| Part | Starts | Lasts | Notes | What it is |", "| --- | --- | --- | --- | --- |"]
            for ph in m["phrases"]:
                lines.append(f"| {ph['part']} | {ph['start_ms'] / 1000:.2f} s | {ph['dur_ms'] / 1000:.2f} s "
                             f"| `{ph['notes']}` | {ph['what']} |")
    lines += [
        "",
        "Measured with `ffmpeg -af ebur128=peak=true` on the WAV files:",
        "",
        "| File | Length | Integrated | Momentary max | True peak |",
        "| --- | --- | --- | --- | --- |",
    ]
    for m in manifest:
        rows = [(m["files"]["wav"], m), (m["files"]["piezo_wav"], m["piezo"])]
        if "syncword_alt" in m:
            rows.append((m["syncword_alt"]["wav"], m["syncword_alt"]))
        for label, stats in rows:
            integrated = "n/a" if stats["integrated_lufs"] <= NO_READING_LUFS else f"{stats['integrated_lufs']:.1f} LUFS"
            lines.append(
                f"| `{label}` | {stats['duration_s']:.2f} s | {integrated} "
                f"| {stats['momentary_max_lufs']:.1f} LUFS | {stats['true_peak_dbtp']:.1f} dBTP |"
            )
    return "\n".join(lines)


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(base_dir, "dist")
    sim_dir = os.path.join(dist_dir, "piezo_simulated")
    rtttl_dir = os.path.join(base_dir, "rtttl")
    for d in (dist_dir, rtttl_dir):
        shutil.rmtree(d, ignore_errors=True)
    alt_dir = os.path.join(dist_dir, "alt")
    for d in (dist_dir, sim_dir, alt_dir, rtttl_dir):
        os.makedirs(d)

    rendered = {}
    for item in SUITE:
        name, events, total_ms = parse_rtttl(item["rtttl"])
        rendered[item["id"]] = {
            "events": events,
            "total_ms": total_ms,
            "studio": render_studio(events, total_ms, item["bell_s"], item["loop"], item.get("antenna", False)),
            "piezo": render_piezo(events, total_ms),
        }

    manifest = []
    for item in SUITE:
        key = item["id"]
        r = rendered[key]
        wav_path = os.path.join(dist_dir, f"{key}.wav")
        stats = normalize(wav_path, *r["studio"])
        duration, tail_db = wav_stats(wav_path)
        encoded = encode(wav_path, dist_dir, key)

        piezo_path = os.path.join(sim_dir, f"{key}_piezo.wav")
        piezo = normalize(piezo_path, *r["piezo"], fallback_momentary=stats["momentary_max_lufs"])
        piezo["duration_s"], piezo["tail_peak_dbfs"] = wav_stats(piezo_path)

        with open(os.path.join(rtttl_dir, f"{key}.rtttl"), "w") as f:
            f.write(item["rtttl"] + "\n")

        tails = [(wav_path, tail_db), (piezo_path, piezo["tail_peak_dbfs"])]
        alt = None
        if item.get("syncword_alt"):
            alt_path = os.path.join(alt_dir, f"{key}_syncword.wav")
            alt = normalize(alt_path, *render_studio(r["events"], r["total_ms"], item["bell_s"], item["loop"],
                                                     item.get("antenna", False), SYNCWORD_OFFSETS))
            alt["duration_s"], alt["tail_peak_dbfs"] = wav_stats(alt_path)
            alt["wav"] = os.path.relpath(alt_path, base_dir)
            tails.append((alt_path, alt["tail_peak_dbfs"]))

        for label, t in tails:
            if t > -60.0:
                raise RuntimeError(f"{label} does not end in silence: {t:.1f} dBFS")

        files = {"wav": wav_path, **encoded}
        manifest.append({
            "id": key,
            "title": item["title"],
            "use": item["use"],
            "device": item["device"],
            "loop": item["loop"],
            "rtttl": item["rtttl"],
            "rtttl_bytes": len(item["rtttl"].encode("ascii")),
            "rtttl_ms": r["total_ms"],
            "rtttl_sounding_ms": sounding_ms(r["events"]),
            "notes": [e["note"] or "p" for e in r["events"]],
            "duration_s": round(duration, 3),
            "tail_peak_dbfs": None if tail_db == float("-inf") else round(tail_db, 1),
            **stats,
            "files": {
                **{ext: os.path.relpath(p, base_dir) for ext, p in files.items()},
                "rtttl": f"rtttl/{key}.rtttl",
                "piezo_wav": os.path.relpath(piezo_path, base_dir),
            },
            "bytes": {ext: os.path.getsize(p) for ext, p in files.items()},
            "piezo": {k: (None if v == float("-inf") else round(v, 3)) for k, v in piezo.items()},
            "sweeps": [
                [[round(t0, 3), round(t1, 3), round(f0, 2), round(f1, 2)] for t0, t1, f0, f1 in segments if f0 != f1]
                for segments, _ in studio_paths(r["events"])
            ],
        })
        if "phrases" in item:
            at = 0
            manifest[-1]["phrases"] = []
            for label, text, notes in item["phrases"]:
                _, _, ms = parse_rtttl(f"x:{item['header']}:{notes}")
                manifest[-1]["phrases"].append(
                    {"part": label, "what": text, "notes": notes, "start_ms": at, "dur_ms": ms})
                at += ms
        if alt:
            manifest[-1]["syncword_alt"] = {**item["syncword_alt"],
                                            **{k: (None if v == float("-inf") else v) for k, v in alt.items()}}
        print(f"{key}: {duration:.3f} s, I {stats['integrated_lufs']} LUFS, "
              f"M max {stats['momentary_max_lufs']} LUFS, TP {stats['true_peak_dbtp']} dBTP, "
              f"RTTTL {manifest[-1]['rtttl_bytes']} bytes / {r['total_ms']} ms")

    with open(os.path.join(base_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")

    replace_block(os.path.join(base_dir, "README.md"),
                  "<!-- BEGIN GENERATED: generate_sounds.py -->", "<!-- END GENERATED -->",
                  readme_block(manifest))
    replace_block(os.path.join(base_dir, "index.html"),
                  "/* BEGIN GENERATED: generate_sounds.py */", "/* END GENERATED */",
                  "    const SUITE = " + json.dumps(manifest) + ";")

    for doc in ("README.md", "index.html"):
        with open(os.path.join(base_dir, doc)) as f:
            text = f.read()
        for m in manifest:
            if m["rtttl"] not in text:
                raise RuntimeError(f"{doc} is missing the {m['id']} RTTTL string")
        known = {m["rtttl"] for m in manifest}
        for found in re.findall(r"\w+:d=\d+,o=\d,b=\d+:[a-gp#.,\d]+", text):
            if found not in known:
                raise RuntimeError(f"{doc} has a stale RTTTL string: {found}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
