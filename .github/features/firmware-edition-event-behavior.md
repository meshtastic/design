# Event Firmware Edition — Client Behavior

When a Meshtastic device reports a non-vanilla `firmware_edition` in its `MyNodeInfo`, client applications adapt their UI and notification behavior to provide an event-specific experience. This spec covers the `FirmwareEdition` proto enum, how clients detect event firmware, and the expected behaviors across platforms.

## Overview

The `FirmwareEdition` enum (defined in `meshtastic/mesh.proto`) allows firmware builds to self-identify as event-specific editions. Clients use this field to:

1. **Show event branding** — swap the toolbar/navigation icon with event artwork and display a welcome message.
2. **Adjust notification defaults** — automatically disable noisy new-node notifications at large gatherings.
3. **Display human-readable event names** in device info / firmware sections.

## Proto Definition

```protobuf
enum FirmwareEdition {
  VANILLA        = 0;   // Standard firmware
  SMART_CITIZEN  = 1;   // Environmental monitoring network
  OPEN_SAUCE     = 16;  // Maker conference (CA)
  DEFCON         = 17;  // Hacker conference
  BURNING_MAN    = 18;  // Desert gathering
  HAMVENTION     = 19;  // Dayton amateur radio convention
  DIY_EDITION    = 127; // Placeholder for unofficial events
}
```

**Convention:** Values 0–15 are reserved for project editions; values 16–126 are event editions; 127 is the DIY catch-all.

The field is reported by the device in `MyNodeInfo.firmware_edition` and is available to clients immediately after connection.

## Behavior 1: Event Branding (Easter Egg)

### Trigger

The client observes `MyNodeInfo.firmware_edition` **while the device is in a Connected state**. If the edition maps to a known event, branding activates. On disconnect (or reconnection to vanilla firmware), branding deactivates.

### UI Changes

| Element | Default (Vanilla) | Event Edition |
|---|---|---|
| Toolbar / navigation icon | Meshtastic logo | Event-specific artwork (PNG/SVG) |
| Toolbar icon tap | No action | Shows welcome snackbar/toast (e.g., "Welcome to Hamvention! 🍖📻") |
| Node details firmware section | Raw edition name | Human-readable event name (e.g., "Hamvention") |

### Event Registry

Each event edition maps to display metadata:

| Edition | Display Name | Has Custom Icon | Welcome Message |
|---|---|---|---|
| `OPEN_SAUCE` | Open Sauce | ❌ (fallback to logo) | "Welcome to Open Sauce! 🔧🎉" |
| `DEFCON` | DEFCON | ❌ (fallback to logo) | "Welcome to DEFCON! 💀📡" |
| `BURNING_MAN` | Burning Man | ❌ (fallback to logo) | "Welcome to Burning Man! 🔥🏜️" |
| `HAMVENTION` | Hamvention | ✅ (ham + Meshtastic art) | "Welcome to Hamvention! 🍖📻" |
| `DIY_EDITION` | — | — | Not treated as event |

Events without a custom icon fall back to the standard Meshtastic logo in the toolbar but still show the welcome message on tap and the human-readable name in device info.

### Adding a New Event

To add support for a new event, a client needs:

1. A drawable asset (optional — falls back to default logo if omitted)
2. A localized welcome message string
3. A mapping entry from the `FirmwareEdition` enum value to display metadata

No proto changes are needed unless a new enum value is required (coordinated via the protobufs repo).

## Behavior 2: Notification Auto-Disable

### Problem

At large events (hundreds or thousands of nodes), new-node discovery notifications create excessive noise. Users at events typically don't need to be notified about every new node joining the mesh.

### Trigger

On first connection to a device reporting an event `firmware_edition` (values 16–126), the client automatically disables new-node notifications.

### Rules

| Scenario | Action |
|---|---|
| Connect to event firmware, notifications enabled | Auto-disable new-node notifications; set `autoDisabledByEvent` flag |
| Connect to event firmware, notifications already disabled | No change; do not set flag |
| User manually re-enables notifications while on event firmware | Respect the choice; do not re-disable until next connection |
| Reconnect to vanilla firmware after event auto-disable | Re-enable new-node notifications; clear `autoDisabledByEvent` flag |
| Reconnect to vanilla firmware, was never auto-disabled | No change |

### State

| Key | Type | Default | Description |
|---|---|---|---|
| `autoDisabledByEvent` | Boolean | `false` | Set when the client auto-disables notifications due to event firmware. Cleared on reconnection to vanilla. |

## Sub-tasks

- [ ] Create Android implementation issue.
- [ ] Create iOS implementation issue.
- [ ] Create Web implementation issue.
