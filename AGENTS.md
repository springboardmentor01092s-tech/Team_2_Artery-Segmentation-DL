## Cross-session continuation

- Use the dedicated `.git-publish` application checkout when starting from the outer workspace. Within that checkout, read `reports/MASTER_PROJECT_TASK_QUEUE.md` and the newest entry in `reports/PROJECT_CONTINUATION_LEDGER.md`. Use the PRD and acceptance matrix to resolve gaps.
- Select the highest-priority authorized task whose dependencies are available. Confirm existing evidence before retesting. Reproduce defects, make scoped changes, run relevant tests, and verify the normal user workflow where available.
- Update the queue and ledger with status, evidence, commands, changed files, blockers, and the next executable task. Continue through independent work when a task is blocked. Record the handoff before a session ends.
- Keep clinical, engineering, and deployment acceptance distinct. Mark PASS only for the scope actually verified. Resuming a session does not itself authorize training, deployment, commits, or pushes. Keep local research queues and execution notes out of published source.

## Correctness and evidence policy

Apply the [CoroVision correctness policy](COROVISION_CORRECTNESS_POLICY.md) across Milestones 1–4, evaluation, measurement, severity, explainability, reporting, and deployment. Follow it in manual and scheduled continuation. Maintain separate acceptance outcomes for functional correctness and scientific validity. Keep frozen-model outputs, synthetic known-truth demonstrations, and versioned reviewer measurements explicitly identified, and gate release on reproducible evidence and identity consistency.

# Repository publishing rules

- Target repository: https://github.com/springboardmentor01092s-tech/Team_2_Artery-Segmentation-DL
- Allowed push branches: `lingareddy-dhanush` (working branch) and `review` only. Push the same reviewed commit to both as a fast-forward.
- Never push to `main` or `master`, including when the user simply asks to push work. Push only to `lingareddy-dhanush` and `review`.
- This project is nested in an unrelated parent Git repository. Do not publish that parent's other projects or change its remote. Use the dedicated target checkout for publishing.
- Before publishing, exclude credentials, environment secrets, local databases, user uploads, datasets, checkpoints, archives, caches and generated build artifacts. Review notebook outputs and documentation for secrets.
- Training remains paused unless the user explicitly authorizes resuming it.
- The published branch is application-only: do not reintroduce local training notebooks, training runners/queues, checkpoint evaluation scripts, or training execution notes during later source synchronization unless explicitly requested.
