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
        "rtttl": "Chirpy:d=32,o=6,b=150:c#,f#,p,a#,16f#7,p,c#7,a#,8f#,2p.",
    },
    {
        "id": "chirpy_ack",
        "title": "Chirpy Ack",
        "use": "Delivery receipt or reaction. Client apps only.",
        "device": False,
        "loop": False,
        "bell_s": 0.25,
        "rtttl": "ChirpyAck:d=32,o=6,b=150:a#,c#7,16f#7",
    },
    {
        "id": "chirpy_ringtone",
        "title": "Chirpy Song",
        "use": "Optional longer alert. Loops.",
        "device": True,
        "loop": True,
        "bell_s": 0.55,
        "rtttl": (
            "ChirpySong:d=16,o=6,b=150:"
            "32c#,32f#,32p,32a#,f#7,32p,32c#7,32a#,8f#,8p.,32p,"
            "f#,c#7,d#7,8c#7,4p,p,"
            "a#,c#7,f#7,d#7,8c#7,4p,"
            "32c#,32f#,32a#,32c#7,4f#7.,2p."
        ),
    },
]


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
GLIDE_S = 0.050  # each note slides to the next over its last 50 ms
ATTACK_S = 0.008
RELEASE_S = 0.025
BELL_PARTIALS = ((1.00, 1.00, 1.0), (2.00, 0.25, 0.6), (2.76, 0.18, 0.4), (4.15, 0.04, 0.3))
REFLECTIONS = ((0.016, 0.14, 0.06), (0.034, 0.10, 0.12), (0.058, 0.05, 0.05))


def add_stroke(left, right, group, pan, amp, sr):
    """One swept voice through a run of notes, landing on each note's pitch."""
    start = group[0]["start_ms"] / 1000.0
    end = (group[-1]["start_ms"] + group[-1]["dur_ms"]) / 1000.0
    first = int(start * sr)
    n = int((end - start) * sr)
    att = int(ATTACK_S * sr)
    rel = int(RELEASE_S * sr)
    hold_from = group[-1]["start_ms"] / 1000.0 - start + 0.100
    gain_l, gain_r = pan_gains(pan)

    # Per-note (start, end, f_from, f_to) with the slide at the end of the note.
    segments = []
    for i, e in enumerate(group):
        t0 = e["start_ms"] / 1000.0 - start
        t1 = t0 + e["dur_ms"] / 1000.0
        nxt = group[i + 1]["freq"] if i + 1 < len(group) else e["freq"]
        segments.append((t0, t1, e["freq"], nxt))

    phase = 0.0
    seg = 0
    for i in range(n):
        t = i / sr
        while seg + 1 < len(segments) and t >= segments[seg][1]:
            seg += 1
        t0, t1, f_from, f_to = segments[seg]
        glide = min(GLIDE_S, t1 - t0)
        x = (t - (t1 - glide)) / glide
        freq = f_from if x <= 0.0 else f_from * (f_to / f_from) ** min(1.0, x)
        phase += TWO_PI * freq / sr

        env = raised_cosine(i / att) * raised_cosine((n - 1 - i) / rel)
        if t > hold_from:
            env *= math.exp(-(t - hold_from) / 0.5)
        val = (math.sin(phase) + 0.22 * math.sin(2.0 * phase) + 0.05 * math.sin(3.0 * phase)) * env * amp
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


def render_studio(events, total_ms, bell_s, loop, sr=SAMPLE_RATE):
    """Phone and desktop rendering of the parsed RTTTL events.

    A looping sound is exactly as long as its RTTTL string, trailing rest
    included. A one-shot drops the trailing rest and ends when its tail does.
    """
    groups = note_groups(events)
    sixteenth = min(e["dur_ms"] for e in events) * 2
    bells = []
    for gi, group in enumerate(groups):
        for e in group:
            if e is group[-1] or e["dur_ms"] >= sixteenth:
                amp = 0.45 if e is group[-1] else 0.30
                bells.append((e["start_ms"] / 1000.0, e["freq"], bell_s, -STROKE_PAN[gi % 3], amp))

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

    for gi, group in enumerate(groups):
        add_stroke(dry_l, dry_r, group, STROKE_PAN[gi % 3], STROKE_AMP[gi % 3], sr)
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
    run(["ffmpeg", "-y", "-i", wav_path, "-codec:a", "libmp3lame", "-q:a", "2", out["mp3"]])
    run(["ffmpeg", "-y", "-i", wav_path, "-c:a", "aac", "-b:a", "192k", out["m4a"]])
    run(["ffmpeg", "-y", "-i", wav_path, "-c:a", "libopus", "-b:a", "128k", out["ogg"]])
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
    lines += [
        "",
        "Measured with `ffmpeg -af ebur128=peak=true` on the WAV files:",
        "",
        "| File | Length | Integrated | Momentary max | True peak |",
        "| --- | --- | --- | --- | --- |",
    ]
    for m in manifest:
        for label, stats in ((m["files"]["wav"], m), (m["files"]["piezo_wav"], m["piezo"])):
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
    for d in (dist_dir, sim_dir, rtttl_dir):
        os.makedirs(d)

    rendered = {}
    for item in SUITE:
        name, events, total_ms = parse_rtttl(item["rtttl"])
        rendered[item["id"]] = {
            "events": events,
            "total_ms": total_ms,
            "studio": render_studio(events, total_ms, item["bell_s"], item["loop"]),
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

        for label, t in ((wav_path, tail_db), (piezo_path, piezo["tail_peak_dbfs"])):
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
        })
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
