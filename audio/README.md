# Meshtastic Chirpy //\ Audio &amp; Ringtone Suite

This directory contains the official specification, synthesis engine, and production assets for the **Meshtastic Chirpy Sound Suite**.

It defines an auditory language centered exclusively on **Chirpy** (Meshtastic's anthropomorphic radio node mascot) and the iconic **//\** pattern:
- **Mobile & Desktop Client Apps** (Android, iOS, macOS, Web, Linux) with high-fidelity, studio-quality chimes.
- **Hardware Devices & Radio Nodes** (ESP32, nRF52, RP2040, STM32) with 1:1 hardware RTTTL ringtone strings for piezo buzzers and I2S speakers.

---

## 1. Mascot, Logo, and LoRa Physics: The //\ Motif

**Chirpy is not a bird**—he is an **anthropomorphic Meshtastic radio node** (the friendly green node with an antenna, OLED screen eyes, hands, and the `//\` logo on his chest).

His name and voice originate directly from **LoRa Chirp Spread Spectrum (CSS)** radio physics:
1. **The Visual Brand**: The Meshtastic logo on Chirpy's chest consists of three diagonal strokes: `//\` (two ascending mountain paths reaching a summit, followed by a resolving downward slope).
2. **LoRa Radio Modulation**: In LoRa CSS, packet preambles begin with rising frequency sweeps (upchirps: `/`), while start-of-frame delimiters and framing are denoted by descending frequency sweeps (downchirps: `\`).
3. **The Auditory Gesture**:
   - **Stroke 1 (`/`)**: Upward greeting RF chirp ($C\sharp 6 \to F\sharp 6$, 1108 Hz $\to$ 1568 Hz).
   - **Stroke 2 (`/`)**: Higher upward RF chirp climbing to the crystalline summit ($A\sharp 6 \to F\sharp 7$, 1760 Hz $\to$ 3136 Hz).
   - **Stroke 3 (`\`)**: Cascading downward resolution settling at home ($F\sharp 7 \to C\sharp 7 \to F\sharp 6$, 3136 Hz $\to$ 1480 Hz).

Underneath the tactile synthesizer sweeps, physical acoustic bell chimes resonate on the anchor frequencies of the **$F\sharp$ Major triad** ($F\sharp 6, A\sharp 6, C\sharp 7, F\sharp 7$), linking directly back to the classic firmware boot melody (`firmware/src/buzz/buzz.cpp`).

---

## 2. The Chirpy Sound Suite

| Sound ID | Display Name | Role | Duration | RTTTL Bytes (Max 230) |
| :--- | :--- | :--- | :--- | :--- |
| **`chirpy`** | **Chirpy //\\ (Flagship)** | Primary message notification (DMs, Channels) | 0.85s | **51 B** |
| **`chirpy_ringtone`** | **Chirpy Song (Ringtone)** | Looping ringtone, incoming calls, nag alerts | 3.60s | **135 B** |
| **`chirpy_ack`** | **Chirpy // (Micro Chirp)** | Discrete ACK, reactions, quick tapback | 0.50s | **38 B** |

---

## 3. RTTTL String Reference

All RTTTL strings conform strictly to the Nokia RTTTL specification and the firmware parser (`NRF52RtttlPlayer.cpp` and `NonBlockingRTTTL`), fitting safely within the 230-character protobuf limit:

#### 1. Chirpy //\ (Notification Sound)
```text
Chirpy:d=32,o=6,b=180:c#,f#,p,a#,16f#7,p,c#7,a#,8f#
```
*Cadence: Rising burst `/` &rarr; peak burst `/` &rarr; resolving cascade `\`.*

#### 2. Chirpy Song (Ringtone)
```text
ChirpySong:d=16,o=6,b=160:32c#,32f#,32p,32a#,16f#7,32p,32c#7,8f#,4p,f#,c#7,d#7,8c#7,4p,a#,c#7,f#7,d#7,8c#7,4p,32c#,32f#,32a#,32c#7,4f#7
```
*Cadence: 4-bar looping musical song based on the Chirpy //\ theme.*

#### 3. Chirpy // (Micro Chirp & ACK)
```text
Chirp2:d=32,o=6,b=200:c#,f#,p,a#,16f#7
```
*Cadence: Two rapid ascending chirrups `//`.*

---

## 4. Directory Layout &amp; Asset Formats

```
design/audio/
├── README.md               # Architecture, specification, and integration guide
├── index.html              # Interactive audition web player & Web Audio RTTTL synth
├── manifest.json           # Machine-readable asset metadata
├── generate_sounds.py      # Standalone Python audio synthesis script
├── dist/                   # Production-ready audio files
│   ├── chirpy.*            # Flagship notification (WAV, MP3, CAF, M4A, OGG)
│   ├── chirpy_ringtone.*   # Looping ringtone (WAV, MP3, CAF, M4A, OGG)
│   ├── chirpy_ack.*        # Micro chirp ACK (WAV, MP3, CAF, M4A, OGG)
│   └── piezo_simulated/    # Simulated hardware buzzer audio for bench previews
└── rtttl/                  # Raw .rtttl text files for hardware upload
    ├── chirpy.rtttl
    ├── chirpy_ringtone.rtttl
    └── chirpy_ack.rtttl
```

---

## 5. Platform Integration Guide

### Android Client
1. Place audio assets in `core/resources/src/androidMain/res/raw/`:
   - `chirpy.mp3`
   - `chirpy_ringtone.mp3`
   - `chirpy_ack.mp3`
2. In `NotificationChannelSpec.kt`:
   ```kotlin
   DirectMessages,
   Broadcasts -> {
       val sound = "$SCHEME_ANDROID_RESOURCE://${context.packageName}/${raw.chirpy}".toUri()
       channel.setSound(sound, soundAttributes(AudioAttributes.USAGE_NOTIFICATION))
   }
   Reactions -> {
       val sound = "$SCHEME_ANDROID_RESOURCE://${context.packageName}/${raw.chirpy_ack}".toUri()
       channel.setSound(sound, soundAttributes(AudioAttributes.USAGE_NOTIFICATION))
   }
   ```
3. Hardware Preview: In `ExternalNotificationConfigScreen.android.kt`, users can preview or import `rtttl/chirpy.rtttl` via Android's native `MediaPlayer`.

### Apple Client (iOS / macOS)
1. Add `chirpy.caf` and `chirpy_ack.caf` to the app bundle (`Meshtastic/Resources/Sounds/`).
2. In `LocalNotificationManager.swift`:
   ```swift
   if notification.isReaction {
       content.sound = UNNotificationSound(named: UNNotificationSoundName("chirpy_ack.caf"))
   } else {
       content.sound = UNNotificationSound(named: UNNotificationSoundName("chirpy.caf"))
   }
   ```

### Meshtastic Firmware & CLI
To configure the default ringtone in `userPrefs.jsonc`:
```jsonc
"USERPREFS_RINGTONE_RTTTL": "ChirpySong:d=16,o=6,b=160:32c#,32f#,32p,32a#,16f#7,32p,32c#7,8f#,4p,f#,c#7,d#7,8c#7,4p,a#,c#7,f#7,d#7,8c#7,4p,32c#,32f#,32a#,32c#7,4f#7"
```
Or set Chirpy on any live device via CLI:
```bash
meshtastic --set-ringtone "Chirpy:d=32,o=6,b=180:c#,f#,p,a#,16f#7,p,c#7,a#,8f#"
meshtastic --play-ringtone
```
