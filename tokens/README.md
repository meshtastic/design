# Meshtastic design tokens

Single source of truth for brand values across web (Claude Design kit), Android (Compose), and Apple (SwiftUI). Belongs in **`meshtastic/design`** (e.g. as `tokens/`), not in an app repo.

## Build

```bash
npm install
npm run build        # the check: emits 3 files or fails
```

Outputs:
| File | Feeds |
|---|---|
| `build/css/tokens.css` | the Claude Design web kit (`@import` from its `styles.css`) |
| `build/compose/MeshtasticTokens.kt` | Meshtastic-Android theme |

Meshtastic-Apple is **not** an output here: it already consumes the standards via SwiftUI named asset colorsets (`Color+Brand.swift`), not Swift color literals. A faithful Apple output = generated `.colorset` `Contents.json` (light+dark) — a custom-format follow-up.

## Scope (deliberate)

- **Colors only.** Proves the bridge end-to-end without the unit-transform footgun: the predefined `compose`/`ios-swift` transform groups multiply `rem`→dp/sp, which mangles bare numbers like radius `12`. Add sizing/typography tokens **with a custom transformGroup**, not into this seed.
- **Full v1.4 color palette** (brand, tonal scales, semantic), authored in DTCG (`$value` + group `$type: color`) — predefined `compose`/`ios-swift` color transforms only fire on `$type`, not legacy `value`. Values from `standards/meshtastic_design_standards_v1_4.md` (canonical).
- **Typography + dimensions deferred.** Font families don't quote correctly and size tokens get rem→dp/sp mangled by the predefined groups — both need a custom transformGroup.
- Uses Style Dictionary **predefined** formats/transform groups. Fine for colors; that's the ceiling.

`add when:` you want spacing/radius/type shared too → add a custom transformGroup and the size/font tokens. Until then, colors are the bridge.
