# [ALIGNMENT]: 2.8 messaging, direct message availability and public key handling

## Decision

Clients must not offer to send a direct message the radio will refuse, and must never send the radio a contact with an empty public key.

On 2.8 a direct message is encrypted with PKC, and a radio holding no public key for the destination returns `PKI_SEND_FAIL_PUBLIC_KEY` rather than falling back to the channel key. A client that shows a message action for such a node is offering a path that cannot work. Separately, `add_contact` carrying an empty key clears the key the radio already holds, which turns a working conversation into a failing one.

## Context

PKC is an ECDH between the sender's private key and the recipient's public key, so each side needs the other's key. A single missing key breaks the pair in both directions, and the two directions fail differently, which makes this hard to recognize in the field.

When the sender has no key for the recipient, the sending radio refuses before transmit and the user sees "Recipient key unavailable". When the recipient has no key for the sender, the message transmits, the far end cannot decrypt it and never acks, and the sender sees `MAX_RETRANSMIT`, which looks like an RF problem rather than a key problem.

A node whose packets have been heard but whose NodeInfo has not arrived has no key on file. This is common rather than exceptional. On one test radio, 28 of its 37 direct neighbors had no key.

The recovery is Exchange User Info, which sends `NODEINFO_APP` with `want_response`. That portnum is exempt from PKC, so it still sends when no key is held, and it resolves both directions at once.

Firmware applies `add_contact` through `CopyUserToNodeInfoLite`, which assigns `public_key` unconditionally. Firmware has since gained a guard that preserves a stored key when a keyless contact arrives, but only builds carrying that guard are protected, so clients should not send these at all.

## Required Client Behavior

Applies to Android, Apple, and Web wherever direct messages are offered.

1. Do not show a message action for a node with no public key on file. Keep the existing unmessagable check alongside it; the two are separate signals and one does not imply the other.
2. Leave nodes that cannot be messaged out of the contact list, but keep any node an existing conversation exists with, so a thread is never hidden.
3. In node detail, say that no public key has been received and point at Exchange User Info. Showing nothing leaves the user without a reason or a next step.
4. Never send `add_contact` with an empty public key, whether it is generated before a direct message or imported from a QR code, link, or NFC tag. Refuse the import and say why.
5. Do not describe the open lock as a fallback to channel encryption. It means the node cannot be messaged.

## Client Status

Apple:

- [x] Message action hidden when no public key is held ([Meshtastic-Apple#2417](https://github.com/meshtastic/Meshtastic-Apple/pull/2417))
- [x] Existing conversations stay reachable
- [x] Contact list excludes nodes that cannot be messaged
- [x] Node detail shows "No Public Key" and points at Exchange User Info
- [x] Exchange User Info offered from node detail
- [x] Refuses to send a contact with an empty public key
- [x] Refuses to import a contact with an empty public key

Android:

- [x] Message action hidden when no public key is held. `canDirectMessage` is `!isEffectivelyUnmessageable && hasPKC` ([IsEffectivelyUnmessageable.kt#L33](https://github.com/meshtastic/Meshtastic-Android/blob/a0d992989582691ab112ad4ae05c0fece890f94d/feature/node/src/commonMain/kotlin/org/meshtastic/feature/node/model/IsEffectivelyUnmessageable.kt#L33)), consumed at [DeviceActions.kt#L115](https://github.com/meshtastic/Meshtastic-Android/blob/a0d992989582691ab112ad4ae05c0fece890f94d/feature/node/src/commonMain/kotlin/org/meshtastic/feature/node/component/DeviceActions.kt#L115).
- [x] Existing conversations stay reachable. `showsDirectMessageAction(hasConversation)` is `canDirectMessage || hasConversation` ([IsEffectivelyUnmessageable.kt#L42](https://github.com/meshtastic/Meshtastic-Android/blob/a0d992989582691ab112ad4ae05c0fece890f94d/feature/node/src/commonMain/kotlin/org/meshtastic/feature/node/model/IsEffectivelyUnmessageable.kt#L42)).
- [x] Contact list excludes nodes that cannot be messaged. The list is built from existing conversations, and a new DM starts from the gated action above, so a keyless node with no thread cannot appear. Keyless threads stay and are flagged ([ContactsViewModel.kt#L145](https://github.com/meshtastic/Meshtastic-Android/blob/a0d992989582691ab112ad4ae05c0fece890f94d/feature/messaging/src/commonMain/kotlin/org/meshtastic/feature/messaging/ui/contact/ContactsViewModel.kt#L145)).
- [x] Node detail explains a missing key. `NoPublicKeyItem` renders when the key is absent and the node is remote ([NodeDetailsSection.kt#L212](https://github.com/meshtastic/Meshtastic-Android/blob/a0d992989582691ab112ad4ae05c0fece890f94d/feature/node/src/commonMain/kotlin/org/meshtastic/feature/node/component/NodeDetailsSection.kt#L212), definition at [#L465](https://github.com/meshtastic/Meshtastic-Android/blob/a0d992989582691ab112ad4ae05c0fece890f94d/feature/node/src/commonMain/kotlin/org/meshtastic/feature/node/component/NodeDetailsSection.kt#L465)).
- [x] Exchange User Info offered from node detail, via `requestUserInfo`
- [x] Refuses to send a contact with an empty public key ([MessagingControllerImpl.kt#L115](https://github.com/meshtastic/Meshtastic-Android/blob/a0d992989582691ab112ad4ae05c0fece890f94d/core/service/src/commonMain/kotlin/org/meshtastic/core/service/MessagingControllerImpl.kt#L115)).
- [x] Refuses to import a contact with an empty public key ([MessagingControllerImpl.kt#L130](https://github.com/meshtastic/Meshtastic-Android/blob/a0d992989582691ab112ad4ae05c0fece890f94d/core/service/src/commonMain/kotlin/org/meshtastic/core/service/MessagingControllerImpl.kt#L130)).

## Open question, favoriting on send

Both clients favorite the destination when a direct message is sent, to keep it from aging out of the node db. Android treats favoriting and the contact push as alternatives gated on firmware, sending the contact on 2.7.12 and later and favoriting only below that. Apple does both on every direct message regardless of firmware.

One of those is wrong on 2.8. Either the contact push supersedes favoriting, in which case Apple is pinning nodes it does not need to, or favoriting is still wanted, in which case Android stopped too early. This should be settled before either client changes further.

Both clients already skip nodes that are already favorited, and neither auto favorites when the connected node is CLIENT_BASE.

## Acceptance Criteria

- No client offers a message action for a node it holds no public key for.
- A node that cannot be messaged does not appear in the contact list unless a conversation with it already exists.
- Node detail states when no public key has been received and offers Exchange User Info.
- No client sends `add_contact` with an empty public key, from any path.
- Client documentation does not describe the open lock as channel encryption for direct messages.

