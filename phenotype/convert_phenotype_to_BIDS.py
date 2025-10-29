#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extracts demographics variables from a REDCap CSV and converts responses based on definitions in the Demographics sheet of REDCap_variables_definitions.xlsx.
Authors: Sophia LoParco, Mary Miedema

Usage:
    python extract_demographics.py --data_csv <input.csv> --defs_xlsx <REDCap_variables_definitions.xlsx> --out_csv <output.csv>
"""
import argparse
import json
import pandas as pd
import logging
import sys
import os
import re

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def get_entry_cols(q_var,q_data,q_dict):
    # first get a list of the variables corresponding to that entry from q_dict
    dict_rows = q_dict[q_dict['Form Name'] == q_var]
    dict_vars = dict_rows['Variable / Field Name'].tolist()
    # next check which of those variables also exist as columns in q_dict
    data_cols = q_data.columns.tolist()
    q_cols = list(set(dict_vars) & set(data_cols))
    return q_cols

def write_entry(entry,e_cols,q_data,out_dir):
    e_data =  q_data[e_cols]

    # rename to participant_id
    e_data_renamed = e_data.rename(columns={'redcap_survey_identifier': 'participant_id'})

    # reject rows which are not affiliated with a subject number
    # also sort by subject number
    e_data_tidied = e_data_renamed.dropna(subset=['participant_id'])
    e_data_sorted = e_data_tidied.sort_values(by='participant_id')

    # add n/a for data which is not available
    e_data_filled = e_data_sorted.fillna('n/a')

    # write file to phenotype directory within BIDS directory
    out_file = os.path.join(out_dir,'phenotype',entry+".tsv")
    e_data_filled.to_csv(out_file, sep='\t', index=False)
    
def write_entry_metadata(entry,e_cols,q_dict,meta_config,out_dir):
    metadata = {
        "MeasurementToolMetadata": meta_config[entry]["MeasurementToolMetadata"]
    }

    # TO DO: check for calculated variables and add in Derivatives field

    for var in e_cols:
        if var == "redcap_survey_identifier":
            pass
        else:
            dict_row = q_dict.loc[q_dict['Variable / Field Name'] == var]
            
            # generate description for this variable
            desc_C = str(dict_row.iloc[0]['Section Header'])
            desc_E = str(dict_row.iloc[0]['Field Label'])
            desc_G = str(dict_row.iloc[0]['Field Note'])

            desc_list = [x for x in [desc_C, desc_E, desc_G] if str(x) != 'nan']
            dict_desc_raw = " ".join(filter(None, desc_list))

            # remove formatting information
            dict_desc = re.sub(r'<[^>]*>', '', dict_desc_raw)
            dict_desc = re.sub(r'\n', " ", dict_desc)
            dict_desc = re.sub(r'\u00a0', " ", dict_desc)            
            
            # check if there are levels in this variable
            levels_string = str(dict_row.iloc[0]['Choices, Calculations, OR Slider Labels'])
            if "|" in levels_string:
                delimiter = "|"
                levels_parts = levels_string.split(delimiter)
                levels_dict = {}
                for level_part in levels_parts:
                    delimiter = ","
                    level_split = level_part.split(delimiter, maxsplit=1)
                    # remove any leading/trailing spaces from key
                    level_split[0] = level_split[0].strip()
                    levels_dict[level_split[0]] = level_split[1]

                metadata_entry = {
                    "Description": dict_desc,
                    "Levels": levels_dict
                    }

            else:

                metadata_entry = {
                    "Description": dict_desc
                    }


            metadata[var] = metadata_entry
    out_file = os.path.join(out_dir,'phenotype',entry+".json")
    with open(out_file, "w") as json_file:
        json.dump(metadata, json_file, indent=4, sort_keys=False)
    return

def main():
    setup_logging()
    parser = argparse.ArgumentParser(description="Extract and convert REDCap demographics variables.")
    parser.add_argument("--data_csv", type=str, required=True, help="Path to REDCap CSV file")
    parser.add_argument("--dict_csv", type=str, required=True, help="Path to REDCap data dictionary")
    parser.add_argument("--bids_cfg", type=str, required=True, help="Path to configuration file for BIDS file organization and metadata definition")
    parser.add_argument("--out_dir", type=str, required=True, help="Location of study BIDS directory")
    args = parser.parse_args()

    # read in the configuration file
    meta_config_file = args.bids_cfg
    try:
        with open(meta_config_file, "r") as f:
            meta_config = json.load(f)
    except FileNotFoundError:
        logging.warning(f"File not found: {meta_config_file}.")
    
    # entries correspond to separate BIDS files
    bids_entries = meta_config.keys()

    # check for/load in data/dict files
    data_csv_file = args.data_csv
    try:
        q_data = pd.read_csv(data_csv_file, dtype=str)
    except FileNotFoundError:
        logging.warning(f"File not found: {data_csv_file}.")
    dict_csv_file = args.dict_csv
    try:
        q_dict = pd.read_csv(dict_csv_file, dtype=str)
    except FileNotFoundError:
        logging.warning(f"File not found: {dict_csv_file}.") 

    # TO DO: check if output directory exists
    # TO DO: add support for conditional overwrite 

    logging.info(f"Beginning conversion to BIDS!")

    for entry in bids_entries:

        e_handle = meta_config[entry]["DataDictionary_B"]

        if isinstance(e_handle, str):
            e_cols = get_entry_cols(q_var=e_handle,q_data=q_data,q_dict=q_dict)
        # otherwise will amalgamate several REDCap qs into one BIDS q
        elif isinstance(e_handle, list) and all(isinstance(item, str) for item in e_handle):
            e_cols = []
            for e_handle_i in e_handle:
                q_cols = get_entry_cols(q_var=e_handle_i,q_data=q_data,q_dict=q_dict)
                e_cols.extend(q_cols)
        else:
            logging.warning(f"'{e_handle}' is unexpected, check the BIDS configuration file.")
    
        # order the columns as they are found in the original csv
        original_cols = list(q_data.columns)
        e_cols_sorted = sorted(e_cols, key=lambda x: original_cols.index(x))

        # now add in the subject column
        e_cols_sorted.insert(0, "redcap_survey_identifier")

        # convert data
        write_entry(entry,e_cols_sorted,q_data,args.out_dir)

        # add appopriate metadata sidecars
        write_entry_metadata(entry,e_cols_sorted,q_dict,meta_config,args.out_dir)

    logging.info(f"Wrote all data to {args.out_dir}")

if __name__ == "__main__":
    main()
