# [PARENT] [ALIGNMENT]: Status Message

## Decision

A node publishes one short free-text status, an away message such as "Going to the farm.. to grow wheat.", "Battery Low", or "Ready to mesh". Clients display other nodes' status wherever that node's identity already appears, and let the local node edit its own.

An empty status renders nothing. No placeholder, no em dash, no "No status" row.

The value is untrusted free text from the mesh. Display it verbatim as plain text, never as markup, links, or HTML.

Editing happens from the connected node's long-press menu, not from a standalone config screen.

## Context

Firmware 2.8 carries this as `ModuleConfig.StatusMessageConfig` with a `NodeStatus` broadcast. Android is the reference build for the display side.

A status can arrive either from the node's module config or as a broadcast update, so a current status may be known before the config has been read.

The editing surface changed after this spec was first written. A dedicated config screen is too much ceremony for one short text field, so editing moved to the connected node's long-press menu beside the display name edit, and the standalone screen goes away. Display rules were not affected by that change.

## Data model

`node_status` is a UTF-8 string with a maximum of 80 bytes. The limit is counted in bytes rather than characters, so emoji and non-Latin scripts consume the budget faster.

There is one status per node. Setting a new value replaces the old one, and clearing sends an empty string. Empty and unset are treated identically.

The feature requires firmware 2.8.0 or later. On older firmware, hide or disable the editor rather than showing a broken or empty field.

## Required Client Behavior

1. On the node list or node card, show a single row directly beneath the node's name and role, only when the status is non-empty. Use a leading Notes glyph at roughly 16dp in a low-emphasis outline tint to label the row, with the status text in body or medium type in the standard on-surface color. Clamp to two lines with an ellipsis so status can never grow the card without bound.
2. In node details, show a labeled row with the label "Status Message", the full status as its value, and the same Notes glyph for continuity. There is more room here, so the two-line clamp may be relaxed.
3. Use the same Notes icon on every surface and every client. Do not substitute a different glyph per platform.
4. Do not tint the status text with node-identity color or status-indicator colors.
5. Offer editing from the connected node's long-press or context menu, next to the display name edit, opening the same style of popup input. The node-details status row may offer the same popup for the local node as an additional entry point.
6. Use a single-line plain-text input with a trailing clear action that appears only when the field is non-empty. Clearing sends an empty string.
7. Offer editing only for the connected node. The action is absent on other nodes' menus, while disconnected, and on firmware older than 2.8.0.
8. Prefill the editor from the node's current broadcast status when no config value has been read, so the user edits the live status rather than a blank field.
9. Enforce the 80-byte ceiling at input. Prefer a remaining-budget hint over silent truncation, and make clear that the limit is in bytes when multi-byte text overflows earlier than expected.
10. While disconnected, keep showing the last known value on existing displays even though the edit action is gone.

## Accessibility

The leading Notes icon is decorative and should be hidden from assistive technology; the status text is the accessible content. Node details exposes the label and value as one readable pair. The clear action needs an accessible label. Keep contrast at 4.5:1 or better, honor Dynamic Type and OS text scaling, and clamp on line count rather than a fixed height.

## Localization

The field label, screen title, and the "Status Message" detail label are localized chrome. The status value itself is user content and must never be translated, transformed, or reflowed. Reuse the emoji and right-to-left handling already used for message text.

The only reference string is `status_message`, "Status Message" in English.

## Acceptance Criteria

- A non-empty status appears on both the node card and node details, with the same icon on every client.
- An empty, unset, or whitespace-only status renders no row at all.
- Status text never exceeds two lines on the node card.
- The edit action appears only for the connected node, only on firmware 2.8.0 or later, and only while connected.
- The editor enforces 80 bytes and reports the limit in bytes.
- Status renders as plain text, with no markup, link, or HTML interpretation.

## Platform Tracking

- [x] Android display, Meshtastic-Android#5987, shipped in #4163, #4577, and #5070
- [x] Android editing move, [Meshtastic-Android#6932](https://github.com/meshtastic/Meshtastic-Android/issues/6932), shipped in [#6951](https://github.com/meshtastic/Meshtastic-Android/pull/6951) and [#7047](https://github.com/meshtastic/Meshtastic-Android/pull/7047). The standalone screen, its `ModuleRoute` and its settings entry are gone, and touch-and-hold the connected node gives Update status.
- [x] Apple, Meshtastic-Apple#1996, editing move Meshtastic-Apple#2362
- [ ] Web, meshtastic/web#1193
- [x] BaseUI, meshtastic/firmware#10806
- [ ] MUI, [standalone-ui#36](https://github.com/meshtastic/standalone-ui/issues/36) and [device-ui#332](https://github.com/meshtastic/device-ui/issues/332). Neither started. [device-ui#333](https://github.com/meshtastic/device-ui/issues/333) is a closed duplicate of #332, not abandoned work.

