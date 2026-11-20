# Local Python dependency refresh

The derivative image `corovision:python-refresh-local` (index SHA-256 `e0b1bc9bfc91db0022457b18380c7b6247dcc8016343bccc72eb49d529c3d81a`) updates pip to 26.3 and setuptools to 84.2.1. The parent is the previously tested automatic-report image. The build used only a Dockerfile on standard input. Dependency consistency and network-disabled imports of torch, torchvision, OpenCV and SQLite passed.

Offline Trivy used the same local advisory database. Python high findings fell from eight to one. The remaining Python finding is setuptools 70.3.0, declared in pip's vendor manifest and SBOM. The installed setuptools distribution is 84.2.1. Debian findings remained at 60 high and three critical. This derivative establishes the effect of the Python upgrades and still needs production startup and representative workload verification before adoption. The checked-in Dockerfile was unchanged.
