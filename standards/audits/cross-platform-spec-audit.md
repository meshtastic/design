# Cross-Platform Feature Spec Audit

**Status:** Reference Document  
**Scope:** iOS/macOS (Meshtastic-Apple) vs Android (Meshtastic-Android)  
**Last Updated:** 2026-05-17  

> **Purpose:** This document audits all SpecKit feature specifications written to date across the Apple and Android Meshtastic client repositories, surfaces which features are specced on one platform but not the other, and flags opportunities for cross-platform alignment.

---

## Feature Specification Matrix

| Feature | Android Spec | Android Status | Apple Spec | Apple Status | Notes |
|---------|-------------|----------------|-----------|--------------|-------|
| Local Mesh Discovery | [20260507-161658-local-mesh-discovery](https://github.com/meshtastic/Meshtastic-Android/tree/main/specs/20260507-161658-local-mesh-discovery) | 🟡 Not Started | [001-local-mesh-discovery](https://github.com/meshtastic/Meshtastic-Apple/tree/main/specs/001-local-mesh-discovery) | ✅ Implemented | Paired spec — Apple implementation is a reference |
| Node List Layout (Compact / Complete) | [20260507-161758-node-list-layout](https://github.com/meshtastic/Meshtastic-Android/tree/main/specs/20260507-161758-node-list-layout) | 🟡 Not Started | [002-node-list-layout](https://github.com/meshtastic/Meshtastic-Apple/tree/main/specs/002-node-list-layout) | ✅ Implemented | Paired spec — Android uses Compose Multiplatform (commonMain) |
| App Documentation (Web + In-App + AI) | [20260507-161858-app-docs-markdown](https://github.com/meshtastic/Meshtastic-Android/tree/main/specs/20260507-161858-app-docs-markdown) | 🟡 Not Started | [003-app-docs-markdown](https://github.com/meshtastic/Meshtastic-Apple/tree/main/specs/003-app-docs-markdown) | ✅ Implemented | Paired spec — Android uses Gemini Nano; Apple uses Foundation Models |
| TAK v2 Protocol Integration | [005-tak-v2-protocol](https://github.com/meshtastic/Meshtastic-Android/tree/main/specs/005-tak-v2-protocol) | 🔵 Draft | _(not spec'd)_ | — | Android-led; Apple has legacy TAK v1 but no formal v2 spec |
| Message Formatting Toolbar | _(not spec'd)_ | — | [004-message-formatting-toolbar](https://github.com/meshtastic/Meshtastic-Apple/tree/main/specs/004-message-formatting-toolbar) | 🔵 Draft | Apple-led; strong candidate for Android spec — relates to design [#21](https://github.com/meshtastic/design/issues/21) |
| Docs Auto-Translation | _(not spec'd)_ | — | [008-docs-auto-translation](https://github.com/meshtastic/Meshtastic-Apple/tree/main/specs/008-docs-auto-translation) | ✅ Implemented | Apple-only (Apple Translation framework); Android approach would differ |
| Docs Translation Pipeline (CDN + crowd-source) | _(not spec'd)_ | — | [009-docs-translation-pipeline](https://github.com/meshtastic/Meshtastic-Apple/tree/main/specs/009-docs-translation-pipeline) | ✅ Implemented | Apple-only; outputs to shared `meshtastic/translations` repo |
| Compose Preview Screenshot Testing | [20260511-211823-compose-screenshot-testing](https://github.com/meshtastic/Meshtastic-Android/tree/main/specs/20260511-211823-compose-screenshot-testing) | 🔵 Draft | _(not applicable)_ | — | Android internal dev tooling; not a user-facing feature |

### Status Key

| Icon | Meaning |
|------|---------|
| ✅ Implemented | Feature is shipped and in production |
| 🔵 Draft | Spec is written; implementation not yet started or in early stages |
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
| **TAK v2 Protocol** | [005-tak-v2-protocol](https://github.com/meshtastic/Meshtastic-Android/tree/main/specs/005-tak-v2-protocol) | Medium | Apple has legacy TAK v1 support. The v2 spec introduces zstd compression and full CoT type coverage. An Apple v2 spec would ensure wire-protocol and UX parity. |

---

## Paired Features — Implementation Comparison

These features have been spec'd on both platforms. Apple implementations are complete; Android implementations are all Not Started.

### 1. Local Mesh Discovery

A diagnostic tool that cycles through LoRa modem presets to audit the local RF environment, capturing node visibility and signal data per preset and presenting results as maps, tables, and best-preset recommendations.

| Aspect | Android | Apple |
|--------|---------|-------|
| Spec | [20260507-161658](https://github.com/meshtastic/Meshtastic-Android/tree/main/specs/20260507-161658-local-mesh-discovery) | [001](https://github.com/meshtastic/Meshtastic-Apple/tree/main/specs/001-local-mesh-discovery) |
| Status | 🟡 Not Started | ✅ Implemented |
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
| Status | 🟡 Not Started | ✅ Implemented |
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
| Status | 🟡 Not Started | ✅ Implemented |
| Web docs | GitHub Pages (Jekyll) | GitHub Pages (Jekyll) |
| In-app AI assistant | Gemini Nano (on-device Q&A) | Foundation Models (Apple Intelligence) |
| CI generation | GitHub Actions (auto-regen on push) | GitHub Actions (auto-regen on push) |
| Screenshot source | Compose Preview Screenshot Testing | Existing snapshot tests |

---

## Recommendations

1. **Prioritise Android implementation of the three paired specs.** Local Mesh Discovery, Node List Layout, and App Docs are all Implemented on Apple and Not Started on Android. The Apple specs serve as a stable reference for intended behaviour and acceptance criteria.

2. **Write an Android spec for the Message Formatting Toolbar.** This feature is in Draft on Apple and aligns directly with design issue [#21](https://github.com/meshtastic/design/issues/21). The Android Compose text field is a natural host for a markdown formatting toolbar.

3. **Write an Apple spec for TAK v2.** Apple already ships legacy TAK v1 support. The Android v2 spec defines the wire protocol, CoT type mappings, and zstd compression scheme; a parallel Apple spec would scope the iOS/macOS upgrade and surface any client-side UX differences.

4. **Coordinate the translation pipeline across platforms.** The `meshtastic/translations` repo is populated by the Apple pipeline today. Once the Android docs feature ships, Android should adopt the same CDN-first / on-device-fallback strategy so both clients contribute translations that benefit all users.
