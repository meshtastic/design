# Cross-Platform Settings Validation Matrix

**Status:** Reference Document  
**Sources:** [settings-validation-android.md](../../.github/docs/validation/settings-validation-android.md) · [settings-validation-apple.md](../../.github/docs/validation/settings-validation-apple.md)  
**Last Updated:** 2026-05-17  

> **Purpose:** This document cross-references the Android and Apple settings validation references to surface missing screens, missing fields, and constraint mismatches that should be aligned.

---

## 1. Settings Screen Coverage

### Config Screens

| Screen | Android | Apple | Notes |
|--------|---------|-------|-------|
| User Config | ✅ | ✅ | — |
| Device Config | ✅ | ✅ | — |
| Position Config | ✅ | ✅ | — |
| Power Config | ✅ | ✅ | — |
| Network Config | ✅ | ✅ | Apple exposes fewer fields — see §3 |
| Display Config | ✅ | ✅ | — |
| LoRa Config | ✅ | ✅ | Several constraint mismatches — see §3 |
| Bluetooth Config | ✅ | ✅ | Fixed-PIN validation differs — see §3 |
| Security Config | ✅ | ✅ | Minor structural differences |

### Module Config Screens

| Screen | Android | Apple | Notes |
|--------|---------|-------|-------|
| MQTT | ✅ | ✅ | Byte-limit mismatches — see §3 |
| Telemetry | ✅ | ✅ | Android has air quality fields; Apple does not |
| Canned Messages | ✅ | ✅ | Max bytes differ |
| Detection Sensor | ✅ | ✅ | Apple has sensor/client role picker |
| External Notification | ✅ | ✅ | — |
| Store & Forward | ✅ | ✅ | Android: free-form inputs. Apple: fixed pickers |
| Serial | ✅ | ✅ | — |
| Range Test | ✅ | ✅ | — |
| RTTTL / Ringtone | ✅ (within Ext. Notification) | ✅ (separate screen) | Byte limit differs by 2 |
| Ambient Lighting | ✅ | ✅ | Current range differs |
| TAK Module | ✅ | ✅ | Apple has `enabled` toggle; Android does not |
| Paxcounter | ✅ | ✅ | Android has RSSI threshold fields; Apple does not |
| Audio | ✅ | ❌ | Android only |
| Remote Hardware | ✅ | ❌ | Android only |
| Neighbor Info | ✅ | ❌ | Android only |
| Status Message | ✅ | ❌ | Android only |
| Traffic Management | ✅ | ❌ | Android only |

---

## 2. Screens Only on Android

These module config screens are present in Android but have no equivalent in the Apple app.

### Audio (`ModuleConfig.AudioConfig`)

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

### Neighbor Info (`ModuleConfig.NeighborInfoConfig`)

| Field | Android Validation |
|-------|--------------------|
| `enabled` | Toggle |
| `update_interval` | Numeric input (seconds) |
| `transmit_over_lora` | Toggle |

### Status Message (`ModuleConfig.StatusMessageConfig`)

| Field | Android Validation |
|-------|--------------------|
| `node_status` | max 80 bytes; requires `supportsStatusMessage` capability |

### Traffic Management (`ModuleConfig.TrafficManagementConfig`)

| Field | Android Validation |
|-------|--------------------|
| `enabled` | Toggle; requires `supportsTrafficManagementConfig` capability |
| `position_dedup_enabled` | Toggle |
| `position_precision_bits` | Numeric input |
| `position_min_interval_secs` | Numeric input |
| `nodeinfo_direct_response` | Toggle |
| `nodeinfo_direct_response_max_hops` | Numeric input |
| `rate_limit_enabled` | Toggle |
| `rate_limit_window_secs` | Numeric input |
| `rate_limit_max_packets` | Numeric input |
| `drop_unknown_enabled` | Toggle |
| `unknown_packet_threshold` | Numeric input |
| `exhaust_hop_telemetry` / `exhaust_hop_position` | Toggle |
| `router_preserve_hops` | Toggle |

---

## 3. Shared Screens — Field-Level Mismatches

### LoRa Config

| Field | Android | Apple | Discrepancy |
|-------|---------|-------|-------------|
| `tx_power` | Signed integer, no enforced range | `Stepper(in: 0...30)` — 0 labelled "Max Transmit Power" | ✅ **Fixed May 2026.** Apple now allows 0 dBm (firmware default). Both platforms accept 0 as "use max legal continuous power." |
| `spread_factor` | Numeric input | `Picker(ForEach 7..<13)` i.e. 7–12 | Android allows out-of-range entry; Apple enforces 7–12 |
| `coding_rate` | Numeric input | `Picker(ForEach 5..<9)` i.e. 5–8 | Android allows out-of-range entry; Apple enforces 5–8 |
| `bandwidth` | Numeric input | Picker (enum `BandwidthCodes`) | Android allows arbitrary integer; Apple is enum-constrained |
| `pa_fan_disabled` | Shown when `hasPaFan = true` | Not present | Android-only field |

### Bluetooth Config

| Field | Android | Apple | Discrepancy |
|-------|---------|-------|-------------|
| `fixed_pin` | Exactly 6 digits | Exactly 6 digits, **strips all `"0"` characters if the first character is `"0"`** | ⚠️ **Apple removes ALL zeros** rather than only leading zeros. A PIN like `100200` becomes `12` on Apple. Known bug — see Apple issue #1152. |

### Security Config

| Field | Android | Apple | Discrepancy |
|-------|---------|-------|-------------|
| `is_managed` | Only enabled when `admin_key` list is non-empty | Free toggle (no guard) | Android enforces the dependency; Apple does not |
| `admin_key` | Single list field, maxCount: 3 | Three separate fields (`adminKey`, `adminKey2`, `adminKey3`) | Different UX, same data model |
| `admin_channel_enabled` | Toggle | Not present | Android-only field |

### Network Config

| Field | Android | Apple | Discrepancy |
|-------|---------|-------|-------------|
| `ntp_server` | String, max 32 bytes | Not present | Android-only field |
| `rsyslog_server` | String, max 32 bytes | Not present | Android-only field |
| `address_mode` / `ipv4_config` (ip, gateway, subnet, dns) | Shown when `address_mode = STATIC` | Not present | Android-only: full static IPv4 configuration |
| `udp_enabled` | Not present | Toggle | Apple-only field |

### MQTT Config

| Field | Android | Apple | Discrepancy |
|-------|---------|-------|-------------|
| `address` | max **63** bytes | max **62** bytes | ⚠️ 1-byte mismatch — Android aligns with proto max_size (64) minus 1; Apple is off by 1 |
| `password` | max **63** bytes | max **30** bytes | ⚠️ **Significant mismatch** — Apple enforces a much tighter limit than the proto (64 bytes) or Android |
| `map_report_settings.position_precision` | Slider 12–15 bits | `Slider(in: 12...15, step: 1)` | ✅ Aligned |

### Telemetry Config

| Field | Android | Apple | Discrepancy |
|-------|---------|-------|-------------|
| `air_quality_enabled` | Toggle | Not present | Android-only field |
| `air_quality_interval` | Dropdown: `BROADCAST_SHORT` intervals | Not present | Android-only field |
| `device_telemetry_enabled` | Shown when `canToggleTelemetryEnabled` capability | Shown when firmware ≥ 2.7.12 | Different visibility condition; functionally equivalent |

### Display Config

| Field | Android | Apple | Discrepancy |
|-------|---------|-------|-------------|
| `compass_orientation` | Dropdown: `CompassOrientation` enum | Not present | Android-only field |

### Power Config

| Field | Android | Apple | Discrepancy |
|-------|---------|-------|-------------|
| `adc_multiplier_override` | Must be > 0.0 | `FloatField(isValid: { (2.0...6.0).contains($0) })` — **2.0–6.0** | ⚠️ Android only validates > 0; Apple restricts to 2.0–6.0 |
| `is_power_saving` | Toggle | Shown only for ESP32/ESP32S3 or specific roles | Both platform-conditional but different conditions documented |

### Canned Messages Config

| Field | Android | Apple | Discrepancy |
|-------|---------|-------|-------------|
| `messages` | max **200** bytes | max **198** bytes | ⚠️ 2-byte mismatch |
| `allow_input_source` | max 63 bytes (proto max_size: 16; UI intentionally larger) | Not present | Android-only field |

### External Notification / RTTTL Config

| Field | Android | Apple | Discrepancy |
|-------|---------|-------|-------------|
| `ringtone` | max **230** bytes (within External Notification screen) | max **228** bytes (separate RTTTL Config screen) | ⚠️ 2-byte mismatch; also different screen placement |

### Ambient Lighting Config

| Field | Android | Apple | Discrepancy |
|-------|---------|-------|-------------|
| `current` | Unrestricted numeric input | `Stepper(in: 0...31)` — **0–31** | Android allows values > 31; Apple restricts to 0–31 |
| RGB values | Three separate numeric inputs (0–255 each) | Single `ColorPicker` | Same data, different UX |

### TAK Module Config

| Field | Android | Apple | Discrepancy |
|-------|---------|-------|-------------|
| `enabled` | Not present (no enable toggle) | Toggle (entire form shown only for TAK/TAK_TRACKER roles) | Apple has an explicit enable toggle; Android does not |

### Paxcounter Config

| Field | Android | Apple | Discrepancy |
|-------|---------|-------|-------------|
| `wifi_threshold` | Signed integer (RSSI dBm), default −80 | Not present | Android-only field |
| `ble_threshold` | Signed integer (RSSI dBm), default −80 | Not present | Android-only field |

### Store & Forward Config

| Field | Android | Apple | Discrepancy |
|-------|---------|-------|-------------|
| `records` | Numeric input (free-form) | Picker: 0, 25, 50, 75, 100 | Different UX — Apple constrains to presets |
| `history_return_max` | Numeric input (free-form) | Picker: 0, 25, 50, 75, 100 | Same |
| `history_return_window` | Numeric input (seconds, free-form) | Picker: 0, 60, 300, 600, 900, 1800, 3600, 7200 | Same |

---

## 4. Discrepancy Summary

### ⚠️ Bugs / Alignment Issues

| # | Area | Field | Firmware limit (nanopb `.options`) | Android | Apple | Path to alignment |
|---|------|-------|------------------------------------|---------|-------|-------------------|
| ~~1~~ | ~~LoRa Config~~ | ~~`tx_power`~~ | — | — | — | ~~Apple `Stepper(in: 1...30)` could not express 0 dBm.~~ **Fixed May 2026** — `Stepper(in: 0...30)` with 0 labelled "Max Transmit Power". |
| 2 | Bluetooth Config | `fixed_pin` | `uint32` — no size constraint | ✅ Accepts any 6-digit number unchanged | ❌ When the first character is `"0"`, strips **all** `"0"` characters (e.g. `100200` → `12`). Open issue Apple #1152. | Apple: replace `fixedPin.replacing("0", with: "")` with logic that discards or reverts the input when it starts with `"0"`, rather than removing all zeros globally. |
| 3 | MQTT Config | `password` | **`max_size:32` → 31 bytes max** | ❌ Enforces 63 bytes. Internal comment incorrectly reads `max_size:64`; the `.options` file specifies `max_size:32`. Passwords of 32–63 bytes are accepted by Android but silently truncated by firmware. | ❌ Enforces 30 bytes — off by 1 below firmware limit. | **Both** platforms should enforce 31 bytes. Android: change `maxSize = 63` → `31` and fix the comment. Apple: change `> 30` → `> 31`. |
| 4 | MQTT Config | `address` | `max_size:64` → 63 bytes max | ✅ Enforces 63 bytes | ❌ Enforces 62 bytes (off by 1) | Apple: change `while totalBytes > 62` → `> 63`. |
| 5 | Canned Messages | `messages` | `max_size:201` → 200 bytes max | ✅ Enforces 200 bytes | ❌ Enforces 198 bytes (off by 2) | Apple: change `while totalBytes > 198` → `> 200`. |
| 6 | External Notification | `ringtone` | `max_size:231` → 230 bytes max | ✅ Enforces 230 bytes | ❌ Enforces 228 bytes (off by 2) | Apple: change `while totalBytes > 228` → `> 230`. |
| 7 | Power Config | `adc_multiplier_override` | `float` — proto comment: *"Should be set to floating point value between 2 and 6"*; `0` = use firmware default | ❌ Validates only `> 0.0`; any positive float accepted; no explicit UI for the `0 = disabled` semantic | ✅ `FloatField` restricted to `(2.0...6.0)`; ADC Override toggle sets field to `0` when off | Android: add range validation `2.0..6.0` and consider a toggle to express `0 = use firmware default`, matching Apple's approach. |
| 8 | Security Config | `is_managed` | `repeated bytes admin_key` must be set before managed mode is meaningful | ✅ Toggle is `.enabled = formState.admin_key.isNotEmpty()` — disabled when no key present | ❌ Administration section visible when `adminKey.length > 0 \|\| UserDefaults.enableAdministration`; the `enableAdministration` UserDefault bypasses the key requirement, and no secondary guard prevents enabling the toggle without a key | Apple: require a valid `adminKey` regardless of `enableAdministration`; disable the toggle when `adminKey.length == 0`; remove or scope the `UserDefaults.enableAdministration` bypass. |

### Fields Present on Android but Missing from Apple

| Area | Fields |
|------|--------|
| LoRa Config | `pa_fan_disabled` |
| Network Config | `ntp_server`, `rsyslog_server`, static IPv4 (`address_mode`, `ip`, `gateway`, `subnet`, `dns`) |
| Security Config | `admin_channel_enabled` |
| Display Config | `compass_orientation` |
| Telemetry Config | `air_quality_enabled`, `air_quality_interval` |
| Canned Messages | `allow_input_source` |
| Paxcounter | `wifi_threshold`, `ble_threshold` |
| Module screens | Audio, Remote Hardware, Neighbor Info, Status Message, Traffic Management |

### Fields Present on Apple but Missing from Android

| Area | Field | Notes |
|------|-------|-------|
| App Settings | Enable Administration | Apple-only toggle |
| Network Config | `udp_enabled` | Apple-only toggle |
| TAK Module | `enabled` | Apple shows an explicit enable toggle |
