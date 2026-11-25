# Chirpy notification sounds

Notification sounds for the Meshtastic client apps and for devices. They are named for Chirpy, the Meshtastic mascot.

Each sound is one RTTTL string. A device plays the string on its buzzer or I2S speaker. `generate_sounds.py` parses the same string to render the phone and desktop files, so both follow the same notes at the same times. Everything is in F# major, the key of the firmware boot melody (F#, A#, C#).

## What they draw from

The sounds draw from three things: the shape of the logo (`logo/logo.svg`), the chirps a LoRa radio sends, and the Chirpy art (`chirpy/chirpy.png`).

The logo shape is literal. The mark is a `/` on its own, then a joined `/\`, with all three strokes the same height and angle. `chirpy` is a rise from F#6 to F#7, a short gap, the same rise again, and a fall straight from the top back to F#6 with no gap at the peak. In the phone file the three sweeps cover the same octave in the same 150 ms. In RTTTL each stroke is the four notes F#, A#, C#, F#, with the top note shared between the second rise and the fall.

The LoRa part is inspired by, not a model of, the radio. A LoRa packet opens with identical rising chirps and its start-of-frame marker is falling chirps, and a chirp moves through frequency at a constant rate. The sweeps in the phone files are straight lines in frequency for that reason. `dist/alt/chirpy_syncword.wav` goes one step further: its two rising sweeps start part of the way up, run off the top and wrap around to finish where they started, the way LoRa sync symbols are shifted chirps. The starting points are 2/16 and 11/16 of the sweep, after the two digits of the Meshtastic sync word `0x2b`. That is a nod to the number. It does not encode it and is not how a radio places its sync symbols. It is an alternate, not the default, because a wrapped sweep does not end at the peak, so the second stroke can no longer join the fall the way the logo does.

The last note of `chirpy` in the phone file has a small zigzag in pitch, 6 cents either way for three cycles, after the zigzag antenna in the art.

## The sounds

`chirpy` is the message sound.

`chirpy_ack` is for delivery receipts and reactions. It is one rising stroke from A#6 to F#7, so it starts on a different note from `chirpy`. It is for client apps only. Firmware has no slot for a second sound, and the RTTTL string is here as the definition of the sound and for reference.

`chirpy_ringtone` is a longer four-phrase tune that opens with `chirpy`. It is an optional alert for someone who wants more than the short sound. Its file is exactly as long as its RTTTL string, including the closing rest, so it loops.

The table, the strings and the measurements below are written by `generate_sounds.py`. Don't edit them by hand.

<!-- BEGIN GENERATED: generate_sounds.py -->
| Sound | Use | Phone file | Device RTTTL | RTTTL bytes |
| --- | --- | --- | --- | --- |
| `chirpy` | Message notification. Recommended device default. | 1.23 s | 0.75 s, then 1.20 s rest | 66 |
| `chirpy_ack` | Delivery receipt or reaction. Client apps only. | 0.48 s | 0.20 s (reference only) | 37 |
| `chirpy_ringtone` | Optional longer alert. Loops. | 5.00 s | 3.80 s, then 1.20 s rest | 170 |

`chirpy`

```text
Chirpy:d=32,o=6,b=150:f#,a#,c#7,f#7,p,f#,a#,c#7,f#7,c#7,a#,8f#,2p.
```

`chirpy_ack`

```text
ChirpyAck:d=32,o=6,b=150:a#,c#7,16f#7
```

`chirpy_ringtone`

```text
ChirpySong:d=16,o=6,b=150:32f#,32a#,32c#7,32f#7,32p,32f#,32a#,32c#7,32f#7,32c#7,32a#,8f#,8p,32p,f#,c#7,d#7,8c#7,4p,p,a#,c#7,f#7,d#7,8c#7,4p,32c#,32f#,32a#,32c#7,4f#7.,2p.
```

Measured with `ffmpeg -af ebur128=peak=true` on the WAV files:

| File | Length | Integrated | Momentary max | True peak |
| --- | --- | --- | --- | --- |
| `dist/chirpy.wav` | 1.23 s | -16.0 LUFS | -14.5 LUFS | -11.8 dBTP |
| `dist/piezo_simulated/chirpy_piezo.wav` | 1.95 s | -16.0 LUFS | -14.4 LUFS | -18.0 dBTP |
| `dist/alt/chirpy_syncword.wav` | 1.23 s | -16.0 LUFS | -14.4 LUFS | -11.5 dBTP |
| `dist/chirpy_ack.wav` | 0.48 s | -16.0 LUFS | -16.0 LUFS | -10.0 dBTP |
| `dist/piezo_simulated/chirpy_ack_piezo.wav` | 0.25 s | n/a | -16.0 LUFS | -17.0 dBTP |
| `dist/chirpy_ringtone.wav` | 5.00 s | -16.0 LUFS | -12.4 LUFS | -9.7 dBTP |
| `dist/piezo_simulated/chirpy_ringtone_piezo.wav` | 5.00 s | -16.0 LUFS | -14.1 LUFS | -18.4 dBTP |
<!-- END GENERATED -->

The phone file for `chirpy` leaves off the string's closing rest and runs until the bell tail has faded. The piezo previews keep the rest.

## Files

- `dist/<id>.wav`, `.caf`, `.mp3`, `.m4a`, `.ogg` are the phone and desktop sounds. WAV and CAF are 48 kHz 16-bit stereo PCM. MP3, AAC and Opus add encoder padding, so use WAV or CAF where a seamless loop matters.
- `dist/alt/chirpy_syncword.wav` is the sync-word variant of `chirpy` described above. WAV only.
- `dist/piezo_simulated/<id>_piezo.wav` is a square-wave preview of the RTTTL string, for hearing roughly what a buzzer will play.
- `rtttl/<id>.rtttl` holds the string on one line.
- `manifest.json` lists every sound with its string, lengths, file sizes and measured loudness.
- `index.html` plays all of the above. Open it from disk.

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

### iOS and macOS

Add the `.caf` to the app bundle and use `UNNotificationSound(named:)`. The file has to be in the bundle (or the app's `Library/Sounds`) and under 30 seconds, or the system plays the default sound.

### Firmware

A device has one ringtone, `rtttlConfig.ringtone`. The external notification module plays it for every alert and starts it again each time it ends until the nag timeout runs out. `chirpy` is the recommended default because it is short. Its closing rest keeps the repeats apart.

Set it at build time in `userPrefs.jsonc`:

```jsonc
"USERPREFS_RINGTONE_RTTTL": "Chirpy:d=32,o=6,b=150:f#,a#,c#7,f#7,p,f#,a#,c#7,f#7,c#7,a#,8f#,2p.",
```

Or on a running device:

```sh
meshtastic --set-ringtone "Chirpy:d=32,o=6,b=150:f#,a#,c#7,f#7,p,f#,a#,c#7,f#7,c#7,a#,8f#,2p."
```

`chirpy_ringtone` can be set the same way.
