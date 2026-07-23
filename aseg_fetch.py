import os
import glob
import pandas as pd

base_dir = "/home/ae516/rds/rds-rb643-ukbiobank2/Data_Imaging"
out_dir = ""
os.makedirs(out_dir, exist_ok=True)

# -----------------------------------------------------
# STRUCTURE TABLE PARSER
# -----------------------------------------------------
def load_stats(f):
    cols, data = [], []

    with open(f) as fp:
        for l in fp:
            l = l.strip()

            if l.startswith("#") and "ColHeaders" in l:
                cols = l.split("ColHeaders")[1].split()

            elif cols and l and not l.startswith("#"):
                data.append(l.split())

    if not cols or not data:
        return None

    df = pd.DataFrame(data, columns=cols)
    df = df[["StructName", "Volume_mm3"]]
    df["Volume_mm3"] = pd.to_numeric(df["Volume_mm3"], errors="coerce")

    return df


# -----------------------------------------------------
# MEASURE BLOCK PARSER
# -----------------------------------------------------
def load_measures(f):
    measures = {}

    with open(f) as fp:
        for l in fp:
            if not l.startswith("# Measure"):
                continue

            parts = [x.strip() for x in l.split(",")]
            if len(parts) < 4:
                continue

            name = parts[1]
            value = float(parts[3])

            # ignore hemisphere-specific measures
            if name.startswith("lh") or name.startswith("rh"):
                continue

            measures[name] = value

    return measures


# -----------------------------------------------------
# CLEAN LEFT/RIGHT PREFIXES
# -----------------------------------------------------
def base_name(x):
    if x.startswith("Left-"):
        return x.replace("Left-", "")
    if x.startswith("Right-"):
        return x.replace("Right-", "")
    return x


# -----------------------------------------------------
# SUBJECT LOOP
# -----------------------------------------------------
for stats_dir in glob.glob(os.path.join(base_dir, "UKB*", "surfaces", "UKB*", "stats")):

    subject_id = os.path.basename(os.path.dirname(stats_dir))
    aseg_file = os.path.join(stats_dir, "aseg.stats")
    out_file = os.path.join(out_dir, f"{subject_id}_aseg.csv")

    if os.path.exists(out_file):
        print(f"skip {subject_id}")
        continue

    if not os.path.exists(aseg_file):
        print(f"missing {subject_id}")
        continue

    # -----------------------------------------------------
    # LOAD STRUCTURE TABLE
    # -----------------------------------------------------
    df = load_stats(aseg_file)

    if df is None:
        print(f"bad {subject_id}")
        continue

    # -----------------------------------------------------
    # REMOVE REDUNDANT WM HYPODENSITIES
    # -----------------------------------------------------
    df = df[~df["StructName"].isin([
        "Left-WM-hypointensities",
        "Right-WM-hypointensities",
        "Left-non-WM-hypointensities",
        "Right-non-WM-hypointensities"
    ])]

    # -----------------------------------------------------
    # CLEAN STRUCT NAMES
    # -----------------------------------------------------
    df["StructName"] = df["StructName"].apply(base_name)

    # -----------------------------------------------------
    # BILATERAL AVERAGING
    # -----------------------------------------------------
    df = df.groupby("StructName", as_index=False)["Volume_mm3"].mean()

    # -----------------------------------------------------
    # LOAD MEASURE BLOCK
    # -----------------------------------------------------
    measures = load_measures(aseg_file)
    meas_df = pd.DataFrame({
        "StructName": list(measures.keys()),
        "Volume_mm3": list(measures.values())
    })

    # -----------------------------------------------------
    # CAPTURE ORDER BEFORE CONCAT 
    # -----------------------------------------------------
    struct_cols = df["StructName"].tolist()
    meas_cols = meas_df["StructName"].tolist()

    # -----------------------------------------------------
    # CONCAT STRUCTURES + MEASURES 
    # -----------------------------------------------------
    df = pd.concat([df, meas_df], ignore_index=True)

    # -----------------------------------------------------
    # ADD SUBJECT ID
    # -----------------------------------------------------
    df["eid"] = subject_id

    # -----------------------------------------------------
    # PIVOT TO WIDE FORMAT
    # -----------------------------------------------------
    wide = df.pivot(
        index="eid",
        columns="StructName",
        values="Volume_mm3"
    ).reset_index()

    # -----------------------------------------------------
    # APPLY CLEAN ORDER
    # -----------------------------------------------------
    order = ["eid"] + struct_cols + meas_cols
    order = [c for c in order if c in wide.columns]

    wide = wide[order]

    # -----------------------------------------------------
    # SAVE OUTPUT
    # -----------------------------------------------------
    wide.to_csv(out_file, index=False)

    print(f"saved {subject_id}")

