# Meshtastic Cross-Platform Menu Alignment Audit

**Status:** Reference Document  
**Scope:** iOS (Meshtastic-Apple) vs Android (Meshtastic-Android)  
**Areas Covered:** Bottom navigation, node list, node list context menu, node details, filters/sort, settings

> **Purpose:** This document audits the six common navigation surfaces shared by the iOS and Android Meshtastic clients, identifies ordering and structural mismatches, and recommends a canonical order for each surface to guide future alignment work.

---

## 1. Bottom Navigation Tabs

### Current State

| # | iOS label | Android label |
|---|-----------|---------------|
| 1 | **Messages** | **Conversations** |
| 2 | **Connect** | **Nodes** |
| 3 | **Nodes** | **Map** |
| 4 | **Mesh Map** | **Settings** |
| 5 | **Settings** | **Connections** |

### Mismatches

| Issue | Detail |
|-------|--------|
| **Label mismatch** | The messaging tab is called "Messages" on iOS and "Conversations" on Android. |
| **Label mismatch** | The connection-management tab is called "Connect" on iOS and "Connections" on Android. |
| **Label mismatch** | The map tab is called "Mesh Map" on iOS and "Map" on Android. |
| **Order mismatch** | iOS places the BLE connection tab immediately after messaging (position 2); Android places it last (position 5). |
| **Order mismatch** | iOS places Nodes at position 3, Mesh Map at 4, Settings at 5. Android places Nodes at 2, Map at 3, Settings at 4. |

### Recommended Canonical Order

Proposed alignment moves the connection/device tab to the end (less frequently used once paired) and standardises labels:

| # | Canonical label | Rationale |
|---|-----------------|-----------|
| 1 | **Messages** | Primary use-case; matches SMS/messaging-app conventions |
| 2 | **Nodes** | Core mesh view; used frequently after initial setup |
| 3 | **Map** | Spatial companion to the node list |
| 4 | **Settings** | Configuration; infrequently accessed |
| 5 | **Connect** | Device pairing; needed mainly at setup or when switching hardware |

### Tracking

| Platform | Issue |
|----------|-------|
| iOS (Meshtastic-Apple) | [#1840](https://github.com/meshtastic/Meshtastic-Apple/issues/1840) |
| Android (Meshtastic-Android) | [#5543](https://github.com/meshtastic/Meshtastic-Android/issues/5543) |

---

## 2. Node List — Row Layout

### Current State

**iOS (`NodeListItem` — standard density)**

Row layout (fields hidden if data absent, top-to-bottom):
1. Short-name circle + battery compact
2. Lock/key icon + Long Name (+ star if favourite)
3. "Connected" indicator (own node only)
4. Last heard + online/offline dot
5. Role icon + label
6. Unmonitored badge / Store & Forward badge
7. Distance + bearing (remote nodes with position)
8. Channel number (if > 0)
9. MQTT indicator
10. Log availability icons
11. Hops away
12. LoRa signal meter (direct-link nodes)

**Android (`NodeItem`)**

Row layout (fields hidden if data absent, top-to-bottom):
1. Node chip/avatar + PKC key icon + Long Name + last heard + transport icon + status icons (favourite, mute, unmessageable)
2. Status message (if set)
3. Battery + voltage | Distance | Elevation
4. Signal row: SNR + RSSI (direct), or hops count (indirect); channel; satellite count
5. Sensor grid: PAX, temperature, humidity, pressure, soil, voltage, current, IAQ
6. Footer: hardware model | role | node ID

### Mismatches

| Issue | Detail |
|-------|--------|
| **Layout philosophy** | iOS uses a two-column left/right layout; Android uses stacked horizontal rows. |
| **Key status placement** | iOS puts the lock/key icon inline with the long name; Android puts a separate `NodeKeyStatusIcon` beside the avatar. |
| **Telemetry inline** | Android shows temperature, humidity, pressure, etc. directly in the node card; iOS does not (accessible only via node detail). |
| **Hardware model** | Android shows the hardware model name in the list row footer; iOS does not. |
| **Node ID** | Android shows the node ID in the list row footer; iOS does not. |
| **Mute status** | Android shows a mute icon in the row header; iOS uses "Hide alerts" but does not surface the muted state in the list row. |
| **Status message** | Android shows the node's status message in the list row; iOS does not. |
| **Signal display** | Both show signal strength, but iOS uses a signal meter bar for direct nodes; Android shows SNR + RSSI text values. |

---

## 3. Node List — Long-Press Context Menu

### Current State

**iOS (10 items for non-connected node):**

| # | Label |
|---|-------|
| 1 | Hide alerts / Show alerts |
| 2 | Share Contact QR |
| 3 | Add to favorites / Remove from favorites |
| 4 | Message |
| 5 | Exchange Positions |
| 6 | Exchange User Info |
| 7 | Trace Route |
| 8 | Client History *(conditional: S&F routers only)* |
| 9 | Ignore Node / Remove from ignored *(destructive)* |
| 10 | Delete Node *(destructive)* |

**Android (4 items, excluding own node):**

| # | Label |
|---|-------|
| 1 | Add Favorite / Remove Favorite |
| 2 | Ignore / Remove Ignored |
| 3 | Mute Always / Unmute *(conditional: capability flag)* |
| 4 | Remove *(destructive)* |

### Mismatches

| Issue | Detail |
|-------|--------|
| **Action count** | iOS context menu has 10 items; Android has 4. iOS exposes many actions that Android surfaces only within the node detail screen. |
| **Actions absent from Android context menu** | Message, Share Contact QR, Exchange Positions, Exchange User Info, Trace Route, Client History. |
| **Mute vs. alert silencing** | iOS uses "Hide alerts / Show alerts"; Android uses "Mute Always / Unmute". Same intent, different wording. |
| **Order difference** | iOS leads with the alert-mute toggle (position 1) then favourite (position 3); Android leads with favourite (position 1) then ignore (position 2). |
| **Destructive item label** | iOS uses "Delete Node"; Android uses "Remove". |

### Recommended Canonical Order

Keeping the menu concise (4–6 items) while surfacing the most-used actions:

| # | Canonical label | Notes |
|---|-----------------|-------|
| 1 | **Add to favorites / Remove from favorites** | Most common non-destructive toggle |
| 2 | **Mute notifications / Unmute** | Alert silencing (merge iOS "Hide alerts" and Android "Mute") |
| 3 | **Message** | Quick access to chat |
| 4 | **Trace Route** | Frequently used diagnostic |
| 5 | **Ignore / Remove from ignored** | Maintenance action |
| 6 | **Remove** | Destructive; placed last. iOS renames "Delete Node" to match Android and firmware API |

### Tracking

| Platform | Issue |
|----------|-------|
| iOS (Meshtastic-Apple) | [#1841](https://github.com/meshtastic/Meshtastic-Apple/issues/1841) |
| Android (Meshtastic-Android) | [#5544](https://github.com/meshtastic/Meshtastic-Android/issues/5544) |

---

## 4. Node Details View

### Current State

**iOS sections (in order):**

| # | Section | Notes |
|---|---------|-------|
| 1 | Hardware (NodeInfoItem) | Hero image of device model |
| 2 | Node | ID, key, firmware, role, uptime, first/last heard |
| 3 | Environment *(conditional)* | Sensor grid or WeatherKit widget |
| 4 | Power *(conditional)* | Power metrics widget |
| 5 | Logs | Links to 7–8 log sub-views |
| 6 | Actions | Message, favourites, exchange, trace route, navigation, etc. |
| 7 | Administration *(conditional)* | Reboot, power off, refresh metadata |

**Android sections (in order):**

| # | Section | Notes |
|---|---------|-------|
| 1 | Details | Short name, role, node ID, node number, last heard, hops, uptime, SNR, RSSI, MQTT, key |
| 2 | Actions | DM button, Share Contact, Favourite toggle; Ignore/Mute/Remove toggles; full Telemetry sub-card with logs and request buttons |
| 3 | Device *(conditional)* | Hardware image, model name, support status |
| 4 | Notes *(conditional, favourites only)* | Free-text field for personal notes |
| 5 | Administration + Firmware *(conditional)* | Remote admin, session state, firmware version info |

### Mismatches

| Issue | Detail |
|-------|--------|
| **Actions placement** | iOS places Actions near the bottom (section 6 of 7); Android places them second (section 2 of 5), making them immediately accessible. |
| **Hardware info placement** | iOS places the hardware card first; Android places it third as a conditional card. |
| **Telemetry vs. Logs** | iOS has a dedicated "Logs" section listing sub-view links; Android integrates both log-view links and request/refresh buttons inside the "Telemetry" sub-card within Actions. |
| **Inline sensor data** | Android shows current sensor readings inline within the Details and Telemetry sections; iOS shows them in a separate conditional "Environment" section. |
| **Notes field** | Android provides a free-text notes field for favourited nodes; iOS has no equivalent. |
| **Firmware info** | Android shows installed and latest firmware versions in the Administration section; iOS shows only the installed version in the Node section. |
| **PKC key mismatch banner** | Both platforms show a warning when public keys do not match, but iOS places it at the top of the Node section while Android places it inline in the Details section. |
| **Navigation actions** | iOS includes "Open Compass", "Navigate to node", and "Foxhunt on your watch" in Actions; Android has no equivalents. |
| **Exchange actions** | iOS includes "Exchange Positions" and "Exchange User Info" in Actions; Android surfaces these via Telemetry request buttons instead. |

### Recommended Section Order

| # | Canonical section | Notes |
|---|-------------------|-------|
| 1 | **Details** | Identity, IDs, key, firmware, role, uptime, first/last heard |
| 2 | **Actions** | Message, favourite, mute, trace route, exchange, navigate |
| 3 | **Telemetry / Logs** | Signal, environment, power, position logs with request buttons |
| 4 | **Hardware** | Device model image, support status |
| 5 | **Notes** *(conditional)* | Free-text, only for favourited nodes |
| 6 | **Administration** *(conditional)* | Reboot, shutdown, factory reset, firmware |

---

## 5. Node List Filters and Sort

### Current State

**iOS — Filter toggles (bottom sheet):**

| # | Filter |
|---|--------|
| 1 | Via LoRa |
| 2 | Via MQTT |
| 3 | Online |
| 4 | Encrypted |
| 5 | Favorites |
| 6 | Ignored *(node list only)* |
| 7 | Environment *(node list only)* |
| 8 | Distance *(toggle + range picker)* |
| 9 | Hops Away *(slider, −1 to 7)* |
| 10 | Roles *(toggle + multi-select list)* |

iOS sort order: not user-configurable (always last-heard descending; favourites pinned first; connected node always at top).

**Android — Sort radio buttons:**

| # | Sort option |
|---|-------------|
| 1 | Last Heard |
| 2 | Alphabetical |
| 3 | Distance |
| 4 | Hops Away |
| 5 | Channel |
| 6 | Via MQTT |
| 7 | Via Favorite |

**Android — Filter checkboxes:**

| # | Filter |
|---|--------|
| 1 | Exclude Infrastructure |
| 2 | Include Unknown |
| 3 | Only Online |
| 4 | Only Direct |
| 5 | Show Ignored |
| 6 | Exclude MQTT |

### Mismatches

| Issue | Detail |
|-------|--------|
| **Sort is configurable on Android only** | Android lets users choose from 7 sort orders; iOS always sorts by last-heard with favourites pinned — no UI to change this. |
| **Different filter framing** | iOS has an "Via MQTT" inclusion toggle; Android has an "Exclude MQTT" exclusion checkbox. The logic is inverted. |
| **"Online" filter naming** | iOS uses "Online"; Android uses "Only Online" — same intent, minor label difference. |
| **Filters absent from Android** | iOS has: Encrypted, Environment (has sensors), Hops Away slider, Roles multi-select, Distance range picker. |
| **Filters absent from iOS** | Android has: Exclude Infrastructure, Include Unknown, Only Direct (0-hop), Sort options. |
| **"Favorites" filter** | iOS has an inclusion filter; Android achieves the same through the "Via Favorite" sort option (top of list) rather than a filter toggle. |
| **Ignored nodes** | iOS uses a toggle to include ignored nodes; Android uses "Show Ignored" with a count badge and a warning banner when active. |
| **Distance filter** | iOS surfaces distance as a filter with a range picker; Android surfaces it as a sort dimension only. |

### Recommended Canonical Filter/Sort Set

**Sort (user-selectable, matching Android's existing options):**

| # | Option |
|---|--------|
| 1 | Last Heard *(default)* |
| 2 | Alphabetical |
| 3 | Distance |
| 4 | Hops Away |
| 5 | Via Favorite |

**Filters:**

| # | Filter | Framing |
|---|--------|---------|
| 1 | Online only | Inclusion toggle |
| 2 | Direct only (0 hops, not MQTT) | Inclusion toggle |
| 3 | Favorites only | Inclusion toggle |
| 4 | Exclude MQTT | Exclusion toggle |
| 5 | Exclude infrastructure roles | Exclusion toggle |
| 6 | Show ignored | Inclusion toggle (with count badge) |
| 7 | Roles | Multi-select |
| 8 | Max hops away | Numeric picker / slider |

---

## 6. Settings Navigation

### Current State

**iOS — always-visible top-level items:**

| # | Item |
|---|------|
| 1 | About Meshtastic |
| 2 | Help & Documentation |
| 3 | App Settings |
| 4 | Local Mesh Discovery |
| 5 | Routes |
| 6 | Route Recorder |
| 7 | Firmware Updates |

**iOS — Radio Configuration (when connected):**

| # | Item |
|---|------|
| 1 | LoRa |
| 2 | Channels |
| 3 | Security |
| 4 | Share QR Code |

**iOS — Device Configuration (when connected):**

| # | Item |
|---|------|
| 1 | User |
| 2 | Bluetooth |
| 3 | Device |
| 4 | Display |
| 5 | Network |
| 6 | Position |
| 7 | Power |

**iOS — Module Configuration (when connected):**

| # | Item |
|---|------|
| 1 | Ambient Lighting |
| 2 | Canned Messages |
| 3 | Detection Sensor |
| 4 | External Notification |
| 5 | MQTT |
| 6 | Range Test |
| 7 | PAX Counter |
| 8 | Ringtone |
| 9 | Serial |
| 10 | Store & Forward |
| 11 | TAK Server |
| 12 | Telemetry |

---

**Android — Radio Configuration section:**

| # | Item |
|---|------|
| 1 | User |
| 2 | LoRa |
| 3 | Channels |
| 4 | Security |

**Android — Device Configuration sub-screen:**

| # | Item |
|---|------|
| 1 | Device |
| 2 | Position |
| 3 | Power |
| 4 | Network *(conditional)* |
| 5 | Display |
| 6 | Bluetooth *(conditional)* |

**Android — Module Settings sub-screen:**

| # | Item |
|---|------|
| 1 | MQTT |
| 2 | Serial |
| 3 | External Notification |
| 4 | Store & Forward |
| 5 | Range Test |
| 6 | Telemetry |
| 7 | Canned Message |
| 8 | Audio |
| 9 | Remote Hardware |
| 10 | Neighbor Info |
| 11 | Ambient Lighting |
| 12 | Detection Sensor |
| 13 | Paxcounter |
| 14 | Status Message *(conditional)* |
| 15 | Traffic Management *(conditional)* |
| 16 | TAK *(conditional)* |

**Android — Administration sub-screen (via Settings):**

| # | Item |
|---|------|
| 1 | Reboot |
| 2 | Shutdown |
| 3 | Factory Reset |
| 4 | NodeDB Reset |

### Mismatches

#### Radio Configuration

| Issue | Detail |
|-------|--------|
| **"User" placement** | iOS places "User" in Device Configuration; Android places "User" in Radio Configuration as the first item. |
| **LoRa ordering** | iOS lists LoRa first in Radio Configuration; Android lists it second (after User). |
| **"Share QR Code"** | iOS includes this inside Radio Configuration; Android exposes QR sharing from node actions, not from Settings. |

#### Device Configuration

| Issue | Detail |
|-------|--------|
| **Item ordering** | iOS: User, Bluetooth, Device, Display, Network, Position, Power. Android: Device, Position, Power, Network, Display, Bluetooth. These orderings are completely different. |
| **"User" grouping** | iOS groups "User" with device config; Android groups it with radio config. |
| **Conditional items** | Android conditionally shows Network (WiFi/Ethernet only) and Bluetooth (BLE-capable only). iOS always shows both. |

#### Module Configuration

| Issue | Detail |
|-------|--------|
| **Ordering** | iOS sorts alphabetically; Android uses a custom order (MQTT first, then by approximate importance). |
| **"Ringtone" vs "Audio"** | iOS lists "Ringtone" as a separate module; Android has "Audio" (which includes ringtone config). |
| **Android-only modules** | Android has: Audio, Remote Hardware, Neighbor Info, Status Message, Traffic Management. |
| **iOS-only module entry** | iOS lists "PAX Counter"; Android uses "Paxcounter" — different capitalisation. |
| **"Canned Messages" label** | iOS: "Canned Messages" (plural). Android: "Canned Message" (singular). |

#### Administration / App Settings

| Issue | Detail |
|-------|--------|
| **Reboot/Shutdown location** | iOS surfaces Reboot and Power Off inside the Node Detail "Administration" section. Android surfaces them in a dedicated "Administration" sub-screen inside Settings. |
| **Factory Reset / NodeDB Reset** | Android has both in the Administration sub-screen; iOS does not expose Factory Reset or NodeDB Reset in the UI. |
| **Firmware update** | iOS has "Firmware Updates" as a top-level Settings item. Android has "Firmware Update" inside the "Advanced" section and shows current/latest firmware on the Node Detail screen. |
| **App Settings structure** | iOS groups all app preferences under a single "App Settings" top-level item. Android spreads them across Privacy, Appearance, Persistence, and Info sub-sections within Settings. |
| **Route Recorder** | iOS has "Route Recorder" and "Routes" as top-level Settings items; Android has no direct equivalent. |
| **Local Mesh Discovery** | iOS has "Local Mesh Discovery" as a top-level Settings item; Android handles this via the Connections tab. |

### Recommended Canonical Settings Structure

**Top level (always visible):**

| # | Section / Item | Notes |
|---|----------------|-------|
| 1 | **Radio Configuration** | User, LoRa, Channels, Security, Share QR Code |
| 2 | **Device Configuration** | Expandable sub-screen |
| 3 | **Module Configuration** | Expandable sub-screen |
| 4 | **App Settings** | Appearance, notifications, privacy, data |
| 5 | **Administration** | Reboot, shutdown, factory reset, NodeDB reset, firmware |
| 6 | **About / Help** | Version, documentation, acknowledgements |

**Recommended Radio Configuration order:**

| # | Item |
|---|------|
| 1 | User |
| 2 | LoRa |
| 3 | Channels |
| 4 | Security |
| 5 | Share QR Code |

**Recommended Device Configuration order:**

| # | Item |
|---|------|
| 1 | Device |
| 2 | Display |
| 3 | Position |
| 4 | Power |
| 5 | Network *(conditional)* |
| 6 | Bluetooth *(conditional)* |

**Recommended Module Configuration order (by frequency of use):**

| # | Item |
|---|------|
| 1 | MQTT |
| 2 | Telemetry |
| 3 | Canned Messages |
| 4 | External Notification |
| 5 | Store & Forward |
| 6 | Neighbor Info |
| 7 | Detection Sensor |
| 8 | Ambient Lighting |
| 9 | Range Test |
| 10 | Serial |
| 11 | Audio / Ringtone |
| 12 | PAX Counter |
| 13 | Remote Hardware |
| 14 | TAK *(conditional)* |
| 15 | Status Message *(conditional)* |
| 16 | Traffic Management *(conditional)* |

---

## Summary of All Mismatches

### High Priority (most user-facing impact)

| # | Area | Mismatch |
|---|------|----------|
| 1 | **Nav tabs — order** | Connection tab is position 2 on iOS, position 5 on Android |
| 2 | **Nav tabs — labels** | "Messages" vs "Conversations"; "Connect" vs "Connections"; "Mesh Map" vs "Map" |
| 3 | **Context menu — actions** | iOS has 10 actions; Android has 4; Message, Trace Route, Exchange, Share QR absent from Android context menu |
| 4 | **Context menu — order** | iOS leads with alert-mute; Android leads with Favorite |
| 5 | **Node detail — Actions placement** | iOS: section 6 of 7; Android: section 2 of 5 |
| 6 | **Settings — User placement** | iOS: Device Configuration; Android: Radio Configuration |
| 7 | **Settings — Device Configuration order** | Completely different ordering between platforms |

### Medium Priority

| # | Area | Mismatch |
|---|------|----------|
| 8 | **Filters — sort** | Configurable sort on Android only; iOS always uses last-heard |
| 9 | **Filters — filter set** | Different filters on each platform; some have inverse framing (include vs. exclude) |
| 10 | **Node detail — Telemetry vs. Logs** | iOS: separate Logs section with links; Android: integrated Telemetry card with inline data and request buttons |
| 11 | **Node detail — sections** | iOS: Hardware first; Android: Hardware third |
| 12 | **Settings — Module order** | iOS: alphabetical; Android: by approximate importance |
| 13 | **Settings — Administration location** | iOS: inside Node Detail; Android: inside Settings |

### Low Priority (minor label/terminology)

| # | Area | Mismatch |
|---|------|----------|
| 14 | **Context menu — destructive label** | "Delete Node" (iOS) vs "Remove" (Android) |
| 15 | **Module label** | "Canned Messages" (iOS) vs "Canned Message" (Android) |
| 16 | **Module label** | "PAX Counter" (iOS) vs "Paxcounter" (Android) |
| 17 | **Module label** | "Ringtone" (iOS) vs "Audio" (Android) |
| 18 | **Filter label** | "Online" (iOS) vs "Only Online" (Android) |
| 19 | **Context menu — mute label** | "Hide alerts" (iOS) vs "Mute Always" (Android) |

---

## Sources

| Platform | Commit | Key files |
|----------|--------|-----------|
| iOS (Meshtastic-Apple) | `725906848e` | `ContentView.swift`, `NodeList.swift`, `NodeListItem.swift`, `NodeListFilter.swift`, `NodeDetail.swift`, `Settings.swift`, `AppSettings.swift` |
| Android (Meshtastic-Android) | `ed806c036f` | `TopLevelDestination.kt`, `NodeListScreen.kt`, `NodeItem.kt`, `NodeDetailContent.kt`, `SettingsScreen.kt`, `RadioConfig.kt` |
