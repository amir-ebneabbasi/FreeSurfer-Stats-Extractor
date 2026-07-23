import os
import glob
import pandas as pd


base_dir = "/home/ae516/rds/rds-rb643-ukbiobank2/Data_Imaging"
out_dir = ""
os.makedirs(out_dir, exist_ok=True)


# -----------------------------------------------------
# PARSER
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

    for c in df.columns:
        if c != "StructName":
            df[c] = pd.to_numeric(df[c], errors="coerce")

    return df


# -----------------------------------------------------
# SUBJECT LOOP
# -----------------------------------------------------
for stats_dir in glob.glob(os.path.join(base_dir, "UKB*", "surfaces", "UKB*", "stats")):

    subject_id = os.path.basename(os.path.dirname(stats_dir))
    out_file = os.path.join(out_dir, f"{subject_id}_aparc.csv")

    if os.path.exists(out_file):
        print(f"skip {subject_id}")
        continue

    lh_file = os.path.join(stats_dir, "lh.aparc.stats")
    rh_file = os.path.join(stats_dir, "rh.aparc.stats")

    if not (os.path.exists(lh_file) and os.path.exists(rh_file)):
        print(f"missing {subject_id}")
        continue


    # -----------------------------------------------------
    # LOAD DATA
    # -----------------------------------------------------
    lh = load_stats(lh_file)
    rh = load_stats(rh_file)

    if lh is None or rh is None:
        print(f"bad {subject_id}")
        continue


    # -----------------------------------------------------
    # MERGE LH + RH
    # -----------------------------------------------------
    m = lh.merge(rh, on="StructName", suffixes=("_L", "_R"), how="outer")

    metrics = [c for c in lh.columns if c != "StructName"]


    # -----------------------------------------------------
    # AVERAGE LH + RH
    # -----------------------------------------------------
    avg = (m[[f"{c}_L" for c in metrics]].values +
           m[[f"{c}_R" for c in metrics]].values) / 2


    # -----------------------------------------------------
    # TRANSPOSE
    # -----------------------------------------------------
    out = pd.DataFrame(
        avg.T,
        index=metrics,
        columns=m["StructName"]
    )


    # -----------------------------------------------------
    # FINAL FORMAT
    # -----------------------------------------------------
    out = out.reset_index().rename(columns={"index": "metric"})
    out.insert(0, "eid", subject_id)


    # -----------------------------------------------------
    # SAVE
    # -----------------------------------------------------
    out.to_csv(out_file, index=False)

    print(f"saved {subject_id}")
