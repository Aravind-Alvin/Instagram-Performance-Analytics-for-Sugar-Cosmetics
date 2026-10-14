"""Data loading, cleaning and calculated fields for the Sugar Cosmetics dashboard.

Run directly to export a cleaned copy of the dataset:
    python data_prep.py
"""
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).parent
RAW_PATH = BASE_DIR / "data" / "sugar_cosmetics_instagram_data.xlsx"
CLEAN_PATH = BASE_DIR / "data" / "sugar_cosmetics_instagram_clean.csv"

NUMERIC_COLS = [
    "Impressions", "Reach", "Likes", "Comments", "Shares",
    "Saves", "Profile Visits", "Follows",
]
TEXT_COLS = ["Post Type", "Campaign Type", "Hashtags", "Audience Emotion", "Engagement Source"]


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Clean raw data and add calculated fields."""
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]

    # Stable post id = original row position (1-based) so labels survive sorting/filtering
    df["Post ID"] = range(1, len(df) + 1)

    # Types
    df["Post Date"] = pd.to_datetime(df["Post Date"], errors="coerce")
    for c in NUMERIC_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in TEXT_COLS:
        df[c] = df[c].astype(str).str.strip()

    # Quality rules: drop rows with missing keys, exact duplicates, impossible values
    df = df.dropna(subset=["Post Date", "Reach"] + NUMERIC_COLS)
    df = df.drop_duplicates(subset=[c for c in df.columns if c != "Post ID"])
    df = df[df["Reach"] > 0]
    df[NUMERIC_COLS] = df[NUMERIC_COLS].astype(int)

    # Calculated fields
    df["Total Engagement"] = df["Likes"] + df["Comments"] + df["Shares"] + df["Saves"]
    df["Engagement Rate"] = df["Total Engagement"] / df["Reach"] * 100  # % of reach
    df["Month"] = df["Post Date"].dt.to_period("M").dt.to_timestamp()
    df["Month Label"] = df["Month"].dt.strftime("%b %Y")
    df["Day Name"] = df["Post Date"].dt.day_name()
    df["Hashtag List"] = df["Hashtags"].str.split(r"\s*,\s*")
    df["Num Hashtags"] = df["Hashtag List"].str.len()
    df["Post Label"] = (
        df["Post Type"] + " | " + df["Campaign Type"] + " | "
        + df["Post Date"].dt.strftime("%d %b %y") + " | #" + df["Post ID"].astype(str)
    )
    return df.sort_values("Post Date").reset_index(drop=True)


def load_raw(path_or_buffer=RAW_PATH) -> pd.DataFrame:
    return pd.read_excel(path_or_buffer, sheet_name=0)


def load_clean(path_or_buffer=RAW_PATH) -> pd.DataFrame:
    return clean(load_raw(path_or_buffer))


if __name__ == "__main__":
    out = load_clean()
    out.drop(columns=["Hashtag List"]).to_csv(CLEAN_PATH, index=False)
    print(f"Saved {len(out):,} cleaned rows -> {CLEAN_PATH}")
