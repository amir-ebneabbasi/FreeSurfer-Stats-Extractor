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

    data = []

    start = False

    with open(f) as fp:

        for l in fp:

            l = l.strip()

            if not l:
                continue

            s = l.split()

            # -------------------------------------------------
            # START AFTER ??? LINE
            # -------------------------------------------------
            if s[-1] == "???":

                start = True
                continue

            # -------------------------------------------------
            # IGNORE EVERYTHING BEFORE TABLE
            # -------------------------------------------------
            if not start:
                continue

            data.append(s)

    if len(data) == 0:
        return None


    # -------------------------------------------------
    # MANUAL HEADERS
    # -------------------------------------------------
    cols = [
        "NumVert",
        "SurfArea",
        "GrayVol",
        "ThickAvg",
        "ThickStd",
        "MeanCurv",
        "GausCurv",
        "FoldInd",
        "CurvInd",
        "StructName"
    ]

    df = pd.DataFrame(data, columns=cols)


    # -------------------------------------------------
    # NUMERIC CONVERSION
    # -------------------------------------------------
    for c in cols[:-1]:

        df[c] = pd.to_numeric(
            df[c],
            errors="coerce"
        )

    return df


# -----------------------------------------------------
# SUBJECT LOOP
# -----------------------------------------------------
for stats_dir in glob.glob(
    os.path.join(
        base_dir,
        "UKB*",
        "surfaces",
        "UKB*",
        "stats"
    )
):

    subject_id = os.path.basename(
        os.path.dirname(stats_dir)
    )

    out_file = os.path.join(
        out_dir,
        f"{subject_id}_hcp.csv"
    )


    # -----------------------------------------------------
    # SKIP IF EXISTS
    # -----------------------------------------------------
    if os.path.exists(out_file):

        print(f"skip {subject_id}")
        continue


    # -----------------------------------------------------
    # FILES
    # -----------------------------------------------------
    lh_file = os.path.join(
        stats_dir,
        "lh.HCP.fsaverage.aparc.log"
    )

    rh_file = os.path.join(
        stats_dir,
        "rh.HCP.fsaverage.aparc.log"
    )


    # -----------------------------------------------------
    # CHECK FILES
    # -----------------------------------------------------
    if not (
        os.path.exists(lh_file)
        and
        os.path.exists(rh_file)
    ):

        print(f"missing {subject_id}")
        continue


    # -----------------------------------------------------
    # LOAD
    # -----------------------------------------------------
    lh = load_stats(lh_file)
    rh = load_stats(rh_file)

    if lh is None or rh is None:

        print(f"bad {subject_id}")
        continue


    # -----------------------------------------------------
    # CLEAN ROI NAMES
    # -----------------------------------------------------
    lh["StructName"] = (
        lh["StructName"]
        .str.replace(r"^L_", "", regex=True)
        .str.replace(r"_ROI$", "", regex=True)
    )

    rh["StructName"] = (
        rh["StructName"]
        .str.replace(r"^R_", "", regex=True)
        .str.replace(r"_ROI$", "", regex=True)
    )


    # -----------------------------------------------------
    # MERGE LH + RH
    # -----------------------------------------------------
    m = lh.merge(
        rh,
        on="StructName",
        suffixes=("_L", "_R"),
        how="inner"
    )


    # -----------------------------------------------------
    # METRICS
    # -----------------------------------------------------
    metrics = [c for c in lh.columns if c != "StructName"]

    # -----------------------------------------------------
    # LH/RH AVERAGE
    # -----------------------------------------------------
    avg = (
        m[[f"{c}_L" for c in metrics]].values
        +
        m[[f"{c}_R" for c in metrics]].values
    ) / 2


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
    out = out.reset_index()

    out = out.rename(
        columns={"index": "metric"}
    )

    out.insert(0, "eid", subject_id)


    # -----------------------------------------------------
    # SAVE
    # -----------------------------------------------------
    out.to_csv(
        out_file,
        index=False
    )

    print(f"saved {subject_id}")
