#!/usr/bin/env python3
r"""
Meshtastic 'Chirpy' Audio & Ringtone Generator
Exclusively synthesizes the official 'Chirpy' sound suite.
Chirpy is Meshtastic's anthropomorphic radio node mascot, named after
LoRa Chirp Spread Spectrum (CSS) radio modulation.

The sounds embody the iconic //\ (Upchirp, Upchirp, Downchirp)
LoRa packet syncword and chest logo pattern.

Zero external dependencies (uses Python standard library: math, wave, struct, json, os).
Encodes to MP3, M4A, CAF, OGG using system tools (afconvert / ffmpeg) when available.
"""

import math
import struct
import wave
import os
import json
import subprocess

SAMPLE_RATE = 48000
TWO_PI = 2.0 * math.pi

# Note frequency table (Hz)
NOTES = {
    'c#6': 1108.73, 'f#6': 1479.98,
    'a#6': 1864.66, 'c#7': 2217.46,
    'd#7': 2489.02, 'f#7': 2959.96,
    'p': 0.0 # Rest
}


# ==============================================================================
# 1. Synthesis Engines: Electronic LoRa Node Chirps + Resonant Chimes
# ==============================================================================

def synth_chirpy_notification(sample_rate=SAMPLE_RATE):
    """
    Flagship Chirpy //\\ Notification Sound (0.85s).
    The electronic vocalization of Chirpy the anthropomorphic radio node:
      Stroke 1 (/): Upward greeting RF chirp (C#6 -> F#6)
      Stroke 2 (/): Higher upward RF chirp to summit peak (A#6 -> F#7)
      Stroke 3 (\\): Cascading downward resolution (F#7 -> C#7 -> F#6)
    """
    total_sec = 0.85
    total_samples = int(total_sec * sample_rate)
    left = [0.0] * total_samples
    right = [0.0] * total_samples

    # Tactile LoRa CSS sweeps for the //\\ strokes
    chirp_strokes = [
        # (start_t, dur, f_start, f_end, pan, amp)
        (0.000, 0.065, 1108.73, 1568.0, -0.25, 0.55),  # Stroke 1: /
        (0.085, 0.090, 1760.0,  3136.0,  0.20, 0.70),  # Stroke 2: /
        (0.190, 0.140, 3136.0,  1479.98, 0.05, 0.60),  # Stroke 3: \
    ]

    for start_t, dur, f0, f1, pan, amp in chirp_strokes:
        start_idx = int(start_t * sample_rate)
        n = int(dur * sample_rate)
        phase = 0.0
        att = int(0.006 * sample_rate)
        rel = int(0.020 * sample_rate)

        pan_l = math.cos((pan + 1.0) * math.pi / 4.0)
        pan_r = math.sin((pan + 1.0) * math.pi / 4.0)

        for i in range(n):
            idx = start_idx + i
            if idx >= total_samples:
                break
            t = i / n
            freq = f0 * ((f1 / f0) ** t)
            phase += TWO_PI * freq / sample_rate

            env = math.sin((i / att) * (math.pi / 2)) if i < att else (
                  math.sin(((n - i) / rel) * (math.pi / 2)) if i > n - rel else 1.0)

            # Node synthesizer voice: fundamental + gentle 2nd harmonic + tactile sparkle
            val = (math.sin(phase) + 0.22 * math.sin(2.0 * phase) + 0.05 * math.sin(3.0 * phase)) * env * amp
            left[idx] += val * pan_l
            right[idx] += val * pan_r

    # Acoustic Bell / Chime Resonance on key F# Major triad anchors
    chimes = [
        (0.000, 1479.98, 0.45, -0.20, 0.35), # F#6
        (0.150, 2959.96, 0.55,  0.25, 0.50), # F#7
        (0.240, 2217.46, 0.45,  0.10, 0.30), # C#7
        (0.280, 1479.98, 0.55, -0.10, 0.40), # F#6
    ]

    add_bell_resonance(left, right, chimes, total_samples, sample_rate)
    return apply_ambience_and_normalize(left, right, sample_rate)


def synth_chirpy_ack(sample_rate=SAMPLE_RATE):
    """
    Chirpy Quick // ACK Chirp (0.50s).
    Two rapid upward strokes (//) for tapbacks, receipts, and fast pings.
    """
    total_sec = 0.50
    total_samples = int(total_sec * sample_rate)
    left = [0.0] * total_samples
    right = [0.0] * total_samples

    chirp_strokes = [
        (0.000, 0.055, 1108.73, 1568.0, -0.20, 0.60),  # Stroke 1: /
        (0.075, 0.080, 1864.66, 2959.96,  0.20, 0.75),  # Stroke 2: / (bright peak)
    ]

    for start_t, dur, f0, f1, pan, amp in chirp_strokes:
        start_idx = int(start_t * sample_rate)
        n = int(dur * sample_rate)
        phase = 0.0
        att = int(0.005 * sample_rate)
        rel = int(0.018 * sample_rate)

        pan_l = math.cos((pan + 1.0) * math.pi / 4.0)
        pan_r = math.sin((pan + 1.0) * math.pi / 4.0)

        for i in range(n):
            idx = start_idx + i
            if idx >= total_samples:
                break
            t = i / n
            freq = f0 * ((f1 / f0) ** t)
            phase += TWO_PI * freq / sample_rate

            env = math.sin((i / att) * (math.pi / 2)) if i < att else (
                  math.sin(((n - i) / rel) * (math.pi / 2)) if i > n - rel else 1.0)

            val = (math.sin(phase) + 0.22 * math.sin(2.0 * phase) + 0.05 * math.sin(3.0 * phase)) * env * amp
            left[idx] += val * pan_l
            right[idx] += val * pan_r

    chimes = [
        (0.000, 1479.98, 0.35, -0.15, 0.30),
        (0.120, 2959.96, 0.40,  0.25, 0.45),
    ]

    add_bell_resonance(left, right, chimes, total_samples, sample_rate)
    return apply_ambience_and_normalize(left, right, sample_rate)


def synth_chirpy_ringtone(sample_rate=SAMPLE_RATE):
    """
    Chirpy Song Ringtone (3.6s loopable).
    4 melodic phrases featuring Chirpy the node's //\\ theme:
      Bar 1: Flagship //\\ call
      Bar 2: Playful answer
      Bar 3: Mesh hops
      Bar 4: Grand //\\ ascending finale with sustained singing peak
    """
    total_sec = 3.6
    total_samples = int(total_sec * sample_rate)
    left = [0.0] * total_samples
    right = [0.0] * total_samples

    strokes = [
        # Bar 1: //\
        (0.000, 0.060, 1108.73, 1568.0, -0.25, 0.55),
        (0.080, 0.085, 1760.0,  3136.0,  0.20, 0.70),
        (0.185, 0.130, 3136.0,  1479.98, 0.00, 0.60),

        # Bar 2: Answer
        (0.850, 0.080, 1479.98, 2217.46, -0.15, 0.50),
        (0.950, 0.080, 2217.46, 2489.02,  0.15, 0.55),
        (1.050, 0.140, 2489.02, 2217.46,  0.00, 0.50),

        # Bar 3: Mesh Hops
        (1.700, 0.060, 1864.66, 2217.46, -0.20, 0.50),
        (1.780, 0.075, 2217.46, 2959.96,  0.25, 0.65),
        (1.880, 0.120, 2959.96, 2217.46,  0.05, 0.55),

        # Bar 4: Grand //\ Finale
        (2.550, 0.050, 1108.73, 1479.98, -0.25, 0.50),
        (2.620, 0.050, 1479.98, 1864.66, -0.10, 0.55),
        (2.690, 0.060, 1864.66, 2217.46,  0.10, 0.60),
        (2.770, 0.380, 2217.46, 2959.96,  0.25, 0.75),
    ]

    for start_t, dur, f0, f1, pan, amp in strokes:
        start_idx = int(start_t * sample_rate)
        n = int(dur * sample_rate)
        phase = 0.0
        att = int(0.006 * sample_rate)
        rel = int(0.025 * sample_rate)

        pan_l = math.cos((pan + 1.0) * math.pi / 4.0)
        pan_r = math.sin((pan + 1.0) * math.pi / 4.0)

        for i in range(n):
            idx = start_idx + i
            if idx >= total_samples:
                break
            t = i / n
            freq = f0 * ((f1 / f0) ** t)
            if dur > 0.2 and i > att * 2:
                freq *= (1.0 + 0.015 * math.sin(TWO_PI * 18.0 * (i / sample_rate)))

            phase += TWO_PI * freq / sample_rate

            env = math.sin((i / att) * (math.pi / 2)) if i < att else (
                  math.sin(((n - i) / rel) * (math.pi / 2)) if i > n - rel else 1.0)

            val = (math.sin(phase) + 0.22 * math.sin(2.0 * phase) + 0.05 * math.sin(3.0 * phase)) * env * amp
            left[idx] += val * pan_l
            right[idx] += val * pan_r

    chimes = [
        (0.000, 1479.98, 0.40, -0.20, 0.35),
        (0.150, 2959.96, 0.50,  0.25, 0.45),
        (0.260, 1479.98, 0.50, -0.10, 0.40),
        (0.850, 1479.98, 0.35, -0.15, 0.30),
        (1.050, 2217.46, 0.50,  0.10, 0.35),
        (1.700, 1864.66, 0.35, -0.15, 0.30),
        (1.850, 2959.96, 0.50,  0.20, 0.40),
        (2.000, 2217.46, 0.45,  0.00, 0.30),
        (2.550, 1479.98, 0.35, -0.20, 0.35),
        (2.770, 2959.96, 0.85,  0.30, 0.55),
    ]

    add_bell_resonance(left, right, chimes, total_samples, sample_rate)
    return apply_ambience_and_normalize(left, right, sample_rate)


def add_bell_resonance(left, right, chimes, total_samples, sample_rate):
    """Layers physical bell/tine partials underneath the electronic chirp."""
    bell_partials = [
        (1.00, 1.00, 1.0),
        (2.00, 0.25, 0.6),
        (2.76, 0.18, 0.4),
        (4.15, 0.04, 0.3)
    ]

    for start_t, freq, dur_sec, pan, amp in chimes:
        start_idx = int(start_t * sample_rate)
        n = int(dur_sec * sample_rate)
        att = int(0.004 * sample_rate)
        decay_tau = 0.25 * (1500.0 / freq) ** 0.3

        pan_l = math.cos((pan + 1.0) * math.pi / 4.0)
        pan_r = math.sin((pan + 1.0) * math.pi / 4.0)

        phases = [0.0] * len(bell_partials)
        phase_inc = [TWO_PI * (freq * p[0]) / sample_rate for p in bell_partials]

        for i in range(n):
            idx = start_idx + i
            if idx >= total_samples:
                break
            t = i / sample_rate
            env = math.sin((i / att) * (math.pi / 2)) if i < att else 1.0
            val = 0.0
            for p_idx, (mult, p_amp, d_mult) in enumerate(bell_partials):
                p_decay = math.exp(-t / (decay_tau * d_mult))
                val += p_amp * p_decay * math.sin(phases[p_idx])
                phases[p_idx] += phase_inc[p_idx]

            sample_val = val * env * amp * 0.40
            left[idx] += sample_val * pan_l
            right[idx] += sample_val * pan_r


def apply_ambience_and_normalize(left, right, sample_rate):
    """Applies subtle stereo reflections and normalizes peak to -1.0 dBFS."""
    n = len(left)
    out_l = list(left)
    out_r = list(right)

    reflections = [
        (int(0.016 * sample_rate), 0.14, 0.06),
        (int(0.034 * sample_rate), 0.10, 0.12),
        (int(0.058 * sample_rate), 0.05, 0.05),
    ]

    for delay_s, g_dir, g_cross in reflections:
        for i in range(delay_s, n):
            out_l[i] += left[i - delay_s] * g_dir + right[i - delay_s] * g_cross
            out_r[i] += right[i - delay_s] * g_dir + left[i - delay_s] * g_cross

    max_peak = max(max(abs(l), abs(r)) for l, r in zip(out_l, out_r))
    if max_peak > 0:
        gain = 0.89125 / max_peak  # -1.0 dBFS
        out_l = [s * gain for s in out_l]
        out_r = [s * gain for s in out_r]

    return out_l, out_r


def render_piezo_simulation(score, bpm, sample_rate=SAMPLE_RATE):
    """Simulates hardware piezo buzzer (pure square wave with physical damping)."""
    sec_per_beat = 60.0 / bpm
    note_events = []
    current_time = 0.0

    for item in score:
        note_name = item[0]
        dur_beats = item[1]
        dur_sec = dur_beats * sec_per_beat
        freq = NOTES.get(note_name.lower(), 0.0)
        note_events.append((current_time, freq, dur_sec))
        current_time += dur_sec

    total_duration = current_time + 0.1
    total_samples = int(total_duration * sample_rate)
    mix = [0.0] * total_samples

    for (start_t, freq, dur_sec) in note_events:
        if freq <= 0.0:
            continue
        start_idx = int(start_t * sample_rate)
        note_len = int(dur_sec * sample_rate)
        gate_samples = int(note_len * 0.90)
        ramp = int(0.002 * sample_rate)

        phase = 0.0
        phase_inc = TWO_PI * freq / sample_rate

        for i in range(min(gate_samples, total_samples - start_idx)):
            sq = 1.0 if math.sin(phase) >= 0.0 else -1.0
            phase += phase_inc

            env = 1.0
            if i < ramp:
                env = i / ramp
            elif i > gate_samples - ramp:
                env = (gate_samples - i) / ramp

            mix[start_idx + i] += sq * 0.6 * env

    max_peak = max(abs(s) for s in mix) if mix else 1.0
    if max_peak > 0:
        gain = 0.8 / max_peak
        mix = [s * gain for s in mix]

    return mix, mix


# ==============================================================================
# 2. File Conversion Utilities
# ==============================================================================

def write_wav(filename, left, right, sample_rate=SAMPLE_RATE):
    """Writes 16-bit stereo PCM WAV file."""
    n_samples = len(left)
    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(2)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)

        frames = bytearray()
        for i in range(n_samples):
            l_val = max(-32767, min(32767, int(left[i] * 32767.0)))
            r_val = max(-32767, min(32767, int(right[i] * 32767.0)))
            frames.extend(struct.pack('<hh', l_val, r_val))

        wav_file.writeframes(frames)
    print(f"  [WAV] Created: {filename} ({n_samples/sample_rate:.2f}s)")


def convert_audio(wav_path, output_dir, base_name):
    """Converts WAV to MP3, M4A, CAF, OGG."""
    mp3_path = os.path.join(output_dir, f"{base_name}.mp3")
    m4a_path = os.path.join(output_dir, f"{base_name}.m4a")
    caf_path = os.path.join(output_dir, f"{base_name}.caf")
    ogg_path = os.path.join(output_dir, f"{base_name}.ogg")

    # MP3 (Android & Web)
    subprocess.run(["ffmpeg", "-y", "-i", wav_path, "-codec:a", "libmp3lame", "-q:a", "2", mp3_path],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if os.path.exists(mp3_path):
        print(f"  [MP3] Created: {mp3_path}")

    # M4A / AAC
    subprocess.run(["ffmpeg", "-y", "-i", wav_path, "-c:a", "aac", "-b:a", "192k", m4a_path],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if os.path.exists(m4a_path):
        print(f"  [M4A] Created: {m4a_path}")

    # CAF (Apple CoreAudio Format)
    caf_success = False
    try:
        res = subprocess.run(["afconvert", "-f", "caff", "-d", "LEI16", wav_path, caf_path],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0 and os.path.exists(caf_path) and os.path.getsize(caf_path) > 0:
            caf_success = True
    except Exception:
        pass
    if not caf_success:
        subprocess.run(["ffmpeg", "-y", "-i", wav_path, "-c:a", "pcm_s16le", caf_path],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if os.path.exists(caf_path) and os.path.getsize(caf_path) > 0:
        print(f"  [CAF] Created: {caf_path}")

    # OGG / Opus
    subprocess.run(["ffmpeg", "-y", "-i", wav_path, "-c:a", "libopus", "-b:a", "128k", ogg_path],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if os.path.exists(ogg_path):
        print(f"  [OGG] Created: {ogg_path}")


# ==============================================================================
# 3. Dedicated Chirpy Sound Suite
# ==============================================================================

CHIRPY_SUITE = {
    # 1. Chirpy //\ Flagship Notification Sound
    "chirpy": {
        "title": "Chirpy //\\ (Notification Sound)",
        "description": "The official Meshtastic notification sound. A friendly vocalization from Chirpy, the anthropomorphic radio node mascot, embodying the //\\ (Up, Up, Down) logo and LoRa CSS syncword pattern.",
        "bpm": 180,
        "synth_fn": synth_chirpy_notification,
        "score": [
            # Stroke 1: /
            ("c#6", 0.125), ("f#6", 0.125), ("p", 0.0625),
            # Stroke 2: /
            ("a#6", 0.125), ("f#7", 0.25),  ("p", 0.0625),
            # Stroke 3: \
            ("c#7", 0.125), ("a#6", 0.125), ("f#6", 0.50),
        ],
        "rtttl": "Chirpy:d=32,o=6,b=180:c#,f#,p,a#,16f#7,p,c#7,a#,8f#"
    },

    # 2. Chirpy Song Ringtone
    "chirpy_ringtone": {
        "title": "Chirpy Song (Ringtone)",
        "description": "Full 4-bar looping musical ringtone based on Chirpy the node's //\\ theme. For incoming calls and node external buzzer notifications.",
        "bpm": 160,
        "synth_fn": synth_chirpy_ringtone,
        "score": [
            # Bar 1: //\ Call
            ("c#6", 0.125), ("f#6", 0.125), ("p", 0.0625),
            ("a#6", 0.125), ("f#7", 0.25),  ("p", 0.0625),
            ("c#7", 0.125), ("f#6", 0.50),  ("p", 0.25),
            # Bar 2: Answer
            ("f#6", 0.25),  ("c#7", 0.25),  ("d#7", 0.25), ("c#7", 0.50), ("p", 0.25),
            # Bar 3: Mesh Hops
            ("a#6", 0.25),  ("c#7", 0.25),  ("f#7", 0.25), ("d#7", 0.25), ("c#7", 0.50), ("p", 0.25),
            # Bar 4: //\ Finale
            ("c#6", 0.125), ("f#6", 0.125), ("a#6", 0.125), ("c#7", 0.125), ("f#7", 1.00),
        ],
        "rtttl": "ChirpySong:d=16,o=6,b=160:32c#,32f#,32p,32a#,16f#7,32p,32c#7,8f#,4p,f#,c#7,d#7,8c#7,4p,a#,c#7,f#7,d#7,8c#7,4p,32c#,32f#,32a#,32c#7,4f#7"
    },

    # 3. Chirpy Quick // (Micro ACK Chirp)
    "chirpy_ack": {
        "title": "Chirpy // (Micro Chirp & ACK)",
        "description": "A compact two-stroke upward LoRa chirp (//) for packet delivery receipts, tapbacks, and message reactions.",
        "bpm": 200,
        "synth_fn": synth_chirpy_ack,
        "score": [
            ("c#6", 0.125), ("f#6", 0.125), ("p", 0.0625),
            ("a#6", 0.125), ("f#7", 0.35),
        ],
        "rtttl": "Chirp2:d=32,o=6,b=200:c#,f#,p,a#,16f#7"
    }
}


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(base_dir, "dist")
    rtttl_dir = os.path.join(base_dir, "rtttl")
    sim_dir = os.path.join(base_dir, "dist", "piezo_simulated")
    os.makedirs(dist_dir, exist_ok=True)
    os.makedirs(rtttl_dir, exist_ok=True)
    os.makedirs(sim_dir, exist_ok=True)

    print("=========================================================")
    print("      Meshtastic Chirpy (The Node) Audio Suite           ")
    print("=========================================================\n")

    manifest = []

    for key, item in CHIRPY_SUITE.items():
        print(f"Generating '{key}': {item['title']}...")
        bpm = item["bpm"]
        score = item["score"]
        rtttl = item["rtttl"]

        # 1. High-fidelity Studio Master
        l_samples, r_samples = item["synth_fn"](sample_rate=SAMPLE_RATE)
        wav_path = os.path.join(dist_dir, f"{key}.wav")
        write_wav(wav_path, l_samples, r_samples)
        convert_audio(wav_path, dist_dir, key)

        # 2. Hardware Piezo Simulation
        piezo_l, piezo_r = render_piezo_simulation(score, bpm)
        piezo_wav = os.path.join(sim_dir, f"{key}_piezo.wav")
        write_wav(piezo_wav, piezo_l, piezo_r)

        # 3. Save RTTTL file
        rtttl_path = os.path.join(rtttl_dir, f"{key}.rtttl")
        with open(rtttl_path, "w") as f:
            f.write(rtttl + "\n")
        print(f"  [RTTTL] String ({len(rtttl)} bytes, max 230):")
        print(f"          \"{rtttl}\"")
        print(f"  [RTTTL] File: {rtttl_path}\n")

        manifest.append({
            "id": key,
            "title": item["title"],
            "description": item["description"],
            "bpm": bpm,
            "rtttl": rtttl,
            "rtttl_bytes": len(rtttl),
            "files": {
                "wav": f"dist/{key}.wav",
                "mp3": f"dist/{key}.mp3",
                "m4a": f"dist/{key}.m4a",
                "caf": f"dist/{key}.caf",
                "ogg": f"dist/{key}.ogg",
                "rtttl": f"rtttl/{key}.rtttl",
                "piezo_wav": f"dist/piezo_simulated/{key}_piezo.wav"
            }
        })

    # Save manifest.json
    manifest_path = os.path.join(base_dir, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"Successfully generated Chirpy sound assets and manifest at {manifest_path}!")


if __name__ == "__main__":
    main()
