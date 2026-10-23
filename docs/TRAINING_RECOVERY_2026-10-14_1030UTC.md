# Training recovery — 14 October 2026, 10:30 UTC

The earlier CADICA training and queue processes were no longer present. The
cause of interruption is unknown. The saved `last.pt` loaded successfully with
`weights_only=True`: epoch 2, seed 42, input size 512, original seven classes.

Resumed CADICA with the same configuration and `--resume`, restoring optimizer,
scheduler and saved RNG state. The process printed `device=mps; input_size=512;
start_epoch=2`. Observed PID 43029, execution session 4896. These identifiers
must be checked for freshness before any future restart.

MSD preprocessing has 303 case-property files. It was not repeated. Restored
the sequential queue (execution session 13083) waiting on the new CADICA PID;
the preprocessing PID is now optional rather than an obsolete required PID.
No second GPU training job was started concurrently.

Opened the existing Colab notebook in a new Chrome tab. It initially showed
Connect GPU and no active execution counts. Requested connection; it showed
Connecting to T4. The user then switched Chrome to another window, so no
further browser input was sent. Connection, stenosis checkpoint survival and
final evaluation are NOT yet verified. Do not rerun training blindly.

The measured-results report was refreshed. Only ARCADE syntax has a recovered
completed final-test report. CADICA epoch-2 validation results are intermediate,
not final held-out results. ICA, DCA1 and Mendeley gates remain unresolved.
