# Meshtastic Client Design Standards (v1.0)

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

### Agent Implementation Checklist (v1.9)
- [ ] Are **Circular IDs** used only for the *other* party in chat views?
- [ ] Are **List Rows** neutral (no colored backgrounds for the whole row)?
- [ ] Does the UI strictly follow **Light OR Dark** mode without mixing?
- [ ] Does the UI **hide** fields where data is unavailable (Null Data Suppression)?
- [ ] Are all navigation icons accompanied by **Text Labels**?
- [ ] Do interactive elements meet the **44x44px** hit target?
- [ ] Is the body text at least **16px** by default?
