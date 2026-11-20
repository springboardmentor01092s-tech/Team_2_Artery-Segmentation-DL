# Docker parity defects and runtime evidence

Fresh standard parity project on loopback port 8003 started with separate SQLite/storage volume and the read-only 3D overlay. Both 2D and 3D reported available. Image ID: `sha256:4f28f429374c69ba752170bd17635aa784cb34f5633c9e4e965dbf36704a6fb8`. Next exercise administrator onboarding and actual inference in this fresh project.

- Standard container `git-publish-app-1`: image `sha256:5973d9331246c1141cf07c04d343cc1f1bee8b243b689cb1c48b6874ed3779e0`. Its `trained_release.py` SHA-256 `d7ccc04b2b26279add923e7716ef3557517ae6d65fb3aff27f79a25f96cd9a6c` differs from current checkout. Readiness reports 3D unavailable.
- Isolated `corovision-demo-app-1`: image `sha256:48d16b817e894e5d47cb87db12e3f072e4783d93fdf688f2210713a17e3e1bc0`. Source file SHA-256 `67f1b4064a21295b8c08d4db70aced932f67cafeb711160257d1122f521f6fe4` matches checkout. Python 3.13.18 and pip check passed. Both Compose configurations validated.
- Demo and checkout SHA-256 matched for artery `ea692f8c9c655791a44a340907629cda4e812138a6f15d93cdb2a45166177a7c`, stenosis `f0bc898c95b6efdd53863d5a430fb4b850c2451b440c5a53b92a73e73c5be2e3`, and ImageCAS `b77271b1780f32100bc954ccbec2ac5c4efa54a10e0f5975b631924c8a2f553d`. This proves bytes match current assets, not historical prediction identity.
- Added `compose.3d.yaml` for standard Compose with an explicit read-only mount. Both overlays accept `COROVISION_VOLUME_MODEL_DIR` and reject missing host paths rather than creating empty ones.
- Restored port 8002 serves the older app and lacks the current readiness route. Its historical database remains separate. Earlier cross-port login failure was corrected through same-origin API routing.
- Focused backend regressions: 31 passed, one opt-in model integration skipped. Frontend: 20 passed. No new matched dev/container measurements or release scan in this audit.
