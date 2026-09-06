# Meshtastic-Firmware — Settings Validation Reference

This document describes the **firmware** layer of settings validation: the values
a device installs as defaults and streams to a client during the `want_config`
handshake, and the validation it applies to inbound `AdminMessage.set_*` writes
(over the PhoneAPI or remote admin).

It is the peer of [settings-validation-android.md](settings-validation-android.md)
and [settings-validation-apple.md](settings-validation-apple.md): where those
describe each client's **UI form layer**, this describes the device firmware
beneath them — the source of every default value and the final gatekeeper for
every write.

> **⚠️ Most config is copied wholesale.** Unlike the client form layers, the
> firmware applies **no per-field validation** to the majority of settings. The
> `set_config` / `set_module_config` handlers copy each sub-message into storage
> with a single struct assignment. The `Validation` column below reads `none` for
> every field the firmware accepts verbatim — which is most of them. Only fields
> with an explicit rule are checked; everything else relies on the client form
> layer for sanity. nanopb still enforces wire-level `max_size` / `max_count` /
> `int_size` limits from the `.options` files — an over-length value fails decode
> and the whole message is dropped.

**Sourced from:** `meshtastic/firmware`, branch `develop`, commit `91f930d5c`
(2026-05-22). Default installers live in `src/mesh/NodeDB.cpp`; inbound handlers
in `src/modules/AdminModule.cpp`. A fuller firmware reference (PhoneAPI handshake,
`MyNodeInfo` / `DeviceMetadata`, complete per-role default matrices) is maintained
in the firmware repo under `docs/`.

## Validation vocabulary

| Term | Meaning |
|------|---------|
| **none** | Field stored exactly as received — no firmware check. |
| **clamp** | Out-of-range value silently corrected; the write still succeeds. |
| **reject** | Message refused with a `Routing_Error`; nothing stored. |
| **sanitize** | Value rewritten in place to a safe form. |
| **fallback** | Disallowed value replaced with a specific safe default. |

Default values assume a stock build and the default `CLIENT` device role; the
`USERPREFS_*` compile-time overrides and per-role overrides are noted where they
apply (see [Role-Based Default Overrides](#role-based-default-overrides)).

---

## Table of Contents

- [Device Config Screens](#device-config-screens)
  - [User](#user-user)
  - [Device](#device-configdeviceconfig)
  - [Position](#position-configpositionconfig)
  - [Power](#power-configpowerconfig)
  - [Network](#network-confignetworkconfig)
  - [Display](#display-configdisplayconfig)
  - [LoRa](#lora-configloraconfig)
  - [Bluetooth](#bluetooth-configbluetoothconfig)
  - [Security](#security-configsecurityconfig)
- [Module Config Screens](#module-config-screens)
  - [MQTT](#mqtt-moduleconfigmqttconfig)
  - [Serial](#serial-moduleconfigserialconfig)
  - [External Notification](#external-notification-moduleconfigexternalnotificationconfig)
  - [Store & Forward](#store--forward-moduleconfigstoreforwardconfig)
  - [Range Test](#range-test-moduleconfigrangetestconfig)
  - [Telemetry](#telemetry-moduleconfigtelemetryconfig)
  - [Canned Message](#canned-message-moduleconfigcannedmessageconfig)
  - [Audio](#audio-moduleconfigaudioconfig)
  - [Remote Hardware](#remote-hardware-moduleconfigremotehardwareconfig)
  - [Neighbor Info](#neighbor-info-moduleconfigneighborinfoconfig)
  - [Ambient Lighting](#ambient-lighting-moduleconfigambientlightingconfig)
  - [Detection Sensor](#detection-sensor-moduleconfigdetectionsensorconfig)
  - [Paxcounter](#paxcounter-moduleconfigpaxcounterconfig)
  - [Status Message](#status-message-moduleconfigstatusmessageconfig)
  - [Traffic Management](#traffic-management-moduleconfigtrafficmanagementconfig)
  - [TAK](#tak-moduleconfigtakconfig)
- [Channel Config](#channel-config)
- [Role-Based Default Overrides](#role-based-default-overrides)
- [Authorization & Session Passkey](#authorization--session-passkey)
- [Inbound Packet Rate Limits](#inbound-packet-rate-limits)

---

## Device Config Screens

### User (`User`)

The User screen edits the device `owner` (a `User` protobuf). Defaults installed
by `installDefaultDeviceState()`; inbound writes via `set_owner` →
`handleSetOwner()`.

| Field | Default | Validation | Notes |
|-------|---------|------------|-------|
| `long_name` | `"Meshtastic xxxx"` (last 4 hex of node num) | **reject** + **sanitize** | Rejected (`BAD_REQUEST`) if non-empty and all-whitespace; otherwise copied into the 40-byte buffer, force-terminated, and `sanitizeUtf8()`. Empty value ⇒ left unchanged. |
| `short_name` | `"xxxx"` (last 4 hex of node num) | **reject** + **sanitize** | Same whitespace check; 5-byte buffer. |
| `is_licensed` | `false` | **none** | A change triggers `ensureLicensedOperation()` (may strip channel PSKs). |
| `is_unmessagable` | `false` | **none** | Role overrides set `true` for `ROUTER*` / `SENSOR` / `TRACKER` / `TAK_TRACKER`. |
| `id` | `"!" + node num` | **fallback** | Ignored on input — firmware always overwrites with `"!%08x"`. |
| `macaddr`, `hw_model`, `role`, `public_key` | firmware-managed | **none** | Not read from an inbound `set_owner`. |

`sanitizeUtf8()` replaces invalid lead bytes, truncated sequences, overlong
encodings, and surrogates with `?`. It runs **only** on the owner name fields —
no other inbound string is UTF-8-sanitized.

### Device (`Config.DeviceConfig`)

Installed by `installDefaultConfig()` + `installRoleDefaults()`; inbound via
`set_config` → `handleSetConfig()`.

| Field | Default | Validation | Notes |
|-------|---------|------------|-------|
| `role` | `CLIENT` | **fallback** | Deprecated `ROUTER_CLIENT` / `REPEATER` ⇒ `CLIENT`. On `USERPREFS_EVENT_MODE` builds, `ROUTER` / `ROUTER_LATE` ⇒ `CLIENT`. A role change triggers `installRoleDefaults()`. |
| `rebroadcast_mode` | `ALL` | **fallback** | `NONE` while role is `ROUTER` / `ROUTER_LATE` ⇒ forced to `ALL` (+ client warning). |
| `node_info_broadcast_secs` | `10800` (CLIENT) | **clamp** | Floored to `3600` (`min_node_info_broadcast_secs`) if lower. Role-dependent default. |
| `double_tap_as_button_press` | `false` | **none** | |
| `disable_triple_click` | `false` | **none** | |
| `led_heartbeat_disabled` | `false` | **none** | |
| `tzdef` | `""` | **none** | |
| `button_gpio` | `0` | **none** | `0` ⇒ board `BUTTON_PIN` define. |
| `buzzer_gpio` | `0` | **none** | `0` ⇒ board `PIN_BUZZER` define. |
| `buzzer_mode` | `ALL_ENABLED` | **none** | |

### Position (`Config.PositionConfig`)

Installed by `installDefaultConfig()` + `initConfigIntervals()`. Inbound via
`set_config`; the whole sub-message is copied with **no field validation**.
Latitude/longitude/altitude are not part of this message — fixed position is set
by the `set_fixed_position` admin action (also unvalidated).

| Field | Default | Validation | Notes |
|-------|---------|------------|-------|
| `position_broadcast_secs` | `3600` (CLIENT) | **none** | `IF_ROUTER(43200, 3600)`. |
| `position_broadcast_smart_enabled` | `true` | **none** | |
| `broadcast_smart_minimum_interval_secs` | `300` | **none** | |
| `broadcast_smart_minimum_distance` | `100` | **none** | metres. |
| `fixed_position` | `false` | **none** | Toggled by `set_fixed_position` / `remove_fixed_position`. |
| `gps_mode` | `ENABLED` | **none** | `DISABLED` / `NOT_PRESENT` on boards without GPS hardware. |
| `gps_update_interval` | `120` (CLIENT) | **none** | `IF_ROUTER(86400, 120)`. |
| `position_flags` | `811` (`ALTITUDE｜ALTITUDE_MSL｜SPEED｜HEADING｜DOP｜SATINVIEW`) | **none** | `TAK` / `TAK_TRACKER` use `777`. |
| `rx_gpio`, `tx_gpio`, `gps_en_gpio` | `0` | **none** | |

### Power (`Config.PowerConfig`)

| Field | Default | Validation | Notes |
|-------|---------|------------|-------|
| `is_power_saving` | `false` | **none** | Forced `true` on `USE_POWERSAVE` builds. |
| `on_battery_shutdown_after_secs` | `0` | **clamp** | If `> 0` and `< 30` ⇒ raised to `30`. `0` (never) stays `0`. |
| `adc_multiplier_override` | `0` | **none** | `0` ⇒ board `ADC_MULTIPLIER`. Firmware does **not** enforce the proto's documented 2.0–6.0 range. |
| `wait_bluetooth_secs` | `60` (CLIENT) | **none** | `IF_ROUTER(1, 60)`. |
| `sds_secs` | `4294967295` (CLIENT) | **none** | `IF_ROUTER(86400, UINT32_MAX)`. |
| `ls_secs` | `300` (CLIENT) | **none** | `IF_ROUTER(86400, 300)`. |
| `min_wake_secs` | `10` | **none** | |
| `device_battery_ina_address` | `0` | **none** | |
| `powermon_enables` | `0` | **none** | |

### Network (`Config.NetworkConfig`)

Every field is copied verbatim — no firmware-side validation.

| Field | Default | Validation | Notes |
|-------|---------|------------|-------|
| `wifi_enabled` | `false` | **none** | |
| `wifi_ssid` | `""` | **none** | nanopb limit 33 bytes. |
| `wifi_psk` | `""` | **none** | nanopb limit 65 bytes. Redacted on `get_config` responses. |
| `ntp_server` | `"meshtastic.pool.ntp.org"` | **none** | |
| `eth_enabled` | `false` | **none** | |
| `address_mode` | `DHCP` | **none** | |
| `ipv4_config` (`ip`, `gateway`, `subnet`, `dns`) | `0` | **none** | No IP-format check (the firmware stores raw `fixed32`s). |
| `rsyslog_server` | `""` | **none** | |
| `enabled_protocols` | `0` | **none** | |
| `ipv6_enabled` | `false` | **none** | |

### Display (`Config.DisplayConfig`)

Every field is copied verbatim — no firmware-side validation.

| Field | Default | Validation | Notes |
|-------|---------|------------|-------|
| `screen_on_secs` | `600` (CLIENT) | **none** | `IF_ROUTER(1, 600)`; `30` on `USE_POWERSAVE` / `T_WATCH_S3`. |
| `auto_screen_carousel_secs` | `0` | **none** | |
| `flip_screen` | `false` | **none** | `true` on `DISPLAY_FLIP_SCREEN` boards. |
| `units` | `METRIC` | **none** | |
| `oled` | `OLED_AUTO` | **none** | |
| `displaymode` | `DEFAULT` | **none** | `COLOR` on `HAS_TFT` boards. Setting `COLOR` disables Bluetooth (side effect). |
| `heading_bold` | `false` | **none** | |
| `wake_on_tap_or_motion` | `false` | **none** | `true` on `RAK4630` / `T_WATCH_S3`. |
| `compass_orientation` | `DEGREES_0` | **none** | |
| `use_12h_clock` | `false` | **none** | |
| `use_long_node_name` | `false` | **none** | |
| `enable_message_bubbles` | `false` | **none** | `true` on large-TFT boards. |
| `compass_north_top`, `gps_format` | `false` / `0` | **none** | Deprecated. |

### LoRa (`Config.LoRaConfig`)

The only heavily-validated sub-message. Inbound `set_config` for LoRa is validated
against a local copy (`handleSetConfig()` + `RadioInterface` helpers).

| Field | Default | Validation | Notes |
|-------|---------|------------|-------|
| `region` | `UNSET` | **reject** | Licensed-only regions require `owner.is_licensed`. `LORA_24` requires radio `wideLora()` capability (else `BAD_REQUEST`). A region change is fully validated; on failure the entire new LoRa config is discarded. |
| `use_preset` | `true` | **clamp** | Coerced by `clampConfigLora()` if the resulting config is invalid. |
| `modem_preset` | `LONG_FAST` | **clamp** / **reject** | Must be valid for the region. Invalid from the local client ⇒ clamped to the region default; invalid from a remote node ⇒ reverted to the previous value. |
| `bandwidth` | `0` | **clamp** / **reject** | Must fit the region's frequency span (manual mode). |
| `spread_factor` | `0` | **clamp** | Must be in `[5, 12]`; out of range (incl. `0`) ⇒ `11` (`LORA_SF_DEFAULT`). |
| `coding_rate` | `0` | **clamp** | Must be in `[4, 8]`; out of range ⇒ `5` (`LORA_CR_DEFAULT`). |
| `hop_limit` | `3` | **none** | Proto max is 7; firmware does not re-check inbound writes. |
| `channel_num` | `0` | **clamp** / **reject** | Must be ≤ the region's slot count. |
| `tx_enabled` | `true` | **fallback** | Forced `true` when moving from `UNSET` to a real region; `false` when moving to `UNSET`. |
| `tx_power` | `0` | **none** | `0` ⇒ max legal continuous power. |
| `frequency_offset` | `0` | **none** | |
| `override_frequency` | `0` | **none** | |
| `override_duty_cycle` | `false` | **none** | |
| `sx126x_rx_boosted_gain` | `true` | **none** | |
| `ignore_mqtt` | `false` | **fallback** | Forced `true` on a region change if the region's duty cycle is `< 100%`. |
| `config_ok_to_mqtt` | `false` | **none** | |
| `fem_lna_mode` | `NOT_PRESENT` (`ENABLED` on FEM boards) | **sanitize** | Normalized to `NOT_PRESENT` on FEM hardware that cannot control the LNA. |
| `pa_fan_disabled` | `false` | **none** | |
| `ignore_incoming` | empty | **none** | nanopb limit 3 entries. |
| `serial_hal_only` | `false` | **none** | |

**Region/preset validation** is performed by `RadioInterface::validateConfigRegion()`
and `checkOrClampConfigLora()`. A key firmware behaviour: an invalid LoRa config
from the **local client** is **clamped** to working values, but the same config
from a **remote admin node** is **rejected** (reverted) — a remote node must not
be able to knock a device onto incompatible radio parameters.

### Bluetooth (`Config.BluetoothConfig`)

Every field is copied verbatim — no firmware-side validation.

| Field | Default | Validation | Notes |
|-------|---------|------------|-------|
| `enabled` | `true` | **none** | `false` on TFT/MUI boards. |
| `mode` | `RANDOM_PIN` | **none** | `FIXED_PIN` on screenless boards. |
| `fixed_pin` | `123456` | **none** | **Not** range-checked or digit-counted by the firmware — any `uint32` is accepted. |

### Security (`Config.SecurityConfig`)

| Field | Default | Validation | Notes |
|-------|---------|------------|-------|
| `public_key` | empty | **sanitize** | Regenerated from the private key when a valid region is set. |
| `private_key` | empty | **sanitize** | A non-32-byte private key triggers a fresh keypair (unless licensed / region unset). |
| `admin_key` | empty | **none** | nanopb limits: max 3 entries, 32 bytes each. |
| `is_managed` | `false` | **fallback** | Forced `false` if no `admin_key` entry is 32 bytes (+ client warning) — prevents locking admin out. |
| `serial_enabled` | `true` | **none** | |
| `debug_log_api_enabled` | `false` | **none** | |
| `admin_channel_enabled` | `false` | **none** | |

---

## Module Config Screens

Inbound module config arrives via `set_module_config` → `handleSetModuleConfig()`.
Only `mqtt` and `serial` can cause a **reject** (a `BAD_REQUEST`); every other
module is copied wholesale.

### MQTT (`ModuleConfig.MQTTConfig`)

Validated by `MQTT::isValidConfig()` before the copy.

| Field | Default | Validation | Notes |
|-------|---------|------------|-------|
| `enabled` | `false` | **reject** | If `enabled` and not `proxy_to_client_enabled` on a build with no networking ⇒ reject. |
| `address` | `"mqtt.meshtastic.org"` | **reject** | The default server with a non-default port ⇒ reject. An unreachable custom server only logs a warning — config still saved. |
| `username` | `"meshdev"` | **none** | |
| `password` | `"large4cats"` | **none** | nanopb limit 32 bytes. |
| `encryption_enabled` | `true` | **none** | |
| `json_enabled` | `false` | **none** | Deprecated — ignored. |
| `tls_enabled` | `false` | **reject** | If `true` on a build without TLS support ⇒ reject. |
| `root` | `"msh"` | **none** | A region change appends `/<region>`. |
| `proxy_to_client_enabled` | `false` | **none** | |
| `map_reporting_enabled` | `false` | **none** | |
| `map_report_settings` (`publish_interval_secs`, `position_precision`, `should_report_location`) | `0` | **none** | The firmware does **not** enforce the client-side 3600 s minimum. |

### Serial (`ModuleConfig.SerialConfig`)

Validated by `SerialModule::isValidConfig()` — but **only** on `ARCH_ESP32` /
`ARCH_NRF52` / `ARCH_RP2040` (excl. ESP32-S2 / ESP32-C3). All defaults proto-zero.

| Field | Default | Validation | Notes |
|-------|---------|------------|-------|
| `override_console_serial_port` + `mode` | `false` / `DEFAULT` | **reject** | If `override_console_serial_port` is `true`, `mode` must be `NMEA` / `CALTOPO` / `MS_CONFIG`. |
| `enabled`, `echo`, `rxd`, `txd`, `baud`, `timeout` | `false` / `0` | **none** | |

### External Notification (`ModuleConfig.ExternalNotificationConfig`)

All defaults are board-pin-dependent; on a board with no notification hardware
every field is `0` / `false`. No firmware-side validation of any field.

| Field | Default | Validation | Notes |
|-------|---------|------------|-------|
| `enabled` | `false` | **none** | `true` if the board defines `PIN_BUZZER` / `PIN_VIBRATION` / `LED_NOTIFICATION` / `HAS_I2S`. |
| `output`, `output_buzzer`, `output_vibra` | `0` | **none** | Board pin defaults. |
| `output_ms` | `0` | **none** | `500` / `1000` on boards with vibra / LED. |
| `nag_timeout` | `0` | **none** | `2` / `15` on boards with vibra / buzzer. |
| `active`, `use_pwm`, `use_i2s_as_buzzer` | `false` | **none** | |
| `alert_message*`, `alert_bell*` | `false` | **none** | Board-conditional. |

### Store & Forward (`ModuleConfig.StoreForwardConfig`)

All defaults `0` / `false`. No firmware-side validation.

| Field | Default | Validation |
|-------|---------|------------|
| `enabled`, `heartbeat`, `is_server` | `false` | **none** |
| `records`, `history_return_max`, `history_return_window` | `0` | **none** |

### Range Test (`ModuleConfig.RangeTestConfig`)

All defaults `0` / `false`. No firmware-side validation.

| Field | Default | Validation |
|-------|---------|------------|
| `enabled`, `save`, `clear_on_reboot` | `false` | **none** |
| `sender` | `0` | **none** |

### Telemetry (`ModuleConfig.TelemetryConfig`)

`device_update_interval` is set by `initModuleConfigIntervals()`; all other
defaults proto-zero. No firmware-side validation.

| Field | Default | Validation | Notes |
|-------|---------|------------|-------|
| `device_update_interval` | `2147483647` (`MAX_INTERVAL`) | **none** | Coalesced to a real cadence at runtime; role overrides set shorter values. |
| `device_telemetry_enabled` | `false` | **none** | |
| `environment_measurement_enabled` | `false` | **none** | `true` for the `SENSOR` role. |
| `environment_update_interval` | `0` | **none** | `300` for the `SENSOR` role. |
| `environment_screen_enabled`, `environment_display_fahrenheit` | `false` | **none** | |
| `air_quality_enabled` | `false` | **none** | |
| `air_quality_interval` | `0` | **none** | |
| `power_measurement_enabled`, `power_screen_enabled` | `false` | **none** | |
| `power_update_interval` | `0` | **none** | |
| `health_measurement_enabled`, `health_screen_enabled` | `false` | **none** | |
| `health_update_interval` | `0` | **none** | |
| `air_quality_screen_enabled` | `false` | **none** | |

### Canned Message (`ModuleConfig.CannedMessageConfig`)

All defaults proto-zero on a stock build (`T_LORA_PAGER` sets the rotary-input
fields). No firmware-side validation.

| Field | Default | Validation | Notes |
|-------|---------|------------|-------|
| `rotary1_enabled`, `updown1_enabled`, `send_bell` | `false` | **none** | |
| `inputbroker_pin_a` / `_b` / `_press` | `0` | **none** | |
| `inputbroker_event_cw` / `_ccw` / `_press` | `NONE` | **none** | |
| `enabled`, `allow_input_source` | `false` / `""` | **none** | Deprecated. |

The canned-message **text** is a separate `CannedMessageModuleConfig.messages`
string, default `"Hi|Bye|Yes|No|Ok"`, set via `set_canned_message_module_messages`
— `strncpy` into the buffer, **no** content check or UTF-8 sanitization.

### Audio (`ModuleConfig.AudioConfig`)

All defaults `0` / `false`. No firmware-side validation.

| Field | Default | Validation |
|-------|---------|------------|
| `codec2_enabled` | `false` | **none** |
| `ptt_pin`, `i2s_ws`, `i2s_sd`, `i2s_din`, `i2s_sck` | `0` | **none** |
| `bitrate` | `CODEC2_DEFAULT` | **none** |

### Remote Hardware (`ModuleConfig.RemoteHardwareConfig`)

All defaults `0` / `false`. No firmware-side validation.

| Field | Default | Validation | Notes |
|-------|---------|------------|-------|
| `enabled`, `allow_undefined_pin_access` | `false` | **none** | |
| `available_pins` | empty | **none** | nanopb limit 4 entries. |

### Neighbor Info (`ModuleConfig.NeighborInfoConfig`)

| Field | Default | Validation | Notes |
|-------|---------|------------|-------|
| `enabled` | `false` | **none** | |
| `update_interval` | `0` | **clamp** | If below `14400` (`min_neighbor_info_broadcast_secs`) it is reset to `21600` (`default_neighbor_info_broadcast_secs`). |
| `transmit_over_lora` | `false` | **none** | |

### Ambient Lighting (`ModuleConfig.AmbientLightingConfig`)

No firmware-side validation — note the client form layers enforce 0–31 / 0–255
ranges that the firmware does **not**.

| Field | Default | Validation | Notes |
|-------|---------|------------|-------|
| `led_state` | `false` | **none** | |
| `current` | `10` | **none** | |
| `red`, `green`, `blue` | derived from node number | **none** | `nodenum` byte values. |

### Detection Sensor (`ModuleConfig.DetectionSensorConfig`)

No firmware-side validation.

| Field | Default | Validation | Notes |
|-------|---------|------------|-------|
| `enabled` | `false` | **none** | |
| `minimum_broadcast_secs` | `45` | **none** | |
| `state_broadcast_secs` | `0` | **none** | |
| `send_bell`, `use_pullup` | `false` | **none** | |
| `name` | `""` | **none** | |
| `monitor_pin` | `0` | **none** | |
| `detection_trigger_type` | `LOGIC_HIGH` | **none** | Not the enum-zero (`LOGIC_LOW`). |

### Paxcounter (`ModuleConfig.PaxcounterConfig`)

All defaults `0` / `false`. No firmware-side validation.

| Field | Default | Validation | Notes |
|-------|---------|------------|-------|
| `enabled` | `false` | **none** | |
| `paxcounter_update_interval` | `0` | **none** | |
| `wifi_threshold`, `ble_threshold` | `0` | **none** | Proto documents an intended `-80`; firmware stores `0` and the module applies `-80` at runtime. |

### Status Message (`ModuleConfig.StatusMessageConfig`)

| Field | Default | Validation |
|-------|---------|------------|
| `node_status` | `""` | **none** |

### Traffic Management (`ModuleConfig.TrafficManagementConfig`)

All 14 fields default proto-zero. No firmware-side validation. `Default.h`
defines intended runtime defaults (`position_precision_bits` 24,
`position_min_interval_secs` 43200) that the module applies at runtime when the
stored field is `0` — they are **not** written into the stored config.

| Field | Default | Validation |
|-------|---------|------------|
| `enabled`, `position_dedup_enabled`, `nodeinfo_direct_response`, `rate_limit_enabled`, `drop_unknown_enabled`, `exhaust_hop_telemetry`, `exhaust_hop_position`, `router_preserve_hops` | `false` | **none** |
| `position_precision_bits`, `position_min_interval_secs`, `nodeinfo_direct_response_max_hops`, `rate_limit_window_secs`, `rate_limit_max_packets`, `unknown_packet_threshold` | `0` | **none** |

### TAK (`ModuleConfig.TAKConfig`)

| Field | Default | Validation | Notes |
|-------|---------|------------|-------|
| `team` | `Unspecifed_Color` (firmware renders Cyan) | **none** (no-op) | `handleSetModuleConfig()` has **no `case` for `tak`** — a `set_module_config` carrying the `tak` variant is silently a no-op (nothing stored, no error returned). TAK config cannot be set via `set_module_config` in this firmware revision. |
| `role` | `Unspecifed` (firmware renders TeamMember) | **none** (no-op) | Same. |

---

## Channel Config

Inbound via `set_channel` → `handleSetChannel()` → `Channels::setChannel()`.
A factory device exposes 8 channel slots (`MAX_NUM_CHANNELS`): index 0 is the
populated primary, indexes 1–7 are `DISABLED` with empty settings.

| Field | Default (channel 0) | Validation | Notes |
|-------|----------------------|------------|-------|
| `index` | `0` | **reject** | Must be `0 ≤ index < 8`; otherwise `BAD_REQUEST`. `get_channel_request` is rejected the same way. |
| `role` | `PRIMARY` | **sanitize** | Setting a channel to `PRIMARY` demotes every other `PRIMARY` channel to `SECONDARY`. |
| `name` | `""` | **none** | nanopb limit 12 bytes. Empty ⇒ rendered as the modem-preset name. |
| `psk` | `{0x01}` (default-key shorthand) | **none** | Not validated at write time. `getKey()` later interprets it: `0` = off, `1`–`10` = built-in keys, 16 / 32 bytes = AES-128 / AES-256. A short key (2–15 or 17–31 bytes) is silently **zero-padded** to 16 / 32 — not rejected. |
| `uplink_enabled`, `downlink_enabled` | `false` | **none** | |
| `module_settings.position_precision` | `13` | **none** | |
| `module_settings.is_muted` | `false` | **none** | |

If the owner is licensed, `ensureLicensedOperation()` strips the PSK of the admin
channel and any encrypted channel (plaintext ham operation).

---

## Role-Based Default Overrides

The defaults above are for the `CLIENT` role. `installRoleDefaults()` revises
several values when the role differs. Roles not listed (`CLIENT`, `CLIENT_MUTE`,
`CLIENT_BASE`) use the stock defaults unchanged.

| Setting | ROUTER | ROUTER_LATE | SENSOR | TRACKER | TAK | TAK_TRACKER | LOST_AND_FOUND | CLIENT_HIDDEN |
|---------|--------|-------------|--------|---------|-----|-------------|----------------|----------------|
| `device.rebroadcast_mode` | `CORE_PORTNUMS_ONLY` | — | — | — | — | — | — | `LOCAL_ONLY` |
| `device.node_info_broadcast_secs` | — | — | — | — | `86400` | `86400` | — | `2147483647` |
| `position.position_broadcast_secs` | `43200` | — | — | — | `86400` | `180` | `300` | `2147483647` |
| `position.position_broadcast_smart_enabled` | — | — | — | — | `false` | `true` | `false` | `false` |
| `position.position_flags` | — | — | — | — | `777` | `777` | — | — |
| `telemetry.device_update_interval` | `43200` | `86400` | `3600` | `3600` | `86400` | `86400` | — | `2147483647` |
| `telemetry.environment_measurement_enabled` | — | — | `true` | — | — | — | — | — |
| `owner.is_unmessagable` | `true` | `true` | `true` | `true` | — | `true` | — | — |

`ROUTER` also re-runs the interval initializers, flipping every `IF_ROUTER`
default (`gps_update_interval`, `ls_secs`, `sds_secs`, `wait_bluetooth_secs`,
`screen_on_secs`) to its router branch.

---

## Authorization & Session Passkey

Before any `set_*` is applied, `handleReceivedProtobuf()` runs an authorization
gate — the firmware analog of "who is allowed to write settings at all":

1. **Local origin** (connected client) — allowed unless `security.is_managed`.
2. **Legacy admin channel** — allowed only if `security.admin_channel_enabled`.
3. **PKI-authenticated remote** — the sender's public key must match one of the
   up-to-three 32-byte `security.admin_key[]` entries; otherwise
   `ADMIN_PUBLIC_KEY_UNAUTHORIZED`.
4. Anything else ⇒ `NOT_AUTHORIZED`.

**Session passkey** — a state-changing message from a *remote* node must echo
back an 8-byte `session_passkey` issued on a prior `get_*` response. It is valid
for 300 s; a mismatch or timeout ⇒ `ADMIN_BAD_SESSION_KEY`. Locally-connected
clients skip this check.

---

## Inbound Packet Rate Limits

Beyond settings, the PhoneAPI rate-limits client-originated `MeshPacket`s by
portnum (`handleToRadioPacket()`). Over-limit packets are dropped:

| Portnum | Limit |
|---------|-------|
| `TRACEROUTE_APP` | once per 30 s; multi-hop traceroute to a broadcast address is refused |
| `POSITION_APP`, `WAYPOINT_APP`, `ALERT_APP`, `TELEMETRY_APP` | once per 10 s |
| `TEXT_MESSAGE_APP` | once per 2 s (`RATE_LIMIT_EXCEEDED`) |

Duplicate packet IDs seen recently are also dropped.
