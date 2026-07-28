# Event Firmware Edition — Client Behavior

When a Meshtastic device reports a non-vanilla `firmware_edition` in its `MyNodeInfo`, client applications adapt their UI and notification behavior to provide an event-specific experience. This spec covers the `FirmwareEdition` proto enum, the hosted metadata clients read, and the expected behaviors across platforms.

## Overview

The `FirmwareEdition` enum (defined in `meshtastic/mesh.proto`) allows firmware builds to self-identify as event-specific editions. Clients use this field to:

1. **Show event branding** — swap the toolbar icon for event artwork and open an event info sheet.
2. **Apply the event's theme** — the edition's brand colors and typefaces, with a user opt-out.
3. **Adjust notification defaults** — automatically silence noisy new-node notifications at large gatherings.
4. **Display human-readable event names** in device info / firmware sections.
5. **Nudge users off event firmware** once the event has ended.

## Proto Definition

```protobuf
enum FirmwareEdition {
  VANILLA        = 0;   // Standard firmware
  SMART_CITIZEN  = 1;   // Environmental monitoring network
  OPEN_SAUCE     = 16;  // Maker conference (CA)
  DEFCON         = 17;  // Hacker conference
  BURNING_MAN    = 18;  // Desert gathering
  HAMVENTION     = 19;  // Dayton amateur radio convention
  FAB            = 20;  // International Fab Lab digital fabrication conference
  DIY_EDITION    = 127; // Placeholder for unofficial events
}
```

**Convention:** Values 0–15 are reserved for project editions; values 16–126 are event editions; 127 is the DIY catch-all.

The field is reported by the device in `MyNodeInfo.firmware_edition` and is available to clients immediately after connection.

## Metadata Source

Display metadata is **data-driven, not hardcoded in clients**. Adding an event is a metadata change, not a client release.

| | |
|---|---|
| Source of truth | `GET https://api.meshtastic.org/resource/eventFirmware` |
| Backing repo | `meshtastic/api` — `data/eventFirmware.json` |
| Icons | `meshtastic/api` — `static/eventFirmware/<slug>.png`, served at `resource/eventFirmware/<slug>.png` |
| Offline fallback | Clients bundle a copy of the manifest, refreshed on release |

Clients match the enum **name** reported by the device (`DEFCON`) against each entry's `edition` key. An edition with no manifest entry gets no branding and no theme, but still triggers the notification default in Behavior 3.

### Manifest shape

```jsonc
{
  "edition": "DEFCON",              // FirmwareEdition enum name — the match key
  "displayName": "DEF CON 34",      // human-readable, shown in UI
  "welcomeMessage": "Welcome to DEF CON 34! 💀",
  "tag": "DEFCON",                  // short label
  "eventStart": "2026-08-06",       // ISO-8601, resolved in timeZone
  "eventEnd": "2026-08-09",
  "timeZone": "America/Los_Angeles",// IANA id
  "location": "Las Vegas Convention Center, Las Vegas, Nevada, USA",
  "iconUrl": "https://api.meshtastic.org/resource/eventFirmware/defcon34.png",
  "accentColor": "#0D294A",         // primary; the ambient wash color
  "domain": "defcon.meshtastic.org",
  "links": [{ "label": "Event Website", "url": "https://defcon.org" }],
  "theme": {
    "name": "Agency",               // the event's own theme name
    "tagline": "Agency is self-determination. …",
    "colors": { "primary": "#0D294A", "secondary": "#017FA4", "accent": "#E0004E" },
    "palette": ["#0D294A", "#017FA4", "#105F66", "#6CCDB8", "#F1B435", "#E0004E"],
    "fonts": { "heading": "Lato", "body": "Atkinson Hyperlegible" }
  },
  "firmware": { "slug": "defcon34", "version": "…", "zipUrl": "…", "releaseNotes": "…" }
}
```

Every field except `edition` is optional. Clients must degrade rather than fail: an edition with only an `accentColor` gets a wash and nothing else.

**`welcomeMessage` and `tagline` are deliberately not localized.** Moving them into data traded per-language translation for per-event editability without a client release. Do not route them through the client's translation pipeline; they arrive as authored English.

**`fonts` are family names, not URLs** (`Lato`, not a font file). Resolving them is platform-specific and optional — Android binds them only in the Google flavor, where a downloadable-font provider exists, and falls back to the app typeface elsewhere.

## Behavior 1: Event Branding

### Trigger

The client observes `MyNodeInfo.firmware_edition` **while the device is in a Connected state**. If the edition maps to a manifest entry, branding activates. On disconnect (or reconnection to vanilla firmware), branding deactivates.

### UI Changes

| Element | Default (Vanilla) | Event Edition |
|---|---|---|
| Toolbar / navigation icon | Meshtastic logo | Event artwork, circle-clipped |
| Toolbar icon tap | No action | Opens the event info sheet |
| Device info firmware section | Raw edition name | `displayName` from the manifest |

### Icon resolution

Three tiers, in order — there is never an empty slot:

1. The hosted `iconUrl`.
2. A bundled per-edition asset, if the client ships one.
3. The standard Meshtastic logo.

The bundled tier matters offline and before a manifest refresh reaches users. It also means a client can ship an icon ahead of the hosted one, or vice versa, without coordination.

### Event info sheet

Tapping the branding opens a sheet — not a transient snackbar, since the content is worth dwelling on and contains links. It surfaces, in order, whichever of these the manifest carries:

- Event artwork, `displayName`, and `theme.name`
- `welcomeMessage`
- `theme.tagline`
- `location` and the `eventStart`–`eventEnd` range
- Each entry in `links`, labeled
- The **"Use event theme"** opt-out (Behavior 2)

## Behavior 2: Event Theme

The edition's brand identity applied app-wide, distinct from the branding icon: it is governed by a user-facing opt-out, while the icon and sheet always remain available.

| Surface | Treatment |
|---|---|
| Toolbar background | `accentColor` at ~12% alpha, composited over the app surface |
| Brand rule | `theme.palette` as a horizontal gradient hairline under the toolbar |
| Info sheet header | Flat `accentColor` band, closed by the same palette gradient |
| Typography | `theme.fonts` across the type scale, where the platform can resolve them |

### Why a palette rule and not a richer wash

An ambient wash can only ever show **one** color, and it must stay faint enough to keep title text legible. That makes it a poor carrier for a six-color palette, and actively misleading for editions whose primary is very dark — DEF CON's `#0D294A` washed at 12% over a dark surface is invisible, which read as "theming is broken" rather than "this event's color is navy". The rule is where the rest of the palette shows up, at a size that cannot compete with content.

Keep the sheet header a single flat color for the same reason: a gradient behind the title makes its contrast ratio a function of where the text happens to fall.

### Contrast is the client's responsibility

Brand palettes are authored for the event's own print and web materials, not for a client's light **and** dark surfaces. Binding a brand hex straight to a tint produces illegible UI in one theme or the other — DEF CON's navy fails on dark, FAB26's `#EAB14B` fails on light.

Clients should pick tints by walking candidates in preference order — `theme.colors.accent`, then the rest of `theme.palette` — and taking the first that clears **WCAG AA for graphical objects (3:1)** against the surface it sits on, falling back to the platform's standard secondary content color when none does.

Note the split in intent: `accentColor` / `theme.colors.primary` is the *calm* color, chosen to recede behind text. `theme.colors.accent` is the *loud* one, for small marks that should pop. A bare primary should not be promoted into a highlight.

### Opt-out

A **"Use event theme"** switch in the info sheet disables the wash, the rule, and the fonts. The branding icon and the sheet itself stay — the toggle governs ambient theming, not the client's knowledge of the event. Default on.

## Behavior 3: Notification Auto-Disable

### Problem

At large events (hundreds or thousands of nodes), new-node discovery notifications create excessive noise. Users at events typically don't need to be notified about every new node joining the mesh.

### Trigger

On connection to a device reporting **any non-vanilla `firmware_edition`**, the client automatically disables new-node notifications. This is keyed off the enum alone, not the manifest — an edition with no metadata entry still silences notifications.

### Rules

| Scenario | Action |
|---|---|
| Connect to event firmware, not already auto-disabled | Disable new-node notifications; set the auto-disabled flag |
| Connect to event firmware, flag already set | No change |
| Reconnect to vanilla firmware with the flag set | Re-enable new-node notifications; clear the flag |
| Reconnect to vanilla firmware, flag not set | No change |

### State

| Key | Type | Default | Description |
|---|---|---|---|
| auto-disabled-for-event | Boolean | `false` | Set when the client silences notifications due to event firmware. Cleared on reconnection to vanilla. Android calls this `nodeEventsAutoDisabledForEvent`. |

### Known divergences

Two cases the current Android implementation handles differently from an earlier draft of this spec. Flagged rather than silently blessed — other platforms should decide deliberately, and ideally all three converge:

- **A user who had already turned new-node notifications off** still gets the flag set on connecting to event firmware, and is therefore force-*re-enabled* on returning to vanilla. Gating the flag on the notifications having actually been on would preserve the user's choice.
- **Manually re-enabling notifications while on event firmware** does not clear the flag, so a later reconnect to vanilla re-enables them again (harmless), and subsequent event connections never re-disable them.

## Behavior 4: Post-Event Nudge

Event firmware ships factory-default configuration and is not intended as a daily driver. Once `eventEnd` has passed **in the event's own `timeZone`**, a client connected to that edition should surface a persistent, non-dismissable prompt toward the firmware update flow.

Drive this from the metadata date, not from a stored "event is over" bit: the prompt then appears whenever an ended-event device connects and disappears on its own once the device is re-flashed. A missing or unparseable `eventEnd` must never be treated as ended.

## Adding a New Event

For an event whose enum value already exists, no client changes are needed:

1. Add an entry to `data/eventFirmware.json` in `meshtastic/api`.
2. Add `static/eventFirmware/<slug>.png` and point `iconUrl` at it.

Optionally, clients may bundle the icon so it appears offline and before their next manifest refresh.

A new enum value requires a proto change coordinated via the `meshtastic/protobufs` repo, and clients must then pick up the new protobufs release.

## Platform Status

| Platform | Branding | Theme | Notifications | Post-event | Notes |
|---|---|---|---|---|---|
| Android | ✅ | ✅ | ✅ | ✅ | Fonts are Google-flavor only |
| Apple | — | — | — | — | Not yet implemented |
| Web | — | — | — | — | Not yet implemented |

## Sub-tasks

- [x] Android implementation.
- [ ] Create iOS implementation issue.
- [ ] Create Web implementation issue.
- [ ] Resolve the two notification divergences above and align all platforms.
