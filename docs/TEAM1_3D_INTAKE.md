# Team 1 3D review intake

Source reviewed: `springboardmentor01092s-tech/Team_1_Artery-Segmentation-DL`, branch `team-1/vascuai-review`, commit `e4c8673`.

The source snapshot is MIT licensed. Its bounded NIfTI ingestion design informed the container preflight in `backend/app/volume_inference.py`: complete gzip/CRC reading, declared-payload truncation checks, datatype/bit-depth agreement and rejection of unsupported header/image pairs. The implementation was adapted to CoroVision's stricter scalar 3D, explicit-millimetre and 96-million-voxel ImageCAS contract.

Useful viewer findings retained as design guidance:

- verify source identity and CT/mask shape and affine before overlay;
- bound browser transfer, decompression, CPU/GPU memory and WebGL texture use;
- cancel pending downloads/workers when navigation, session or selected run changes;
- prefer the coded sform over qform to match NiBabel geometry;
- use nearest-neighbour rendering for binary masks and release WebGL resources on close;
- fall back to authenticated artifact downloads when a browser cannot safely render a volume.

Not imported:

- Team 1's unrelated API, database, authentication and React application stack;
- its SmallUNet3D handoff or any checkpoint, dataset or private artifact;
- synthetic stenosis/explanation fixtures as medical evidence;
- claims of validated 3D stenosis, diameter or severity, because the source explicitly states those capabilities remain unavailable.

No training was resumed and no model release was changed by this intake.
