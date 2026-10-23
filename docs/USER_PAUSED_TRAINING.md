# Training paused by user — 14 October 2026

User requested stopping because the laptop is overheating. Do not restart any
training, GPU queue, or monitoring until the user explicitly asks to continue.

Stopped verified CADICA PID 43029 and queue PID 43047; process check confirmed
both exited. Deleted automation `finish-corovision-model-training`.
CADICA best.pt and last.pt remain saved at epoch 2 under
`models/individual/cadica_mps_20261014/`. Unsaved partial-epoch work is not retained.
ARCADE syntax results remain under `output/colab_runs/20261014_syntax/`.
MSD preprocessing remains under `data/nnunet_preprocessed/`.
No Colab tab was open in the observed Chrome window; remote runtime state is
unverified. Do not reconnect or allocate a new runtime while paused.

Migration: copy the complete project plus any original dataset archives stored
outside it and recovered result ZIPs from Downloads. Preserve datasets, original
annotations, split manifests, models, output/outputs, reports, scripts, ml, colab
and docs. Do not rely on copying backend/.venv between operating systems; recreate
dependencies and configure the destination GPU. Update absolute paths in saved
manifests without changing sample membership. Verify checksums and checkpoint
loading before resuming. A CUDA move requires adapting the currently MPS-specific
local queue; do not run it unchanged on an NVIDIA laptop.
