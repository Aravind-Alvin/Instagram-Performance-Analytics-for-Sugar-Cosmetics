"""Pure-pandas aggregations used by both the Streamlit app and the report.
Keeping them separate from the UI makes every number easy to verify."""
import re

import pandas as pd

DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
FUNNEL_STAGES = ["Impressions", "Reach", "Likes", "Comments", "Shares", "Saves"]


def safe_div(a, b):
    return a / b if b else 0.0


def kpis(df: pd.DataFrame) -> dict:
    return {
        "posts": len(df),
        "likes": int(df["Likes"].sum()),
        "comments": int(df["Comments"].sum()),
        "shares": int(df["Shares"].sum()),
        "saves": int(df["Saves"].sum()),
        "reach": int(df["Reach"].sum()),
        "impressions": int(df["Impressions"].sum()),
        "profile_visits": int(df["Profile Visits"].sum()),
        "follows": int(df["Follows"].sum()),
        "avg_er": float(df["Engagement Rate"].mean()) if len(df) else 0.0,
        # weighted ER = all engagements / all reach (alternative definition)
        "weighted_er": safe_div(df["Total Engagement"].sum(), df["Reach"].sum()) * 100,
        "visit_rate": safe_div(df["Profile Visits"].sum(), df["Reach"].sum()) * 100,
        "follow_conv": safe_div(df["Follows"].sum(), df["Profile Visits"].sum()) * 100,
    }


def monthly_posts(df):
    return df.groupby("Month").size().rename("Posts").reset_index()


def monthly_growth(df):
    g = df.groupby("Month").agg(
        Posts=("Post ID", "size"), Follows=("Follows", "sum"),
        ProfileVisits=("Profile Visits", "sum"), Reach=("Reach", "sum"),
        ER=("Engagement Rate", "mean"),
    ).reset_index()
    return g


def top_posts(df, by="Likes", n=10):
    cols = ["Post ID", "Post Label", "Post Date", "Post Type", "Campaign Type", "Hashtags",
            "Reach", "Likes", "Comments", "Shares", "Saves", "Engagement Rate"]
    return df.nlargest(n, by)[cols].reset_index(drop=True)


def post_type_perf(df):
    return df.groupby("Post Type").agg(
        Posts=("Post ID", "size"), AvgLikes=("Likes", "mean"), AvgComments=("Comments", "mean"),
        AvgSaves=("Saves", "mean"), AvgShares=("Shares", "mean"), AvgER=("Engagement Rate", "mean"),
    ).reset_index()


def dow_perf(df):
    g = df.groupby("Day Name").agg(
        Posts=("Post ID", "size"), AvgER=("Engagement Rate", "mean"),
        AvgEngagement=("Total Engagement", "mean"),
    ).reindex(DAY_ORDER).reset_index()
    return g.dropna()


def funnel(df):
    vals = [int(df[s].sum()) for s in FUNNEL_STAGES]
    out = pd.DataFrame({"Stage": FUNNEL_STAGES, "Total": vals})
    out["% of previous"] = out["Total"] / out["Total"].shift(1) * 100
    out["% of impressions"] = out["Total"] / out["Total"].iloc[0] * 100 if vals[0] else 0
    return out


def tag_mask(df, tags):
    """Rows whose hashtag string contains ANY of the given tags (whole-tag match)."""
    if not tags:
        return pd.Series(True, index=df.index)
    pat = "|".join(r"(?:^|,\s*)" + re.escape(t) + r"(?:\s*,|$)" for t in tags)
    return df["Hashtags"].str.contains(pat, regex=True)


def explode_tags(df):
    return df.explode("Hashtag List").rename(columns={"Hashtag List": "Hashtag"})


def hashtag_perf(df):
    e = explode_tags(df)
    return e.groupby("Hashtag").agg(
        Posts=("Post ID", "size"), AvgER=("Engagement Rate", "mean"),
        AvgReach=("Reach", "mean"), AvgLikes=("Likes", "mean"),
    ).reset_index().sort_values("Posts", ascending=False)


def combo_perf(df, min_posts=100):
    g = df.groupby("Hashtags").agg(
        Posts=("Post ID", "size"), AvgER=("Engagement Rate", "mean"), AvgReach=("Reach", "mean"),
    ).reset_index()
    return g[g["Posts"] >= min_posts].sort_values("AvgER", ascending=False)


def category_perf(df, col):
    g = df.groupby(col).agg(
        Posts=("Post ID", "size"), AvgER=("Engagement Rate", "mean"),
        TotalEng=("Total Engagement", "sum"), Likes=("Likes", "sum"), Comments=("Comments", "sum"),
        Shares=("Shares", "sum"), Saves=("Saves", "sum"), Follows=("Follows", "sum"),
        Reach=("Reach", "sum"), AvgReach=("Reach", "mean"),
    ).reset_index()
    g["Follows per 1K reach"] = g["Follows"] / g["Reach"] * 1000
    return g


def human(n, decimals=1):
    """12345 -> 12.3K, 30_000_000 -> 30.0M, 1.2e9 -> 1.28bn"""
    n = float(n)
    for div, suf in ((1e9, "bn"), (1e6, "M"), (1e3, "K")):
        if abs(n) >= div:
            d = 2 if suf == "bn" else decimals
            return f"{n / div:.{d}f}{suf}"
    return f"{n:,.0f}"
