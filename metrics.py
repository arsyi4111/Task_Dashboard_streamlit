import pandas as pd
import datetime

def load_performance_data(filepath="data/performance/performance_all.csv"):
    """Load the full performance dataset"""
    df = pd.read_csv(filepath)
    return df

def get_metrics(df):
    """Calculate YtD and MtD metrics from performance data"""
    today = datetime.date.today()
    current_month = today.month
    current_year = today.year

    # --- FY ---
    ytd = df
    ytd_total = ytd["Kinerja 2025"].sum()
    ytd_target = ytd["Target Tahun Ini"].sum()
    ytd_ach = ytd_total / ytd_target * 100 if ytd_target > 0 else 0

    # --- MtD ---
    mtd = df[df["bulan"] == current_month]
    mtd_total = mtd["Kinerja 2025"].sum()
    mtd_target = mtd["Target Tahun Ini"].sum()
    mtd_ach = mtd_total / mtd_target * 100 if mtd_target > 0 else 0

    return {
        "ytd_total": ytd_total,
        "ytd_target": ytd_target,
        "ytd_ach": ytd_ach,
        "mtd_total": mtd_total,
        "mtd_target": mtd_target,
        "mtd_ach": mtd_ach,
    }
