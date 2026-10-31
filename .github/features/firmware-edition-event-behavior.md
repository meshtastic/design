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

Display metadata is **data-driven, not hardcoded in clients**. Adding an event is a metadata change, not a client release — subject to the caching rules below.

| | |
|---|---|
| Source of truth | `GET https://api.meshtastic.org/resource/eventFirmware` |
| Backing repo | `meshtastic/api` — `data/eventFirmware.json` |
| Icons | `meshtastic/api` — `static/eventFirmware/<slug>.png`, served at `resource/eventFirmware/<slug>.png` |
| Offline seed | Clients bundle a copy of the manifest, refreshed at release |

Clients match the enum **name** reported by the device (`DEFCON`) against each entry's `edition` key. An edition with no manifest entry gets no branding and no theme, but still triggers the notification default in Behavior 3.

### Caching and staleness

Recommended shape: a persistent cache **seeded from the bundled snapshot** and refreshed from the endpoint stale-while-revalidate — serve what's cached, refresh behind it, and rate-limit refresh *attempts* so a failing fetch offline doesn't retry on every lookup. Persist rather than hold in memory, so the snapshot survives a process restart.

This bounds what "no client release" actually buys:

| Client state | Sees a newly added event? |
|---|---|
| Online, cache already refreshed | Yes |
| Online, first lookup | Only if the refresh completes within the lookup's bounded wait — otherwise not until branding is re-evaluated (see below) |
| Offline since install | **No** — bundled seed only, until the client next reaches the network |
| Offline, cached from an earlier fetch | Whatever that fetch contained |

So a client release is still what guarantees an event reaches *every* user. Add events to the manifest early enough that clients have refreshed before the event starts, and treat bundling the icon (see Behavior 1) as the offline path.

**A cache write must re-evaluate the active edition.** Refreshing the manifest is only useful if the currently connected device's branding, theme, and sheet contents are recomputed when new rows land — atomically, so artwork from one edition never pairs with a name from another. Expose the lookup as an **observable** keyed on the edition name rather than a one-shot read: a one-shot resolves once when the connection or edition changes, so a refresh that arrives afterward sits in the cache unseen until the user reconnects.

This is the shape to copy, not the shape that shipped — Android currently resolves the edition with a suspending one-shot inside a `combine` over connection state, so it has exactly the staleness described above. Tracked as a sub-task.

### Trust boundary

The manifest is first-party but **remote**, and it drives rendered text, opened links, fetched images, and font selection. Clients must treat it as untrusted input at the point of use:

- **Tolerate schema drift.** Ignore unknown fields and accept missing ones rather than failing the whole payload — one malformed entry must not take down branding for every other edition. Drop entries whose `edition` is absent.
- **Restrict URLs.** Require `https` for `iconUrl` and every `links[].url`, and reject anything else before fetching or opening it. A link field is a navigation primitive; without a scheme allowlist the manifest can invoke arbitrary handlers on the device.
- **Hold `firmware.zipUrl` to a higher bar than the rest.** It is the only field that feeds an *executable artifact* onto a device, so a scheme check is not sufficient. Before presenting or consuming it: require `https`, validate the host against an **approved-origin allowlist** (the project's own release hosts — not merely "some HTTPS URL"), and verify artifact integrity — a checksum or signature carried out of band, plus the firmware's own image validation — before anything is written to a device. A manifest compromise must not become arbitrary firmware delivery. Clients that only display the event's firmware version, and never fetch it, should say so explicitly rather than leaving the sink implied. Android does not consume this field today.
- **Treat all text as display-only.** `displayName`, `welcomeMessage`, `tagline`, and `links[].label` render as plain text — never as markup, HTML, or a link target.
- **Bound images.** Enforce a decoded size limit and accept only expected image types; render the fallback icon on violation.
- **`fonts` are family-name identifiers, not URLs.** Resolve them only against the platform's own font provider. Never treat the value as a fetchable location.
- **Colors are `#RRGGBB`.** Parse strictly and drop malformed entries rather than substituting a default that misrepresents the brand.

### Executable firmware is authorized separately

The display manifest does not authorize installation. In particular,
`firmware.zipUrl` is informational and must never be promoted directly into an
in-app OTA action. A client that offers event firmware OTA fetches a separately
signed contract for the selected edition:

```text
GET https://api.meshtastic.org/resource/eventFirmware/{EDITION}/ota
```

Unknown editions return `404`. If the API signing key is unavailable, the
endpoint fails closed with `503`; it must not return an unsigned contract.

The response is an Ed25519 envelope. `payload` is the exact UTF-8 JSON bytes,
base64 encoded, that were signed:

```jsonc
{
  "keyId": "event-release-2026",
  "payload": "<base64 contract JSON>",
  "signature": "<base64 Ed25519 signature over decoded payload bytes>"
}
```

Clients ship the trusted public key keyed by `keyId`. A key delivered by this
endpoint, the display manifest, or an artifact host is not a trust root.
Unknown keys, malformed base64, invalid signatures, expired contracts, and
unsupported schema versions make in-app installation unavailable.
After signature verification, the client requires `payload.edition` to exactly
match the requested `{EDITION}`. Contract caches are keyed by edition; a valid
contract for one edition must never satisfy a request for another.

The schema-1 contract is scoped to one event release:

```jsonc
{
  "schemaVersion": 1,
  "releaseId": "defcon34-2.8.0.b00d76f",
  "edition": "DEFCON",
  "version": "2.8.0.b00d76f",
  "issuedAt": "2026-07-29T00:00:00Z",
  "expiresAt": "2026-10-01T00:00:00Z",
  "artifacts": [
    {
      "pioEnv": "tbeam-s3-core",
      "hwModel": 12,
      "architecture": "esp32-s3",
      "version": "2.8.0.b00d76f",
      "format": "bin",
      "url": "https://raw.githubusercontent.com/meshtastic/meshtastic.github.io/<40-hex-commit>/event/...",
      "sha256": "<64 lowercase hex characters>",
      "byteCount": 2383792,
      "minimumSourceVersion": "2.7.26",
      "partitionRole": "app0",
      "partitionScheme": "8MB",
      "dfuProtocol": null,
      "minimumBootloaderVersion": null
    }
  ],
  "standardArtifacts": [
    {
      "pioEnv": "tbeam-s3-core",
      "hwModel": 12,
      "architecture": "esp32-s3",
      "version": "2.7.26.54e0d8d",
      "format": "bin",
      "url": "https://raw.githubusercontent.com/meshtastic/meshtastic.github.io/<40-hex-commit>/firmware-2.7.26.54e0d8d/firmware-tbeam-s3-core-2.7.26.54e0d8d.bin",
      "sha256": "<64 lowercase hex characters>",
      "byteCount": 2213168,
      "minimumSourceVersion": "2.7.26",
      "partitionRole": "app0",
      "partitionScheme": "8MB",
      "dfuProtocol": null,
      "minimumBootloaderVersion": null
    }
  ]
}
```

`issuedAt` and `expiresAt` use UTC ISO-8601 timestamps with whole-second
precision (`yyyy-MM-dd'T'HH:mm:ss'Z'`). `releaseId` and `keyId` are stable,
bounded identifiers; they are not URLs or user-facing labels.

`artifacts` installs the event edition. `standardArtifacts` provides the
explicit return path to ordinary Meshtastic firmware. A production contract
must contain both sets; a client must not infer the return artifact by editing
an event URL or selecting whatever release happens to be latest.

Selection is exact on `pioEnv`, `hwModel`, and `architecture`, with exactly one
matching artifact. The client also enforces `minimumSourceVersion` and
architecture-specific compatibility:

Signed versions use `MAJOR.MINOR.PATCH` or
`MAJOR.MINOR.PATCH.SOURCE`, where the first three components are non-negative
decimal integers and `SOURCE` contains only ASCII letters, digits, `_`, or `-`.
A connected device version may additionally begin with `v`. Clients remove
that prefix, compare the three numeric components lexicographically, and ignore
the source-reference suffix for minimum-version ordering. Short versions,
extra suffix components, integer overflow, and every other grammar are
unsupported and reject the artifact.

- ESP32 artifacts are bare application `.bin` payloads for `app0`, never
  factory, merged, filesystem, or OTA-loader images. Their partition scheme
  must exactly match the connected target. `partitionRole` and
  `partitionScheme` are required and non-null; missing, null, or unknown values
  reject the artifact before compatibility checks.
- nRF52 artifacts are target-specific Nordic DFU OTA ZIPs. The contract names
  the DFU protocol and minimum compatible bootloader. `dfuProtocol` and
  `minimumBootloaderVersion` are required and non-null; missing, null, or
  unknown values reject the artifact before compatibility checks. A client
  that cannot establish the installed bootloader's compatibility must not
  offer in-app DFU.
- Unsupported architectures and devices without a proven app OTA path use the
  web flasher.

Artifact URLs are HTTPS, use an approved project origin, and identify immutable
content. For `raw.githubusercontent.com`, the revision path component is a
40-hex commit SHA. Clients reject redirects, enforce the signed byte count while
downloading, then verify both byte count and SHA-256 before opening the existing
OTA/DFU flow. Any failure falls back to the web flasher without writing bytes to
the device.

Signing keys are release infrastructure. Private keys live only in deployment
secrets; public keys ship in clients. Rotation adds a new `keyId` and public key
to clients before the API begins signing with it. Revocation requires removing
the affected contract and shipping a client update when the trust key itself is
compromised.

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

Where a UI element needs a value that is absent, fall back rather than render blank. In particular, **`displayName` falls back to the raw enum name** (`DEFCON`), so a minimal entry — or an edition with no entry at all — still labels the firmware section correctly.

**`welcomeMessage` and `tagline` are deliberately not localized.** Moving them into data traded per-language translation for per-event editability without a client release. Do not route them through the client's translation pipeline; they arrive as authored English.

**`fonts` are family names, not URLs** (`Lato`, not a font file). Resolving them is platform-specific and optional — Android binds them only in the Google flavor, where a downloadable-font provider exists, and falls back to the app typeface elsewhere.

## Behavior 1: Event Branding

### Trigger

The client observes `MyNodeInfo.firmware_edition` **while the device is in a Connected state**. If the edition maps to a manifest entry, branding activates. On disconnect (or reconnection to vanilla firmware), branding deactivates.

Treat the active edition as **derived state, not a latched one-shot**: it should follow the currently connected device's reported value for as long as that connection lasts. A change from one non-vanilla edition to another — reconnecting to a different device, or re-flashing between events — must swap the artwork, name, theme, and sheet contents together. Recomputing from the reported edition gets this for free; caching the first edition seen does not, and leaves stale branding on screen.

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

Event firmware ships factory-default configuration and is not intended as a daily driver. Once the event is over, a client connected to that edition should surface a persistent, non-dismissable prompt toward the firmware update flow.

### The date boundary

`eventEnd` is date-only, so the rule must be stated exactly. **`eventEnd` is inclusive — the event has ended when the current local date in the event's `timeZone` is strictly later than `eventEnd`.**

```text
ended = today(in: timeZone) > eventEnd
```

A device is therefore *not* nudged during the final day of the event, and is nudged from local midnight at the start of the following day. Resolve "today" in the event's own zone, not the device's: an attendee who flies home the last night should not be nudged early because their phone moved timezone.

Fall back to the device zone only when `timeZone` is absent or unparseable, and **never treat a missing or unparseable `eventEnd` as ended** — an unknown end date must not nudge users off working firmware.

Drive this from the metadata date, not from a stored "event is over" bit: the prompt then appears whenever an ended-event device connects and disappears on its own once the device is re-flashed.

## Behavior 5: Event Firmware Installation

An event info or firmware-updates screen may offer a convenient install action,
but only when the signed contract above authorizes one exact artifact for the
connected device. Display metadata alone never enables the action.

Before installation the client:

1. Confirms the same device is still connected.
2. Fetches and verifies the edition's signed contract.
3. Selects one exact target and validates source-version and OTA compatibility.
4. Downloads with a signed size ceiling and verifies SHA-256.
5. Re-checks that the same device is connected, rebuilds its target identity,
   and repeats exact-target and compatibility selection. A disconnect or
   identity change during download aborts the install.
6. Hands the local verified file to the platform's existing OTA/DFU flow.

If any step is unavailable or fails, the primary action opens
`https://flasher.meshtastic.org`. After the event, a compatible device running
the event edition uses `standardArtifacts` through the same process. Clients
must label this as a firmware rewrite, keep their existing OTA safety UI, and
must not imply that background execution can keep a BLE/Wi-Fi transfer alive.

## Adding a New Event

For an event whose enum value already exists, no client code changes are needed:

1. Add an entry to `data/eventFirmware.json` in `meshtastic/api`.
2. Add `static/eventFirmware/<slug>.png` and point `iconUrl` at it.
3. To enable in-app OTA, add a reviewed entry to
   `data/eventFirmwareOTA.json` with immutable per-target event and standard
   artifacts, then configure the API's release signing key. The signing
   `keyId` and public key must already be trusted by released clients. If they
   are not, first ship a client release containing the public key and wait for
   that release to reach users before publishing or enabling the OTA contract.

Land both **well before the event** so online clients have refreshed their cache by the time attendees arrive. Per the caching table above, users who have been offline since install will not see the event until their client next reaches the network — bundling the icon and shipping the manifest snapshot in a client release is what covers them.

A new enum value requires a proto change coordinated via the `meshtastic/protobufs` repo, and clients must then pick up the new protobufs release.

## Platform Status

| Platform | Branding | Theme | Notifications | Post-event | Notes |
|---|---|---|---|---|---|
| Android | ✅ | ✅ | ✅ | ✅ | Fonts Google-flavor only; no URL scheme allowlist; edition lookup is a one-shot, so a cache refresh needs a reconnect |
| Apple | PR | PR | PR | PR | Signed event OTA contract and installer are in draft; hardware event install remains untested |
| Web | — | — | — | — | Not yet implemented |

## Sub-tasks

- [x] Android implementation.
- [ ] Create iOS implementation issue.
- [ ] Create Web implementation issue.
- [ ] Resolve the two notification divergences above and align all platforms.
- [ ] Enforce the URL scheme allowlist on link and icon fetches (Android does not today).
- [ ] Make the edition lookup observable so a manifest refresh re-evaluates active branding without a reconnect (Android).
- [ ] Provision and document the production event-firmware signing key and rotation process.
- [ ] Hardware-validate each artifact target before adding it to a signed OTA contract.
