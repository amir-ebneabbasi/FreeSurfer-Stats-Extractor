# FreeSurfer Stats Extraction

This repository contains Python scripts for extracting and standardising regional brain measures from FreeSurfer outputs generated for UK Biobank participants. Each script processes a specific type of FreeSurfer statistics file, merges left and right hemisphere measurements when appropriate, computes bilateral averages, and exports one standardized CSV file per subject for downstream statistical analyses.

## Scripts

- **`extract_aparc.py`** – Parses FreeSurfer `lh.aparc.stats` and `rh.aparc.stats` files (Desikan–Killiany cortical atlas), computes bilateral averages for cortical metrics (e.g., cortical thickness, surface area, curvature, and gray matter volume), and exports one CSV file per subject.

- **`extract_hcp_log.py`** – Parses FreeSurfer `lh.HCP.fsaverage.aparc.log` and `rh.HCP.fsaverage.aparc.log` files (HCP-MMP1 cortical atlas), standardizes ROI names, computes bilateral averages for cortical metrics including cortical thickness (mean and SD), gray matter volume, surface area, vertex count, mean curvature, Gaussian curvature, folding index, and curvature index, and exports one CSV file per subject.

- **`extract_aseg.py`** – Parses FreeSurfer `aseg.stats` files, extracts subcortical structure volumes and global volumetric measures, averages homologous left and right structures into bilateral regions, removes redundant entries, and exports one standardized wide-format CSV file per subject.
