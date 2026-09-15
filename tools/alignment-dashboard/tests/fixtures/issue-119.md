# 📡 Site Planner coverage round-trip — client spec

> [!IMPORTANT]
> **Let a client display Site Planner RF-coverage on its map, and (optionally) drive an estimate from the app.** There are **two halves with two different mechanisms** — and, critically, **no headless params→GeoJSON API**: the [Site Planner](https://github.com/meshtastic/meshtastic-site-planner) is a client-side WASM SPLAT!/ITM simulator, so coverage is only ever computed in a browser context.
> - **Inbound (planner → app):** the planner exports a **styled GeoJSON FeatureCollection** and hands it over via the **OS share sheet / open-in**. Clients register a handler for `.geojson` / `application/geo+json`, import it, and render it as a named map overlay. This is the primary, always-available path.
> - **Outbound (app → planner):** the app opens the planner at a **flat query contract** (`?lat=&lon=&name=&tx_power=&…&run=1`) that prefills the transmitter and **autoruns** the sim. In a normal browser the result comes back via the share sheet; inside a **native WebView embed** the planner posts the GeoJSON straight to a `window.__meshtasticNative` bridge (`&bridge=1`).

**Tracking:** design#119 · **Planner (source of truth):** [#70](https://github.com/meshtastic/meshtastic-site-planner/pull/70) simplestyle export · [#72](https://github.com/meshtastic/meshtastic-site-planner/pull/72) "Send to App" share · [#73](https://github.com/meshtastic/meshtastic-site-planner/pull/73) prefill + autorun + source metadata · [#74](https://github.com/meshtastic/meshtastic-site-planner/pull/74) native bridge + full flat query contract (merged + deployed) · **Reference build:** [Meshtastic-Android#6136](https://github.com/meshtastic/Meshtastic-Android/pull/6136)

> [!NOTE]
> **Status (2026-09-02): ✅ Complete on Apple and Android — both halves shipped on both clients, planner side fully merged.** Android [#6136](https://github.com/meshtastic/Meshtastic-Android/pull/6136) (merged 2026-07-07) delivered import + estimate together; Apple shipped import in [#2056](https://github.com/meshtastic/Meshtastic-Apple/pull/2056) (merged 2026-07-15) and the outbound estimate in [#2081](https://github.com/meshtastic/Meshtastic-Apple/pull/2081) (merged 2026-07-16). Planner [#70](https://github.com/meshtastic/meshtastic-site-planner/pull/70)/[#72](https://github.com/meshtastic/meshtastic-site-planner/pull/72)/[#73](https://github.com/meshtastic/meshtastic-site-planner/pull/73)/[#74](https://github.com/meshtastic/meshtastic-site-planner/pull/74) all merged 2026-07-05–07.

---

## Coverage GeoJSON format (source of truth)

The interchange artifact is a standard **RFC 7946 `FeatureCollection`** of coverage polygons, MIME `application/geo+json` (accept `application/json`, `application/vnd.geo+json`, and `.geojson` by extension too). Rendering is driven by the [**simplestyle-spec**](https://github.com/mapbox/simplestyle-spec), so any client that speaks GeoJSON + simplestyle can display it without planner-specific code.

**Top-level foreign member** (RFC 7946 §6.1 — carried for provenance / layer naming):

| Member | Type | Meaning |
|---|---|---|
| `properties.generator` | string | e.g. `"meshtastic-site-planner"` — identifies the source. |
| `properties.name` | string | the transmitter/site name; clients use it as the default **layer name**. |

**Per-feature `properties`:**

| Property | Type | Meaning |
|---|---|---|
| `fill` | hex `#rrggbb` | simplestyle fill colour (from the chosen colormap). **Primary** styling signal. |
| `fill-opacity` | number 0–1 | simplestyle fill opacity. |
| `stroke` | hex `#rrggbb` | simplestyle stroke colour. |
| `stroke-opacity` | number 0–1 | simplestyle stroke opacity. |
| `color` | CSS colour | **Legacy** colour — clients must **fall back** to this if `fill` is absent (older exports / other producers). |
| `dbm` | number | signal level for that band, dBm. Informational (labels/legend). |
| `label` | string | human band label. Informational. |

> [!NOTE]
> Clients should render from **simplestyle first, `color` as fallback**, and tolerate `rgb()` as well as hex (Apple's parser already handles `rgb()`; Android's `parseCssColor` handles hex + `rgb()`). Never hard-fail on an unknown/missing style — draw with a sane default.

---

## Inbound — import coverage (all clients)

The always-available half. No app→planner coupling; the planner (or any file manager, chat app, cloud drive) simply *hands the client a file*.

- **Register an import target** for `application/geo+json` / `application/json` / `.geojson` (and KML if the client supports it) via the platform's share/open-in mechanism. On Android that's `ACTION_VIEW` + `ACTION_SEND` intent filters; on iOS it's the document/share extension (open-in + share sheet).
- **Parse** the FeatureCollection, **name** the layer from `properties.name` (fall back to the filename), **apply** simplestyle (→ `color` fallback), and add it as a **toggleable map overlay** alongside the mesh.
- The planner's **"Send to App"** ([#72](https://github.com/meshtastic/meshtastic-site-planner/pull/72)) is just `navigator.share({ files: [<.geojson>] })` with `application/geo+json` — nothing planner-specific reaches the client, so the same import path serves any GeoJSON source.
- ⚠️ **File / share-sheet only — never fetch a remote URL handed in by a deep link.** A deep-link variant that took a URL and fetched it was removed from Apple as an **SSRF surface** ([Meshtastic-Apple#2129](https://github.com/meshtastic/Meshtastic-Apple/pull/2129), merged 2026-07-20): a link from any source could make the app issue arbitrary requests from the user's network. Clients accept coverage only as a **file already handed to them** by the OS (open-in, share sheet, drag-and-drop, file picker). No client-initiated fetch of a caller-supplied URL.

---

## Outbound — estimate coverage (all clients)

The app hands the planner a configured, auto-running view. **Flat query contract** ([#73](https://github.com/meshtastic/meshtastic-site-planner/pull/73)/[#74](https://github.com/meshtastic/meshtastic-site-planner/pull/74)) — a partial transmitter merged over planner defaults, so a client never needs to know the planner's internal parameter schema:

| Query key | Unit | Meaning |
|---|---|---|
| `lat` / `lon` | decimal degrees | transmitter position. |
| `name` | string (%-encoded) | site name → becomes `properties.name` on export. |
| `tx_power` | watts | transmit power. |
| `tx_freq` | MHz | centre frequency. |
| `tx_height` | metres | antenna height AGL. |
| `tx_gain` | dBi | antenna gain. |
| `color_scale` | enum | coverage palette ([#74](https://github.com/meshtastic/meshtastic-site-planner/pull/74)) — one of `plasma` (default), `viridis`, `CMRmap`, `cool`, `turbo`, `jet`. Unknown → plasma. |
| `run` | `1` | **autorun**: fire the simulation on map-load, no user click in the planner. |
| `bridge` | `1` | native-embed only: deliver the result to the JS bridge instead of the share sheet. |

- **Advanced params (all sections, [#74](https://github.com/meshtastic/meshtastic-site-planner/pull/74)):** the flat contract now also carries every applicable planner field as readable keys, so a client can expose "advanced" params without base64-encoding a `#cfg` blob — receiver: `rx_sensitivity` (dBm), `rx_height` (m), `rx_loss` (dB); simulation: `max_range` (km), `high_res` (`1`), `situation_fraction` / `time_fraction` (%); environment: `radio_climate`, `polarization`, `clutter_height`, `ground_dielectric`, `ground_conductivity`, `atmosphere_bending`; display: `min_dbm`, `max_dbm`, `overlay_transparency`. Unknown enum values fall back to the default. (`rx_gain` is omitted — ignored for area coverage.) The `#cfg=<base64url(JSON)>` permalink still composes for full fidelity.
- **Match the planner's factory defaults + validation** (`store.ts` / the `*.vue` inputs), so an untouched form equals a fresh planner session: `tx_power=0.1 W`, `tx_freq=907 MHz`, `tx_height=2 m`, `tx_gain=2 dBi`, `rx_sensitivity=-130 dBm` (range −150…−30), `max_range=30 km` (≤150, or ≤70 with `high_res`), `color_scale=plasma`.
- **Prefill from the connected radio where possible** (each client from its own config): transmit frequency (the radio's computed primary-channel MHz), transmit power (device dBm → W, guarding "0 = region max"), and a receiver sensitivity mapped from the modem preset (per the planner's `parameters.md` table); antenna gain/height aren't in device config, so keep the planner defaults. Present locale-aware units per meshtastic/design#99; the wire values stay W/MHz/m/dBi/dBm.
- **Present the form the planner's way:** mirror its `Site Parameters` panel order + grouping — **Site / Transmitter** → **Receiver** → **Environment** → **Simulation Options** → **Display** (Transmitter + Display open, the rest collapsed) — so clients feel consistent with the planner.

### Native bridge (embedded WebView only — optional)

For clients that want the round-trip **without** a share-sheet hop, load the planner **headless** in an in-app WebView with `&run=1&bridge=1` and inject:

```js
window.__meshtasticNative = { onCoverage: (geojsonString) => { /* import as overlay */ } }
```

On simulation success the planner calls `onCoverage(JSON.stringify(coverageFeatureCollection))` (before it randomizes the transmitter name, so the payload keeps the source `name`) — [`postCoverageToBridge`](https://github.com/meshtastic/meshtastic-site-planner/pull/74) is a **no-op in a normal browser**, so the same build still works via share sheet. Notes for implementers: the WebView must be **attached and non-zero-size** (WebGL/WASM won't get a context otherwise, and autorun waits on map-load), and the JS callback arrives on the planner's thread — **hop to the UI thread** before touching app state.

---

## UX affordances (all clients)

- **Import** needs no dedicated UI beyond being a share/open-in target and listing the result in the existing map-layer manager.
- **Estimate** entry points: a map-toolbar control, and an **"Estimate coverage"** action on a **node's detail** screen (only when the node has a position).
- **Params form:** name, position, TX power / frequency, antenna height / gain, and a **palette picker** (gradient swatches per colormap). **Validate** coordinates + numerics; disable submit on an empty/`0,0` fix.
- **Location shortcuts** to fill the coordinates: **device GPS**, **the selected node**, and **the current map center** — each shown only when it can produce a fix.
- **Progress:** while the (headless) sim runs, show a cancelable progress state, not the raw planner.

---

## Reference implementations

### Android — [#6136](https://github.com/meshtastic/Meshtastic-Android/pull/6136) (first end-to-end round-trip)

- **Inbound (production-ready):** `MainActivity` VIEW/SEND intent filters (Google flavor — the flavor that renders overlays) → one-slot `MapFileImportBus` → existing `addMapLayer` pipeline. Styling via `applySimpleStyleSpec` ([#6088](https://github.com/meshtastic/Meshtastic-Android/pull/6088), merged; `fill`/`stroke` → `color` fallback, hex + `rgb()`).
- **Outbound:** cell-tower map control + node-detail "Estimate coverage" → M3 `ModalBottomSheet` form (validated fields, palette picker with gradient swatches, three location shortcuts) → hidden headless `WebView` at `?…&run=1&bridge=1` → `window.__meshtasticNative.onCoverage` → recenters + imports as overlay. Enabled in the **Google flavor** (`sitePlannerAvailable()`), targets the hosted `https://site.meshtastic.org`; planner [#74](https://github.com/meshtastic/meshtastic-site-planner/pull/74) is **merged + deployed**, and the round-trip is verified end-to-end on-device (headless run → bridge → imported overlay, map recentered).
- **Flavor split:** coverage is **Google-flavor only** on Android — Google Maps + Maps-Utils supply the `GeoJsonLayer`/`KmlLayer` render; the F-Droid/OSMdroid build has no overlay-layer pipeline yet. Parity (share layer UI + logic to common, add an OSMdroid render sink) tracked in [Meshtastic-Android#6138](https://github.com/meshtastic/Meshtastic-Android/issues/6138).

#### What it looks like (Android reference — the form mirrors the planner's own panels)

| Site / Transmitter (device-prefilled) | Receiver + Display | Simulation Options |
| --- | --- | --- |
| <!-- drop siteplanner-1-transmitter-prefilled.png here --> | <!-- drop siteplanner-2-receiver-display.png here --> | <!-- drop siteplanner-3-simulation.png here --> |
| Collapsible sections in the planner's order (Site / Transmitter open). Frequency (906.875 MHz) + TX power (1.0 W) prefilled from the connected radio's config. | Receiver sensitivity **−139 dBm** derived from the radio's LONG_FAST modem preset; palette picker in Display. | Max range + high-resolution terrain toggle. |

Imported coverage renders as a styled overlay on the mesh map: <!-- drop siteplanner-4-map-overlay.png here -->

### Apple — ✅ full round-trip shipped

- **Inbound:** [#2056](https://github.com/meshtastic/Meshtastic-Apple/pull/2056) (merged 2026-07-15). `Info.plist` already declared the app a document handler for `.geojson`/`public.json`, so it appeared as an "Open in Meshtastic" destination — but `onOpenURL` only handled the `meshtastic://` scheme, so tapping it launched the app and silently did nothing. Adds `Router.importMapFile(url:)` calling `MapDataManager.processUploadedFile` directly. Styling (`rgb()` + `color` fallback): [#2037](https://github.com/meshtastic/Meshtastic-Apple/pull/2037) (merged).
- **Outbound:** [#2081](https://github.com/meshtastic/Meshtastic-Apple/pull/2081) (merged 2026-07-16, closes #2058) — Option A, headless WKWebView bridge. `SitePlannerParameters` implements the flat query-contract model + URL builder (`run=1`, `bridge=1`, percent-encoded name), validation bounds mirroring the planner's ranges, and radio prefill (device dBm→W, preset→`rx_sensitivity`).
- **Refinements past the spec:** [#2096](https://github.com/meshtastic/Meshtastic-Apple/pull/2096) radio-tower icon + standard form layout, [#2185](https://github.com/meshtastic/Meshtastic-Apple/pull/2185) Mesh coverage palette default, [#2129](https://github.com/meshtastic/Meshtastic-Apple/pull/2129) SSRF hardening, [#2357](https://github.com/meshtastic/Meshtastic-Apple/pull/2357) layer provenance + persistent visibility.

---

## Per-client tracking (sub-issues)

- [x] **Meshtastic-Android** — [#6136](https://github.com/meshtastic/Meshtastic-Android/pull/6136) **merged 2026-07-07**, import + estimate in one PR, round-trip E2E-verified on-device. Follow-ups: overlays migrated to maps-utils 5.0 ([#6304](https://github.com/meshtastic/Meshtastic-Android/pull/6304)), per-layer opacity ([#6958](https://github.com/meshtastic/Meshtastic-Android/pull/6958)). Coverage is **Google-flavor only**; F-Droid/OSMdroid parity tracked separately in [#6138](https://github.com/meshtastic/Meshtastic-Android/issues/6138) ([#6148](https://github.com/meshtastic/Meshtastic-Android/pull/6148) moved the shared layer UI/logic to common).
- [x] **Meshtastic-Apple** — import [#2056](https://github.com/meshtastic/Meshtastic-Apple/pull/2056) + styling [#2037](https://github.com/meshtastic/Meshtastic-Apple/pull/2037) + outbound estimate [#2081](https://github.com/meshtastic/Meshtastic-Apple/pull/2081) (closes #2058), all merged July 2026.
- [ ] **Meshtastic Web** — no tracker opened. **Does not gate this issue**: cross-platform alignment is scored on Apple + Android parity.
- [x] **Site Planner** — [#70](https://github.com/meshtastic/meshtastic-site-planner/pull/70), [#72](https://github.com/meshtastic/meshtastic-site-planner/pull/72), [#73](https://github.com/meshtastic/meshtastic-site-planner/pull/73), [#74](https://github.com/meshtastic/meshtastic-site-planner/pull/74) all merged 2026-07-05–07 and deployed.

## Notes / open items

- **No headless API exists and none is planned** — the sim is WASM in the page. The share sheet (inbound) and the autorun query + optional bridge (outbound) are the *only* integration seams. Don't design against a server endpoint.
- ✅ **`color_scale` is live** — [#74](https://github.com/meshtastic/meshtastic-site-planner/pull/74) merged and deployed; both clients ship a palette picker against it (Apple defaults to the Mesh palette per [#2185](https://github.com/meshtastic/Meshtastic-Apple/pull/2185)).
- **Layer lifecycle + provenance:** coverage overlays are static snapshots; clients should let users name, toggle, and remove them like any imported layer. Nothing ties an overlay back to a live node.
  - **Record where each layer came from** and treat the two sources differently — added to the spec from [Meshtastic-Apple#2357](https://github.com/meshtastic/Meshtastic-Apple/pull/2357) (merged 2026-08-26). A **planner run replaces the previous planner run** (successive estimates otherwise stack up and obscure each other), while a **user's manual upload is never auto-removed**. Apple models this as a `MapDataMetadata.source` of `sitePlanner` or `manualUpload`, decoding pre-existing manifests as manual uploads.
  - **Per-layer visibility must persist across launches.** Apple's toggles wrote to a transient set rebuilt from stored state on relaunch, so hiding a layer never stuck; that is a bug worth checking for on any client.
  - 🔍 **Parity check open for Android** — no equivalent source/provenance handling was found on `main`, so successive planner runs may still accumulate there. Android has since added per-layer opacity ([#6958](https://github.com/meshtastic/Meshtastic-Android/pull/6958), merged 2026-08-30), so the layer manager is the natural place for it.
- **Basemap caveat:** an imported overlay only reads well over a populated basemap; on a blank/no-tile basemap the contours render but there's no geographic context.






