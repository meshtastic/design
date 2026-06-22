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
| `build/swift/MeshtasticTokens.swift` | Meshtastic-Apple |

## Scope (deliberate)

- **Colors only.** Proves the bridge end-to-end without the unit-transform footgun: the predefined `compose`/`ios-swift` transform groups multiply `rem`→dp/sp, which mangles bare numbers like radius `12`. Add sizing/typography tokens **with a custom transformGroup**, not into this seed.
- **Seed values**, not the full palette. Expand the scales/semantic roles from `standards/meshtastic_design_standards_v1_4.md` (canonical) — the full set is already digested in the Claude Design project's `tokens/colors.css`, paste-able here.
- Uses Style Dictionary **predefined** formats/transform groups. Known ceiling — fine for colors; revisit when adding dimensions/type.

`add when:` you want spacing/radius/type shared too → add a custom transformGroup and the size/font tokens. Until then, colors are the bridge.
