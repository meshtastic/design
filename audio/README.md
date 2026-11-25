# Chirpy notification sounds

Notification sounds for the Meshtastic client apps and for devices. They are named for Chirpy, the Meshtastic mascot, and follow the shape of the `//\` logo: two rising strokes, then a falling one.

Each sound is one RTTTL string. A device plays the string on its buzzer or I2S speaker. `generate_sounds.py` parses the same string to render the phone and desktop files, so both play the same notes at the same times. Everything is in F# major, the key of the firmware boot melody (F#, A#, C#).

## The sounds

`chirpy` is the message sound. Its strokes are C#6 to F#6, A#6 to F#7, then C#7, A#6, F#6.

`chirpy_ack` is for delivery receipts and reactions. It is one rising stroke, A#6, C#7, F#7, so it starts higher than `chirpy` and can be told apart from the first note. It is for client apps only. Firmware has no slot for a second sound, and the RTTTL string is here as the definition of the sound and for reference.

`chirpy_ringtone` is a longer four-phrase tune that opens with `chirpy`. It is an optional alert for someone who wants more than the short sound. Its file is exactly as long as its RTTTL string, including the closing rest, so it loops.

The table, the strings and the measurements below are written by `generate_sounds.py`. Don't edit them by hand.

<!-- BEGIN GENERATED: generate_sounds.py -->
| Sound | Use | Phone file | Device RTTTL | RTTTL bytes |
| --- | --- | --- | --- | --- |
| `chirpy` | Message notification. Recommended device default. | 1.11 s | 0.65 s, then 1.20 s rest | 55 |
| `chirpy_ack` | Delivery receipt or reaction. Client apps only. | 0.46 s | 0.20 s (reference only) | 37 |
| `chirpy_ringtone` | Optional longer alert. Loops. | 5.00 s | 3.80 s, then 1.20 s rest | 150 |

`chirpy`

```text
Chirpy:d=32,o=6,b=150:c#,f#,p,a#,16f#7,p,c#7,a#,8f#,2p.
```

`chirpy_ack`

```text
ChirpyAck:d=32,o=6,b=150:a#,c#7,16f#7
```

`chirpy_ringtone`

```text
ChirpySong:d=16,o=6,b=150:32c#,32f#,32p,32a#,f#7,32p,32c#7,32a#,8f#,8p.,32p,f#,c#7,d#7,8c#7,4p,p,a#,c#7,f#7,d#7,8c#7,4p,32c#,32f#,32a#,32c#7,4f#7.,2p.
```

Measured with `ffmpeg -af ebur128=peak=true` on the WAV files:

| File | Length | Integrated | Momentary max | True peak |
| --- | --- | --- | --- | --- |
| `dist/chirpy.wav` | 1.11 s | -16.0 LUFS | -14.3 LUFS | -9.8 dBTP |
| `dist/piezo_simulated/chirpy_piezo.wav` | 1.85 s | -16.0 LUFS | -14.3 LUFS | -17.3 dBTP |
| `dist/chirpy_ack.wav` | 0.46 s | -16.0 LUFS | -16.0 LUFS | -9.9 dBTP |
| `dist/piezo_simulated/chirpy_ack_piezo.wav` | 0.25 s | n/a | -16.0 LUFS | -17.0 dBTP |
| `dist/chirpy_ringtone.wav` | 5.00 s | -16.0 LUFS | -11.6 LUFS | -8.9 dBTP |
| `dist/piezo_simulated/chirpy_ringtone_piezo.wav` | 5.00 s | -16.0 LUFS | -13.8 LUFS | -18.1 dBTP |
<!-- END GENERATED -->

The phone file for `chirpy` leaves off the string's closing rest and runs until the bell tail has faded. The piezo previews keep the rest.

## Files

- `dist/<id>.wav`, `.caf`, `.mp3`, `.m4a`, `.ogg` are the phone and desktop sounds. WAV and CAF are 48 kHz 16-bit stereo PCM. MP3, AAC and Opus add encoder padding, so use WAV or CAF where a seamless loop matters.
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
"USERPREFS_RINGTONE_RTTTL": "Chirpy:d=32,o=6,b=150:c#,f#,p,a#,16f#7,p,c#7,a#,8f#,2p.",
```

Or on a running device:

```sh
meshtastic --set-ringtone "Chirpy:d=32,o=6,b=150:c#,f#,p,a#,16f#7,p,c#7,a#,8f#,2p."
```

`chirpy_ringtone` can be set the same way.
