# Chirpy notification sounds

Notification sounds for the Meshtastic client apps and for devices. They are named for Chirpy, the Meshtastic mascot.

Each sound is one RTTTL string. A device plays the string on its buzzer or I2S speaker. `generate_sounds.py` parses the same string to render the phone and desktop files, so both follow the same notes at the same times. Everything is in F# major, the key of the firmware boot melody (F#, A#, C#).

## What they draw from

The sounds draw from three things: the shape of the logo (`logo/logo.svg`), the chirps a LoRa radio sends, and the Chirpy art (`chirpy/chirpy.png`).

The logo shape is literal. The mark is a `/` on its own, then a joined `/\`, with all three strokes the same height and angle. `chirpy` is a rise from F#5 to F#6, a short gap, the same rise again, and a fall straight from the top back to F#5 with no gap at the peak. In the phone file the three sweeps cover the same octave in the same 150 ms. In RTTTL each stroke is the four notes F#, A#, C#, F#, with the top note shared between the second rise and the fall.

The LoRa part is inspired by, not a model of, the radio. A LoRa packet opens with identical rising chirps and its start-of-frame marker is falling chirps, and a chirp moves through frequency at a constant rate. The sweeps in the phone files are straight lines in frequency for that reason. `dist/alt/chirpy_syncword.wav` takes the idea further and is described with the strings below.

The last note of `chirpy` in the phone file has a small zigzag in pitch, 6 cents either way for three cycles, after the zigzag antenna in the art.

Everything sits in octave 5 (740 to 1480 Hz) with a soft voice, mostly the fundamental. An octave higher measured as shrill: its energy centered near 3 kHz, where the ear is most sensitive. A piezo buzzer is louder higher up, so `o=6` is the fallback for a buzzer that is too quiet at this pitch.

## The sounds

`chirpy` is the message sound.

`chirpy_ack` is for delivery receipts and reactions. It is one rising stroke from A#5 to F#6, so it starts on a different note from `chirpy`. It is for client apps only. Firmware has no slot for a second sound, and the RTTTL string is here as the definition of the sound and for reference.

`chirpy_ringtone` is the long alert. It is the device ringtone for someone who wants a longer sound, and the suggested sound for the Android Alerts channel and for iOS critical alerts. Its file is exactly as long as its RTTTL string, including the closing rest, so it loops.

It is laid out like a LoRa frame, played with the `chirpy` stroke. Each part is one line:

- Logo: `chirpy`, note for note, so the sound is recognized first.
- Preamble: four identical rising strokes from F#5 to F#6, evenly spaced.
- Sync word: two more rising strokes, spaced like the two rises in the logo. The second runs straight into the first fall, which makes the logo's joined `/\` again.
- Start of frame: two full falls from F#6 to F#5, then a quarter of a fall that stops on D#6.
- Close: F#5 held, then a rest.

The order of the parts, the direction of the chirps in each part, and the two and a quarter falls are how a LoRa frame is built. The rest is inspired by it. A Meshtastic preamble is 16 chirps and this one is 4. The sync part stands in for the sync word and does not encode `0x2b`. A real quarter fall would stop about 1295 Hz, which is not a note in F# major, so it is rounded to D#6 (1245 Hz). Every stroke has the same span and slope as the strokes in `chirpy`.

The table, the strings and the measurements below are written by `generate_sounds.py`. Don't edit them by hand.

<!-- BEGIN GENERATED: generate_sounds.py -->
| Sound | Use | Phone file | Device RTTTL | RTTTL bytes |
| --- | --- | --- | --- | --- |
| `chirpy` | Message notification. Recommended device default. | 1.23 s | 0.75 s, then 1.20 s rest | 66 |
| `chirpy_ack` | Delivery receipt or reaction. Client apps only. | 0.48 s | 0.20 s (reference only) | 37 |
| `chirpy_ringtone` | The long alert: a longer device ringtone, and the suggested sound for client alert channels. Loops. | 4.70 s | 3.90 s, then 0.80 s rest | 223 |

`chirpy`

```text
Chirpy:d=32,o=5,b=150:f#,a#,c#6,f#6,p,f#,a#,c#6,f#6,c#6,a#,8f#,2p.
```

`chirpy_ack`

```text
ChirpyAck:d=32,o=5,b=150:a#,c#6,16f#6
```

`chirpy_ringtone`

```text
ChirpyRing:d=32,o=5,b=150:f#,a#,c#6,f#6,p,f#,a#,c#6,f#6,c#6,a#,8f#,8p,p,f#,a#,c#6,f#6,16p,f#,a#,c#6,f#6,16p,f#,a#,c#6,f#6,16p,f#,a#,c#6,f#6,16p,f#,a#,c#6,f#6,p,f#,a#,c#6,f#6,c#6,a#,f#,16p,f#6,c#6,a#,f#,16p,f#6,d#6,8p,4f#,2p
```

`dist/alt/chirpy_syncword.wav`: Not the default. The rising strokes start 2/16 and 11/16 of the way up and wrap around, like a LoRa radio's sync word chirps, as a nod to Meshtastic's `0x2b` (it doesn't encode it). A wrapped stroke can't run into the fall, so it loses the logo's joined peak.

The parts of `chirpy_ringtone`:

| Part | Starts | Lasts | Notes | What it is |
| --- | --- | --- | --- | --- |
| Logo | 0.00 s | 1.00 s | `f#,a#,c#6,f#6,p,f#,a#,c#6,f#6,c#6,a#,8f#,8p,p` | `chirpy`, note for note. |
| Preamble | 1.00 s | 1.20 s | `f#,a#,c#6,f#6,16p,f#,a#,c#6,f#6,16p,f#,a#,c#6,f#6,16p,f#,a#,c#6,f#6,16p` | Four identical rising strokes, evenly spaced. |
| Sync word | 2.20 s | 0.45 s | `f#,a#,c#6,f#6,p,f#,a#,c#6,f#6` | Two more rising strokes, spaced like the logo's. The second runs into the first fall. |
| Start of frame | 2.65 s | 0.85 s | `c#6,a#,f#,16p,f#6,c#6,a#,f#,16p,f#6,d#6,8p` | Two full falls and a quarter of one, which stops on D#6. |
| Close | 3.50 s | 1.20 s | `4f#,2p` | F#5 held, then a rest before the loop repeats. |

Haptics, from the same strokes:

| Sound | On/off pattern (ms: wait, on, off, on, ...) | Core Haptics |
| --- | --- | --- |
| `chirpy` | `25, 150, 100, 300` | `haptics/chirpy.ahap` |
| `chirpy_ack` | `25, 100` | `haptics/chirpy_ack.ahap` |
| `chirpy_ringtone` | `25, 150, 100, 300, 450, 150, 150, 150, 150, 150, 150, 150, 150, 150, 100, 300, 150, 150, 150, 50, 225, 200` | `haptics/chirpy_ringtone.ahap` |

Measured with `ffmpeg -af ebur128=peak=true` on the WAV files:

| File | Length | Integrated | Momentary max | True peak |
| --- | --- | --- | --- | --- |
| `dist/chirpy.wav` | 1.23 s | -16.0 LUFS | -14.0 LUFS | -9.3 dBTP |
| `dist/piezo_simulated/chirpy_piezo.wav` | 1.95 s | -16.0 LUFS | -14.4 LUFS | -16.6 dBTP |
| `dist/alt/chirpy_syncword.wav` | 1.23 s | -16.0 LUFS | -14.1 LUFS | -10.3 dBTP |
| `dist/chirpy_ack.wav` | 0.48 s | -16.0 LUFS | -16.0 LUFS | -9.4 dBTP |
| `dist/piezo_simulated/chirpy_ack_piezo.wav` | 0.25 s | n/a | -16.0 LUFS | -15.6 dBTP |
| `dist/chirpy_ringtone.wav` | 4.70 s | -16.0 LUFS | -13.2 LUFS | -8.5 dBTP |
| `dist/piezo_simulated/chirpy_ringtone_piezo.wav` | 4.70 s | -16.0 LUFS | -14.3 LUFS | -16.5 dBTP |
<!-- END GENERATED -->

The phone file for `chirpy` leaves off the string's closing rest and runs until the bell tail has faded. The piezo previews keep the rest.

## Files

- `dist/<id>.wav`, `.caf`, `.mp3`, `.m4a`, `.ogg` are the phone and desktop sounds. WAV and CAF are 48 kHz 16-bit stereo PCM. MP3, AAC and Opus add encoder padding, so use WAV or CAF where a seamless loop matters.
- `dist/alt/chirpy_syncword.wav` is the alternate take on `chirpy` described under the strings above. WAV only.
- `dist/piezo_simulated/<id>_piezo.wav` is a square-wave preview of the RTTTL string, for hearing roughly what a buzzer will play.
- `rtttl/<id>.rtttl` holds the string on one line.
- `haptics/<id>.ahap` is the vibration for each sound as a Core Haptics pattern.
- `manifest.json` lists every sound with its string, lengths, file sizes, measured loudness and haptic patterns.
- `index.html` plays all of the above. Open it from disk. Its Vibrate button works where the browser supports `navigator.vibrate`, which is Chrome on Android.

## Haptics

Each sound has a vibration made from the same strokes, so the `//\` shape can be felt as well as heard. A motor can't follow pitch, so each stroke is one buzz and the pitch becomes intensity: a rise gets stronger, a fall gets weaker. `chirpy` is a 150 ms buzz, a 100 ms gap, then a 300 ms buzz that swells and fades. Strokes closer than 60 ms are merged, since a motor can't stop and restart faster than that.

There are three forms, all in `manifest.json` under `haptics`:

- `pattern_ms` is on and off only: wait, on, off, on, and so on. It fits Android's `NotificationChannel.setVibrationPattern` and a plain vibration motor on a GPIO pin.
- `waveform_timings_ms` and `waveform_amplitudes` add strength in 25 ms steps, for Android's `VibrationEffect.createWaveform` inside the app.
- `haptics/<id>.ahap` adds intensity and sharpness curves that follow the pitch, for Core Haptics on iOS inside the app.

None of the clients or firmware use these yet. Possible follow-ups:

- Android could set `pattern_ms` on its notification channels. As with sounds, a channel's vibration is fixed when the channel is created, so this needs new channel IDs.
- Android could play the waveform for in-app events.
- iOS can't set a custom vibration on a notification, which always uses the system's. The `.ahap` files are for in-app events only.
- Firmware could play `pattern_ms` on the vibration motor instead of toggling it at a fixed rate, and a sequence of DRV2605 ramp effects on boards with that driver.

These timings come from the sound. On a Pixel 6a and a Pixel 9 Pro they were preferred over two alternatives: wider ramps from near zero at twice the length, and Android's built-in rise and fall primitives. The ramps are subtle on both phones; a pattern's rhythm reads more clearly than its intensity.

## Loudness

Every file is set to -16 LUFS integrated, with true peak under -1 dBTP. `chirpy_ack_piezo.wav` is shorter than the 400 ms block an integrated reading needs, so it is set to the same momentary maximum as `chirpy_ack.wav` instead. Momentary maximum is measured with half a second of silence appended, so a short sound still fills the window. Every file ends in silence.

## Regenerating

```sh
python3 generate_sounds.py
```

It needs Python 3 and ffmpeg, and nothing else. It deletes and rewrites `dist/` and `rtttl/`, then rewrites `manifest.json` and the generated parts of this file and `index.html`. To change a sound, edit its RTTTL string in `SUITE` and run it again.

The strings stay within what all three firmware players read the same way: a `d=,o=,b=` header in that order, octaves 4 to 7, a tempo that divides 60000, a dot only after the octave digit or on a note without one, and 230 bytes at most.

## Using them

### Android

Put the file in `res/raw` and set it with `NotificationChannel.setSound`. A channel's sound is fixed when the channel is created, so an existing install keeps its old sound. Shipping a changed sound needs new channel IDs, with the old channels deleted.

The Alerts channel plays `meshtastic_alert` with `AudioAttributes.USAGE_ALARM`. `chirpy_ringtone` is the suggested replacement for it.

### iOS and macOS

Add the `.caf` to the app bundle and use `UNNotificationSound(named:)`. The file has to be in the bundle (or the app's `Library/Sounds`) and under 30 seconds, or the system plays the default sound.

Critical alerts use `UNNotificationSound.defaultCritical`. `chirpy_ringtone.caf` with `UNNotificationSound.criticalSoundNamed(_:)` is the suggested replacement.

### Firmware

A device has one ringtone, `rtttlConfig.ringtone`. The external notification module plays it for every alert and starts it again each time it ends until the nag timeout runs out. `chirpy` is the recommended default because it is short. Its closing rest keeps the repeats apart.

Set it at build time in `userPrefs.jsonc`:

```jsonc
"USERPREFS_RINGTONE_RTTTL": "Chirpy:d=32,o=5,b=150:f#,a#,c#6,f#6,p,f#,a#,c#6,f#6,c#6,a#,8f#,2p.",
```

Or on a running device:

```sh
meshtastic --set-ringtone "Chirpy:d=32,o=5,b=150:f#,a#,c#6,f#6,p,f#,a#,c#6,f#6,c#6,a#,8f#,2p."
```

`chirpy_ringtone` can be set the same way, for someone who wants a longer ringtone.
