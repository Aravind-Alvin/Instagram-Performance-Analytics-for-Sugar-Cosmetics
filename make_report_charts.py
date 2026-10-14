"""Creates the chart images used in the business-insights report (same numbers as the dashboard)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import analytics as an
from data_prep import load_clean

PURPLE, CYAN, PINK, MAGENTA, VIOLET = "#5a3ea6", "#2fb8b8", "#e070d8", "#c2398f", "#9b5de5"
INK = "#3b1a5a"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": INK, "axes.labelcolor": INK, "xtick.color": INK,
                     "ytick.color": INK, "text.color": INK, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.dpi": 150, "savefig.bbox": "tight", "savefig.facecolor": "#f6e6f5"})
OUT = "report_assets/"
d = load_clean()


def fin(fig, name):
    fig.patch.set_facecolor("#f6e6f5")
    for ax in fig.axes:
        ax.set_facecolor("#f6e6f5")
    fig.savefig(OUT + name)
    plt.close(fig)


# 1 monthly posts
m = an.monthly_posts(d)
fig, ax = plt.subplots(figsize=(7.5, 3.2))
ax.plot(m["Month"], m["Posts"], color=PURPLE, lw=2.5, marker="o", mfc=MAGENTA, mec=MAGENTA)
for x, y in zip(m["Month"], m["Posts"]):
    ax.annotate(f"{y:,}", (x, y), textcoords="offset points", xytext=(0, 7), ha="center", fontsize=8)
ax.set_ylim(0, m["Posts"].max() * 1.2); ax.set_ylabel("Posts"); ax.set_title("Posts per month", fontweight="bold")
ax.set_xticks(m["Month"]); ax.set_xticklabels(m["Month"].dt.strftime("%b %y"), rotation=45)
fin(fig, "monthly.png")

# 2 top 10 likes / ER
for by, name, col in (("Likes", "top_likes.png", PURPLE), ("Engagement Rate", "top_er.png", MAGENTA)):
    t = an.top_posts(d, by).iloc[::-1]
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    ax.barh(t["Post Label"], t[by], color=col)
    for y, v in enumerate(t[by]):
        ax.text(v, y, f" {v:,.0f}" if by == "Likes" else f" {v:.1f}%", va="center", fontsize=8)
    ax.set_xlim(0, t[by].max() * 1.12); ax.tick_params(axis="y", labelsize=7.5)
    ax.set_title(f"Top 10 posts by {by.lower()}", fontweight="bold")
    fin(fig, name)

# 3 post type
p = an.post_type_perf(d)
fig, axes = plt.subplots(1, 3, figsize=(8, 3))
for ax, (c, n) in zip(axes, [("AvgLikes", "Avg likes"), ("AvgComments", "Avg comments"), ("AvgSaves", "Avg saves")]):
    ax.bar(p["Post Type"], p[c], color=[PURPLE, CYAN, PINK, MAGENTA])
    for x, v in zip(p["Post Type"], p[c]):
        ax.text(x, v, f"{v:,.0f}", ha="center", va="bottom", fontsize=8)
    ax.set_ylim(0, p[c].max() * 1.2); ax.set_title(n, fontsize=10, fontweight="bold"); ax.tick_params(axis="x", labelsize=8)
fig.tight_layout(); fin(fig, "post_type.png")

# 4 day of week
g = an.dow_perf(d)
fig, ax = plt.subplots(figsize=(7.5, 3.2))
best = g["AvgER"].idxmax()
ax.bar(g["Day Name"], g["AvgER"], color=[MAGENTA if i == best else PURPLE for i in g.index])
for x, v in zip(g["Day Name"], g["AvgER"]):
    ax.text(x, v, f"{v:.2f}%", ha="center", va="bottom", fontsize=8)
ax.set_ylim(0, g["AvgER"].max() * 1.2); ax.set_ylabel("Avg engagement rate (%)")
ax.set_title("Average engagement rate by weekday", fontweight="bold")
fin(fig, "dow.png")

# 5 funnel
f = an.funnel(d)
fig, ax = plt.subplots(figsize=(7.5, 3.4))
vals = f["Total"].tolist(); n = len(vals)
ax.barh(range(n)[::-1], vals, color=[PURPLE, VIOLET, MAGENTA, PINK, CYAN, "#d65db1"], height=0.75)
for i, (s, v, pct) in enumerate(zip(f["Stage"], vals, f["% of impressions"])):
    ax.text(v, n - 1 - i, f" {an.human(v)} ({pct:.1f}%)", va="center", fontsize=8)
ax.set_yticks(range(n)[::-1]); ax.set_yticklabels(f["Stage"]); ax.set_xlim(0, max(vals) * 1.3); ax.set_xticks([])
ax.set_title("Engagement funnel (% of impressions)", fontweight="bold")
fin(fig, "funnel.png")

# 6 hashtags
h = an.hashtag_perf(d).sort_values("AvgER", ascending=False)
fig, ax = plt.subplots(figsize=(7.5, 3.2))
ax.bar(h["Hashtag"], h["AvgER"], color=PURPLE)
for x, v in zip(h["Hashtag"], h["AvgER"]):
    ax.text(x, v, f"{v:.2f}%", ha="center", va="bottom", fontsize=8)
ax.set_ylim(0, h["AvgER"].max() * 1.2); ax.set_ylabel("Avg engagement rate (%)")
ax.set_title("Average engagement rate by hashtag", fontweight="bold")
fin(fig, "hashtag.png")

# 7 growth
gr = an.monthly_growth(d)
fig, ax = plt.subplots(figsize=(7.5, 3.2))
ax.bar(gr["Month"], gr["Follows"], width=20, color=PURPLE, label="New follows")
ax2 = ax.twinx(); ax2.plot(gr["Month"], gr["ProfileVisits"], color=MAGENTA, lw=2.5, marker="o", label="Profile visits")
ax.set_xticks(gr["Month"]); ax.set_xticklabels(gr["Month"].dt.strftime("%b %y"), rotation=45)
ax.set_ylabel("Follows"); ax2.set_ylabel("Profile visits"); ax2.spines["right"].set_visible(True)
ax.set_title("Follower-growth signals by month", fontweight="bold")
h1_, l1_ = ax.get_legend_handles_labels(); h2_, l2_ = ax2.get_legend_handles_labels()
ax.legend(h1_ + h2_, l1_ + l2_, loc="lower center", ncol=2, fontsize=8, frameon=False)
ax.set_ylim(0, gr["Follows"].max() * 1.25); ax2.set_ylim(0, gr["ProfileVisits"].max() * 1.25)
fin(fig, "growth.png")
print("charts done")
