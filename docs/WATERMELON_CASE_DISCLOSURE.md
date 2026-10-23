# Case actions disclosure

Adapted from https://registry.watermelon.sh/r/create-new-disclosure.json.
The shadcn import was previewed before adaptation. Its demo tiles are replaced
with controlled Create case / Find case actions. Existing dependencies already
provide motion and icons; no shared components or global theme variables are
overwritten by the registry CLI.

Dashboard create and sidebar plus open the same creation form. Dashboard browse
opens Find case. Both modes live in the same in-page disclosure, with visible
pressed states, labelled controls, Escape-to-close, focus return and reduced
motion. No new network operation is introduced: case creation uses the existing
authorized endpoint; search filters only accessible case records. The original
case list remains visible below the disclosure. Source, modality, anatomy and
task controls are preserved. Viewer navigation remains unchanged.

Shared application buttons retain their primary / outline / ghost hierarchy,
theme colours, 44px minimum height and consistent corner radius and icon gaps.
