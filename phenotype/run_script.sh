#!/usr/bin/env bash
set -euo pipefail
Q_DIR=".."
WORK="."
source "${WORK}/.venv/Scripts/activate"

METADATA_CONFIG="${WORK}/phenotype_cfg.json"
REDCAP_DATA="${Q_DIR}/InvestigationOfTheLo_DATA_2025-10-07_1124.csv" \
REDCAP_DICTIONARY="${Q_DIR}/InvestigationOfTheLongtermAuto_DataDictionary_2025-10-24.csv"
BIDS_DIR="./test"

python -u "${WORK}/convert_phenotype_to_BIDS.py" \
  --data_csv $REDCAP_DATA \
  --dict_csv $REDCAP_DICTIONARY \
  --bids_cfg $METADATA_CONFIG \
  --out_dir $BIDS_DIR

# TO DO: add log levels back in later