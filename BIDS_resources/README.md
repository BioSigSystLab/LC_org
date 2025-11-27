# Getting started with this repository
This directory is a good place to centralize resources for converting various study-related data to the Brain Imaging Data Structure (BIDS) format. Scripts used in this conversion process should be gathered in top-level modality-specific directories (see the ../phenotype directory as an example).

# Getting started with BIDS
(to be added)

# Why are we using BIDS?
(to be added)

# Using BIDS with physiological data
Some specific principles for working with physiological data in BIDS format can be found [here](https://bids-specification.readthedocs.io/en/stable/modality-specific-files/physiological-recordings.html). In general, these data will be stored as .tsv files with accompanying .json files providing important metadata. You can find more general principles and options for working with .tsv files in the BIDS ecosystem [here](https://bids-specification.readthedocs.io/en/stable/common-principles.html#tabular-files).

For converting files to BIDS, a useful Python tool is [phys2bids](https://phys2bids.readthedocs.io/en/latest/), which can convert .acq files directly to the appropriate .tsv format. This tool also allows the user to set up a heuristic file to automatically populate the accompanying .json file. However, for our study, we propose to manually populate the .json file at scan time, starting from several pre-filled study templates. This will allow us to  adjusting these files with specific settings and observations which may differ from scan to scan. You can find the template .json files in this directory (file names to be added).

# Using BIDS with derivatives
