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

| # | Area | Field | Issue |
|---|------|-------|-------|
| ~~1~~ | ~~LoRa Config~~ | ~~`tx_power`~~ | ~~Apple `Stepper(in: 1...30)` cannot express 0 dBm.~~ **Fixed May 2026** — `Stepper(in: 0...30)` with 0 labelled "Max Transmit Power". |
| 2 | Bluetooth Config | `fixed_pin` | Apple strips ALL zero characters when the first digit is zero (e.g. `100200` → `12`). Should only strip leading zeros before the first non-zero digit. Known open issue Apple #1152. |
| 3 | MQTT Config | `password` | Apple enforces 30-byte max; Android enforces 63-byte max (matching proto). A password between 31–63 bytes is valid on Android but silently truncated on Apple. |
| 4 | MQTT Config | `address` | Apple enforces 62-byte max; Android enforces 63-byte max. |
| 5 | Canned Messages | `messages` | Apple enforces 198-byte max; Android enforces 200-byte max. |
| 6 | External Notification | `ringtone` | Apple enforces 228-byte max; Android enforces 230-byte max. |
| 7 | Power Config | `adc_multiplier_override` | Android validates only > 0; Apple restricts to 2.0–6.0. The protobuf does not define a range — the correct constraint should be defined and aligned. |
| 8 | Security Config | `is_managed` | Android guards this toggle behind a non-empty `admin_key`; Apple does not, allowing managed mode to be enabled with no admin key configured. |

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
---

## 5. Deprecated Field Handling

This section audits all fields and enum values marked `[deprecated = true]` in the Meshtastic protobufs and compares how Android and Apple handle them in their UIs. Fields may be deprecated because: they were moved to a different message, replaced by a successor field, or removed from active firmware support.

### Methodology

Proto files were inspected for the `[deprecated = true]` annotation. The `.options` files were also cross-referenced. For each deprecated item the UI source code of both apps was read to determine whether the item is: **hidden** (not shown to users), **shown but read-only / informational**, **still writable** (the deprecated field is actively surfaced and written), or **actively migrated** (the app converts the old value to the replacement on load).

---

### 5.1 Deprecated Enum Values

These proto enum values are annotated `[deprecated = true]` and should not be offered in new configurations.

| Enum | Value | Deprecated since | Reason | Android | Apple |
|------|-------|-----------------|--------|---------|-------|
| `DeviceConfig.Role` | `ROUTER_CLIENT = 3` | v2.3.15 | Improper usage impacting public meshes; use ROUTER or CLIENT instead | ✅ **Filtered out** — `DropDownPreference` uses JVM reflection (`isDeprecatedEnumEntry()`) to remove all deprecated enum constants from the picker at runtime. `@Suppress("DEPRECATION")` allows the existing value to be read and displayed if a device already has this role. | ✅ **Absent from enum + actively migrated** — `DeviceRoles` Swift enum has no `routerClient` case. On view load, `setDeviceValues()` silently rewrites role 3 → 1 (`CLIENT_MUTE`): `if node?.deviceConfig?.role ?? 0 == 3 { node?.deviceConfig?.role = 1 }` |
| `DeviceConfig.Role` | `REPEATER = 4` | v2.7.11 | Creates "holes" in the mesh rebroadcast chain | ✅ **Filtered out** via `isDeprecatedEnumEntry()` reflection. Still readable/displayable if device has it. Included in `infrastructureRoles` list so it triggers the router role confirmation dialog. | ⚠️ **Absent from enum but no migration** — `DeviceRoles` has no `repeater` case. A device configured as REPEATER will have `deviceRole = 4`, which won't match any `DeviceRoles` case; `DeviceRoles(rawValue: 4)` returns `nil`. No explicit migration to a replacement role. |
| `LoRaConfig.ModemPreset` | `LONG_SLOW = 1` | v2.7 | Unpopular slow preset | ✅ **Filtered out** via `isDeprecatedEnumEntry()` reflection. | ❌ **Still offered** — `ModemPresets` Swift enum includes `case longSlow = 1` and it is not excluded from `userSelectable`. Users can still select LONG_SLOW from the modem preset picker. |
| `LoRaConfig.ModemPreset` | `VERY_LONG_SLOW = 2` | v2.5 | Works only with TCXO and unusably slow | ✅ **Filtered out** via `isDeprecatedEnumEntry()` reflection. | ✅ **Absent from enum** — `ModemPresets` has no `veryLongSlow` case. A device with this preset will have an unrecognised raw value in the picker. No migration logic. |

---

### 5.2 Deprecated Fields — Moved to Another Message

These fields were physically relocated to a different proto message. They remain in the original message for backward compatibility but should no longer be written.

| Proto message | Field | Moved to | Android | Apple |
|--------------|-------|----------|---------|-------|
| `DeviceConfig` | `serial_enabled = 2` | `SecurityConfig.serial_enabled` | ✅ **Not shown** — DeviceConfigScreen has no reference to `serial_enabled`. The current value lives in SecurityConfig. | ✅ **Not shown** — DeviceConfig.swift has no reference. |
| `DeviceConfig` | `is_managed = 9` | `SecurityConfig.is_managed` | ✅ **Not shown** in DeviceConfigScreen. Correctly surfaced only via SecurityConfigScreen. | ✅ **Not shown** in DeviceConfig.swift. Correctly surfaced only via SecurityConfig.swift. |

---

### 5.3 Deprecated Fields — Replaced by a Successor Field

These fields were superseded by a newer field in the same message. The deprecated field should not be written and ideally should not be shown.

| Proto message | Deprecated field | Successor field | Android | Apple |
|--------------|-----------------|----------------|---------|-------|
| `PositionConfig` | `gps_enabled = 4` — *"Is GPS enabled for this node?"* | `gps_mode = 13` (`GpsMode` enum: `NOT_PRESENT`, `ENABLED`, `DISABLED`) | ✅ **Not shown** — PositionConfigScreen uses `gps_mode` exclusively. | ⚠️ **Read at load, written on save** — `setPositionValues()` reads `gpsMode` but also reads `deviceGpsEnabled` (the deprecated field) as a fallback: `if node?.positionConfig?.deviceGpsEnabled ?? false && gpsMode != 1 { self.gpsMode = 1 }`. On save, `pc.gpsEnabled = gpsMode == 1` actively writes the deprecated field alongside the new `pc.gpsMode`. |
| `PositionConfig` | `gps_attempt_time = 6` — *"Deprecated in favor of using smart / regular broadcast intervals"* | Implicit via `position_broadcast_smart_enabled` / `position_broadcast_secs` | ✅ **Not shown** — no reference in PositionConfigScreen. | ✅ **Not shown** — no reference in PositionConfig.swift. |
| `DisplayConfig` | `compass_north_top = 4` — *"If set, compass always points north"* | `compass_orientation` (enum: `DEGREES`, `NORTH_UP`, etc.) | ❌ **Still shown and writable** — DisplayConfigItemList renders a `SwitchPreference` bound to `formState.value.compass_north_top` and writes it back on save. The replacement `compass_orientation` field is not surfaced. | ❌ **Still shown and writable** — DisplayConfig.swift renders `Toggle(isOn: $compassNorthTop)`, reads `node?.displayConfig?.compassNorthTop` on load, and writes `dc.compassNorthTop = compassNorthTop` on save. The replacement `compass_orientation` field is not surfaced. |
| `DisplayConfig` | `gps_format = 2` — *"Deprecated in 2.7.4: Unused. How GPS coordinates are formatted on the OLED."* | — (removed entirely, no replacement) | ✅ **Not shown** — no reference in DisplayConfigItemList. | ⚠️ **State variable exists but not rendered** — `@State var gpsFormat = 0` is declared and loaded from `node?.displayConfig?.gpsFormat`, but there is no UI element that reads or writes it. Dead code; field is never written on save. |

---

### 5.4 Deprecated Fields — Removed from Active Use

These fields have been deprecated without a direct named successor and are no longer relevant to firmware.

| Proto message | Deprecated field | Android | Apple |
|--------------|-----------------|---------|-------|
| `CannedMessageConfig` | `enabled = 9` — *"Enable/disable CannedMessageModule"* (replaced by the module always being active when configured) | ❌ **Still shown and writable** — `CannedMessageConfigItemList` renders a `SwitchPreference` for `formState.value.enabled` and writes it back. Also has a max_size comment bug: `// allow_input_source max_size:16` on the wrong field (see §5.5). | ❌ **Still shown and writable** — CannedMessagesConfig.swift renders an `enabled` toggle and writes `cmc.enabled = enabled` on save. |
| `CannedMessageConfig` | `allow_input_source = 10` — *"Input event origin, e.g. 'rotEnc1', 'upDownEnc1', '_any'"* | ❌ **Still shown and writable** — `CannedMessageConfigItemList` renders an `EditTextPreference` for `allow_input_source` with `maxSize = 63`. This is also a validation bug: the `.options` file specifies `max_size:16` (15 chars max) but Android enforces 63 bytes, which is a silent over-limit. | ❌ **Still shown and writable** — CannedMessagesConfig.swift writes `cmc.allowInputSource = "rotEnc1"`, `"upDown1"`, or `"_any"` via hard-coded option buttons. These are functional but writing a deprecated field. |
| `User` | `macaddr = 4` — *"Deprecated in 2.1.x. Radio MAC address, added by ESP32 when broadcasting"* | ✅ **Not written** — no reference in settings UIs. Internal proto field only. | ✅ **Not written** — no reference in settings UIs. |
| `MeshPacket` | `delayed = 13` | ✅ **Not referenced** in settings UIs. | ✅ **Not referenced** in settings UIs. |

---

### 5.5 Additional Finding: `allow_input_source` max_size mismatch

While auditing deprecated field handling, a secondary validation bug was identified in Android's `CannedMessageConfigItemList`:

```kotlin
EditTextPreference(
    title = stringResource(Res.string.allow_input_source),
    value = formState.value.allow_input_source,
    maxSize = 63, // allow_input_source max_size:16  ← comment references the wrong field
    ...
)
```

The `.options` annotation is `*CannedMessageConfig.allow_input_source max_size:16` (max 15 chars). Android enforces 63 bytes — 4× the firmware limit. Since this field is also deprecated, the recommended fix is removal of the UI element rather than a size correction.

---

### 5.6 Recommendations

| Priority | Action | Rationale |
|----------|--------|-----------|
| **High** | **Apple: remove `LONG_SLOW` from `ModemPresets.userSelectable`** | Deprecated in v2.7. Android already filters it. New users can inadvertently select a deprecated, unsupported preset. Existing devices using LONG_SLOW should continue to display the label but not be offered the option. |
| **High** | **Both: replace `compass_north_top` with `compass_orientation`** | The deprecated toggle is still the only compass UI on both platforms. The replacement `compass_orientation` enum field is fully defined in the proto and present in firmware but not exposed in either app. |
| **High** | **Apple: add a migration for `REPEATER` role** | Unlike `ROUTER_CLIENT` (which Apple migrates to `CLIENT_MUTE`), a device configured as `REPEATER` will have `DeviceRoles(rawValue: 4)` return `nil`, producing undefined UI behaviour. Should migrate to an appropriate replacement (e.g. `CLIENT` or display an explicit deprecation warning). |
| **Medium** | **Both: stop writing `CannedMessageConfig.enabled` and `allow_input_source`** | Both fields are deprecated. `enabled` has no firmware effect in current versions. `allow_input_source` should be removed from UI; input routing is now handled by the hardware-specific toggles (`rotary1_enabled`, `updown1_enabled`). |
| **Medium** | **Apple: stop writing `PositionConfig.gps_enabled` on save** | The deprecated `gps_enabled` field is redundantly written alongside `gps_mode`. Firmware ignores the deprecated field in current versions; writing it risks confusing older firmware and creates unnecessary proto churn. Remove `pc.gpsEnabled = gpsMode == 1`. |
| **Low** | **Apple: remove `gpsFormat` dead-code state variable** | `@State var gpsFormat` is loaded but never rendered or written. Remove it to reduce noise. |
| **Low** | **Android: fix the misplaced `allow_input_source` comment** | `maxSize = 63, // allow_input_source max_size:16` — the comment is on the line, not the field, and the size is wrong. Moot if the field is removed (recommended above), but should be fixed if it is retained. |
