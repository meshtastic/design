# Meshtastic Cross-Platform NFC Tag Alignment Audit

**Status:** Reference Document
**Scope:** iOS/macOS (Meshtastic-Apple) vs Android (Meshtastic-Android) vs Web (meshtastic/web) vs Firmware (meshtastic/firmware)
**Areas Covered:** NFC tag read/write, contact & channel sharing, tag-based provisioning, shared data model, hardware support, design-standards conformance
**Design Standards:** v1.4 ([meshtastic_design_standards_latest.md](../meshtastic_design_standards_latest.md))
**Last Updated:** 2026-09-10

> **Revised 2026-09-10.** The first revision described iOS as write-only, contacts-only and reachable only from a Tools screen. Meshtastic-Apple [#2136](https://github.com/meshtastic/Meshtastic-Apple/pull/2136) closed that on 2026-07-24, six days after this document was written, and four of the nine recorded mismatches are gone. The grades in §4 have been re-checked against both codebases rather than carried forward; two moved because the original reading was wrong, not because the code changed, and those are called out in place.

> **Purpose:** NFC tag support shipped on the client apps without a design artifact to keep the platforms aligned. This document records exactly what each platform does with NFC today, identifies the mismatches, grades every NFC surface against the Meshtastic Client Design Standards v1.4, recommends a canonical NFC experience, and explores concrete new features to build — including on firmware. It is the parent reference for a `[ALIGNMENT]` issue (see appendix); no code changes are proposed here.

---

## 1. Feature Overview & Shared Data Model

NFC on Meshtastic is **not a bespoke data format**. An NFC tag is just another carrier for the *same* base64url share URLs already used by QR codes and deep links. So "NFC alignment" is really about **UX and platform reach**, not about the payload — the payload is already shared and stable across platforms.

Two share URLs exist; both put their payload in the URL **fragment (`#`)**, which is never transmitted to the server (a deliberate privacy property — the channel/contact secret stays on-device):

| Share type | URL | Payload (protobuf) | Source |
|-----------|-----|--------------------|--------|
| **Contact** | `https://meshtastic.org/v/#<base64url>` | `SharedContact` | [admin.proto](https://github.com/meshtastic/protobufs/blob/5ba1936/meshtastic/admin.proto) |
| **Channel set** | `https://meshtastic.org/e/#<base64url>`, or `https://meshtastic.org/e/?add=true#<base64url>` when adding to existing channels (query **before** the fragment) | `ChannelSet` | [apponly.proto](https://github.com/meshtastic/protobufs/blob/5ba1936/meshtastic/apponly.proto) |

### Shared protobuf building blocks

```protobuf
// admin.proto — the contact payload behind /v/#
message SharedContact {
  uint32 node_num          = 1;  // contact's node number
  User   user              = 2;  // full identity (see below)
  bool   should_ignore     = 3;  // add to blocked/ignored list
  bool   manually_verified = 4;  // sets the IS_KEY_MANUALLY_VERIFIED bit
}

// mesh.proto — the node identity an NFC tag actually encodes
message User {
  string id            = 1;  // "!xxxxxxxx"
  string long_name     = 2;
  string short_name    = 3;
  bytes  macaddr       = 4 [deprecated = true];
  HardwareModel hw_model = 5;
  bool   is_licensed   = 6;
  Config.DeviceConfig.Role role = 7;
  bytes  public_key    = 8;  // PKC public key
  optional bool is_unmessagable = 9;
}

// apponly.proto — the channel payload behind /e/#
message ChannelSet {
  repeated ChannelSettings settings = 1;
  Config.LoRaConfig        lora_config = 2;
}
```

A scanned/tapped payload is written to the node's NodeDB over the mesh via `AdminMessage`:

| AdminMessage field | # | Purpose |
|--------------------|---|---------|
| `set_owner` | 32 | Set this node's owner/identity (`User`) |
| `add_contact` | 66 | Add a contact (`SharedContact`) to the NodeDB |
| `remove_by_nodenum` | 38 | Remove a node from the NodeDB |

**Takeaway:** the data layer is already fully shared and cross-platform. Everything below is a divergence in *which platforms expose NFC*, *how*, and *how well it follows the design standards* — not in the bytes on the tag.

---

## 2. Current State

### 2.1 iOS / macOS (Meshtastic-Apple)

**NFC: read and write, contacts and channels, from the share sheets. iOS 18+, no Mac Catalyst.**

PR [#2136](https://github.com/meshtastic/Meshtastic-Apple/pull/2136) closed most of what this section previously recorded as missing. What follows is the state after it, plus [#2189](https://github.com/meshtastic/Meshtastic-Apple/pull/2189) and [#2464](https://github.com/meshtastic/Meshtastic-Apple/pull/2464).

| Capability | State |
|-----------|-------|
| NFC write — contact (`/v/#`) | ✅ Yes — `NFCNDEFReaderSession` → `tag.writeNDEF(...)`, from `ShareContactQRDialog` |
| NFC write — channel (`/e/#`) | ✅ Yes — from `ShareChannels` |
| NFC read (in-app scan session) | ✅ Yes — `NFCReader.scanToRead`, reachable from Settings → Tools only |
| OS-driven tag read | ✅ Universal-link dispatch as before, now alongside the in-app reader |
| Minimum OS | iOS **18** (`@available(iOS 18, *)`) — unchanged |
| macOS (Catalyst) | ❌ CoreNFC imported under `#if !targetEnvironment(macCatalyst)` — no NFC on the Mac build |
| Entry point | Write is co-located with the QR on both share surfaces. The in-app reader is still Settings → Tools |

**Key files** (Meshtastic-Apple `main` @ `14a47966`):

- NFC read/write: `Meshtastic/Helpers/NFCReader.swift` — `NFCReader` with a `write(payload:)` and a `scanToRead(onURL:)` mode, plus the shared `NFCWriteButton` view (`Label("Write to NFC Tag", systemImage: "tag")`, bordered capsule, large control size) that both share surfaces use.
- Share surfaces: `Views/Nodes/Helpers/ShareContactQRDialog.swift` and `Views/Settings/ShareChannels.swift` — each renders a `ShareLink` and an `NFCWriteButton` with its own caption. `Views/Settings/Tools.swift` keeps the in-app reader.
- Import confirm: `Views/Nodes/Helpers/AddContactConfirmationView.swift`.
- Contact QR: [`Meshtastic/Views/Nodes/Helpers/ShareContactQRDialog.swift`](https://github.com/meshtastic/Meshtastic-Apple/blob/e531f15/Meshtastic/Views/Nodes/Helpers/ShareContactQRDialog.swift) — builds `SharedContact { nodeNum, user, manuallyVerified }`, `urlPrefix = "https://meshtastic.org/v/#"`, QR via `CIFilter.qrCodeGenerator()`, shares via `ShareLink`.
- Contact import: [`Meshtastic/Helpers/ContactURLHandler.swift`](https://github.com/meshtastic/Meshtastic-Apple/blob/e531f15/Meshtastic/Helpers/ContactURLHandler.swift) → confirmation alert → `accessoryManager.addContactFromURL(...)`; provisioning in [`AccessoryManager+ToRadio.swift`](https://github.com/meshtastic/Meshtastic-Apple/blob/e531f15/Meshtastic/Accessory/Accessory%20Manager/AccessoryManager+ToRadio.swift) via `AdminMessage.addContact`.
- Channel URL: [`Meshtastic/Helpers/MeshtasticChannelURL.swift`](https://github.com/meshtastic/Meshtastic-Apple/blob/e531f15/Meshtastic/Helpers/MeshtasticChannelURL.swift) (`/e/#` `ChannelSet`); generate [`ShareChannels.swift`], receive [`SaveChannelQRCode.swift`].
- Routing: [`Meshtastic/MeshtasticApp.swift`](https://github.com/meshtastic/Meshtastic-Apple/blob/e531f15/Meshtastic/MeshtasticApp.swift) `onOpenURL`; App Intent entry [`AddContactIntent.swift`].
- Config: [`Info.plist`](https://github.com/meshtastic/Meshtastic-Apple/blob/e531f15/Meshtastic/Info.plist) `NFCReaderUsageDescription = "We use NFC tags to share node contacts"`; [`Meshtastic.entitlements`](https://github.com/meshtastic/Meshtastic-Apple/blob/e531f15/Meshtastic/Meshtastic.entitlements) `com.apple.developer.nfc.readersession.formats = TAG`.

**Entitlement/code inconsistency to verify:** the shipped entitlement format is `TAG`, but the code uses `NFCNDEFReaderSession`/`writeNDEF` (which is the **NDEF** family). This is the result of PR [#1657 "revert NFC entitlement from NDEF back to TAG"](https://github.com/meshtastic/Meshtastic-Apple/pull/1657). Flagged as an observation, not a confirmed runtime bug.

**History:** PR [#1600](https://github.com/meshtastic/Meshtastic-Apple/pull/1600) added NFC write (2026-04-06) after an earlier attempt+revert (PRs [#1537](https://github.com/meshtastic/Meshtastic-Apple/pull/1537)/[#1545](https://github.com/meshtastic/Meshtastic-Apple/pull/1545)); PR [#1657](https://github.com/meshtastic/Meshtastic-Apple/pull/1657) reverted the entitlement to `TAG` (2026-04-07); PR [#1659](https://github.com/meshtastic/Meshtastic-Apple/pull/1659) gated the feature to iOS 18 (2026-04-16). Related sharing UX: [#756](https://github.com/meshtastic/Meshtastic-Apple/issues/756), [#1238](https://github.com/meshtastic/Meshtastic-Apple/issues/1238).

### 2.2 Android (Meshtastic-Android)

**NFC: full read + write, contacts and channels, co-located with QR, with an enable-prompt. Tag emulation in review.**

| Capability | State |
|-----------|-------|
| NFC write — contact (`/v/#`) | ✅ Yes |
| NFC write — channel (`/e/#`) | ✅ Yes |
| NFC read (in-app scan session) | ✅ Yes — `enableReaderMode(...)` |
| OS-driven tag read | ✅ `ACTION_NDEF_DISCOVERED` intent filter for `/e/,/E/,/v/,/V/` (tap-to-import) |
| Minimum OS | Android 8.0 (**minSdk 26**); the manifest declares `uses-feature android.hardware.nfc required="false"`, so the app runs on devices without an NFC radio |
| Capability / enable handling | ⚠️ `NfcDisabledDialog` prompts to open NFC settings when NFC is off, but `MainActivity` supplies `LocalNfcScannerSupported provides true` unconditionally rather than checking `FEATURE_NFC`, so the affordance also appears on hardware that has no NFC radio at all |
| Entry point | Shared **`QrDialog`** (icon button beside the QR) + a "Share Connected Node" node-list action. Reading is on the import FAB on both the contact and channel screens |
| Tag emulation (phone acts as the tag) | 🚧 [#7124](https://github.com/meshtastic/Meshtastic-Android/pull/7124) — host card emulation serving the same URL as a Type 4 tag while the share dialog is in the foreground. No iOS equivalent is possible |
| Share to another app (link/QR image) | ❌ None. Copy to clipboard only |

**Key files** (Meshtastic-Android `main` @ `0da4c78`, app version base 2.8.0; refactored into a KMP multi-module project — legacy `app/src/main/...`, `ChannelFragment`, `QrCodeImage` no longer exist):

- NFC module: [`core/nfc/src/androidMain/kotlin/org/meshtastic/core/nfc/NfcScanner.kt`](https://github.com/meshtastic/Meshtastic-Android/blob/0da4c78/core/nfc/src/androidMain/kotlin/org/meshtastic/core/nfc/NfcScanner.kt) — `NfcScannerEffect(onResult, onNfcDisabled)` (read via `enableReaderMode`, flags `FLAG_READER_NFC_A|B|F|V|BARCODE`, `Ndef.get(tag)`, `record.toUri()`); `NfcWriterEffect(url, onResult, onNfcDisabled)` (write via `NdefRecord.createUri(url)` → `writeNdefMessage`). Plus [`core/nfc/README.md`].
- Capability contract: [`core/ui/.../util/LocalNfcScannerProvider.kt`] (`LocalNfcScannerProvider`, `LocalNfcScannerSupported`, `LocalNfcWriterProvider`); enable prompt [`core/ui/.../component/NfcDialogs.kt`] (`NfcDisabledDialog`).
- Share surface: [`core/ui/.../component/QrDialog.kt`] renders the QR **and** a "Write to NFC" button that writes the same channel/contact URL (`write_nfc` / `write_nfc_text` / `write_nfc_success` / `write_nfc_failed` strings).
- URL model: [`core/model/.../util/MeshtasticUrlConstants.kt`] (`CONTACT_URL_PREFIX = "https://meshtastic.org/v/#"`, `CHANNEL_URL_PREFIX = "https://meshtastic.org/e/"`); [`ChannelSet.kt`] `getChannelUrl()`/`toChannelSet()`; [`SharedContact.kt`] `getSharedContactUrl()`/`toSharedContact()`.
- Read handling: [`androidApp/src/main/kotlin/org/meshtastic/app/MainActivity.kt`] handles `ACTION_NDEF_DISCOVERED` → `handleMeshtasticUri` → `UIViewModel.handleDeepLink` (routes `/v/` → contact dialog, `/e/` → channel dialog).
- Import: [`core/service/.../MessagingControllerImpl.kt`] `importContact()` → `AdminMessage(add_contact = contact.copy(manually_verified = true))` + `nodeManager.handleReceivedUser(...)`. QR scanning: [`core/barcode/`] (ML Kit on the Google flavor, ZXing on F-Droid, both via CameraX).
- Manifest: `uses-permission android.permission.NFC`; `uses-feature android.hardware.nfc required="false"`; the `NDEF_DISCOVERED` intent-filter above.

**History:** PR [#6030](https://github.com/meshtastic/Meshtastic-Android/pull/6030) added NFC tag **writing** for contacts and channels (v2.8.0); the **read**/scan path predates it — PR [#4471](https://github.com/meshtastic/Meshtastic-Android/pull/4471) (QR/NFC scanning with ML Kit + CameraX) and PR [#4482](https://github.com/meshtastic/Meshtastic-Android/pull/4482) (NFC enable prompt), tracking issue [#397](https://github.com/meshtastic/Meshtastic-Android/issues/397).

### 2.3 Web (meshtastic/web)

**NFC: none.** The browser Web NFC API (`NDEFReader`) exists but is **Chromium-on-Android only** (not Safari/iOS, not desktop Firefox), so it can never be the primary share path. Web already generates and parses the same `/e/#` and `/v/#` URLs for QR/link sharing; NFC would be an additive, capability-detected enhancement on supported browsers only.

### 2.4 Firmware (meshtastic/firmware)

**NFC: none — no module, no driver, no NDEF handling.** But the hardware story is more interesting than "not supported":

| Finding | Detail | Source |
|---------|--------|--------|
| **Real NFC chip, undriven** | LilyGO **T-LoRa Pager** wires an **ST25R3916** NFC reader/transceiver (`NFC_INT 5`, `NFC_CS 39`) — but the part name appears in exactly one comment, with no driver and no `lib_deps` entry. Hardware present, firmware support absent. | [`variants/esp32s3/tlora-pager/variant.h`](https://github.com/meshtastic/firmware/blob/62df860/variants/esp32s3/tlora-pager/variant.h) |
| **nRF "NFC" = GPIO** | nRF52840/nRF54L15 boards define `PIN_NFC1 (9)`/`PIN_NFC2 (10)` and set `-D CONFIG_NFCT_PINS_AS_GPIOS=1` — i.e. the NFC antenna pins are *reclaimed as ordinary GPIO/I2C*, the opposite of an NFC feature. | `variants/nrf52840/*/variant.h` |
| **Dormant OOB idea** | A comment notes BLE security "can be re-enabled once a display or **NFC OOB path** is available" — an idea, no code. | [`src/platform/nrf54l15/NRF54L15Bluetooth.cpp`](https://github.com/meshtastic/firmware/blob/62df860/src/platform/nrf54l15/NRF54L15Bluetooth.cpp) |
| **Open request** | "NFC tag interface for quick onboarding of stations" — an I2C NFC tag whose content is set from a phone, for in-field config of BLE-less relays (incl. GPS coordinates). | firmware [#7236](https://github.com/meshtastic/firmware/issues/7236) |

---

## 3. Mismatches

Rows 1, 2, 3 and 6 from the 2026-07-18 revision are closed and have been removed. What remains, plus what the closing work exposed:

| # | Area | iOS | Android | Web | Firmware | Priority |
|---|------|-----|---------|-----|----------|----------|
| 1 | **Share to another app** | ✅ `ShareLink` on both surfaces, sends the QR image and the URL | ❌ Copy to clipboard only | — | — | **High** |
| 2 | **In-app reader entry point** | Settings → Tools only | Import FAB on both the contact and channel screens | ❌ | ❌ | Medium |
| 3 | **Minimum OS gate** | iOS 18 only, no Mac Catalyst | Android 8 (minSdk 26) | n/a | n/a | Medium |
| 4 | **Affordance hidden without hardware** | Version-gated, no runtime check | ⚠️ `LocalNfcScannerSupported` hardcoded `true` | n/a | n/a | Medium |
| 5 | **Naming of the channel share surface** | "Generate QR Code" | "Share Channels QR Code" | n/a | n/a | Medium |
| 6 | **Channel add-vs-replace explained** | ✅ Toggle in the share screen with a consequence line | ⚠️ Segmented buttons on the channel list, no consequence text, away from the share action | — | — | Medium |
| 7 | **What the surface says it is** | Names the node and explains the QR | ❌ Explains NFC only, never the QR, and does not name what is being shared | — | — | Medium |
| 8 | **Tag emulation** | ❌ Not possible on iOS | 🚧 [#7124](https://github.com/meshtastic/Meshtastic-Android/pull/7124) | ❌ | ❌ | Low (platform limit) |
| 9 | **Reader entitlement vs code** | `TAG` entitlement, NDEF code (see §2.1) | NDEF URL records (consistent) | n/a | n/a | Low |
| 10 | **Web NFC** | — | — | ❌ None (additive, Chromium-Android only) | — | Low |
| 11 | **Firmware NFC** | — | — | — | ❌ None (ST25R3916 wired but undriven; request [#7236](https://github.com/meshtastic/firmware/issues/7236)) | Low (Exploratory) |

---

## 4. Design Standards Conformance (v1.4)

Every NFC surface graded against [meshtastic_design_standards_latest.md](../meshtastic_design_standards_latest.md), using the verdict legend from [community-alignment-matrix.md](community-alignment-matrix.md):

| Icon | Meaning |
|------|---------|
| ✅ | Aligns with the design standards |
| ⚠️ | Partially aligned — some tension |
| ❌ | Conflicts with a standard |
| 🔇 | Standards silent / not applicable |

| NFC surface | Standard § | iOS | Android | Notes |
|-------------|-----------|-----|---------|-------|
| Show NFC affordance only when hardware present/enabled | **§3** Dynamic Layout & Conditional Visibility | ⚠️ | ❌ | Neither checks the radio. Android's `MainActivity` supplies `LocalNfcScannerSupported provides true` unconditionally, so the affordance shows on a phone with no NFC; iOS only version-gates. Corrected from ✅ on 2026-09-10 — the earlier grade read the CompositionLocal's default rather than what the app provides. |
| Labeled action, not icon-only (+ web tooltip) | **§4** Iconography & Descriptive Text | ✅ | ⚠️ | iOS uses `Label("Write to NFC Tag", systemImage: "tag")` in a bordered capsule. Android's are `IconButton`s whose text exists only as a content description. §4 does not require a visible label on mobile, but it does require a hover tooltip for icon-only buttons on Desktop and Web, and `QrDialog` ships to the Compose Desktop app with none. The NFC button is hidden there (capability defaults false); Copy is not. |
| Plain-language subtext explaining the tap | **§6** Information Architecture | ✅ | ⚠️ | iOS carries a per-surface caption naming the thing being shared, and a line explaining the QR. Android has one generic NFC subtext shared by both surfaces and no explanation of the QR itself. |
| Native scan sheet, 44×44 targets, Dynamic Type | **§5** Vision-Centric & Native Patterns | ✅ | ✅ | iOS now uses the native `NFCNDEFReaderSession` system sheet. |
| Circular identifier in the import-confirm dialog | **§1** Node Identity (Circle Standard) | ✅ | ✅ | iOS added `AddContactConfirmationView`; Android's `SharedContactDialog` renders a `NodeChip`. Neither *share* dialog identifies the node being shared, which is mismatch 7 rather than a §1 finding. |
| QR + dialog contrast in light & dark | **§2** Light & Dark Mode | ✅ | ✅ | Keep QR quiet-zone/contrast WCAG-AA in both themes; never a hybrid screen. |
| Success/failure feedback + tappable links use semantic colors | **§7** Color Palette / Semantic Colors | 🔇 | ✅ | Android's write feedback uses `SemanticColors.Success` and `colorScheme.error`. |
| Firmware fixed-station GPS provisioning (see §6.B2) | **§10** Units & Measurement | 🔇 | 🔇 | Any coordinates written to a tag are stored/transmitted in canonical units (data-layer note). |

**Applicable v1.4 Agent Implementation Checklist items** (standards doc, "Agent Implementation Checklist (v1.4)") that any NFC work must satisfy:

- [ ] Interactive elements (Write/Scan buttons, dialog actions) meet the **44×44px** hit target (§5).
- [ ] The NFC action carries a **text label** and, on Web/desktop, a hover **tooltip** (§4).
- [ ] The NFC affordance is **hidden** where NFC is unsupported/disabled — Null Data / Conditional Visibility (§3).
- [ ] Import-confirm uses the node's **Circular Identifier** (§1).
- [ ] The share/scan UI is strictly **Light OR Dark**, WCAG-AA 4.5:1 in both (§2).
- [ ] **Accent green is never used as text** or as the success color; **Success = `Green 600 #3FB86D`**, links = **`Blue 400 #9BA8E0`** (§7).
- [ ] Setting subtext uses **plain language** (§6).

---

## 5. Recommended Canonical NFC Behavior

A unified target experience, each point tied to the standard it satisfies:

1. **NFC lives beside QR.** Every client surfaces "Write to NFC" from the *same* share sheet as the QR code, for **both** contacts and channels — one share chokepoint, not a separate Tools screen (**§6** IA). Android already does this; iOS and Web should follow.
2. **Symmetric read + write.** In addition to OS tap-to-open, each client offers a deterministic in-app **"Scan NFC tag"** action using the native reader sheet (**§5**).
3. **Capability-aware.** The NFC affordance appears only when the device has NFC, with an "enable NFC / not supported" prompt when it's off or absent (**§3**).
4. **Explained in plain language.** A short subtext tells the user what a tap does (**§4/§6**).
5. **Identity-forward confirmation.** The contact-import confirmation shows the incoming node's circular identifier and name before adding (**§1**).
6. **Theme-safe + semantic feedback.** QR/dialog meet WCAG-AA in both themes (**§2**); write success/failure use Success/Error semantic colors, links use Blue 400 (**§7**).
7. **One consistent verification rule.** Decide once — cross-platform — whether a *physical tap* implies `manually_verified = true` (Android's current behavior) or honors the encoded flag (iOS's current behavior). See §6 cross-cutting notes.
8. **One payload convention.** Keep NDEF **URI records** carrying the canonical `/v/#` and `/e/#` URLs as the interoperable baseline; treat a raw-protobuf **MIME record** as an optional additive (see §6).

**Per-platform path to canonical**

| Platform | To reach canonical |
|----------|--------------------|
| iOS | Move the in-app reader out of Settings → Tools onto the share and import surfaces; resolve the `TAG`↔NDEF entitlement; re-evaluate the iOS 18 gate and Catalyst exclusion; rename the channel screen off "Generate QR Code". |
| Android | Add a share-to-another-app action; gate the affordance on `FEATURE_NFC`; name what is being shared and explain the QR; give channel add-vs-replace a consequence line next to the share action; add desktop tooltips for icon-only buttons; rename "Share Channels QR Code". |
| Web | Add capability-detected Web NFC read/write (`NDEFReader`) on supported browsers, with graceful fallback to QR/link; tooltips per §4. |
| Firmware | Out of scope for parity; see §6.B exploration. |

---

## 6. Feature Exploration — Detailed Proposals

### 6.A Client parity (near-term, low-risk)

A1 through A5 shipped in Meshtastic-Apple [#2136](https://github.com/meshtastic/Meshtastic-Apple/pull/2136) and are struck from the table below. A6 remains.

| # | Proposal | Where | Standards |
|---|----------|-------|-----------|
| A6 | **iOS: resolve `TAG`↔NDEF entitlement** | `Meshtastic.entitlements` vs `NFCNDEFReaderSession` usage (see §2.1) | — |
| A7 | **Web: capability-detected Web NFC** | `NDEFReader` read/write behind feature detection; reuse existing `/e/#` `/v/#` URL codecs | §3, §4 |
| A8 | **Android: share the link and QR to another app** | an `ACTION_SEND` platform util behind the existing `expect`/`actual` in `core/ui`, matching iOS `ShareLink` | §6 |
| A9 | **Android: gate the affordance on `FEATURE_NFC`** | `MainActivity` currently provides `LocalNfcScannerSupported = true` unconditionally | §3 |
| A10 | **Both: say what the surface does** | name the node or channel set being shared, explain the QR, and give channel add-vs-replace a consequence line beside the share action | §6 |
| A11 | **Both: rename the channel share surface** | "Generate QR Code" / "Share Channels QR Code" both predate link and NFC sharing | §6 |

### 6.B Firmware NFC (new ground)

Each proposal notes hardware, protobuf/URL, and security considerations. None exists in firmware today.

**B1 — Static NFC "identity tag" (ST25DV dynamic NFC EEPROM).**
Add a cheap I2C **ST25DV** dynamic-NFC EEPROM to a board; firmware writes the node's own `https://meshtastic.org/v/#<SharedContact>` URL into it (refreshed whenever owner/keys change). Anyone can then **tap the physical node** to add it as a contact / read its identity — a hardware "business card." Purely a tag the phone *reads*; no new protobuf needed (reuses `SharedContact`/`User`). *Security:* writing `User.public_key` to a passively-readable tag is a public-identity disclosure — acceptable for a contact card, but should be opt-in and documented.

**B2 — Tap-to-provision a station (firmware [#7236](https://github.com/meshtastic/firmware/issues/7236)).**
A phone writes a `ChannelSet` (and optionally `set_owner` + a fixed GPS position) to an I2C NFC tag on the node; firmware reads it on boot/wake and self-provisions. Targets relays/repeaters that ship without BLE for cost/lockdown reasons. *Needs:* a firmware ingestion path and likely a small **new "provisioning payload"** (owner + channels + LoRa config + fixed position) — or a composition of the existing `/e/#` `ChannelSet` + `AdminMessage.set_owner`. Coordinate any new field via [meshtastic/protobufs](https://github.com/meshtastic/protobufs). *Security:* physical write access = full control of the node — gate behind the same trust model as serial/USB config; consider interaction with Lockdown Mode.

**B3 — Drive the ST25R3916 on the T-LoRa Pager.**
The Pager already has the reader chip wired ([§2.4](#24-firmware-meshtasticfirmware)). Add an actual ST25R3916 SPI driver so the device can **read tags and do phone-to-device taps** — first-class firmware NFC on existing hardware (e.g. tap another node's identity tag, or tap a phone to exchange a contact). Highest effort; establishes the firmware NFC abstraction the other proposals can reuse.

**B4 — NFC out-of-band BLE pairing.**
Realize the dormant nRF54L15 idea: use NFC OOB to bootstrap secure BLE pairing — tap phone to node to pair without a PIN or display. Depends on the nRF BLE stack and an NFC-capable pin/chip; naturally complements B1/B3.

**Cross-cutting design notes (decide once, apply everywhere):**
- **Verification semantics.** Should a physical tap imply `manually_verified = true`? Android forces it on import; iOS honors the encoded flag (Mismatch #6). Physical proximity is a reasonable trust signal, but pick one rule across clients *and* any firmware ingestion.
- **Public-key privacy.** `SharedContact` carries `User.public_key`; a static readable tag (B1) publishes it. Make identity-tag exposure explicit and opt-in.
- **NDEF URL record vs MIME record.** URL records depend on associated-domain/App-Links resolution to open the app; a raw-protobuf **MIME-type** NDEF record would enable fully **offline** import without a URL round-trip. Keep the URL record as the interoperable baseline and treat a MIME record as an additive, cross-platform decision.

### 6.C Prioritized backlog

| Priority | Item | Platforms | Rough effort | Dependency |
|----------|------|-----------|--------------|------------|
| P0 | A8 Android share-to-another-app | Android | S–M | none |
| P1 | A9 Android `FEATURE_NFC` gate | Android | S | none |
| P1 | A10 say what the surface does | Both | S | none |
| P1 | A11 rename the channel share surface | Both | S | none |
| P1 | A6 iOS entitlement `TAG`↔NDEF resolution | iOS | S | verify runtime |
| P2 | iOS in-app reader onto the share/import surfaces | iOS | S | none |
| P2 | A7 Web NFC (capability-detected) | Web | M | Chromium-Android only |
| P2 | B1 ST25DV identity tag | Firmware + HW | M | board with ST25DV |
| P3 | B2 tap-to-provision station (#7236) | Firmware + protobufs | L | new provisioning payload |
| P3 | B3 ST25R3916 driver (T-LoRa Pager) | Firmware | L | hardware access |
| P3 | B4 NFC OOB BLE pairing | Firmware | L | nRF BLE stack |

---

## 7. Sub-tasks

- [x] iOS parity work (channel write, in-app reader, share-sheet placement, confirm view) — shipped in Meshtastic-Apple [#2136](https://github.com/meshtastic/Meshtastic-Apple/pull/2136).
- [ ] Android: share-to-another-app, `FEATURE_NFC` gate, surface copy, channel consequence line, desktop tooltips.
- [ ] Both: rename the channel share surface off "QR".
- [ ] iOS: entitlement resolution, reader entry point, iOS 18 / Catalyst review.
- [ ] Create **Web** alignment issue (capability-detected Web NFC read/write with graceful fallback).
- [ ] Create **Firmware** tracking issue (NFC exploration B1–B4; cross-link firmware [#7236](https://github.com/meshtastic/firmware/issues/7236)).

---

## 8. Sources

| Platform | Ref | Key files |
|----------|-----|-----------|
| iOS (Meshtastic-Apple) | `main` @ `14a47966` | `Views/Settings/Tools.swift`, `Views/Nodes/Helpers/ShareContactQRDialog.swift`, `Helpers/ContactURLHandler.swift`, `Helpers/MeshtasticChannelURL.swift`, `Accessory/Accessory Manager/AccessoryManager+ToRadio.swift`, `MeshtasticApp.swift`, `Info.plist`, `Meshtastic.entitlements` |
| Android (Meshtastic-Android) | `main` @ `a0d99298` (v2.8.2) | `core/nfc/src/androidMain/.../NfcScanner.kt`, `core/ui/.../component/QrDialog.kt`, `core/ui/.../component/NfcDialogs.kt`, `core/ui/.../util/LocalNfcScannerProvider.kt`, `core/model/.../util/MeshtasticUrlConstants.kt`, `core/model/.../util/{ChannelSet,SharedContact}.kt`, `core/service/.../MessagingControllerImpl.kt`, `androidApp/.../MainActivity.kt`, `androidApp/src/main/AndroidManifest.xml` |
| Firmware (meshtastic/firmware) | `master` @ `62df860` | `variants/esp32s3/tlora-pager/variant.h` (ST25R3916), `variants/nrf52840/*/variant.h` (`CONFIG_NFCT_PINS_AS_GPIOS`), `src/platform/nrf54l15/NRF54L15Bluetooth.cpp`; issue [#7236](https://github.com/meshtastic/firmware/issues/7236) |
| Protobufs (meshtastic/protobufs) | `master` @ `5ba1936` | `admin.proto` (`SharedContact`, `AdminMessage.add_contact` #66, `set_owner` #32), `mesh.proto` (`User`, `public_key`), `apponly.proto` (`ChannelSet`) |
| Standards | v1.4 | [meshtastic_design_standards_latest.md](../meshtastic_design_standards_latest.md) §1–§10 |

> All source blob links are pinned to the commit SHAs above (Apple `14a47966`, Android `a0d99298`, firmware `62df860`, protobufs `5ba1936`) so the audit is reproducible; line numbers cited in prose may still differ if you browse a different revision. Links inside §2 that still carry the older Apple `e531f15` and Android `0da4c78` SHAs point at the revision this document originally described and are left as they are.

---

## Appendix — Ready-to-file `[ALIGNMENT]` issue

Paste into a new [meshtastic/design](https://github.com/meshtastic/design/issues/new?template=cross-platform-alignment.md) issue (template: *Cross-Platform Alignment*). No issue is filed by this document.

```markdown
**Title:** [ALIGNMENT]: NFC tag feature-set (contact & channel sharing / provisioning)

**Area of Alignment**

NFC tag support is live but divergent across clients, and absent on firmware:

- Android: read + write, contacts and channels, in the shared QR dialog, with an
  enable-NFC prompt and tap-to-import (v2.8.0, PR #6030). No share-to-another-app.
- iOS: read + write, contacts and channels, from the share sheets (PR #2136), plus
  `ShareLink` on both. Reader still lives in Settings → Tools; entitlement is `TAG`
  while the code uses NDEF; iOS 18+ and no Mac Catalyst.
- Web: no NFC.
- Firmware: no NFC — though the T-LoRa Pager already carries an undriven ST25R3916 and
  request #7236 asks for NFC tap-to-provision.

NFC carries the same `meshtastic.org/v/#` (SharedContact) and `meshtastic.org/e/#`
(ChannelSet) URLs as QR — so this is a UX + platform-reach alignment, not a data-format one.
All work must conform to Design Standards v1.4 (§1 circular ID, §2 light/dark, §3 conditional
visibility, §4 labeled actions, §5 native/44×44, §6 plain language, §7 semantic colors).

Full audit: standards/audits/nfc-alignment-audit.md

**Sub-tasks**

- [ ] Create Android alignment issue.
- [ ] Create iOS alignment issue.
- [ ] Create Web alignment issue.
- [ ] Create Firmware tracking issue (NFC exploration; cross-link firmware #7236).
```
