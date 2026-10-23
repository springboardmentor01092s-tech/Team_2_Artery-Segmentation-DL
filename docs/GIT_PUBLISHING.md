# Publishing CoroVision AI

Repository: https://github.com/springboardmentor01092s-tech/Team_2_Artery-Segmentation-DL

Working branch: `lingareddy-dhanush`. Never push to `main` or `master`.

The source workspace lives inside a different parent repository. Publishing uses a separate checkout; the parent repository and its remotes are not changed.

The dedicated checkout is stored locally in `.git-publish/` within this project and is excluded from published source. Work in that checkout when committing or pushing this project, not in the unrelated parent repository.

Source code, tests, notebooks, configuration examples and project documentation are included. Local secrets, accounts databases, uploaded images, datasets, trained weights, training bundles, caches and generated builds are excluded. Obtain datasets under their original access and licensing terms, and transfer model artifacts separately before running inference that requires them. Aggregate measured-result reports do not imply that all datasets finished training.

For future updates, copy reviewed source changes into the dedicated checkout, check `git status`, inspect the staged diff, commit on `lingareddy-dhanush`, then run `git push origin HEAD:refs/heads/lingareddy-dhanush`. Do not use a force push.
