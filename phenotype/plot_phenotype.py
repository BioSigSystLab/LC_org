#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Plots phenotype data in BIDS format.
Author: Mary Miedema

Usage:
    python plot_phenotype.py --data_root <input> --out_dir </path/to/output_directory>
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

def load_phenotype(tsv_file_path):
    df = pd.read_csv(tsv_file_path, sep='\t')
    return df

def setup_dataframe(df,figure_params,p_groups=None):
    if p_groups is None:
        # separate into participants with different prefixes
        df.loc[df['participant_id'].str.contains('sub-0'), 'participant_id'] = 'controls'
        df.loc[df['participant_id'].str.contains('sub-1'), 'participant_id'] = 'controls'
        df.loc[df['participant_id'].str.contains('sub-2'), 'participant_id'] = 'patients'
    
    p_var = list(figure_params['Variables'].keys())
    null_scores = figure_params.get("LevelsToExclude")
    
    if null_scores is not None:
        df = df.replace(null_scores, np.nan)
    if p_var is None:
        # by default preserve all variables
        df_melted = pd.melt(df, id_vars=['participant_id'], var_name='Variable_Name', value_name='Score')
        return df_melted
    else:
        if 'participant_id' not in p_var:
            p_var.append('participant_id')
        cropped_df = df[p_var]
        df_melted = pd.melt(cropped_df, id_vars=['participant_id'], var_name='Variable_Name', value_name='Score')
        return df_melted
    
    
def plot_dataframe(df,figure_params,figure_path):
    vsize = len(list(figure_params['Variables'].keys())) + 1
    plt.figure(figsize=(10, vsize))
    ax =  sns.violinplot(data=df, x="Score", y="Variable_Name", hue="participant_id", split=True, orient='h', inner="quart",density_norm='count',saturation=0.65,legend=False)
    for collection in ax.collections:
        collection.set_alpha(0.4) # Set transparency to 50%
    for i, line in enumerate(ax.lines):
        if i % 3 == 1: # This is the median line (50th percentile)
            line.set_color('black')
            line.set_zorder(20)
            line.set_linewidth(1.5)
    warnings.filterwarnings("ignore", module='seaborn')
    #sns.swarmplot(data=df, x="Score", y="Variable_Name", hue="participant_id", dodge=True,size=4)
    ax = sns.stripplot(data=df, x="Score", y="Variable_Name", hue="participant_id", dodge=True, jitter=0,size=3)
    point_collections = ax.collections
    for dots in point_collections:
        offsets = dots.get_offsets()
        #x_coords = offsets[:, 0]
        #y_coords = offsets[:, 1]
        val = 0.1
        jittered_offsets = offsets + np.random.uniform(-val, val, offsets.shape)
        dots.set_offsets(jittered_offsets)
    # set up figure text
    wrapped_title = "\n".join(wrap(figure_params["PlotTitle"], width=100))
    #ax.set_yticklabels(new_labels) # TO DO: generate from cfg and json
    plt.title(wrapped_title)
    plt.xlabel(figure_params["PlotXLabel"])
    plt.ylabel("")
    plt.tight_layout() 
    plt.savefig(figure_path)

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
    parser.add_argument("--data_root", type=str, required=True, help="Path to BIDS phenotype root (no extension)")
    parser.add_argument("--plot_cfg", type=str, required=True, help="Configuration file for figures")
    parser.add_argument("--out_dir", type=str, required=True, help="Location of output figure directory")
    args = parser.parse_args()

    # read in the phenotype data file
    p_root = args.data_root
    p_data_file = p_root+".tsv"
    p_info_file = p_root+".json"
    try:
        p_df = load_phenotype(p_data_file)
    except FileNotFoundError:
        logging.warning(f"Phenotype data not found: {p_data_file}.")

    # read in the configuration file
    plot_config_file = args.plot_cfg
    try:
        with open(plot_config_file, "r") as f:
            plot_config = json.load(f)
    except FileNotFoundError:
        logging.warning(f"File not found: {plot_config_file}.")
    
    # entries correspond to separate figures
    figures = plot_config.keys()

    logging.info(f"Beginning creation of figures!")

    for figure in figures:

        figure_params = plot_config[figure]
        figure_path = args.out_dir + "/" + figure + ".png"

        figure_df = setup_dataframe(p_df,figure_params)

        plot_dataframe(figure_df,figure_params,figure_path)


        # to dos: add support for other plot types, including boxenplot


    logging.info(f"Created all figures in {args.out_dir}")

if __name__ == "__main__":
    main()
