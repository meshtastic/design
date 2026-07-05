# Cross-Platform Settings Validation Matrix

**Status:** Reference Document  
**Sources:** [settings-validation-android.md](data/settings-validation-android.md) · [settings-validation-apple.md](data/settings-validation-apple.md)  
**See also:** [deprecated-fields-audit.md](deprecated-fields-audit.md)  
**Last Updated:** 2026-07-04

> **Purpose:** This document cross-references the Android and Apple settings validation references to surface missing screens, missing fields, and constraint mismatches that should be aligned.
>
> **Verification (2026-07-04):** Claims re-verified against Apple `main` (2026-07-04) and Android `main` (2026-07-02) source. Corrections this pass: Apple `adc_multiplier_override` is already relaxed to `> 0.0` (PR [#1866](https://github.com/meshtastic/Meshtastic-Apple/pull/1866), resolves #1865); Traffic Management flipped to Apple-only (Android removed its screen); the TAK "enabled toggle" attribution was wrong (neither platform has one); `compass_orientation` enum values and the LoRa `bandwidth` enum name corrected.

---

## 1. Settings Screen Coverage

### Config Screens

| Screen | Android | Apple | Notes |
|--------|---------|-------|-------|
| User Config | ✅ | ✅ | — |
| Device Config | ✅ | ✅ | — |
| Position Config | ✅ | ✅ | — |
| Power Config | ✅ | ✅ | — |
| Network Config | ✅ | ✅ | Apple now exposes all fields: Apple PR [#1849](https://github.com/meshtastic/Meshtastic-Apple/pull/1849) added ntp_server, rsyslog_server, static IPv4; Android PR [#5549](https://github.com/meshtastic/Meshtastic-Android/pull/5549) renamed UDP toggle label |
| Display Config | ✅ | ✅ | `compass_orientation` picker added to Apple via PR [#1847](https://github.com/meshtastic/Meshtastic-Apple/pull/1847); deprecated `compass_north_top` now gated on firmware version |
| LoRa Config | ✅ | ✅ | Several constraint mismatches — see §3 |
| Bluetooth Config | ✅ | ✅ | ✅ Both platforms fixed: Apple PR [#1830](https://github.com/meshtastic/Meshtastic-Apple/pull/1830); Android PR [#5477](https://github.com/meshtastic/Meshtastic-Android/pull/5477) |
| Security Config | ✅ | ✅ | `is_managed` guard fixed in Apple PR [#1833](https://github.com/meshtastic/Meshtastic-Apple/pull/1833); `admin_channel_enabled` removed from Android via PR [#5547](https://github.com/meshtastic/Meshtastic-Android/pull/5547) |

### Module Config Screens

| Screen | Android | Apple | Notes |
|--------|---------|-------|-------|
| MQTT | ⚠️ | ✅ | Apple byte limits fixed in PR [#1833](https://github.com/meshtastic/Meshtastic-Apple/pull/1833); Android `password` still enforces 63 bytes (should be 31) |
| Telemetry | ✅ | ✅ | Air quality fields (`air_quality_enabled`, `air_quality_interval`) added to Apple via PR [#1848](https://github.com/meshtastic/Meshtastic-Apple/pull/1848) |
| Canned Messages | ✅ | ✅ | Byte limit aligned — fixed in Apple PR [#1833](https://github.com/meshtastic/Meshtastic-Apple/pull/1833) |
| Detection Sensor | ✅ | ✅ | Apple has sensor/client role picker |
| External Notification | ✅ | ✅ | `ringtone` byte limit fixed in Apple PR [#1833](https://github.com/meshtastic/Meshtastic-Apple/pull/1833); screen placement differs (Android: inline, Apple: separate RTTTL screen) |
| Store & Forward | ✅ | ✅ | Android: free-form inputs. Apple: fixed pickers |
| Serial | ✅ | ✅ | — |
| Range Test | ⚠️ | ✅ | Android PR [#5986](https://github.com/meshtastic/Meshtastic-Android/pull/5986) now blocks Range Test on public/default primary channels; Apple has no equivalent guard yet |
| RTTTL / Ringtone | ✅ (within Ext. Notification) | ✅ (separate screen) | Byte limit differs by 2 |
| Ambient Lighting | ✅ | ✅ | ✅ Both platforms aligned: Android PR [#5477](https://github.com/meshtastic/Meshtastic-Android/pull/5477) enforces 0–31 for current and 0–255 for RGB with error indicators |
| TAK Module | ✅ | ✅ | Neither platform has an `enabled` toggle (only Team + Role pickers). Android role-gates the whole screen (nav-level, TAK/TAK_TRACKER); Apple always renders it and shows a role warning note. See §3 |
| Paxcounter | ✅ | ✅ | RSSI threshold fields added to Apple via PR [#1846](https://github.com/meshtastic/Meshtastic-Apple/pull/1846) |
| Audio | ✅ | ✅ | Apple screen added via PR [#1861](https://github.com/meshtastic/Meshtastic-Apple/pull/1861) |
| Remote Hardware | ✅ | ❌ | Android only |
| Neighbor Info | ✅ | ✅ | Apple screen added via PR [#1860](https://github.com/meshtastic/Meshtastic-Apple/pull/1860) |
| Status Message | ✅ | ✅ | Apple screen added in PR [#1858](https://github.com/meshtastic/Meshtastic-Apple/pull/1858); firmware gate corrected to 2.8.0 in PR [#1997](https://github.com/meshtastic/Meshtastic-Apple/pull/1997) |
| Traffic Management | ❌ | ✅ | ⚠️ **Now Apple-only (verified 2026-07-04)** — Apple added `TrafficManagementConfig`; Android removed its screen because it did not work as intended (no `ModuleRoute` entry; only a stale detekt-baseline reference remains) |

---

## 2. Platform-Exclusive Screens

Module config screens present on only one platform, plus historical entries now on both.

> **Note (updated 2026-07-04):** Audio (PR [#1861](https://github.com/meshtastic/Meshtastic-Apple/pull/1861)), Neighbor Info (PR [#1860](https://github.com/meshtastic/Meshtastic-Apple/pull/1860)), and Status Message (PR [#1858](https://github.com/meshtastic/Meshtastic-Apple/pull/1858)) have been added to Apple. **Remote Hardware** remains the only genuinely Android-only screen. **Traffic Management** has flipped to **Apple-only** — Apple added it; Android removed its screen because it did not work as intended.

### Audio (`ModuleConfig.AudioConfig`) — ✅ Now on both platforms

Apple implementation added in PR [#1861](https://github.com/meshtastic/Meshtastic-Apple/pull/1861).

| Field | Android Validation |
|-------|--------------------|
| `codec2_enabled` | Toggle |
| `ptt_pin` | Numeric input (GPIO) |
| `bitrate` | Dropdown: `Audio_Baud` enum |
| `i2s_ws`, `i2s_sd`, `i2s_din`, `i2s_sck` | Numeric input (GPIO) |

### Remote Hardware (`ModuleConfig.RemoteHardwareConfig`)

| Field | Android Validation |
|-------|--------------------|
| `enabled` | Toggle |
| `allow_undefined_pin_access` | Toggle |
| `available_pins` | maxCount: 4; per-pin GPIO 0–255, name max 14 bytes, type enum |

### Neighbor Info (`ModuleConfig.NeighborInfoConfig`) — ✅ Now on both platforms

Apple implementation added in PR [#1860](https://github.com/meshtastic/Meshtastic-Apple/pull/1860).

| Field | Android Validation |
|-------|--------------------|
| `enabled` | Toggle |
| `update_interval` | Numeric input (seconds) |
| `transmit_over_lora` | Toggle |

### Status Message (`ModuleConfig.StatusMessageConfig`) — ✅ Now on both platforms

Apple implementation added in PR [#1858](https://github.com/meshtastic/Meshtastic-Apple/pull/1858). The firmware gate was later corrected to **2.8.0+** in PR [#1997](https://github.com/meshtastic/Meshtastic-Apple/pull/1997).

| Field | Android Validation |
|-------|--------------------|
| `node_status` | max 80 bytes; requires `supportsStatusMessage` capability |

### Traffic Management (`ModuleConfig.TrafficManagementConfig`) — ⚠️ Now Apple-only

**Platform flip (verified 2026-07-04).** Apple added a `TrafficManagementConfig` screen (wired into Settings navigation). Android **removed** its screen because it did not work as intended — `main` no longer has a `ModuleRoute` entry or source file; only a stale `detekt-baseline.xml` reference to the removed `TrafficManagementConfigScreen` composable remains. The fields below are the Apple screen; per-field `exhaust_hop_*` / `router_preserve_hops` / `position_precision_bits` presence on Apple was not individually re-verified.

| Field | Apple Validation |
|-------|--------------------|
| `enabled` | Toggle (master) |
| `position_dedup_enabled` | Toggle |
| `position_min_interval_secs` | Numeric input (shown when `position_dedup_enabled`) |
| `nodeinfo_direct_response` | Toggle |
| `nodeinfo_direct_response_max_hops` | Numeric input (shown when `nodeinfo_direct_response`) |
| `rate_limit_enabled` | Toggle |
| `rate_limit_window_secs` | Numeric input (shown when `rate_limit_enabled`) |
| `rate_limit_max_packets` | Numeric input (shown when `rate_limit_enabled`) |
| `drop_unknown_enabled` | Toggle |
| `unknown_packet_threshold` | Numeric input (shown when `drop_unknown_enabled`) |

---

## 3. Shared Screens — Field-Level Mismatches

### LoRa Config

| Field | Android | Apple | Discrepancy |
|-------|---------|-------|-------------|
| `tx_power` | Signed integer, no enforced range | `Stepper(in: 0...30)` — 0 labelled "Max Transmit Power" | ✅ **Fixed May 2026.** Apple now allows 0 dBm (firmware default). Both platforms accept 0 as "use max legal continuous power." |
| `spread_factor` | Numeric input; rejects values outside 7–12 with error indicator | `Picker(ForEach 7..<13)` i.e. 7–12 | ✅ **Fixed in Android PR [#5477](https://github.com/meshtastic/Meshtastic-Android/pull/5477)** (May 2026). Both platforms enforce 7–12. |
| `coding_rate` | Numeric input; rejects values outside 5–8 with error indicator | `Picker(ForEach 5..<9)` i.e. 5–8 | ✅ **Fixed in Android PR [#5477](https://github.com/meshtastic/Meshtastic-Android/pull/5477)** (May 2026). Both platforms enforce 5–8. |
| `bandwidth` | Numeric input | Picker (enum `Bandwidths`) | Android allows arbitrary integer; Apple is enum-constrained |
| `pa_fan_disabled` | Shown when `hasPaFan = true` | Not present | Apple issue [#1864](https://github.com/meshtastic/Meshtastic-Apple/issues/1864) |

### Bluetooth Config

| Field | Android | Apple | Discrepancy |
|-------|---------|-------|-------------|
| `fixed_pin` | String input with `KeyboardType.NumberPassword`; preserves leading zeros; shows error indicator for incomplete/invalid PINs | Exactly 6 digits; strips leading zeros only via `.drop(while: { $0 == "0" })`, shows "short pin" warning if result < 6 digits | ✅ **Fixed in Android PR [#5477](https://github.com/meshtastic/Meshtastic-Android/pull/5477)** (May 2026) — now treats PIN as string, preserves leading zeros, shows error for invalid input. Apple ✅ fixed in PR [#1830](https://github.com/meshtastic/Meshtastic-Apple/pull/1830). |

### Security Config

| Field | Android | Apple | Discrepancy |
|-------|---------|-------|-------------|
| `is_managed` | Only enabled when `admin_key` list is non-empty | Disabled when `adminKey.length == 0`; shows warning "An admin key must be set before enabling managed mode." | ✅ **Fixed in Apple PR [#1833](https://github.com/meshtastic/Meshtastic-Apple/pull/1833)** (May 17, 2026) |
| `admin_key` | Single list field, maxCount: 3 | Three separate fields (`adminKey`, `adminKey2`, `adminKey3`) | Different UX, same data model |
| ~~`admin_channel_enabled`~~ | ~~Toggle~~ | Not present | ✅ **Removed from Android** in PR [#5547](https://github.com/meshtastic/Meshtastic-Android/pull/5547) (May 2026). Field no longer shown on either platform. |

### Network Config

| Field | Android | Apple | Discrepancy |
|-------|---------|-------|-------------|
| `ntp_server` | String, max 32 bytes | String, max 32 bytes | ✅ **Added to Apple** in PR [#1849](https://github.com/meshtastic/Meshtastic-Apple/pull/1849) (May 2026) |
| `rsyslog_server` | String, max 32 bytes | String, max 32 bytes | ✅ **Added to Apple** in PR [#1849](https://github.com/meshtastic/Meshtastic-Apple/pull/1849) (May 2026) |
| `address_mode` / `ipv4_config` (ip, gateway, subnet, dns) | Shown when `address_mode = STATIC` | Shown when `address_mode = STATIC` | ✅ **Added to Apple** in PR [#1849](https://github.com/meshtastic/Meshtastic-Apple/pull/1849) (May 2026) |
| `udp_enabled` | Toggle (label updated to match Apple via PR [#5549](https://github.com/meshtastic/Meshtastic-Android/pull/5549)) | Toggle | ✅ Aligned |

### MQTT Config

| Field | Android | Apple | Discrepancy |
|-------|---------|-------|-------------|
| `address` | max **63** bytes | max **63** bytes | ✅ **Fixed in Apple PR [#1833](https://github.com/meshtastic/Meshtastic-Apple/pull/1833)** (May 17, 2026) |
| `password` | max **31** bytes | max **31** bytes | ✅ **Both fixed** — Apple PR [#1833](https://github.com/meshtastic/Meshtastic-Apple/pull/1833) corrected Apple (30→31); Android must also correct 63→31 (see gap row 3) |
| `map_report_settings.position_precision` | Slider 12–15 bits | `Slider(in: 12...15, step: 1)` | ✅ Aligned |

### Telemetry Config

| Field | Android | Apple | Discrepancy |
|-------|---------|-------|-------------|
| `air_quality_enabled` | Toggle | Toggle | ✅ **Added to Apple** in PR [#1848](https://github.com/meshtastic/Meshtastic-Apple/pull/1848) (May 2026) |
| `air_quality_interval` | Dropdown: `BROADCAST_SHORT` intervals | Interval picker | ✅ **Added to Apple** in PR [#1848](https://github.com/meshtastic/Meshtastic-Apple/pull/1848) (May 2026) |
| `device_telemetry_enabled` | Shown when `canToggleTelemetryEnabled` capability | Shown when firmware ≥ 2.7.12 | Different visibility condition; functionally equivalent |

### Display Config

| Field | Android | Apple | Discrepancy |
|-------|---------|-------|-------------|
| `compass_orientation` | Dropdown: `CompassOrientation` enum | Picker over rotation values (`0° / 90° / 180° / 270°` + `… Inverted` variants); firmware ≥ 2.3.13 | ✅ **Added to Apple** in PR [#1847](https://github.com/meshtastic/Meshtastic-Apple/pull/1847) (May 2026); deprecated `compass_north_top` toggle shown only for firmware < 2.3.13 |

### Power Config

| Field | Android | Apple | Discrepancy |
|-------|---------|-------|-------------|
| `adc_multiplier_override` | Must be > 0.0 | `FloatField(isValid: { $0 > 0.0 })` — **> 0.0** | ✅ **Aligned (verified 2026-07-04).** Apple already relaxed the validator to `{ $0 > 0.0 }` in PR [#1866](https://github.com/meshtastic/Meshtastic-Apple/pull/1866) (resolves issue [#1865](https://github.com/meshtastic/Meshtastic-Apple/issues/1865)); both platforms now accept `> 0.0`. Apple retains its ADC Override toggle (0 = firmware default). |
| `is_power_saving` | Toggle | Shown only for ESP32/ESP32S3 or specific roles | Both platform-conditional but different conditions documented |

### Canned Messages Config

| Field | Android | Apple | Discrepancy |
|-------|---------|-------|-------------|
| `messages` | max **200** bytes | max **200** bytes | ✅ **Fixed in Apple PR [#1833](https://github.com/meshtastic/Meshtastic-Apple/pull/1833)** (May 17, 2026) |
| `allow_input_source` | max 63 bytes (proto max_size: 16; UI intentionally larger) | Not present | Android-only field |

### External Notification / RTTTL Config

| Field | Android | Apple | Discrepancy |
|-------|---------|-------|-------------|
| `ringtone` | max **230** bytes (within External Notification screen) | max **230** bytes (separate RTTTL Config screen) | ✅ **Apple byte limit fixed** in PR [#1833](https://github.com/meshtastic/Meshtastic-Apple/pull/1833); screen placement difference remains (Android: inline; Apple: separate screen) |

### Ambient Lighting Config

| Field | Android | Apple | Discrepancy |
|-------|---------|-------|-------------|
| `current` | Numeric input; rejects values outside 0–31 with error indicator | `Stepper(in: 0...31)` — **0–31** | ✅ **Fixed in Android PR [#5477](https://github.com/meshtastic/Meshtastic-Android/pull/5477)** (May 2026). Both platforms enforce 0–31. |
| RGB values | Three separate numeric inputs; rejects values outside 0–255 with error indicator | Single `ColorPicker` | ✅ **Fixed in Android PR [#5477](https://github.com/meshtastic/Meshtastic-Android/pull/5477)** (May 2026). Same data, different UX; both enforce 0–255. |

### TAK Module Config

| Field | Android | Apple | Discrepancy |
|-------|---------|-------|-------------|
| `enabled` | Not present (no enable toggle) | Not present (no enable toggle) | ✅ **Corrected 2026-07-04.** Neither platform exposes an enable toggle — both show only Team + Role pickers. Prior claim that Apple had an `enabled` toggle was wrong. |
| Role gating | Whole screen gated at nav level to TAK / TAK_TRACKER roles (`isApplicable`) | Screen always rendered; shows an orange warning note ("These settings only apply when the device role is TAK or TAK Tracker") when role differs | Different visibility UX; Android hides, Apple warns |

### Paxcounter Config

| Field | Android | Apple | Discrepancy |
|-------|---------|-------|-------------|
| `wifi_threshold` | Signed integer (RSSI dBm), default −80 | Signed integer input (RSSI dBm), default −80 | ✅ **Added to Apple** in PR [#1846](https://github.com/meshtastic/Meshtastic-Apple/pull/1846) (May 2026) |
| `ble_threshold` | Signed integer (RSSI dBm), default −80 | Signed integer input (RSSI dBm), default −80 | ✅ **Added to Apple** in PR [#1846](https://github.com/meshtastic/Meshtastic-Apple/pull/1846) (May 2026) |

### Store & Forward Config

| Field | Android | Apple | Discrepancy |
|-------|---------|-------|-------------|
| `records` | Numeric input (free-form) | Picker: 0, 25, 50, 75, 100 | Different UX — Apple constrains to presets |
| `history_return_max` | Numeric input (free-form) | Picker: 0, 25, 50, 75, 100 | Same |
| `history_return_window` | Numeric input (seconds, free-form) | Picker: 0, 60, 300, 600, 900, 1800, 3600, 7200 | Same |

### Range Test Config

| Field | Android | Apple | Discrepancy |
|-------|---------|-------|-------------|
| `enabled` | Toggle is disabled when the primary channel is public/default; save path also forces `enabled = false` in that case (PR [#5986](https://github.com/meshtastic/Meshtastic-Android/pull/5986)) | Plain toggle; no public/default-channel guard documented | ⚠️ Android now protects shared public meshes from accidental range-test traffic; Apple still lacks the same safeguard |

---

## 4. Discrepancy Summary

### ⚠️ Bugs / Alignment Issues

| # | Area | Field | Firmware limit (nanopb `.options`) | Android | Apple | Path to alignment |
|---|------|-------|------------------------------------|---------|-------|-------------------|
| ~~1~~ | ~~LoRa Config~~ | ~~`tx_power`~~ | — | — | — | ~~Apple `Stepper(in: 1...30)` could not express 0 dBm.~~ **Fixed May 2026** — `Stepper(in: 0...30)` with 0 labelled "Max Transmit Power". |
| ~~2~~ | ~~Bluetooth Config~~ | ~~`fixed_pin`~~ | `uint32` — no size constraint | ✅ Accepts any 6-digit number unchanged | ✅ **Fixed in Apple PR [#1830](https://github.com/meshtastic/Meshtastic-Apple/pull/1830)** (May 17, 2026) — now strips leading zeros only via `.drop(while: { $0 == "0" })` | ✅ Resolved |
| ~~2b~~ | ~~Bluetooth Config~~ | ~~`fixed_pin`~~ | `uint32` — no size constraint | ✅ **Fixed in Android PR [#5477](https://github.com/meshtastic/Meshtastic-Android/pull/5477)** (May 2026) — now uses string input with `KeyboardType.NumberPassword`, preserves leading zeros, shows error indicator for invalid PINs. | ✅ Shows "short pin" warning when stripped value < 6 digits | ✅ Resolved |
| ~~3~~ | ~~MQTT Config~~ | ~~`password`~~ | **`max_size:32` → 31 bytes max** | ⚠️ Enforces 63 bytes. Internal comment incorrectly reads `max_size:64`; the `.options` file specifies `max_size:32`. Passwords of 32–63 bytes are accepted by Android but silently truncated by firmware. | ✅ **Fixed in Apple PR [#1833](https://github.com/meshtastic/Meshtastic-Apple/pull/1833)** — now enforces 31 bytes. | Android still enforces 63 bytes — change `maxSize = 63` → `31` and fix the comment. |
| ~~4~~ | ~~MQTT Config~~ | ~~`address`~~ | `max_size:64` → 63 bytes max | ✅ Enforces 63 bytes | ✅ **Fixed in Apple PR [#1833](https://github.com/meshtastic/Meshtastic-Apple/pull/1833)** — now enforces 63 bytes | ✅ Resolved |
| ~~5~~ | ~~Canned Messages~~ | ~~`messages`~~ | `max_size:201` → 200 bytes max | ✅ Enforces 200 bytes | ✅ **Fixed in Apple PR [#1833](https://github.com/meshtastic/Meshtastic-Apple/pull/1833)** — now enforces 200 bytes | ✅ Resolved |
| ~~6~~ | ~~External Notification~~ | ~~`ringtone`~~ | `max_size:231` → 230 bytes max | ✅ Enforces 230 bytes | ✅ **Fixed in Apple PR [#1833](https://github.com/meshtastic/Meshtastic-Apple/pull/1833)** — now enforces 230 bytes | ✅ Resolved |
| ~~7~~ | ~~Power Config~~ | ~~`adc_multiplier_override`~~ | `float` — proto comment: *"Should be set to floating point value between 2 and 6"*; `0` = use firmware default | ✅ Validates `> 0.0`; any positive float accepted | ✅ Apple relaxed `FloatField` to `{ $0 > 0.0 }` in PR [#1866](https://github.com/meshtastic/Meshtastic-Apple/pull/1866); "ADC Override" toggle (0 = firmware default) retained | ✅ **Resolved (verified 2026-07-04).** Canonical is `> 0.0`; both platforms aligned. Apple issue [#1865](https://github.com/meshtastic/Meshtastic-Apple/issues/1865) resolved. (Supersedes the earlier "Android should tighten to 2.0–6.0" direction — Apple relaxed instead.) |
| ~~8~~ | ~~Security Config~~ | ~~`is_managed`~~ | `repeated bytes admin_key` must be set before managed mode is meaningful | ✅ Toggle is `.enabled = formState.admin_key.isNotEmpty()` | ✅ **Fixed in Apple PR [#1833](https://github.com/meshtastic/Meshtastic-Apple/pull/1833)** — toggle disabled when `adminKey.length == 0`; warning shown | ✅ Resolved |
| 9 | Range Test Config | `enabled` | Public/default primary channels should not be used for automated range-test traffic | ✅ **Fixed in Android PR [#5986](https://github.com/meshtastic/Meshtastic-Android/pull/5986)** (2026-06-27) — UI disables the toggle and save forces `enabled = false` on public/default channels | ❌ No equivalent guard documented | Apple: add the same public/default-channel safety check before enabling or saving Range Test. |

### Fields Present on Android but Missing from Apple

| Area | Fields |
|------|--------|
| LoRa Config | `pa_fan_disabled` | Apple issue [#1864](https://github.com/meshtastic/Meshtastic-Apple/issues/1864) |
| ~~Network Config~~ | ~~`ntp_server`, `rsyslog_server`, static IPv4~~  | ✅ Added to Apple in PR [#1849](https://github.com/meshtastic/Meshtastic-Apple/pull/1849) |
| ~~Security Config~~ | ~~`admin_channel_enabled`~~ | ✅ Removed from Android in PR [#5547](https://github.com/meshtastic/Meshtastic-Android/pull/5547) |
| ~~Display Config~~ | ~~`compass_orientation`~~ | ✅ Added to Apple in PR [#1847](https://github.com/meshtastic/Meshtastic-Apple/pull/1847) |
| ~~Telemetry Config~~ | ~~`air_quality_enabled`, `air_quality_interval`~~ | ✅ Added to Apple in PR [#1848](https://github.com/meshtastic/Meshtastic-Apple/pull/1848) |
| Canned Messages | `allow_input_source` *(deprecated — should be removed from both)* |
| ~~Paxcounter~~ | ~~`wifi_threshold`, `ble_threshold`~~ | ✅ Added to Apple in PR [#1846](https://github.com/meshtastic/Meshtastic-Apple/pull/1846) |
| ~~Module screens~~ | ~~Audio, Neighbor Info~~ | ✅ Added to Apple: Audio PR [#1861](https://github.com/meshtastic/Meshtastic-Apple/pull/1861), Neighbor Info PR [#1860](https://github.com/meshtastic/Meshtastic-Apple/pull/1860) |
| Module screens | Remote Hardware | Only genuinely Android-only screen. Status Message ✅ added to Apple in PR [#1858](https://github.com/meshtastic/Meshtastic-Apple/pull/1858); Traffic Management is now **Apple-only** (Android removed it — see §2) |

### Fields Present on Apple but Missing from Android

| Area | Field | Notes |
|------|-------|-------|
| App Settings | Enable Administration | Apple-only toggle |
| ~~Network Config~~ | ~~`udp_enabled`~~ | ✅ Android PR [#5549](https://github.com/meshtastic/Meshtastic-Android/pull/5549) added/aligned the UDP toggle label |
| ~~TAK Module~~ | ~~`enabled`~~ | ✅ **Corrected 2026-07-04** — Apple has no TAK enable toggle; neither platform exposes one |
| Traffic Management | Entire screen | ✅ **Now Apple-only** — Apple added `TrafficManagementConfig`; Android removed its screen (see §2) |

---

> **Deprecated Field Handling** has been moved to its own document: [deprecated-fields-audit.md](deprecated-fields-audit.md)
