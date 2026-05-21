# Cross-Platform Deprecated Field Handling Audit

**Status:** Reference Document  
**Scope:** iOS/macOS (Meshtastic-Apple) vs Android (Meshtastic-Android)  
**Last Updated:** 2026-05-21  

> **Purpose:** This document audits all fields and enum values marked `[deprecated = true]` in the Meshtastic protobufs and compares how Android and Apple handle them in their UIs. Extracted from the [Cross-Platform Settings Validation Matrix](settings-validation-matrix.md).

---

## Methodology

Proto files (`config.proto`, `module_config.proto`, `mesh.proto`) and their `.options` files were inspected for `[deprecated = true]`. The git log of the protobufs repo was used to identify the commit that added each annotation, and firmware release dates were cross-referenced to identify the first firmware version that shipped the change. The actual UI source code of both apps was then read to determine handling.

**Version column key:** *Announced* = first firmware release (pre or stable) that included the deprecation commit. *Stable* = first stable release.

---

## 1. Deprecated Enum Values

| Enum | Value | Announced | Stable | Reason | Android | Apple |
|------|-------|-----------|--------|--------|---------|-------|
| `DeviceConfig.Role` | `ROUTER_CLIENT = 3` | v2.3.14 | **v2.3.15** (2024-07-08) | Improper usage impacting public meshes; use ROUTER or CLIENT | ✅ **Filtered** — `DropDownPreference` uses JVM reflection (`isDeprecatedEnumEntry()`) to remove all `@Deprecated`-annotated enum constants at runtime. `@Suppress("DEPRECATION")` lets the screen read the value if the device already has this role. | ✅ **Absent + actively migrated** — `DeviceRoles` Swift enum has no `routerClient` case. `setDeviceValues()` rewrites role 3 → 1 (`CLIENT_MUTE`): `if role == 3 { role = 1 }`. |
| `DeviceConfig.Role` | `REPEATER = 4` | **v2.7.11** (2025-10-01) | v2.7.15 (2025-11-19) | Creates "holes" in the mesh rebroadcast chain | ✅ **Filtered** via `isDeprecatedEnumEntry()`. Included in the `infrastructureRoles` guard so it triggers the router confirmation dialog when already set. | ⚠️ **Absent but no migration** — `DeviceRoles` has no `repeater` case. A device configured as REPEATER has `deviceRole = 4`; `DeviceRoles(rawValue: 4)` returns `nil`. No migration to a replacement role. |
| `LoRaConfig.ModemPreset` | `LONG_SLOW = 1` | v2.7.17 (2025-12-20 pre) | *(no stable yet — deprecated after v2.7.15)* | Unpopular slow preset, removed from active firmware support | ✅ **Filtered** via `isDeprecatedEnumEntry()` reflection. | ❌ **Still offered** — `ModemPresets` includes `case longSlow = 1` and it is not excluded from `userSelectable`. Users running any firmware can still select LONG_SLOW. |
| `LoRaConfig.ModemPreset` | `VERY_LONG_SLOW = 2` | v2.7.4 (2025-08-09 pre); proto comment: "Deprecated in 2.5" | v2.7.15 (2025-11-19) | Works only with TCXO; unusably slow | ✅ **Filtered** via `isDeprecatedEnumEntry()`. | ✅ **Absent** — `ModemPresets` has no `veryLongSlow` case. No migration; a device with this preset will show an unrecognised value. |

---

## 2. Deprecated Fields — Moved to Another Message

| Proto message | Field | Moved in | Stable | Moved to | Android | Apple |
|--------------|-------|----------|--------|----------|---------|-------|
| `DeviceConfig` | `serial_enabled = 2` | v2.4.3 (2024-08-15 pre); `[deprecated=true]` annotated v2.7.4 | v2.5.11 | `SecurityConfig.serial_enabled` | ✅ **Not shown** in DeviceConfigScreen. Surfaced via SecurityConfigScreen. | ✅ **Not shown** in DeviceConfig.swift. |
| `DeviceConfig` | `is_managed = 9` | v2.4.3 (2024-08-15 pre); `[deprecated=true]` annotated v2.7.4 | v2.5.11 | `SecurityConfig.is_managed` | ✅ **Not shown** in DeviceConfigScreen. | ✅ **Not shown** in DeviceConfig.swift. |

---

## 3. Deprecated Fields — Replaced by a Successor Field

| Proto message | Deprecated field | Deprecated since | Stable | Successor field | Android | Apple |
|--------------|-----------------|-----------------|--------|----------------|---------|-------|
| `PositionConfig` | `gps_enabled = 4` | `gps_mode` added v2.2.21 (2024-02-01); `[deprecated=true]` annotated **v2.7.4** | v2.7.15 | `gps_mode = 13` (`GpsMode` enum: `NOT_PRESENT / ENABLED / DISABLED`) | ✅ **Not shown** — PositionConfigScreen uses `gps_mode` exclusively. | ⚠️ **Written on every save** — reads `deviceGpsEnabled` as a fallback on load (legacy bridge), and saves `pc.gpsEnabled = gpsMode == 1` alongside `pc.gpsMode` on every write. Sends the deprecated field to all firmware versions regardless. |
| `PositionConfig` | `gps_attempt_time = 6` | **v2.2.18** (2024-01-11 pre); stable v2.2.19 (2024-01-21) | v2.2.19 | Implicit via `position_broadcast_smart_enabled` / intervals | ✅ **Not shown** | ✅ **Not shown** |
| `DisplayConfig` | `compass_north_top = 4` | `compass_orientation` added v2.3.13 (2024-06-18); `[deprecated=true]` annotated **v2.7.4** | v2.7.15 | `compass_orientation` enum (`DEGREES / NORTH_UP / HEADING_UP`) | ❌ **Still shown and writable** — `DisplayConfigItemList` renders a `SwitchPreference` for `compass_north_top` and writes it back. `compass_orientation` is not surfaced on either firmware range. | ✅ **Fixed** in Apple PR [#1847](https://github.com/meshtastic/Meshtastic-Apple/pull/1847) (May 2026) — shows `compass_orientation` picker for firmware ≥ 2.3.13, legacy toggle for older firmware. |
| `DisplayConfig` | `gps_format = 2` | **v2.7.4** (2025-08-09 pre) | v2.7.15 | Removed — unused | ✅ **Not shown** | ✅ **Fixed** in Apple PR [#1857](https://github.com/meshtastic/Meshtastic-Apple/pull/1857) (May 2026) — dead `gpsFormat` state variable removed. |

---

## 4. Deprecated Fields — Removed from Active Use

| Proto message | Deprecated field | Deprecated since | Stable | Android | Apple |
|--------------|-----------------|-----------------|--------|---------|-------|
| `CannedMessageConfig` | `enabled = 9` | **v2.7.4** (2025-08-09 pre) | v2.7.15 | ❌ **Still shown and writable** | ❌ **Still shown and writable** — toggle writes `cmc.enabled` on save |
| `CannedMessageConfig` | `allow_input_source = 10` | **v2.7.4** (2025-08-09 pre) | v2.7.15 | ❌ **Still shown and writable** — also has a max_size bug (enforces 63 bytes; proto `max_size:16` → 15 chars) | ❌ **Still shown and writable** — hard-codes `"rotEnc1"`, `"upDown1"`, `"_any"` on save |
| `User` | `macaddr = 4` | Deprecated in 2.1.x | — | ✅ Not in settings UIs | ✅ Not in settings UIs |
| `MeshPacket` | `delayed = 13` | Deprecated in 2.1.x | — | ✅ Not in settings UIs | ✅ Not in settings UIs |

---

## 5. Additional Finding: `allow_input_source` max_size mismatch (Android)

Android's `CannedMessageConfigItemList` enforces `maxSize = 63` for `allow_input_source`, but the proto `.options` annotation is `max_size:16` (max 15 chars). The comment on the adjacent line even says `// allow_input_source max_size:16` but the constraint value is wrong. Since the field is also deprecated, the correct fix is removal rather than a size correction.

---

## 6. Firmware Version Gating Recommendations

Both apps have built-in infrastructure for version-aware behaviour:

**Android** — `DeviceVersion` (in `core/model`) converts version strings to a comparable integer (`2.7.12` → `20712`). Comparisons use `>=`:
```kotlin
// Pattern already used in the codebase:
if (deviceVersion >= DeviceVersion("2.3.15")) {
    // hide deprecated field / show replacement
}
```

**Apple** — `AccessoryManager.checkIsVersionSupported(forVersion:)` returns `true` when the connected firmware is ≥ the given version (uses `String.compare(..., options: .numeric)`):
```swift
// Pattern already used in the codebase (e.g. supportsTAKv2, heartbeat gating):
if accessoryManager.checkIsVersionSupported(forVersion: "2.3.15") {
    // hide deprecated field / show replacement
}
```

The firmware version is available as `DeviceMetadata.firmware_version` (proto field 1), which both apps already read and store on connection.

### Per-field gating table

| Field / Value | Hide/migrate when firmware ≥ | Backward behaviour for older firmware |
|---------------|------------------------------|---------------------------------------|
| `ROUTER_CLIENT` role | **v2.3.15** | Show as selectable option (both apps currently do this — ✅ Android already correct; ✅ Apple migrates) |
| `REPEATER` role | **v2.7.11** | Show as selectable option; **Apple needs migration** from role 4 → show a "Role deprecated" warning or fall back to CLIENT |
| `LONG_SLOW` preset | **v2.7.17** | Show as selectable option for firmware < 2.7.17; **Apple should add to `userSelectable` exclusion list** gated on `checkIsVersionSupported("2.7.17")` |
| `VERY_LONG_SLOW` preset | **v2.5.0** | Show as selectable option for firmware < 2.5.0 (edge case — very old firmware only) |
| `DeviceConfig.serial_enabled` | **v2.4.3** | Show legacy toggle for firmware < 2.4.3; ✅ both apps already handle this (neither shows the field) |
| `DeviceConfig.is_managed` | **v2.4.3** | Same — ✅ both apps correct |
| `PositionConfig.gps_enabled` write-back | **v2.7.4** | Write `pc.gpsEnabled` only when firmware < 2.7.4 as a backward-compat bridge; remove unconditional write otherwise. **Apple action required.** |
| `PositionConfig.gps_attempt_time` | **v2.2.19** | Show for firmware < 2.2.19 — ✅ both apps already hide it |
| `DisplayConfig.compass_north_top` | **v2.3.13** | Show old toggle only for firmware < 2.3.13; show `compass_orientation` picker for ≥ 2.3.13. ✅ **Apple fixed** in PR [#1847](https://github.com/meshtastic/Meshtastic-Apple/pull/1847) (May 2026). Android still needs updating. |
| `DisplayConfig.gps_format` | **v2.7.4** | ✅ **Apple fixed** in PR [#1857](https://github.com/meshtastic/Meshtastic-Apple/pull/1857) (May 2026) — dead `gpsFormat` state variable removed |
| `CannedMessageConfig.enabled` | **v2.7.4** | Show toggle for firmware < 2.7.4; hide for ≥ 2.7.4. **Both apps need updating.** |
| `CannedMessageConfig.allow_input_source` | **v2.7.4** | Show text field for firmware < 2.7.4; hide for ≥ 2.7.4. **Both apps need updating.** |

### Suggested implementation pattern (Apple — `CannedMessagesConfig.swift`)
```swift
// Only show deprecated enable toggle for firmware that still honours it
if !accessoryManager.checkIsVersionSupported(forVersion: "2.7.4") {
    Toggle("Enable Canned Messages", isOn: $enabled)
}

// Use compass_orientation picker for modern firmware; legacy bool for old firmware
if accessoryManager.checkIsVersionSupported(forVersion: "2.3.13") {
    Picker("Compass Orientation", selection: $compassOrientation) { ... }
} else {
    Toggle("Compass North Top", isOn: $compassNorthTop)
}
```

### Suggested implementation pattern (Android — `CannedMessageConfigItemList.kt`)
```kotlin
val deviceVersion = state.deviceVersion // DeviceVersion from radioConfigState

// Only show deprecated fields for firmware that still uses them
if (deviceVersion < DeviceVersion("2.7.4")) {
    SwitchPreference(title = "Enable", checked = formState.value.enabled, ...)
    EditTextPreference(title = "Input Source", value = formState.value.allow_input_source, ...)
}

// Show compass_orientation for modern firmware, legacy bool for old
if (deviceVersion >= DeviceVersion("2.3.13")) {
    DropDownPreference(title = "Compass Orientation", selectedItem = formState.value.compass_orientation, ...)
} else {
    SwitchPreference(title = "Compass North Top", checked = formState.value.compass_north_top, ...)
}
```

---

## 7. Summary Matrix

| # | Item | Deprecated since (stable) | Android | Apple | Priority |
|---|------|--------------------------|---------|-------|----------|
| A | `ROUTER_CLIENT` role | v2.3.15 | ✅ Filtered | ✅ Migrated | — Done |
| B | `REPEATER` role | v2.7.15 | ✅ Filtered | ❌ No migration; nil rawValue | High |
| C | `LONG_SLOW` preset | *(no stable yet)* | ✅ Filtered | ❌ Still selectable | High |
| D | `compass_north_top` → `compass_orientation` | v2.7.15 | ❌ Still writable | ✅ **Fixed** in Apple PR [#1847](https://github.com/meshtastic/Meshtastic-Apple/pull/1847) — picker for ≥ 2.3.13, legacy toggle for older firmware | High (Android) |
| E | `CannedMessageConfig.enabled` | v2.7.15 | ❌ Still writable | ❌ Still writable | Medium |
| F | `CannedMessageConfig.allow_input_source` | v2.7.15 | ❌ Still writable (+size bug) | ❌ Still writable | Medium |
| G | `PositionConfig.gps_enabled` write-back | v2.7.15 | ✅ Not written | ❌ Written unconditionally | Medium |
| H | `VERY_LONG_SLOW` preset | v2.7.15 (comment: v2.5) | ✅ Filtered | ✅ Absent | — Done |
| I | `gps_format` dead code | v2.7.15 | ✅ Not shown | ✅ **Fixed** in Apple PR [#1857](https://github.com/meshtastic/Meshtastic-Apple/pull/1857) — dead state var removed | — Done |
| J | `DeviceConfig.serial_enabled` / `is_managed` | v2.7.15 | ✅ Correctly hidden | ✅ Correctly hidden | — Done |
| K | `gps_attempt_time` | v2.2.19 | ✅ Not shown | ✅ Not shown | — Done |
