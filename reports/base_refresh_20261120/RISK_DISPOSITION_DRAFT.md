# Container vulnerability disposition: draft for owner approval (20 November 2026)

**Status: DRAFT.** These are proposed dispositions grouped by package family. They become accepted risks only after the project owner signs off. A fresh rebuild and Trivy rescan of the updated `Dockerfile` must confirm the counts.

## What changed in the main `Dockerfile`

- The runtime and web stages move from Debian 12 (`bookworm`) to Debian 13 (`trixie`), the base Codex validated in `reports/base_refresh_20261120/`. The retained scan of that base has **0 critical** (down from 3) and 123 high.
- `apt-get upgrade -y` runs before installing packages, so Debian security fixes that exist are applied at build time. This includes the `zlib1g` fix listed in the inventory.
- The existing `setuptools>=78.1.1` pin covers the one Python finding that has a fix.
- The `libglib2.0-0t64` package name follows Debian 13.

## Proposed disposition of the 123 high findings

| Package family | Findings | Used at runtime by CoroVision? | Proposed disposition |
|---|---:|---|---|
| Kerberos / GSSAPI (`libkrb5-3`, `libgssapi-krb5-2`, `libk5crypto3`, `libkrb5support0`) | 56 | No. Pulled in as a transitive library; the app has no Kerberos or GSSAPI authentication and no Kerberos configuration. | Accept with mitigation; revisit when Debian ships fixes |
| util-linux family (`util-linux`, `mount`, `login`, `bsdutils`, `libblkid1`, `libmount1`, `libsmartcols1`, `libuuid1`, `liblastlog2-2`) | 36 | No. Base OS utilities; the app never mounts filesystems or performs logins. | Accept with mitigation |
| GnuPG family (`gnupg`, `gpg`, `gpg-agent`, `gpgconf`, `gpgsm`, `dirmngr`, `gnupg-l10n`) | 7 | No. Package-signature tooling only. | Accept; candidate for removal from the runtime image |
| `libexpat1` | 4 | Indirect. Python's XML parser; no CoroVision code path parses XML from uploads. | Accept with monitoring |
| `libsqlite3-0` | 3 | Yes. Local SQLite database; all queries are parameterized through SQLAlchemy and no user-supplied SQL is executed. | Accept for local use; hosted deployment should use PostgreSQL |
| `libtiff6` | 2 | Limited. Uploaded TIFFs are decoded by Pillow's bundled library, not the system `libtiff6`; system libtiff is reached only through Poppler. | Accept with monitoring |
| `libcurl3t64-gnutls` | 2 | No outbound fetching by the app through this library. | Accept |
| X11 / ncurses / perl-base / systemd / udev / ACL libraries | 11 | No. | Accept |
| `zlib1g` | 1 | Yes, compression. | **Resolved by rebuild** (`apt-get upgrade` installs `1:1.3.dfsg+really1.3.1-1+deb13u1`) |
| `setuptools` | 1 | Install-time only. | **Resolved** by the `>=78.1.1` pin |

## Mitigations already in place (`compose.yaml`)

- The container runs as the unprivileged user `10001`.
- The root filesystem is read-only, with writable data only in `/data` and a size-capped `/tmp`.
- All Linux capabilities are dropped (`cap_drop: ALL`) and `no-new-privileges` is set.
- The port is published only on `127.0.0.1` locally. A hosted deployment must sit behind HTTPS.

## Owner actions

1. Rebuild and rescan the updated image, then attach the new Trivy JSON.
2. Approve or change each disposition above.
3. Optionally remove the GnuPG packages from the runtime stage after confirming nothing at runtime needs them.
