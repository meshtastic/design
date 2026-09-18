# [PARENT] [ALIGNMENT]: Configurable packet authenticity policy

## Area of alignment

Add one device-owned receive policy for cryptographic packet authenticity, configured consistently by every official client. This builds on [design#113](https://github.com/meshtastic/design/issues/113) and the XEdDSA implementation in [firmware#10478](https://github.com/meshtastic/firmware/pull/10478) / [firmware#10858](https://github.com/meshtastic/firmware/pull/10858).

The policy has three user-facing levels:

1. **Compatible** — authenticate packets when possible, but accept legacy unsigned traffic.
2. **Balanced (default)** — reject malformed or invalid signatures and unsigned broadcast downgrade attempts from nodes known to sign, while retaining compatibility with unknown/legacy, unicast, and oversized packets.
3. **Strict** — accept remote decrypted traffic only when it has a verified XEdDSA signature or was successfully authenticated by PKI/AES-CCM.

This is a firmware enforcement policy surfaced by clients, not a separate app-local filter. Central enforcement keeps modules, connected clients, local history, MQTT, and rebroadcast behavior consistent.

## Why these levels

Comparable systems separate cryptographic validity from rollout policy:

- [RPKI origin validation](https://www.rfc-editor.org/rfc/rfc7115.html) distinguishes Valid, Invalid, and NotFound routes, rejects Invalid routes, and retains an incremental-deployment path for NotFound routes.
- [DNSSEC terminology](https://www.rfc-editor.org/rfc/rfc7719.html) distinguishes Secure, Insecure, Bogus, and Indeterminate results instead of treating all unsigned data as forged.
- [libp2p PubSub](https://github.com/libp2p/js-libp2p/blob/master/doc/CONFIGURATION.md#customizing-pubsub) exposes an explicit `StrictSign` policy.
- [Tailscale Tailnet Lock](https://tailscale.com/docs/features/tailnet-lock) makes signature enforcement an explicit, compatibility-affecting choice.
- [Element device verification](https://docs.element.io/latest/element-support/device-verification/how-to-verify-devices/) clearly communicates that mandatory verification excludes unverified devices.

The resulting product rule is: **invalid is always rejected; unsigned is a compatibility decision; authenticated-only behavior must be explicit and reversible.**

## Protocol proposal

Add `Config.SecurityConfig.packet_signature_policy` with a zero value that preserves current downgrade protection:

```proto
enum PacketSignaturePolicy {
  PACKET_SIGNATURE_POLICY_BALANCED = 0;
  PACKET_SIGNATURE_POLICY_COMPATIBLE = 1;
  PACKET_SIGNATURE_POLICY_STRICT = 2;
}

PacketSignaturePolicy packet_signature_policy = 9;
```

The enum order is compatibility-safe rather than severity-sorted: an absent/default field must remain **Balanced**.

Add `DeviceMetadata.has_xeddsa = 14` as a read-only build capability. Tag 13 is avoided because protobufs PR #956 already claims it. Clients must not offer Strict when the connected firmware cannot verify XEdDSA. `hasPKC` is not a substitute because it can be true when XEdDSA is excluded.

### Receive matrix

| Remote packet after local channel/PKI decode | Compatible | Balanced (default) | Strict |
| --- | --- | --- | --- |
| Valid XEdDSA signature, known key | Accept as verified | Accept as verified | Accept as verified |
| Signed NodeInfo, key not cached, embedded key binds and verifies | Accept, then cache key | Accept, then cache key | Accept, then cache key |
| Signature present, key unavailable, non-NodeInfo | Accept as unverified | Accept as unverified | Drop |
| Invalid signature with known key | Drop | Drop | Drop |
| Malformed nonzero signature length | Drop | Drop | Drop |
| Unsigned, signable broadcast from a known signer | Accept | Drop | Drop |
| Unsigned non-PKI unicast from any sender | Accept | Accept | Drop |
| Unsigned packet from an unknown/legacy node | Accept | Accept | Drop |
| Unsigned packet too large to carry a signature | Accept | Accept | Drop |
| Successfully authenticated PKI/AES-CCM unicast | Accept | Accept | Accept |

Strict applies to **every remote packet the radio decrypts**, regardless of portnum or broadcast/unicast destination. This includes position, NodeInfo, telemetry, text, waypoint, routing, and infrastructure traffic. A header flag alone never establishes PKI authenticity; the exception requires successful local PKI decryption.

Locally originated phone/API traffic is trusted and exempt. XEdDSA signatures live inside encrypted `Data`, so a relay without the channel key cannot classify opaque transit traffic; unknown-channel relay behavior remains unchanged.

### Outbound behavior

This policy does not introduce or version a new authentication system and does not change normal-mode packet construction. Existing XEdDSA-capable firmware continues signing signable channel broadcasts with the existing `from | id | portnum | payload` tuple, and existing PKI/AES-CCM continues authenticating encrypted direct messages. The selected receive policy must never change what a node transmits.

Unsigned normal-mode unicast or oversized traffic remains visible in Compatible/Balanced and is rejected by Strict. A valid existing signature proves that the identity key emitted the signed payload; it does not prove that position/telemetry content is truthful or permanently prevent replay.

Authenticated plaintext licensed/ham broadcasts and direct messages are a separate follow-up in [design#122](https://github.com/meshtastic/design/issues/122). That work must reuse the existing signing system and must not add encryption or a new signature format.

### First-contact bootstrap

Strict must not deadlock discovery when the first signed NodeInfo arrives before its key is cached:

1. Decode the `User` payload without committing it to NodeDB.
2. Require a 32-byte embedded public key.
3. Require `crc32(public_key) == MeshPacket.from`, matching node identity construction.
4. Verify the existing signed tuple against that key.
5. Cache the key and continue normal processing only after successful verification.

An identity-binding or signature failure is a hard rejection and must never mutate NodeDB.

### Rejection semantics

A policy rejection is a hard receive rejection. It must not reach application modules, the connected client, NodeDB/local history, plaintext MQTT downlink, or any rebroadcast path. This includes duplicate/upgrade routing paths that run before ordinary module delivery. Opaque unknown-channel traffic remains relay-compatible because the node cannot evaluate it.

Every ingress path, including already-decoded MQTT and UDP traffic, must apply the same policy. An untrusted inbound `pki_encrypted` flag must not bypass enforcement.

## STM32 support

Capability must be enabled per firmware environment, not inferred from the STM32 family. Final builds with the policy code produce:

| Environment | XEdDSA | Flash | Headroom |
| --- | --- | --- | --- |
| RAK3172 | Enabled | 200,880 / 247,808 (81.1%) | 46,928 B |
| CDEBYTE E77-MBL | Enabled | 197,712 / 247,808 (79.8%) | 50,096 B |
| Wio-E5 | Excluded | 240,084 / 247,808 (96.9%) | 7,724 B; enabling overflows by 10,448 B |
| Russell | Excluded | 243,692 / 247,808 (98.3%) | 4,116 B; enabling overflows by 14,080 B |
| Milesight GS301 | Excluded | XEdDSA instrumentation overflows by 10,080 B | Ordinary debug config also has a pre-existing nanolib-float guard |

Firmware should keep the shared STM32WL exclusion and remove it only in the RAK3172 and CDEBYTE environments that demonstrably fit. `DeviceMetadata.has_xeddsa` must follow the final compile-time guard, so incapable targets report false and clients cannot select Strict. This implements the requirement that every capable node uses XEdDSA without breaking constrained images.

## Client behavior

Add a native selector under **Security → Packet authenticity**:

| Level | Primary text | Supporting text |
| --- | --- | --- |
| Compatible | **Accept unsigned** | Authenticate packets when possible, but accept unsigned traffic for maximum compatibility. |
| Balanced | **Prefer authenticated** | Recommended. Reject unsigned broadcast downgrade attempts from nodes known to sign. |
| Strict | **Require authentication** | Only show and process cryptographically authenticated mesh packets. Older nodes and oversized packets may disappear. |

Requirements:

- Read/write the device `SecurityConfig`; do not create an app-local policy.
- Present Balanced when the protobuf field is absent/defaulted.
- Gate the control on `DeviceMetadata.has_xeddsa`; older/incapable firmware keeps its existing behavior.
- Show a confirmation before enabling Strict and explain reduced mesh visibility, older firmware, oversized packets, and licensed/ham nodes.
- Do not retroactively hide stored messages; enforcement begins after the radio accepts the config.
- Keep the shield (verified XEdDSA) and lock (authenticated PKI DM) meanings from design#113.
- Use platform-native controls, localized text, and accessibility labels.

BaseUI and MUI should expose the same values where their settings architecture supports `SecurityConfig`. Constrained displays may shorten labels to Compatible, Balanced, and Strict.

## Acceptance criteria

- Protobuf zero/default maps to Balanced; the capability defaults false.
- Invalid and malformed signatures are hard-rejected at every level.
- Strict accepts a first-contact NodeInfo only after embedded-key binding and signature verification.
- Strict accepts successfully authenticated PKI traffic but rejects an untrusted PKI flag.
- The receive policy does not change normal-mode outbound signing or PKI wire behavior.
- Every target that demonstrably fits includes XEdDSA and reports the capability; incapable targets report false.
- Firmware tests cover RF decode, already-decoded/MQTT/UDP ingress, duplicate routing, module/client/MQTT delivery, rebroadcast suppression, first-contact bootstrap, PKI, and the policy matrix.
- Every client reads/writes the same enum, uses shared wording, gates on capability, and confirms Strict.
- Client UI tests/screenshots cover all values, confirmation, unavailable state, themes, and relevant compact layouts.
- Firmware and on-device UI PRs remain draft until hardware verification is recorded.

## Sub-tasks

- [ ] [protobufs#982](https://github.com/meshtastic/protobufs/issues/982) — schema and capability.
- [ ] [firmware#10963](https://github.com/meshtastic/firmware/issues/10963) — receive enforcement, capability, STM32, and BaseUI decision.
- [ ] [Meshtastic-Android#6176](https://github.com/meshtastic/Meshtastic-Android/issues/6176) — Android/Desktop settings.
- [ ] [Meshtastic-Apple#2065](https://github.com/meshtastic/Meshtastic-Apple/issues/2065) — Apple settings.
- [ ] [web#1260](https://github.com/meshtastic/web/issues/1260) — Web settings.
- [ ] [standalone-ui#39](https://github.com/meshtastic/standalone-ui/issues/39) — on-device UI design source.
- [ ] [device-ui#340](https://github.com/meshtastic/device-ui/issues/340) — MUI runtime.
- [ ] Documentation follow-up after policy acceptance.

## Open design questions

1. Should BaseUI expose the selector immediately, or remain read-only until its security settings surface is expanded?
2. Is **Packet authenticity** the preferred settings label, or should clients use **Packet authentication**?
3. Should Balanced continue accepting signed-but-unverifiable non-NodeInfo packets as an unknown/legacy compatibility case?

