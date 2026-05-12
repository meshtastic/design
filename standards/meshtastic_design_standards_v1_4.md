# Meshtastic Client Design Standards (v1.4)

**Status:** Implementation Guide  
**Primary Audience:** Client Developers & UI Agents  
**Core Goal:** Cross-platform alignment prioritizing accessibility, native OS familiarity, and consistent theme execution.

---

## 1. Node Identity: The Circle Standard
Every node must be represented by a **Circular Identifier**. This follows the universal design convention for "contacts" in modern messaging apps.

* **Messaging View:**
    * **Others:** Display the circular avatar (initials or emoji) to the left of their message bubble, following the pattern of iMessage or Signal.
    * **Self:** Do not display an avatar for your own messages; use right-side bubble alignment to indicate the sender.
* **List Views:**
    * Use a circle with the node's computed color or emoji.
    * The node's color must **not** be used as a color-wash or background for the entire list item row. Rows must remain a neutral background to ensure maximum text legibility and high contrast.

---

## 2. Light & Dark Mode Standards
Clients must provide full, uncompromising support for both Light and Dark themes. Screens must be one or the other—never a hybrid of both.

* **Mode Consistency:**
    * **Light Mode:** High-contrast dark text on white or light-gray backgrounds.
    * **Dark Mode:** High-contrast light text on deep charcoal or pure black backgrounds.
* **Contrast Compliance:** Both modes must maintain a minimum **4.5:1 contrast ratio** (WCAG AA). 
* **Seamless Transition:** All UI elements (cards, icons, toggles) must flip their color logic entirely when the system mode changes.

---

## 3. Dynamic Layout & Conditional Visibility
* **Enabled-Only Settings:** Only show configuration options or status fields for modules/features currently enabled on the device.
* **Null Data Suppression:** If data is unavailable (e.g., no GPS lock or 0% battery), hide the field entirely from the list view. Avoid "N/A" or "0" placeholders.

---

## 4. Iconography & Descriptive Text
* **Labeled Navigation:** Every icon in the bottom navigation bar or sidebar **must** be accompanied by a bold text label to ensure clarity.
* **Icon-Text Redundancy:** Status indicators (Battery, Signal) should include text (e.g., `[Icon] 88%`).
* **Tooltips:** Desktop and Web clients must provide hover tooltips for all icon-only buttons.

---

## 5. Vision-Centric Design & Native Patterns
* **Typography:** Default body font size is **16px**. The application must support **Dynamic Type** scaling (up to 200%) without clipping text or breaking the layout.
* **Touch Targets:** Minimum **44x44 pixels** for all interactive elements to accommodate varying levels of motor precision.
* **Native Feel:** Follow iOS (HIG) and Android (Material Design) conventions for standard components like headers, chat bubbles, and tab bars.

---

## 6. Information Architecture
* **Plain Language:** Use subtext to explain technical settings in simple, non-technical terms (e.g., "Hop Limit: The number of times a message will be repeated by other nodes in the mesh").

---

## 7. Color Palette

All Meshtastic clients must use the official brand color palette defined below. The palette is derived from the two brand colors — **Primary `#2C2D3C`** and **Accent `#67EA94`** — and provides a complete system for building accessible UIs in both light and dark modes.

A visual reference is available at [color-palette.svg](color-palette.svg).

### 7.1 Brand Colors

| Role | Hex | RGB |
|------|-----|-----|
| **Primary** (Foreground) | `#2C2D3C` | `44 45 60` |
| **Accent** (Secondary/Highlight) | `#67EA94` | `103 234 148` |

### 7.2 Neutral Scale (derived from Primary)

Use these for backgrounds, surfaces, text, borders, and dividers.

| Name | Hex | RGB | Light Mode Usage | Dark Mode Usage |
|------|-----|-----|------------------|-----------------|
| Neutral 950 | `#0F1017` | `15 16 23` | — | Darkest background (OLED) |
| Neutral 900 | `#1A1B26` | `26 27 38` | — | Default background |
| Neutral 800 | `#2C2D3C` | `44 45 60` | Primary text | Surface / elevated card |
| Neutral 700 | `#3D3E50` | `61 62 80` | — | Elevated surface |
| Neutral 600 | `#555668` | `85 86 104` | — | Secondary text |
| Neutral 500 | `#6E7082` | `110 112 130` | Placeholder text | Placeholder text |
| Neutral 400 | `#9496A6` | `148 150 166` | Disabled / tertiary text | Disabled / tertiary text |
| Neutral 300 | `#B8BAC8` | `184 186 200` | Borders | — |
| Neutral 200 | `#D5D6E0` | `213 214 224` | Dividers | — |
| Neutral 100 | `#ECEDF3` | `236 237 243` | Surface / card | — |
| Neutral 50 | `#F5F6FA` | `245 246 250` | Default background | — |

### 7.3 Neutral Variant Scale

A slightly more chromatic version of the Neutral scale. Used for outlines, surface variants, and elements requiring subtle visual separation from plain neutral backgrounds.

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| Neutral Variant 900 | `#1D1E2B` | `29 30 43` | — |
| Neutral Variant 800 | `#303245` | `48 50 69` | Dark mode outlineVariant |
| Neutral Variant 700 | `#444660` | `68 70 96` | Dark mode outline |
| Neutral Variant 600 | `#5C5E78` | `92 94 120` | Light outline |
| Neutral Variant 500 | `#767892` | `118 120 146` | Light outlineVariant |
| Neutral Variant 400 | `#9698B0` | `150 152 176` | — |
| Neutral Variant 300 | `#BDBFCF` | `189 191 207` | — |
| Neutral Variant 200 | `#DADBE7` | `218 219 231` | Light surfaceVariant |
| Neutral Variant 100 | `#EDEEF6` | `237 238 246` | — |
| Neutral Variant 50 | `#F6F7FC` | `246 247 252` | — |

### 7.4 Green Scale (derived from Accent)

Use these for interactive elements, highlights, and success states. Extended to a full tonal range for Material 3 compatibility.

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| Green 950 | `#002E13` | `0 46 19` | Darkest green (onPrimaryContainer dark) |
| Green 900 | `#003D1A` | `0 61 26` | Very dark green |
| Green 800 | `#005C2E` | `0 92 46` | Dark green |
| Green 700 | `#2D8F52` | `45 143 82` | **Theme Primary** — buttons in light mode |
| Green 600 | `#3FB86D` | `63 184 109` | Green text on light backgrounds, success |
| Green 500 | `#67EA94` | `103 234 148` | **Brand accent** — dark-mode primary |
| Green 400 | `#8FF0B2` | `143 240 178` | Hover / active accent |
| Green 300 | `#B5F5CE` | `181 245 206` | Light highlight, primaryContainer light |
| Green 200 | `#CCFADD` | `204 250 221` | — |
| Green 100 | `#E5FCEE` | `229 252 238` | Success tint background |
| Green 50 | `#F0FEF5` | `240 254 245` | Lightest green tint |

### 7.5 Accent Blue Scale (Tertiary)

Used for tertiary/info elements and secondary call-to-action. The key color is `#2855A8`.

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| Blue 950 | `#001849` | `0 24 73` | Darkest blue |
| Blue 900 | `#002366` | `0 35 102` | onTertiaryContainer dark |
| Blue 800 | `#1A3F8C` | `26 63 140` | Deep blue |
| Blue 700 | `#2855A8` | `40 85 168` | **Theme Accent** — tertiary light mode |
| Blue 600 | `#5C6BC0` | `92 107 192` | Info indicators, links |
| Blue 500 | `#7B8AD0` | `123 138 208` | Medium blue |
| Blue 400 | `#9BA8E0` | `155 168 224` | **Link color** — hyperlinks, clickable URLs |
| Blue 300 | `#B0BFF0` | `176 191 240` | Dark-mode tertiary |
| Blue 200 | `#D0D8F5` | `208 216 245` | — |
| Blue 100 | `#E0E3F8` | `224 227 248` | Link tint background |
| Blue 50 | `#E8EAF6` | `232 234 246` | Info tint background |

### 7.6 Error Scale

Extended error palette for complete theme support.

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| Error 900 | `#410002` | `65 0 2` | onErrorContainer light |
| Error 800 | `#690005` | `105 0 5` | onError dark |
| Error 700 | `#93000A` | `147 0 10` | errorContainer dark |
| Error 600 | `#BA1A1A` | `186 26 26` | **Error light mode** (WCAG-safe on white) |
| Error 500 | `#E05252` | `224 82 82` | Brand error — indicators, non-text usage |
| Error 400 | `#FF897D` | `255 137 125` | — |
| Error 300 | `#FFB4AB` | `255 180 171` | Error dark mode text |
| Error 200 | `#FFDAD6` | `255 218 214` | — |
| Error 100 | `#FDEAEA` | `253 234 234` | Error tint background, errorContainer light |

### 7.7 Semantic Colors

Use these for status indicators, alerts, and feedback.

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| Link | `#9BA8E0` | `155 168 224` | Hyperlinks, clickable URLs (Blue 400) |
| Link Light | `#E0E3F8` | `224 227 248` | Link tint background |
| Info | `#5C6BC0` | `92 107 192` | Informational indicators, links |
| Info Light | `#E8EAF6` | `232 234 246` | Info tint background |
| Warning | `#E8A33E` | `232 163 62` | Caution / attention states |
| Warning Light | `#FFF3E0` | `255 243 224` | Warning tint background |
| Error | `#E05252` | `224 82 82` | Errors, destructive actions |
| Error Light | `#FDEAEA` | `253 234 234` | Error tint background |
| Success | `#3FB86D` | `63 184 109` | Success states, confirmations (Green 600) |
| Success Light | `#E5FCEE` | `229 252 238` | Success tint background |

---

## 8. Material 3 Theme Mapping

This section maps the Meshtastic palette to Material 3 color roles. M3 requires 5 tonal palettes (Primary, Secondary, Tertiary, Neutral, Neutral Variant) mapped to specific color roles for light and dark schemes.

### 8.1 Key Color Sources

| M3 Palette | Meshtastic Source | Key Color |
|------------|-------------------|-----------|
| Primary | Green Scale | `#2D8F52` (Green 700) |
| Secondary | Neutral Scale | `#555668` (Neutral 600) |
| Tertiary | Blue Scale | `#2855A8` (Blue 700) |
| Neutral | Neutral Scale | `#2C2D3C` (Neutral 800) |
| Neutral Variant | Neutral Variant Scale | `#303245` (NV 800) |
| Error | Error Scale | `#BA1A1A` (Error 600) |

### 8.2 Light Scheme Role Mapping

| M3 Role | Hex | Source |
|---------|-----|--------|
| `primary` | `#2D8F52` | Green 700 |
| `onPrimary` | `#FFFFFF` | White |
| `primaryContainer` | `#B5F5CE` | Green 300 |
| `onPrimaryContainer` | `#002E13` | Green 950 |
| `secondary` | `#555668` | Neutral 600 |
| `onSecondary` | `#FFFFFF` | White |
| `secondaryContainer` | `#D5D6E0` | Neutral 200 |
| `onSecondaryContainer` | `#2C2D3C` | Neutral 800 |
| `tertiary` | `#2855A8` | Blue 700 |
| `onTertiary` | `#FFFFFF` | White |
| `tertiaryContainer` | `#E8EAF6` | Blue 50 |
| `onTertiaryContainer` | `#001849` | Blue 950 |
| `error` | `#BA1A1A` | Error 600 |
| `onError` | `#FFFFFF` | White |
| `errorContainer` | `#FDEAEA` | Error 100 |
| `onErrorContainer` | `#410002` | Error 900 |
| `background` | `#F5F6FA` | Neutral 50 |
| `onBackground` | `#2C2D3C` | Neutral 800 |
| `surface` | `#F5F6FA` | Neutral 50 |
| `onSurface` | `#2C2D3C` | Neutral 800 |
| `surfaceVariant` | `#DADBE7` | NV 200 |
| `onSurfaceVariant` | `#5C5E78` | NV 600 |
| `outline` | `#767892` | NV 500 |
| `outlineVariant` | `#BDBFCF` | NV 300 |
| `inverseSurface` | `#3D3E50` | Neutral 700 |
| `inverseOnSurface` | `#ECEDF3` | Neutral 100 |
| `inversePrimary` | `#67EA94` | Green 500 |
| `surfaceTint` | `#2D8F52` | Green 700 (= primary) |
| `scrim` | `#000000` | Black |
| `surfaceDim` | `#D5D6E0` | Neutral 200 |
| `surfaceBright` | `#F5F6FA` | Neutral 50 |
| `surfaceContainerLowest` | `#FFFFFF` | White |
| `surfaceContainerLow` | `#F5F6FA` | Neutral 50 |
| `surfaceContainer` | `#ECEDF3` | Neutral 100 |
| `surfaceContainerHigh` | `#E0E1EB` | Interpolated 100↔200 |
| `surfaceContainerHighest` | `#D5D6E0` | Neutral 200 |

### 8.3 Dark Scheme Role Mapping

| M3 Role | Hex | Source |
|---------|-----|--------|
| `primary` | `#67EA94` | Green 500 |
| `onPrimary` | `#0F1017` | Neutral 950 |
| `primaryContainer` | `#2D8F52` | Green 700 |
| `onPrimaryContainer` | `#B5F5CE` | Green 300 |
| `secondary` | `#B8BAC8` | Neutral 300 |
| `onSecondary` | `#1A1B26` | Neutral 900 |
| `secondaryContainer` | `#3D3E50` | Neutral 700 |
| `onSecondaryContainer` | `#D5D6E0` | Neutral 200 |
| `tertiary` | `#B0BFF0` | Blue 300 |
| `onTertiary` | `#001849` | Blue 950 |
| `tertiaryContainer` | `#2855A8` | Blue 700 |
| `onTertiaryContainer` | `#E8EAF6` | Blue 50 |
| `error` | `#FFB4AB` | Error 300 |
| `onError` | `#690005` | Error 800 |
| `errorContainer` | `#93000A` | Error 700 |
| `onErrorContainer` | `#FDEAEA` | Error 100 |
| `background` | `#1A1B26` | Neutral 900 |
| `onBackground` | `#ECEDF3` | Neutral 100 |
| `surface` | `#1A1B26` | Neutral 900 |
| `onSurface` | `#ECEDF3` | Neutral 100 |
| `surfaceVariant` | `#444660` | NV 700 |
| `onSurfaceVariant` | `#BDBFCF` | NV 300 |
| `outline` | `#767892` | NV 500 |
| `outlineVariant` | `#444660` | NV 700 |
| `inverseSurface` | `#ECEDF3` | Neutral 100 |
| `inverseOnSurface` | `#2C2D3C` | Neutral 800 |
| `inversePrimary` | `#2D8F52` | Green 700 |
| `surfaceTint` | `#67EA94` | Green 500 (= primary) |
| `scrim` | `#000000` | Black |
| `surfaceDim` | `#0F1017` | Neutral 950 |
| `surfaceBright` | `#3D3E50` | Neutral 700 |
| `surfaceContainerLowest` | `#0F1017` | Neutral 950 |
| `surfaceContainerLow` | `#1A1B26` | Neutral 900 |
| `surfaceContainer` | `#242533` | Interpolated 900↔800 |
| `surfaceContainerHigh` | `#2C2D3C` | Neutral 800 |
| `surfaceContainerHighest` | `#3D3E50` | Neutral 700 |

### 8.4 Fixed Colors

Fixed colors remain constant regardless of light/dark mode. Use for elements that must maintain visual identity across themes.

| M3 Role | Hex | Source |
|---------|-----|--------|
| `primaryFixed` | `#B5F5CE` | Green 300 |
| `primaryFixedDim` | `#8FF0B2` | Green 400 |
| `onPrimaryFixed` | `#002E13` | Green 950 |
| `onPrimaryFixedVariant` | `#2D8F52` | Green 700 |
| `secondaryFixed` | `#D5D6E0` | Neutral 200 |
| `secondaryFixedDim` | `#B8BAC8` | Neutral 300 |
| `onSecondaryFixed` | `#1A1B26` | Neutral 900 |
| `onSecondaryFixedVariant` | `#555668` | Neutral 600 |
| `tertiaryFixed` | `#E0E3F8` | Blue 100 |
| `tertiaryFixedDim` | `#B0BFF0` | Blue 300 |
| `onTertiaryFixed` | `#001849` | Blue 950 |
| `onTertiaryFixedVariant` | `#2855A8` | Blue 700 |

### 8.5 Dynamic Color (Android 12+)

On Android 12 and above, the system provides dynamic color palettes derived from the user's wallpaper. When dynamic color is available, clients **should** use it as the default to respect user personalization. The static palette above serves as the fallback when dynamic color is unavailable or disabled.

---

## 9. Color Usage Rules

* **Accent on white:** Never use the raw accent `#67EA94` for text on white or light backgrounds — it does not meet WCAG AA contrast. Use `Green 600` (`#3FB86D`) or `Green 700` (`#2D8F52`) instead.
* **Semantic consistency:** Use Info/Warning/Error/Success colors consistently across all views. Do not repurpose semantic colors for decorative use.
* **Node colors:** Individual node-computed colors are separate from this palette. They may use any hue but must still meet the 4.5:1 contrast ratio against their background.
* **Dark mode mapping:** Swap light-mode backgrounds for their dark-mode counterparts from the neutral scale. Do not simply invert colors.
* **Message text legibility:** Message bubble text must use `onSurface` (or equivalent high-contrast token) — never the node's computed foreground color, which may fail contrast when alpha-blended over surfaces.
* **Error accessibility:** Use Error 600 (`#BA1A1A`) for error text in light mode. The brand error `#E05252` (Error 500) is reserved for non-text indicators, containers, and decorative elements where 3:1 contrast (SC 1.4.11) is sufficient.

---

### Agent Implementation Checklist (v1.4)
- [ ] Are **Circular IDs** used only for the *other* party in chat views?
- [ ] Are **List Rows** neutral (no colored backgrounds for the whole row)?
- [ ] Does the UI strictly follow **Light OR Dark** mode without mixing?
- [ ] Does the UI **hide** fields where data is unavailable (Null Data Suppression)?
- [ ] Are all navigation icons accompanied by **Text Labels**?
- [ ] Do interactive elements meet the **44x44px** hit target?
- [ ] Is the body text at least **16px** by default?
- [ ] Are all UI colors drawn from the **official palette** (Sections 7.2–7.6)?
- [ ] Is accent green **never used as text** on light backgrounds?
- [ ] Do all foreground/background pairings meet **WCAG AA 4.5:1** contrast?
- [ ] Are **semantic colors** (Link, Info, Warning, Error, Success) used consistently and not repurposed?
- [ ] Is the **Link** color using `Blue 400` (`#9BA8E0`) for hyperlinks and clickable URLs?
- [ ] Is **Success** using `Green 600` (`#3FB86D`) — not `Green 500` (`#67EA94`)?
- [ ] Does the M3 theme use **Section 8** role mappings (or dynamic color on Android 12+)?
- [ ] Are **Fixed colors** (Section 8.4) used for theme-invariant elements?
- [ ] Does message text use **`onSurface`** — never raw node foreground colors?
- [ ] Is the **Neutral Variant** scale (Section 7.3) used for outline and surfaceVariant roles?
