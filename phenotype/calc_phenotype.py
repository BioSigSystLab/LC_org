#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Performs specified calculations on phenotype data in BIDS format.
Author: Mary Miedema

Usage:
    python calc_phenotype.py --data_root <input> --calc_cfg <input.json> --overwrite <True>
"""
import argparse
import json
import pandas as pd
import logging
import sys
import os
import re
import warnings
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from textwrap import wrap

def rename_variables(p_df,p_info,calc_args):
    var_map = calc_args['VariableMap']
    for var_old in var_map.keys():
        var_new = var_map[var_old]
        if var_old in p_info:
            p_info[var_new] = p_info.pop(var_old)
            p_df = p_df.rename(columns={var_old: var_new})
        else:
            logging.warning(f"Variable not found and not renamed!: {var_old}.")
    # TO DO: check that this functions as expected for multiple replacements
    return p_df, p_info

def replace_levels(p_df,p_info,calc_args):
    levels = calc_args['LevelsToReplace']
    for level in levels.keys():
        new_val = levels[level]["ReplaceWith"]
        if new_val == 'NaN':
            new_val = np.nan
        variables = levels[level]["ReplaceInVariables"]
        p_df[variables] = p_df[variables].replace(level, new_val)
        # TO DO (IMPORTANT): update p_info
    return p_df, p_info

def derivative_differences(p_df,p_info,calc_args):
    # TO DO: check if difference has already been calculated and if that will throw errors
    # TO DO: allow specification of specific variables to difference
    if calc_args is None:
        all_var = p_info.keys()
        # find variables containing a common root + precovid/current
        possible_matches = []
        for s in all_var:
            if s.endswith("_precovid"):
                s_match = s.removesuffix("_precovid")+"_current"
                possible_matches.append(s_match)
        match_roots = [s.removesuffix("_current") for s in all_var if s in possible_matches]
        
        # now take the difference of levels between matched variables
        for match_root in match_roots:
            new_var = match_root + "_diff"
            pre_var = match_root + "_precovid"
            current_var = match_root + "_current"
            # add the difference to the dataframe as a new variable
            p_df[new_var] = p_df[current_var] - p_df[pre_var]
            
            # update the metadata accordingly
            desc_string = "Transformation of data using the following forumula: " + current_var + " - " + pre_var
            p_info[new_var] = {"Description": desc_string,
                               "Derivative": "true"
                               }
        
    return p_df, p_info

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def main():
    setup_logging()
    parser = argparse.ArgumentParser(description="Extract and convert REDCap demographics variables.")
    parser.add_argument("--data_root", type=str, required=True, help="Path to BIDS phenotype directory (no extension)")
    parser.add_argument("--calc_cfg", type=str, required=True, help="Configuration file for phenotype calculations")
    parser.add_argument("--overwrite", type=str, required=True, help="Whether to overwrite existing phenotype files or output new ones.")
    args = parser.parse_args()

    # TO DO: add support for overwrite options

    # read in configuration file
    calc_config_file = args.calc_cfg
    try:
        with open(calc_config_file, "r") as f:
            calc_config = json.load(f)
    except FileNotFoundError:
        logging.warning(f"File not found: {calc_config_file}.")

    # TO DO: check existence of phenotype data root directory
    p_root = args.data_root

    # look for phenotype files that have calculation functions listed
    phenotype_files = calc_config.keys()

    for phenotype_file in phenotype_files:

        # read in the relevant phenotype data file and its metadata        
        p_data_file = p_root+phenotype_file+".tsv"
        p_info_file = p_root+phenotype_file+".json"
        try:
            p_df = pd.read_csv(p_data_file, sep='\t')
        except FileNotFoundError:
            logging.warning(f"Phenotype data not found: {p_data_file}.")
        try:
            with open(p_info_file, "r") as f:
                p_info = json.load(f)
        except FileNotFoundError:
            logging.warning(f"Phenotype information not found: {p_info_file}.")

        logging.info(f"Beginning calculations using data from {p_data_file}!")

        # call calculation functions with their arguments
        calc_list = list(calc_config[phenotype_file].keys())
        glob = globals()
        for i, calc_name in enumerate(calc_list):
            calc_func = glob.get(calc_name, None)
            calc_args = calc_config[phenotype_file][calc_name]
            if calc_func is not None:
                p_df,p_info = calc_func(p_df,p_info,calc_args) 
                # function should modify phenotype file (?)
            else:
                print(f'function {calc_name} not found!')

        # save data as new files or overwrite the original files
        if args.overwrite == True:
            # write data file to phenotype directory within BIDS directory
            out_file = os.path.join(p_root,phenotype_file+".tsv")
            p_df.to_csv(out_file, sep='\t', index=False)
            # write metadata file as well
            out_file = os.path.join(p_root,phenotype_file+".json")
            with open(out_file, "w") as json_file:
                json.dump(p_info, json_file, indent=4, sort_keys=False)
        else:
                        # write data file to phenotype directory within BIDS directory
            out_file = os.path.join(p_root,phenotype_file+"_calc.tsv")
            p_df.to_csv(out_file, sep='\t', index=False)
            # write metadata file as well
            out_file = os.path.join(p_root,phenotype_file+"_calc.json")
            with open(out_file, "w") as json_file:
                json.dump(p_info, json_file, indent=4, sort_keys=False)
            # TO DO: check existing and append a suffix in case of multiple non-overwrites


if __name__ == "__main__":
    main()
