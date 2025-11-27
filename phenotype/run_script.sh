#!/usr/bin/env bash
set -euo pipefail
Q_DIR=".."
WORK="."
source "${WORK}/.venv/Scripts/activate"

# convert redcap data to BIDS format
METADATA_CONFIG="${WORK}/phenotype_cfg.json"
REDCAP_DATA="${Q_DIR}/InvestigationOfTheLo_DATA_2025-10-07_1124.csv" \
REDCAP_DICTIONARY="${Q_DIR}/InvestigationOfTheLongtermAuto_DataDictionary_2025-10-24.csv"
BIDS_DIR="./test"

python -u "${WORK}/convert_phenotype_to_BIDS.py" \
  --data_csv $REDCAP_DATA \
  --dict_csv $REDCAP_DICTIONARY \
  --bids_cfg $METADATA_CONFIG \
  --out_dir $BIDS_DIR

# make figures
PHENOTYPE_DATA="${BIDS_DIR}/phenotype/covid_screen"
FIG_DIR="./fig"
PLOT_CONFIG="${WORK}/plot_cfg.json"

python -u "${WORK}/plot_phenotype.py" \
  --data_root $PHENOTYPE_DATA \
  --plot_cfg $PLOT_CONFIG \
  --out_dir $FIG_DIR

# perform calculations or make other adjustments to phenotype data
CALC_CONFIG="${WORK}/calc_cfg.json"
PHENOTYPE_DATA="${BIDS_DIR}/phenotype/"

python -u "${WORK}/calc_phenotype.py" \
  --data_root $PHENOTYPE_DATA \
  --calc_cfg $CALC_CONFIG \
  --overwrite False


# TO DO: address redundancies and inconsistencies between plot/calc functionality

# TO DO: add log levels back in