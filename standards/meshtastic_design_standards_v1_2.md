# Meshtastic Client Design Standards (v1.2)

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

### 7.3 Green Scale (derived from Accent)

Use these for interactive elements, highlights, and success states.

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| Green 100 | `#E5FCEE` | `229 252 238` | Success tint background |
| Green 300 | `#B5F5CE` | `181 245 206` | Light highlight |
| Green 400 | `#8FF0B2` | `143 240 178` | Hover / active accent |
| Green 500 | `#67EA94` | `103 234 148` | **Brand accent** — primary action buttons, brand highlight |
| Green 600 | `#3FB86D` | `63 184 109` | Green text on light backgrounds |
| Green 700 | `#2D8F52` | `45 143 82` | Strong / dark green text |

### 7.4 Semantic Colors

Use these for status indicators, alerts, and feedback.

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| Accent | `#3949AB` | `57 73 171` | Darker info blue for active/pressed states, text on light backgrounds |
| Accent Light | `#E0E3F8` | `224 227 248` | Accent tint background |
| Info | `#5C6BC0` | `92 107 192` | Informational indicators, links |
| Info Light | `#E8EAF6` | `232 234 246` | Info tint background |
| Warning | `#E8A33E` | `232 163 62` | Caution / attention states |
| Warning Light | `#FFF3E0` | `255 243 224` | Warning tint background |
| Error | `#E05252` | `224 82 82` | Errors, destructive actions |
| Error Light | `#FDEAEA` | `253 234 234` | Error tint background |
| Success | `#3FB86D` | `63 184 109` | Success states, confirmations (Green 600) |
| Success Light | `#E5FCEE` | `229 252 238` | Success tint background |

### 7.5 Color Usage Rules

* **Accent on white:** Never use the raw accent `#67EA94` for text on white or light backgrounds — it does not meet WCAG AA contrast. Use `Green 600` (`#3FB86D`) or `Green 700` (`#2D8F52`) instead.
* **Semantic consistency:** Use Info/Warning/Error/Success colors consistently across all views. Do not repurpose semantic colors for decorative use.
* **Node colors:** Individual node-computed colors are separate from this palette. They may use any hue but must still meet the 4.5:1 contrast ratio against their background.
* **Dark mode mapping:** Swap light-mode backgrounds for their dark-mode counterparts from the neutral scale. Do not simply invert colors.

---

### Agent Implementation Checklist (v1.2)
- [ ] Are **Circular IDs** used only for the *other* party in chat views?
- [ ] Are **List Rows** neutral (no colored backgrounds for the whole row)?
- [ ] Does the UI strictly follow **Light OR Dark** mode without mixing?
- [ ] Does the UI **hide** fields where data is unavailable (Null Data Suppression)?
- [ ] Are all navigation icons accompanied by **Text Labels**?
- [ ] Do interactive elements meet the **44x44px** hit target?
- [ ] Is the body text at least **16px** by default?
- [ ] Are all UI colors drawn from the **official palette** (Sections 7.2–7.4)?
- [ ] Is accent green **never used as text** on light backgrounds?
- [ ] Do all foreground/background pairings meet **WCAG AA 4.5:1** contrast?
- [ ] Are **semantic colors** (Info, Warning, Error, Success) used consistently and not repurposed?
- [ ] Is **Success** using `Green 600` (`#3FB86D`) — not `Green 500` (`#67EA94`)?
