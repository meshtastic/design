# 📡 Unheard-since-config-change - client UI spec

> [!IMPORTANT]
> **Mark nodes the radio hasn't heard on the LoRa settings it is using now.** Changing preset, region or frequency slot moves the radio to a different channel; the node DB doesn't move with it. Clients keep listing nodes that can no longer be reached, and sends into that list fail - silently for channel broadcasts, which carry no ack. Firmware reports it per node; clients mark the unset ones and offer one tap to clear them.

**Tracking:** design#146 · **Firmware:** `NodeInfo.heard_on_current_lora` (meshtastic/protobufs#1060, meshtastic/firmware#11811) · **Origin:** https://redd.it/1w7y2st

---

## Goal

After a config change, a client can tell the user which nodes have gone unreachable, instead of showing a full node list where nothing works.

## Data model

| Field | Type | Notes |
| --- | --- | --- |
| `heard_on_current_lora` | bool | True when this radio has heard the node over RF on the LoRa config in force now. Each node records the slot it was heard on, and firmware **derives** the field by comparing that against the slot the radio is committed to. The slot is region, preset (or custom bw/sf/cr), `override_frequency`, `channel_num`, and the **primary channel name**. Nothing is cleared on a config change, so leaving a config and coming back restores the previous answers. |

- Not set for MQTT hears - those arrived over the internet, not this radio's channel. An MQTT-only node therefore reads false for the life of the entry, not because a setting changed. `via_mqtt` already marks them; see **Don't**.
- Firmware owns it because MUI has no phone, and because config changes made from the device menu or CLI never reach a client.

> [!NOTE]
> **Capability gate - firmware ≥ 2.N.** Older firmware never sends the field and proto3 bools default to false, so an ungated client marks **every** node. Gate **persistence** too: a false read from old firmware must not survive into storage that a later upgrade won't correct until each node is next heard. Where a client's version check defaults permissive on unknown firmware, don't use that default here.

## Where it appears

### Node list / node card
A marker on rows where the bit is unset, **distinguishable from the existing offline/last-heard treatment** - different claim. A node can be online and unheard-on-this-config at once.

### Aggregate
When most of the list is unset, one banner beats a hundred marks: *"87 nodes not heard on your current LoRa settings."* Offer one tap to clear, preserving favourites where the client has that concept.

### Filter
An option to hide unheard nodes, alongside existing node-list filters.

## States

| State | Behavior |
| --- | --- |
| **Heard** | Normal row. No marker. |
| **Unheard** | Marker + counted in the aggregate. |
| **Unsupported (< 2.N)** | No marker, no aggregate, nothing persisted. |

## Accessibility

Append the marker to the row's accessibility label wherever the row already builds one by hand (both Apple rows do). The marker glyph is decorative - the text carries it.

## Don't

- **Don't** say or imply the node is on a different preset. A radio can't observe a channel it isn't tuned to. The honest claim is "not heard on your current LoRa settings" - the field does not say a setting changed, and returning to a previous config restores the marks on its own.
- **Don't** mark or offer up `via_mqtt` nodes. They read false permanently, so acting on the raw field badges every node on an MQTT-uplinked mesh and offers it for removal - where deleting achieves nothing, because the next uplinked packet brings it back.
- **Don't** auto-delete. The client node DB is deliberately a superset of the device's; only a user action may shrink it.
- **Don't** reuse the offline styling - a user needs to tell the two apart.
- **Don't** show anything on pre-feature firmware.

---

## Per-client status

- [x] **Protocol** - meshtastic/protobufs#1060 (merged, `9a78479`)
- [x] **Firmware** - meshtastic/firmware#11745 (merged, `2a01676`)
- [ ] **MUI** - meshtastic/device-ui#387
- [x] **Android** - meshtastic/Meshtastic-Android#7053
- [ ] **iOS** - meshtastic/Meshtastic-Apple#2427
- [ ] **Docs** - meshtastic/meshtastic#2649
- [ ] **Web** - not yet filed

