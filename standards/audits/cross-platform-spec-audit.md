# Cross-Platform Feature Spec Audit

**Status:** Reference Document  
**Scope:** iOS/macOS (Meshtastic-Apple) vs Android (Meshtastic-Android)  
**Last Updated:** 2026-05-17  

> **Purpose:** This document audits all SpecKit feature specifications written to date across the Apple and Android Meshtastic client repositories, surfaces which features are specced on one platform but not the other, and flags opportunities for cross-platform alignment.

---

## Feature Specification Matrix

| Feature | Android Spec | Android Status | Apple Spec | Apple Status | Notes |
|---------|-------------|----------------|-----------|--------------|-------|
| Local Mesh Discovery | [20260507-161658-local-mesh-discovery](https://github.com/meshtastic/Meshtastic-Android/tree/main/specs/20260507-161658-local-mesh-discovery) | 🔴 Branch Complete | [001-local-mesh-discovery](https://github.com/meshtastic/Meshtastic-Apple/tree/main/specs/001-local-mesh-discovery) | ✅ Implemented | Paired spec — branch `feat/discovery`, 50/51 tasks done; awaiting merge |
| Node List Layout (Compact / Complete) | [20260507-161758-node-list-layout](https://github.com/meshtastic/Meshtastic-Android/tree/main/specs/20260507-161758-node-list-layout) | 🔴 Branch Complete | [002-node-list-layout](https://github.com/meshtastic/Meshtastic-Apple/tree/main/specs/002-node-list-layout) | ✅ Implemented | Paired spec — branch `feat/node-list`, 47/47 tasks done; awaiting merge |
| App Documentation (Web + In-App + AI) | [20260507-161858-app-docs-markdown](https://github.com/meshtastic/Meshtastic-Android/tree/main/specs/20260507-161858-app-docs-markdown) | 🔴 Branch Complete | [003-app-docs-markdown](https://github.com/meshtastic/Meshtastic-Apple/tree/main/specs/003-app-docs-markdown) | ✅ Implemented | Paired spec — branch `feat/20260507-161858-app-docs-markdown`, 159/159 tasks done; awaiting merge |
| TAK v2 Protocol Integration | [005-tak-v2-protocol](https://github.com/meshtastic/Meshtastic-Android/tree/main/specs/005-tak-v2-protocol) | ✅ Implemented | _(not spec'd)_ | ✅ Implemented | Android: 80/80 tasks merged to `main`. Apple: ships TAK v2 (`supportsTAKv2`, firmware ≥ 2.8.0) but has no formal spec — gap to address |
| Message Formatting Toolbar | _(not spec'd)_ | — | [004-message-formatting-toolbar](https://github.com/meshtastic/Meshtastic-Apple/tree/main/specs/004-message-formatting-toolbar) | 🔵 Draft | Apple-led; strong candidate for Android spec — relates to design [#21](https://github.com/meshtastic/design/issues/21) |
| Lockdown Mode | [20260513-075218-lockdown-mode](https://github.com/meshtastic/Meshtastic-Android/tree/features/lockdown-v2/specs/20260513-075218-lockdown-mode) | 🔴 Branch Complete | [007-lockdown-mode](https://github.com/meshtastic/Meshtastic-Apple/tree/007-lockdown-mode/specs/007-lockdown-mode) | 🔴 Branch Complete | Paired spec — Android `features/lockdown-v2` (53/53 tasks done); Apple `007-lockdown-mode` (27/28 tasks done); firmware protobuf PR #911 is the shared dependency |
| Compose Preview Screenshot Testing | [20260511-211823-compose-screenshot-testing](https://github.com/meshtastic/Meshtastic-Android/tree/main/specs/20260511-211823-compose-screenshot-testing) | 🔴 Branch Complete | _(not spec'd)_ | ✅ Implemented | Android: 51/51 tasks done on `feat/20260507-161858-app-docs-markdown`, awaiting merge. Apple: existing snapshot tests in production (developed without SpecKit, same pattern as TAK v2) |
| M3 Expressive Design System Adoption | [20260513-160000-m3-expressive-adoption](https://github.com/meshtastic/Meshtastic-Android/tree/20260513-160000-m3-expressive-adoption/specs/20260513-160000-m3-expressive-adoption) | 🔵 In Progress | _(not applicable)_ | — | Android-only; M3 Expressive APIs are Compose-specific. Branch `20260513-160000-m3-expressive-adoption`, 14/58 tasks done |
| Docs Auto-Translation | _(not spec'd)_ | — | [008-docs-auto-translation](https://github.com/meshtastic/Meshtastic-Apple/tree/main/specs/008-docs-auto-translation) | ✅ Implemented | Apple-only (Apple Translation framework); Android approach would differ |
| Docs Translation Pipeline (CDN + crowd-source) | _(not spec'd)_ | — | [009-docs-translation-pipeline](https://github.com/meshtastic/Meshtastic-Apple/tree/main/specs/009-docs-translation-pipeline) | ✅ Implemented | Apple-only; outputs to shared `meshtastic/translations` repo |
| Voice Message | _(not spec'd)_ | — | _(not spec'd)_ | 🔵 In Progress | Apple: branch `voice-message`, work-in-progress (3 commits, last activity 2026-03-09). Bundles Codec2 iOS bindings (`AudioManager.swift`, `AudioMessageView.swift`, Codec2 codec2-ios C library). No Android equivalent spec or branch found |

### Status Key

| Icon | Meaning |
|------|---------|
| ✅ Implemented | Feature is shipped and merged to `main` / production |
| 🔴 Branch Complete | All spec tasks done on a feature branch; awaiting PR merge to `main` |
| 🔵 In Progress | Implementation underway on feature branch; tasks partially complete |
| 🔵 Draft | Spec is written; implementation not yet started |
| 🟡 Not Started | Spec exists but work has not begun |
| — | No spec on this platform |

---

## Cross-Platform Gaps

### Features spec'd on Apple but not Android

| Feature | Apple Spec | Priority | Notes |
|---------|-----------|----------|-------|
| **Message Formatting Toolbar** | [004-message-formatting-toolbar](https://github.com/meshtastic/Meshtastic-Apple/tree/main/specs/004-message-formatting-toolbar) | High | Markdown formatting in the message compose UI. Natural pairing with the Android Compose text field. Relates to design [#21](https://github.com/meshtastic/design/issues/21). |
| **Docs Auto-Translation** | [008-docs-auto-translation](https://github.com/meshtastic/Meshtastic-Apple/tree/main/specs/008-docs-auto-translation) | Medium | Apple uses Apple Translation framework. Android equivalent would use ML Kit Translation or Gemini Nano. Translated output feeds the shared `meshtastic/translations` repo. |
| **Docs Translation Pipeline** | [009-docs-translation-pipeline](https://github.com/meshtastic/Meshtastic-Apple/tree/main/specs/009-docs-translation-pipeline) | Medium | CDN-first / on-device fallback / crowd-sourced commit loop. Android should adopt the same approach once the Android docs feature ships. |

### Features spec'd on Android but not Apple

| Feature | Android Spec | Priority | Notes |
|---------|-------------|----------|-------|
| **TAK v2 Protocol** | [005-tak-v2-protocol](https://github.com/meshtastic/Meshtastic-Android/tree/main/specs/005-tak-v2-protocol) | Medium | Apple ships TAK v2 via `AccessoryManager.supportsTAKv2` (firmware ≥ 2.8.0) but has no formal spec. An Apple v2 spec would ensure full UX parity — especially zstd error recovery, CoT type coverage display, and legacy fallback behaviour. Active TAK enhancement work on Apple branch `copilot/sub-pr-1603` (read-only CoT mode, markers, telemetry — 5 commits, 7 files). |
| **M3 Expressive Design System** | [20260513-160000-m3-expressive-adoption](https://github.com/meshtastic/Meshtastic-Android/tree/20260513-160000-m3-expressive-adoption/specs/20260513-160000-m3-expressive-adoption) | Low | Platform-specific by design; M3 Expressive is Android/Compose-only. Apple platform equivalent would use SwiftUI's native animation and component APIs. No action needed. |

### Features in development without a spec (neither platform)

| Feature | Apple Branch | Android Branch | Notes |
|---------|-------------|---------------|-------|
| **Voice Message** | `voice-message` (🔵 In Progress, last active 2026-03-09) | _(none)_ | Codec2-based voice over LoRa. Apple bundles `codec2-ios` C library, adds `AudioManager.swift`, `AudioMessageView.swift`, voice record button in `TextMessageField`. No SpecKit spec on either platform — strong candidate for a paired spec once the Apple prototype stabilises. |

### Features nearing merge on both platforms (high priority to monitor)

| Feature | Android Branch | Apple Branch | Remaining Blockers |
|---------|---------------|-------------|-------------------|
| **Lockdown Mode** | `features/lockdown-v2` (53/53 tasks) | `007-lockdown-mode` (27/28 tasks) | Shared dependency: firmware protobufs PR #911 must merge first |
| **Local Mesh Discovery** | `feat/discovery` (50/51 tasks) | ✅ `main` | Android final task: full verification run (D048) |
| **Node List Layout** | `feat/node-list` (47/47 tasks) | ✅ `main` | No remaining tasks — ready to open PR |
| **App Documentation** | `feat/20260507-161858-app-docs-markdown` (159/159 tasks) | ✅ `main` | No remaining tasks — ready to open PR |

---

## Paired Features — Implementation Comparison

These features have been spec'd on both platforms.

### 1. Local Mesh Discovery

A diagnostic tool that cycles through LoRa modem presets to audit the local RF environment, capturing node visibility and signal data per preset and presenting results as maps, tables, and best-preset recommendations.

| Aspect | Android | Apple |
|--------|---------|-------|
| Spec | [20260507-161658](https://github.com/meshtastic/Meshtastic-Android/tree/main/specs/20260507-161658-local-mesh-discovery) | [001](https://github.com/meshtastic/Meshtastic-Apple/tree/main/specs/001-local-mesh-discovery) |
| Status | 🔴 Branch Complete (`feat/discovery`) | ✅ Implemented |
| Task progress | 50/51 — D048 (verification run) remaining | — |
| Persistence | Room KMP (`core:database`) | Core Data / SwiftData |
| UI framework | Compose Multiplatform (`commonMain`) | SwiftUI |
| AI recommendations | Gemini Nano (Google-flavor) + deterministic fallback | — |
| Maps | Existing CompositionLocal map providers | MapKit |
| BLE recovery | `BleReconnectPolicy` / `BleRadioTransport` | Existing BLE actor |

### 2. Node List Layout (Compact / Complete Density)

A density-switching system for the node list, letting users choose a full-detail "Complete" view or a condensed "Compact" view with per-field toggle controls.

| Aspect | Android | Apple |
|--------|---------|-------|
| Spec | [20260507-161758](https://github.com/meshtastic/Meshtastic-Android/tree/main/specs/20260507-161758-node-list-layout) | [002](https://github.com/meshtastic/Meshtastic-Apple/tree/main/specs/002-node-list-layout) |
| Status | 🔴 Branch Complete (`feat/node-list`) | ✅ Implemented |
| Task progress | 47/47 — all tasks done | — |
| UI framework | Compose Multiplatform (`commonMain`) | SwiftUI |
| Preferences | DataStore (`core:prefs`) | `@AppStorage` |
| Toggle granularity | Per-field toggles (compact mode only) | Per-field toggles (compact mode only) |
| Live preview | In Settings screen | In Settings screen |
| Relates to design | [#47](https://github.com/meshtastic/design/issues/47) node list configurable | [#47](https://github.com/meshtastic/design/issues/47) node list configurable |

### 3. App Documentation (GitHub Pages + In-App Offline + AI Q&A)

Markdown documentation served as a GitHub Pages Jekyll site, bundled in-app for offline browsing, and queryable via an on-device AI assistant. Auto-regenerated by GitHub Actions on push to `main`.

| Aspect | Android | Apple |
|--------|---------|-------|
| Spec | [20260507-161858](https://github.com/meshtastic/Meshtastic-Android/tree/main/specs/20260507-161858-app-docs-markdown) | [003](https://github.com/meshtastic/Meshtastic-Apple/tree/main/specs/003-app-docs-markdown) |
| Status | 🔴 Branch Complete (`feat/20260507-161858-app-docs-markdown`) | ✅ Implemented |
| Task progress | 159/159 — all tasks done | — |
| Web docs | GitHub Pages (Jekyll) | GitHub Pages (Jekyll) |
| In-app AI assistant | Gemini Nano (on-device Q&A, "Chirpy") | Foundation Models (Apple Intelligence) |
| CI generation | GitHub Actions (auto-regen on push) | GitHub Actions (auto-regen on push) |
| Screenshot source | Compose Preview Screenshot Testing (51/51 tasks done, same branch) | Existing snapshot tests (no SpecKit spec — implemented without formal spec process) |

### 4. Lockdown Mode

Protects unattended Meshtastic nodes from unauthorized physical access. When enabled on firmware, a connecting client must provide a passphrase before viewing or modifying the node's configuration. The client detects locked nodes, prompts for authentication, caches credentials securely, and provides a "Lock Now" action.

| Aspect | Android | Apple |
|--------|---------|-------|
| Spec | [20260513-075218-lockdown-mode](https://github.com/meshtastic/Meshtastic-Android/tree/features/lockdown-v2/specs/20260513-075218-lockdown-mode) | [007-lockdown-mode](https://github.com/meshtastic/Meshtastic-Apple/tree/007-lockdown-mode/specs/007-lockdown-mode) |
| Status | 🔴 Branch Complete (`features/lockdown-v2`) | 🔴 Branch Complete (`007-lockdown-mode`) |
| Task progress | 53/53 | 27/28 — 1 task remaining |
| State machine | `LockdownState`: None / NeedsProvision / Locked / Unlocked / UnlockFailed / UnlockBackoff / LockNowAcknowledged | Same state model adapted to Swift `@Observable` coordinator |
| Credential storage | `LockdownPassphraseStore` (KMP commonMain interface, Android Keystore impl) | Keychain via existing `KeychainHelper` |
| UI entry point | Non-dismissable blocking dialog over all navigation | Non-dismissable `.fullScreenCover` |
| TTL fields | `LockdownTokenInfo(bootsRemaining, expiryEpoch)` — optional inputs | Same fields, optional SwiftUI form fields |
| "Lock Now" | Client flag `wasLockNow`; routes next LOCKED status to acknowledged state | `pendingLockNow` flag; same ACK routing |
| Architecture | KMP `commonMain` `LockdownCoordinator` interface; `androidMain` / `jvmMain` Koin impls | SwiftUI `@Observable` coordinator owned at app scope via `Environment` |
| Shared firmware dependency | protobufs PR #911 (`LockdownStatus`, `LockdownAdminMessage`) | protobufs PR #911 (same) |

---

## Recommendations

1. **Open PRs for the three "Branch Complete" paired specs.** Local Mesh Discovery (D048 remaining), Node List Layout (0 remaining), and App Documentation (0 remaining) are all complete on their Android branches. Apple implementations are already in production. These are the highest-priority merges.

2. **Monitor the Lockdown Mode protobufs dependency.** Both Android (`features/lockdown-v2`) and Apple (`007-lockdown-mode`) have near-complete implementations blocked on firmware protobufs PR #911. As soon as that merges, both client branches can be finalised and merged together.

3. **Write an Apple spec for TAK v2.** Apple already ships TAK v2 (`supportsTAKv2`, firmware ≥ 2.8.0) but with no formal spec. The Android 80-task spec defines wire protocol, CoT type mappings, zstd compression, and legacy fallback. An Apple companion spec would scope the iOS/macOS UX surface differences and ensure ongoing parity as the protocol evolves.

4. **Write an Android spec for the Message Formatting Toolbar.** This feature is in Draft on Apple and aligns directly with design issue [#21](https://github.com/meshtastic/design/issues/21). The Android Compose text field is a natural host for a markdown formatting toolbar.

5. **Coordinate the translation pipeline across platforms.** The `meshtastic/translations` repo is populated by the Apple pipeline today. Once the Android docs feature merges, Android should adopt the same CDN-first / on-device-fallback strategy so both clients contribute translations that benefit all users.

6. **Track M3 Expressive progress.** The Android branch is 14/58 tasks complete. While platform-specific, the interaction patterns (swipe-to-reveal, spring animations, expressive FABs) represent UX conventions that should inform how equivalent interactions are handled on Apple platforms even if the API layer differs.

7. **Write a paired spec for Voice Message before the Apple prototype merges.** The Apple `voice-message` branch has a working Codec2-based implementation but no SpecKit spec. A shared spec would define the wire protocol (Codec2 bitrate, packet framing, message type field), UX (record/playback controls, waveform display, permission handling), and Android implementation approach before the two platforms diverge.
