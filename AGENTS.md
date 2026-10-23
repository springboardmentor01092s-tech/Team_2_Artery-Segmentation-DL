# Repository publishing rules

- Target repository: https://github.com/springboardmentor01092s-tech/Team_2_Artery-Segmentation-DL
- User's working branch: `lingareddy-dhanush`.
- Never push to `main` or `master`, including when the user simply asks to push work. Use the named working branch unless the user explicitly specifies another non-default branch.
- This project is nested in an unrelated parent Git repository. Do not publish that parent's other projects or change its remote. Use the dedicated target checkout for publishing.
- Before publishing, exclude credentials, environment secrets, local databases, user uploads, datasets, checkpoints, archives, caches and generated build artifacts. Review notebook outputs and documentation for secrets.
- Training remains paused unless the user explicitly authorizes resuming it.
