# Device Screen Mirroring & Remote Control — Feature Specification

Status: **draft** · protocol shipped in [meshtastic/protobufs#1054](https://github.com/meshtastic/protobufs/pull/1054) · reference device implementation [meshtastic/firmware#11681](https://github.com/meshtastic/firmware/pull/11681) · reference client [meshtastic/Meshtastic-Android#6987](https://github.com/meshtastic/Meshtastic-Android/pull/6987) · MUI seam [meshtastic/device-ui#394](https://github.com/meshtastic/device-ui/pull/394) · tooling [meshtastic/meshtastic-mcp#78](https://github.com/meshtastic/meshtastic-mcp/pull/78) · prior art [meshtastic/web#224](https://github.com/meshtastic/web/issues/224)

The key words MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY are to be interpreted as in RFC 2119. "Device" means the Meshtastic node firmware; "client" means any locally connected app (Android, desktop, iOS, web, python) speaking the phone API over BLE, USB serial, or TCP.

## 1. Overview

A client can view the device's screen live and drive its UI remotely. The device streams snapshots of its framebuffer to the local client; the client renders them and sends input events back. On devices that paint a monochrome UI onto a color panel, a small palette sideband lets the client reproduce the panel's true colors at monochrome bandwidth.

**Goals**

- Remote support: see what the user's screen says without being there.
- Headless and pocketed nodes: operate a device whose screen/buttons are inaccessible.
- Deterministic UI testing: pixel-exact screen assertions without cameras.

**Non-goals (this revision)**

- Mirroring LVGL/MUI color UIs (RGB565). The wire format reserves fields for it (§4.3 rects); no device implements it yet.
- Mirroring a *remote* node's screen over the mesh. Frames ride `FromRadio`, which never crosses the mesh (§8).
- Audio, video rates, or lossless guarantees. This is a best-effort snapshot stream at UI cadence (~1 fps idle).

## 2. Capability discovery — `DisplayInfo`

`DeviceMetadata.display` (field 16), sent during the connection handshake:

| Field | Meaning |
| --- | --- |
| `width`, `height` | Panel dimensions in pixels |
| `format` | The `DisplayFrame.Format` frames from this device will use (currently always `MONO_VLSB`) |
| `panel_class` | `OLED`, `LCD`, `TFT`, `EINK`, `HUB75`, or `PANEL_CLASS_UNSPECIFIED` (runtime-selected panels, e.g. Linux-native) |
| `has_touch` | Panel accepts touch input |

- Absence of `display` means the device has no screen **or** runs pre-feature firmware. Clients SHOULD show mirroring UI opportunistically in that case, but MUST NOT rely on its presence.
- Clients SHOULD adapt to `panel_class == EINK`: prefer one-shot frame requests over continuous mirroring, and expect multi-second refresh latency (§6.5).
- Clients SHOULD only offer tap-to-touch when `has_touch` is true (§5.2).

## 3. Session model

### 3.1 Arming

Two `AdminMessage` verbs control the stream. Both are **local-connection-only**: a device receiving them over the mesh, or a build without a display, ignores them.

- `get_display_frame_request = 50` (bool): one-shot. Forces one frame on the next redraw, even if the screen is unchanged. Classified as an admin *request* (no session passkey needed). There is **no** `AdminMessage` response; the frame arrives out-of-band as `FromRadio.display_frame`.
- `set_display_mirror = 51` (bool): continuous mirroring on/off. **`false` is meaningful** — unlike most bool admin verbs this is not a trigger. The first frame arrives immediately on enable and acts as the acknowledgement. Not persisted across reboot; clients MUST re-arm after reconnect.

### 3.2 Lifecycle

- The device disarms and frees all mirror state when a client connection closes. Current firmware keeps a **single global arm flag**: any local client's disconnect disarms every client's stream (known limitation; per-client refcounted arming is the planned follow-up).
- Clients MUST disable mirroring when their mirror UI is dismissed and SHOULD treat a disconnect as an implicit disarm (reflect it in UI state rather than assuming the stream survives).
- Clients MUST NOT present a previously received frame as live after a disconnect or device change; clear held frames when a session ends.

## 4. Wire protocol

All messages ride the existing phone API (`FromRadio`, ≤512 bytes encoded per message). Both streams use the same completion rule: `offset + payload length == total` completes the unit.

### 4.1 `FromRadio.display_frame` — `DisplayFrame` (tag 21)

One chunk of a framebuffer snapshot:

| Field | Semantics |
| --- | --- |
| `width`, `height` | Full display dimensions (constant across a device's frames) |
| `format` | Pixel encoding of `data`. `MONO_VLSB = 1`: 1 bpp, vertical LSB-first pages — byte index `x + (y / 8) * width`, bit index `y % 8`. `FORMAT_UNSPECIFIED = 0` MUST NOT be sent |
| `frame_id` | Constant across one frame's chunks; increments per captured frame; wraps at uint32; restarts from 1 on reboot. Treat any change as "a new frame", never as ordering |
| `offset`, `total_size` | Byte position of this chunk in the frame buffer, and the full buffer size |
| `data` | ≤384 bytes of framebuffer |
| `rect_x/y/width/height` | Reserved for future partial-rect updates (unset today; see §9) |
| `palette_signature` | The `DisplayPalette` that colorizes this frame; `0` = render monochrome |

Guarantees a client MAY rely on:

- Chunks of one frame arrive **contiguously** (no other `display_frame` interleaves; `display_palette` messages may) and in **offset order**, so reassembly needs no reordering buffer. It does need loss detection: the device's queue to the client drops its oldest entry when full, and disabling mirroring mid-frame truncates the frame. A client MUST verify that `offset` equals the bytes it has already accumulated for this `frame_id`, MUST discard the partial frame on any gap or `frame_id` change, and MUST NOT render an incomplete frame. `frame_id` cannot reveal loss *within* a frame — every chunk of that frame carries the same value.
- A frame whose streaming has begun is always drained to completion, even if mirroring is disabled mid-frame.
- Only *changed* framebuffers are streamed (the device diffs snapshots), plus one forced frame per one-shot request or enable. A palette change with unchanged pixels also produces a new frame (§4.2).

Client reassembly requirements:

- `offset == 0` MUST start a new frame (this is also the reboot/torn-capture recovery path). Geometry (`width`/`height`) MUST be taken from the first chunk; a later chunk disagreeing MUST drop the partial frame.
- A chunk that is not the exact contiguous continuation (`frame_id`, `offset`, `total_size` all matching expectations) MUST drop the partial frame and await the next `offset == 0`.
- Clients MUST validate before allocating: `format` supported, `width > 0`, `height > 0`, `width * ceil(height / 8) == total_size`, and a sanity cap on `total_size` (reference: 16 KiB — a 320×240 1 bpp frame is 9600 bytes).

### 4.2 `FromRadio.display_palette` — `DisplayPalette` (tag 22)

Color devices paint the 1 bpp UI through a table of colored regions. Streaming that table lets a client render a **color-accurate** mirror at monochrome bandwidth.

| Field | Semantics |
| --- | --- |
| `signature` | Identity of this palette; changes whenever the region table or theme changes. `DisplayFrame.palette_signature` references it |
| `default_on_color`, `default_off_color` | RGB565 for set/clear pixels outside all regions. Authoritative on the `region_offset == 0` chunk |
| `region_offset`, `region_total` | Chunking by region index; `offset + regions length == total` completes the palette |
| `regions[≤16]` | `ColorRegion { x, y, width, height, on_color, off_color }`, in table order |

- All colors are RGB565 in **logical bit layout** (`RRRRRGGGGGGBBBBB`) — the device byte-swaps from panel order before sending.
- Precedence: a region with a **higher table index overrides** lower-indexed ones where they overlap, regardless of chunk boundaries.
- Palettes are sent only when the signature changes (per client), before the frames that reference them. Monochrome devices never send one.
- A client holding partial chunks of a signature that no longer matches incoming chunks MUST discard them. Clients SHOULD cap accepted `region_total` (reference: 512; firmware's own table caps at 48).
- Rendering rule per pixel: find the highest-indexed region containing `(x, y)`; use its `on_color`/`off_color` by the pixel's bit; otherwise the defaults. A frame referencing a palette the client doesn't hold yet SHOULD render monochrome and SHOULD be re-rendered when the palette arrives (frames self-heal to color).
- RGB565 → 8-bit expansion SHOULD use bit replication (`r8 = (r5 << 3) | (r5 >> 2)`), not plain scaling.

### 4.3 Size budget

`DisplayFrame` encodes ≤447 bytes and `DisplayPalette` ≤440, both under the 512-byte `MAX_TO_FROM_RADIO_SIZE` cap. A 128×64 frame is 3 chunks (~1 KB); a 320×240 1 bpp frame is 25 chunks (~10 KB). At the BaseUI idle cadence of 1 fps this is well within BLE throughput; clients need no flow control beyond normal `FromRadio` reads.

## 5. Remote input

Input reuses the pre-existing `AdminMessage.send_input_event = 27` (`InputEvent { event_code, kb_char, touch_x, touch_y }`), which injects into the firmware's InputBroker — the same path physical buttons use, so it works on every device UI unmodified.

### 5.1 Event codes (firmware `input_broker_event`)

| Code | Event | Client mapping guidance |
| --- | --- | --- |
| 10 | `SELECT` | OK button / Enter / Space / touch long-press |
| 11 | `SELECT_LONG` | OK long-press |
| 17–20 | `UP`, `DOWN`, `LEFT`, `RIGHT` | D-pad / arrow keys / swipe on the mirror |
| 24 | `CANCEL` | — |
| 27 | `BACK` | Back button / Esc / Backspace |
| 28 | `USER_PRESS` | Touch tap, **with coordinates** |

### 5.2 Touch forwarding

On `has_touch` devices, clients SHOULD map pointer input on the mirrored image to panel coordinates (`floor(px / rendered_size * panel_size)`, clamped) and send:

- tap → `USER_PRESS` (28) with `touch_x`/`touch_y` — matching what physical touch drivers emit;
- long-press → `SELECT` (10) with coordinates — likewise matching the physical driver.

### 5.3 Input transport & pacing

- Input SHOULD be sent on an immediate/priority path, never queued behind bulk admin traffic.
- Hold-to-repeat SHOULD use ~500 ms initial delay, then ~10 Hz — deliberately slower than OS typematic so events cannot outrun the radio's UI rendering. Repeat directions only; never auto-repeat `SELECT`/`BACK`.

## 6. Client UX requirements & guidance

Derived from TV-remote / emulator-overlay / accessibility research; the Android client is the reference.

1. **Directional cluster**: a circular 5-way ring (four 90° wedges around a center OK disc, hit-test by angle, dead band between disc and ring) is the preferred layout; a well-spaced cross of ≥48 dp targets is an acceptable minimum. `BACK` sits below the cluster. Every control MUST be reachable by assistive tech as a discrete button (per-wedge semantics; gesture surfaces are duplicates, never the only route).
2. **Keyboard capture** (pointer-based platforms): capturing focus on the mirror maps arrows/Enter/Esc per §5.1. Capture MUST be visibly indicated and MUST have an obvious exit (toggle control and/or click-again). Key-up events of captured keys MUST be consumed so they don't leak into the surrounding UI.
3. **Swipe-to-navigate**: a cardinal swipe on the mirror sends one direction event; sub-threshold movements (reference: 48 dp) are ignored.
4. **Rendering**: render each frame once into a native bitmap at 1:1 and upscale with nearest-neighbor filtering (crisp pixels, no interpolation seams). Never redraw per-pixel per UI frame.
5. **E-ink**: steer users toward one-shot Refresh; don't imply live cadence.
6. **State honesty**: the mirror toggle reflects connection state; disconnect resets it (§3.2); a stale frame is never displayed as live.

## 7. Device implementation requirements

For a firmware (or simulator) implementing the device side:

- **Capture point**: snapshot the framebuffer after each committed UI frame, from the thread that draws it. Diff against the last sent snapshot; stream only changes. On palette-driven devices, capture the region table **at paint time** — before any per-frame clearing — and stamp frames with the signature captured *with* that snapshot, not the live one.
- **Multi-client**: each client connection keeps its own drain cursors (frame `(id, offset)`, palette `(signature, region_offset)`) against the single shared snapshot, so coexisting clients receive complete units independently. A frame captured while a client is mid-drain restarts that client at offset 0 of the new frame.
- **Priority**: mirror data drains at the lowest phone-API priority — mesh packets, notifications, and sync replay always outrank pixels. Palette chunks precede frame chunks so the first rendered frame can be colored.
- **Redaction**: builds with display redaction (lockdown) MUST mirror the redacted screen, never the underlying content. Under client access control, frames and palettes MUST only be delivered to authorized clients (same bar as mesh packets).
- **Memory**: allocate nothing until armed; free on disarm/disconnect; account allocations in the platform's memory audit. Refuse panels whose 1 bpp size exceeds internal cursor width rather than truncating.

## 8. Security & privacy

- Screen contents are operator content (messages, positions, node names). They are confined to the local link by construction: frames ride `FromRadio`, which has no mesh path.
- The admin verbs act only from the local connection (`from == 0`); remote nodes cannot arm a mirror, and a passkey-authorized remote admin still cannot receive frames.
- Known gap (owned in firmware#11681): under client access control, an *unauthorized* local client can arm/disarm (control-plane DoS) though never read frames. Fixed by per-client arming.

## 9. Future work

- **Color/MUI streaming**: `Format.RGB565` + the reserved `rect_*` fields turn the same message into a dirty-rect stream fed by LVGL's flush callback — additive, no wire break. Viable over USB/TCP; needs throttling over BLE.
- **Per-client refcounted arming** (replaces the global flag). The per-client cursors it needs already exist.
- **Palette cache**: clients MAY keep the last few palettes keyed by signature so a one-shot frame taken across a theme change still colorizes.
- **Device bezels**: client-side cosmetic frames from the design repo's device art, keyed by `hw_model`, with a canonical screen-viewport rect per asset.
- **Firmware native test suite** (`test_screen_mirror`): chunk reassembly, mid-drain restart, palette signature changes incl. theme-only, memaudit balance.

## 10. Verification status

End-to-end verified on real hardware against the reference client (Android/desktop, shared KMP code):

- **RAK4631 (WisMesh Pocket)** — 128×64 OLED, monochrome mirror, D-pad/keyboard remote control.
- **LILYGO T-Deck** (BaseUI build) — 320×240 ST7789, color-accurate mirror via palette streaming, tap-to-touch, theme-recolor propagation.
- Build-verified additionally on Heltec V3, Heltec Mesh Node T114 (ST7789/nRF52), and the Linux-native target (coloring-disabled TFT combination).

