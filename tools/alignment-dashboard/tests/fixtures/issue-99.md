## Area of Alignment

All Meshtastic clients display the same underlying radio data (always transmitted in metric SI units) but may render it in different units depending on the user's locale. A cross-platform standard is needed to define:

1. **Which units are locale-driven** (converted by the OS/platform)
2. **Which units never change** regardless of locale
3. **Natural scaling rules** (e.g. when to switch from m → km, ft → mi)
4. **The authority for unit preference** — OS locale vs in-app setting

---

## Reference Implementation

The iOS/macOS client documents its approach at [meshtastic.github.io/Meshtastic-Apple/user/units-and-locale](https://meshtastic.github.io/Meshtastic-Apple/user/units-and-locale). Key design decisions:

- **No in-app unit controls.** All unit conversion is delegated to the OS Language & Region setting (iOS: Settings → General → Language & Region).
- **Locale-driven units:**

| Data type | Metric | US Imperial | UK Imperial |
|-----------|--------|-------------|-------------|
| Temperature | °C | °F | °C |
| Distance / altitude | m / km | ft / mi | m / km |
| Speed (GPS ground) | km/h | mph | mph |
| Wind speed | m/s | mph | mph |
| Weight | kg | lbs | stones/lbs |
| Rainfall | mm | in | mm |

- **Units that never change** (international standards):

| Measurement | Unit | Reason |
|-------------|------|--------|
| Barometric pressure | hPa | International meteorological standard |
| Heading / bearing | ° (degrees) | Universal navigation |
| Radiation dosimetry | µR/hr | Standard dosimetry unit |
| GPS coordinates | Decimal degrees | Universal geographic standard |
| Humidity, battery, soil moisture | % | Universal |

- **Natural scaling:** short distances display in m/ft; longer distances auto-switch to km/mi at a threshold. The specific threshold is not yet documented as a cross-platform standard.

---

## Open Questions for Alignment

1. **In-app vs OS locale:** Should all clients delegate unit preference to the OS (Apple's approach), or is an explicit in-app unit selector acceptable? Note that design issue [#87](https://github.com/meshtastic/design/issues/87) specifically requests a configurable wind speed unit setting on Android, which would conflict with an OS-only approach.

2. **Natural scaling thresholds:** At what distance should m → km (or ft → mi) switching occur? Should this be the same value across all clients? Apple uses OS `Measurement` formatting which applies its own threshold; Android would need to match.

3. **Wind speed specifically:** Apple follows locale (m/s or mph). Issue #87 requests an explicit in-app selector. Should wind speed be an exception to the OS-only rule, or should #87 be resolved by improving locale support?

4. **Pressure unit confirmation:** hPa is listed as "never changes" and was discussed in [#84](https://github.com/meshtastic/design/issues/84). Is hPa agreed as the single cross-platform pressure unit? (kPa and mbar display the same data differently.)

5. **Relative time formatting:** Apple uses relative time ("5 min ago") in node list, absolute timestamps elsewhere. What is the agreed cross-platform pattern for last-heard display?

---

## Sub-tasks

- [x] Create Android alignment issue
- [ ] Create iOS alignment issue
- [ ] Create Web alignment issue
- [ ] Define and document the "never changes" unit list as a design standard
- [ ] Define natural scaling thresholds
- [ ] Resolve #87 (wind speed) in the context of this alignment

---

## Related Issues

- [#87](https://github.com/meshtastic/design/issues/87) — Configurable wind speed units
- [#84](https://github.com/meshtastic/design/issues/84) — SI prefixes for large environment values
- [#53](https://github.com/meshtastic/design/issues/53) — Sensor Telemetry UI/UX (PARENT)
