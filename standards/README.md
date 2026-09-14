# Meshtastic Client Design Standards

The current version is v1.5: [meshtastic_design_standards_v1_5.md](meshtastic_design_standards_v1_5.md).

<!-- current-version: meshtastic_design_standards_v1_5.md -->
<!-- Keep this marker and the line above it pointing at the same file as the
     meshtastic_design_standards_latest.md symlink. CI compares them. -->

It governs client UI across Android, Apple, Web and desktop, and section 11 governs the documentation site, the written material in this repository, and the text inside the clients.

## Linking to the standards

Link to this directory. `https://github.com/meshtastic/design/tree/master/standards` renders this page, always names the current version, and never needs updating in the repository doing the linking.

Don't link `meshtastic_design_standards_latest.md` from the web. It is a symlink, and GitHub serves a symlink as its target's filename rather than as the document it points at, so both the blob view and `raw.githubusercontent.com` return 35 bytes of text and no standards. The symlink works normally on a filesystem, so a local clone can still read it:

```shell
cat standards/meshtastic_design_standards_latest.md
```

A tool that needs the document over HTTP can use the REST contents API, which does resolve the symlink:

```shell
gh api repos/meshtastic/design/contents/standards/meshtastic_design_standards_latest.md \
  -H "Accept: application/vnd.github.raw"
```

## Versions

| Version | File | Status |
| --- | --- | --- |
| v1.5 | [meshtastic_design_standards_v1_5.md](meshtastic_design_standards_v1_5.md) | Current |
| v1.4 | [meshtastic_design_standards_v1_4.md](meshtastic_design_standards_v1_4.md) | Superseded |
| v1.3 | [meshtastic_design_standards_v1_3.md](meshtastic_design_standards_v1_3.md) | Superseded |
| v1.2 | [meshtastic_design_standards_v1_2.md](meshtastic_design_standards_v1_2.md) | Superseded |
| v1.0 | [meshtastic_design_standards_v1_0.md](meshtastic_design_standards_v1_0.md) | Superseded |

Superseded versions are published records and are not edited. Changes belong in the current version.

## Cutting a version

Four edits, in one commit:

1. Add the new version file.
2. Repoint the `meshtastic_design_standards_latest.md` symlink at it.
3. Change the version named at the top of this page, and the `current-version` marker beside it.
4. Add a row to the table, and mark the previous version superseded.

Steps three and four are the whole maintenance cost of this page, and they buy every other repository never having to change a link.
