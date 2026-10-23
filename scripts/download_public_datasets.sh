#!/usr/bin/env bash
# Resumable public-source acquisition. Does not access restricted datasets.
set -euo pipefail

root_dir="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root_dir"

mkdir -p data/raw/aortaseg60 data/raw/msd_task08_hepatic_vessel data/raw/cadica data/raw/mendeley_stenosis data/raw/topcow2024 data/raw/ica

fetch() {
  local destination="$1"
  local url="$2"
  curl --fail --location --retry 8 --retry-all-errors --continue-at - --output "$destination" "$url"
}

fetch data/raw/aortaseg60/README.md 'https://zenodo.org/records/18147026/files/README.md?download=1'
for archive in Anev Dissec Nat Old Ven Young; do
  fetch "data/raw/aortaseg60/${archive}.zip" "https://zenodo.org/records/18147026/files/${archive}.zip?download=1"
done
fetch data/raw/msd_task08_hepatic_vessel/Task08_HepaticVessel.tar 'https://msd-for-monai.s3-us-west-2.amazonaws.com/Task08_HepaticVessel.tar'
fetch data/raw/cadica/CADICA_v5.zip 'https://data.mendeley.com/public-api/zip/p9bpx9ctcv/download/5'
fetch data/raw/mendeley_stenosis/stenosis_v3.zip 'https://data.mendeley.com/public-files/datasets/ydrm75xywg/files/61f788d6-65ce-4265-a23a-5ba16931d18b/file_downloaded'
fetch data/raw/topcow2024/TopCoW2024_Data_Release.zip 'https://zenodo.org/records/15692630/files/TopCoW2024_Data_Release.zip?download=1'
fetch data/raw/ica/ICA_NJ_BinarySeg_master.zip 'https://codeload.github.com/MIILab-MTU/ICA_NJ_BinarySeg/zip/refs/heads/master'

md5 -q data/raw/topcow2024/TopCoW2024_Data_Release.zip | grep -qx 'd248a932166316c6c906644b22296d6c'

md5 -q data/raw/aortaseg60/Anev.zip | grep -qx '9e6d8fb0c0e4a0a3cb201ad5667c33c5'
md5 -q data/raw/aortaseg60/Dissec.zip | grep -qx '6775b009d8ab2ac29cc4592f4b698fa3'
md5 -q data/raw/aortaseg60/Nat.zip | grep -qx 'a7a5de2493cd0ce9cf66ab151c440550'
md5 -q data/raw/aortaseg60/Old.zip | grep -qx 'f9a6dd507267679f45ab32021e63c04a'
md5 -q data/raw/aortaseg60/Ven.zip | grep -qx '44c8fe0ee423921658a6c6050087b446'
md5 -q data/raw/aortaseg60/Young.zip | grep -qx 'e9b02228e6c4f4a3e63c181dd2cada91'
