"""Instagram Performance Analytics for Sugar Cosmetics - Streamlit dashboard.

Run:  streamlit run app.py
"""
import inspect

import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

import analytics as an
from data_prep import RAW_PATH, load_clean

st.set_page_config(page_title="Instagram Analytics | Sugar Cosmetics", page_icon="💄", layout="wide")

# Newer Streamlit versions replace use_container_width with width="stretch"
STRETCH = {"width": "stretch"} if "width" in inspect.signature(st.plotly_chart).parameters else {"use_container_width": True}

# ----------------------------------------------------------------------------
# Theme (matches the Power BI reference: purple canvas, pink rounded cards)
# ----------------------------------------------------------------------------
PURPLE, CYAN, PINK, MAGENTA, VIOLET, LIGHT_PINK = "#5a3ea6", "#5fe0e0", "#e070d8", "#c2398f", "#9b5de5", "#ff8fd8"
INK, CARD = "#3b1a5a", "#e3b4e1"
SERIES = [PURPLE, CYAN, PINK, MAGENTA, VIOLET, LIGHT_PINK]
FONT = "Comic Neue, Comic Sans MS, Chalkboard SE, cursive"

st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Comic+Neue:wght@400;700&display=swap');
html, body, [class*="css"], .stApp {{ font-family: {FONT}; }}
.stApp {{ background: linear-gradient(135deg, #5a3a96 0%, #7a4ea6 55%, #5b3f9a 100%); }}
header[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding-top: 1.2rem; max-width: 1500px; }}
section[data-testid="stSidebar"] {{ background: #47296f; }}
/* pink rounded cards = bordered containers */
div[data-testid="stVerticalBlockBorderWrapper"] {{
    background: {CARD}; border: none !important; border-radius: 26px; padding: 0.4rem 0.6rem 0.2rem 0.6rem;
}}
.title-pill {{ background:{CARD}; color:{INK}; border-radius:40px; padding:12px 28px; text-align:center;
    font-weight:700; font-size:1.7rem; width:fit-content; margin:0 auto 18px auto; }}
.kpi {{ background:{CARD}; border-radius:28px; padding:18px 10px; text-align:center; height:130px; }}
.kpi .v {{ color:{INK}; font-size:2.4rem; font-weight:700; line-height:1.15; }}
.kpi .l {{ color:{INK}; font-size:1rem; font-weight:700; }}
.card-title {{ color:{INK}; font-weight:700; font-size:1.02rem; margin:6px 0 0 4px; }}
.card-sub {{ color:#6a3f8f; font-size:.8rem; margin:0 0 0 4px; }}
.note {{ background:rgba(255,255,255,.12); border-radius:16px; padding:10px 16px; font-size:.9rem; }}
button[data-baseweb="tab"] {{ font-weight:700; }}
h1,h2,h3 {{ font-family: {FONT}; }}
.insight {{ background:{CARD}; color:{INK}; border-radius:20px; padding:14px 20px; margin-bottom:10px; }}
.insight b {{ color:{MAGENTA}; }}
</style>
""",
    unsafe_allow_html=True,
)


# ----------------------------------------------------------------------------
# Data
# ----------------------------------------------------------------------------
@st.cache_data(show_spinner="Loading data...")
def get_data(src):
    return load_clean(src)


uploaded = st.sidebar.file_uploader("Use a different dataset (optional)", type=["xlsx"])
try:
    DF = get_data(uploaded if uploaded is not None else RAW_PATH)
except Exception as exc:  # noqa: BLE001
    st.error(f"Could not load data: {exc}. Place the Excel file in data/ or upload it in the sidebar.")
    st.stop()

# ----------------------------------------------------------------------------
# Sidebar filters  (empty selection = All)
# ----------------------------------------------------------------------------
st.session_state.setdefault("reset_n", 0)
R = st.session_state["reset_n"]

st.sidebar.markdown("## Filters")
month_opts = list(DF.drop_duplicates("Month").sort_values("Month")["Month Label"])
f_type = st.sidebar.multiselect("Post Type", sorted(DF["Post Type"].unique()), placeholder="All")
f_month = st.sidebar.multiselect("Month", month_opts, placeholder="All")
f_tag = st.sidebar.multiselect("Hashtag", sorted({t for l in DF["Hashtag List"] for t in l}), placeholder="All")
f_camp = st.sidebar.multiselect("Campaign Type", sorted(DF["Campaign Type"].unique()), placeholder="All")
f_src = st.sidebar.multiselect("Engagement Source", sorted(DF["Engagement Source"].unique()), placeholder="All")
f_emo = st.sidebar.multiselect("Audience Emotion", sorted(DF["Audience Emotion"].unique()), placeholder="All")

base = DF
if f_type: base = base[base["Post Type"].isin(f_type)]
if f_month: base = base[base["Month Label"].isin(f_month)]
if f_tag: base = base[an.tag_mask(base, f_tag)]
if f_camp: base = base[base["Campaign Type"].isin(f_camp)]
if f_src: base = base[base["Engagement Source"].isin(f_src)]
if f_emo: base = base[base["Audience Emotion"].isin(f_emo)]

# Chart-click cross filters (Dashboard tab): click a bar to filter every other chart
XF = {"x_type": "Post Type", "x_day": "Day Name", "x_tag": "Hashtag"}


def apply_cross(df, exclude=()):
    for key, col in XF.items():
        sel = st.session_state.get(key)
        if not sel or key in exclude:
            continue
        df = df[an.tag_mask(df, sel)] if key == "x_tag" else df[df[col].isin(sel)]
    return df


df = apply_cross(base)

active = {k: st.session_state.get(k) for k in XF if st.session_state.get(k)}
if active:
    st.sidebar.markdown("**Chart selections**")
    for k, v in active.items():
        st.sidebar.caption(f"{XF[k]}: {', '.join(map(str, v))}")
if st.sidebar.button("Clear chart selections", disabled=not active):
    for k in XF:
        st.session_state[k] = []
        st.session_state.pop(f"_sig_{k}", None)
    st.session_state["reset_n"] += 1
    st.rerun()

st.sidebar.divider()
st.sidebar.metric("Posts in view", f"{len(df):,}")
st.sidebar.download_button("Download filtered data (CSV)",
                           df.drop(columns=["Hashtag List"]).to_csv(index=False).encode(),
                           "filtered_posts.csv", "text/csv")

if df.empty:
    st.markdown('<div class="title-pill">Instagram Performance Analytics for Sugar Cosmetics</div>', unsafe_allow_html=True)
    st.warning("No posts match the current filters. Adjust or clear the filters.")
    st.stop()


# ----------------------------------------------------------------------------
# UI helpers
# ----------------------------------------------------------------------------
def style(fig, h=300, legend=True):
    fig.update_layout(
        height=h, margin=dict(l=8, r=8, t=24, b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color=INK, size=12), showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0),
    )
    fig.update_xaxes(gridcolor="rgba(59,26,90,.12)", zeroline=False)
    fig.update_yaxes(gridcolor="rgba(59,26,90,.15)", zeroline=False)
    return fig


def show(fig, key):
    st.plotly_chart(fig, key=f"{key}_{R}", config={"displayModeBar": False}, **STRETCH)


def click_chart(fig, key, state_key):
    """Render a chart whose bars act as filters for the whole dashboard."""
    event = st.plotly_chart(fig, key=f"{key}_{R}", on_select="rerun", selection_mode="points",
                            config={"displayModeBar": False}, **STRETCH)
    try:
        pts = event["selection"]["points"]
    except Exception:  # noqa: BLE001
        pts = []
    sig = f"_sig_{state_key}"
    if pts:
        vals = sorted({str(p["x"]) for p in pts if p.get("x") is not None})
        st.session_state[sig] = vals
        if st.session_state.get(state_key) != vals:
            st.session_state[state_key] = vals
            st.rerun()
    elif st.session_state.get(sig):  # bar was un-selected
        st.session_state[sig] = []
        st.session_state[state_key] = []
        st.rerun()


def title(text, sub=None):
    st.markdown(f'<div class="card-title">{text}</div>', unsafe_allow_html=True)
    if sub:
        st.markdown(f'<div class="card-sub">{sub}</div>', unsafe_allow_html=True)


def kpi(value, label):
    return f'<div class="kpi"><div class="v">{value}</div><div class="l">{label}</div></div>'


def table_fig(frame, fmt=None, h=360, widths=None):
    fmt = fmt or {}
    cols = list(frame.columns)
    cells = [[(fmt[c](v) if c in fmt else v) for v in frame[c]] for c in cols]
    fig = go.Figure(go.Table(
        columnwidth=widths,
        header=dict(values=[f"<b>{c}</b>" for c in cols], fill_color=PURPLE, font=dict(color="white", size=12, family=FONT),
                    align="left", height=30),
        cells=dict(values=cells, fill_color="white", font=dict(color=INK, size=12, family=FONT), align="left", height=26),
    ))
    fig.update_layout(height=h, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)")
    return fig


def sel_colors(cats, state_key, default=PURPLE, hl=MAGENTA):
    sel = st.session_state.get(state_key) or []
    return [hl if c in sel else default for c in cats] if sel else [default] * len(cats)


# ----------------------------------------------------------------------------
# Chart builders (each returns a Plotly figure)
# ----------------------------------------------------------------------------
def fig_monthly(d, h=300):
    m = an.monthly_posts(d)
    fig = go.Figure(go.Scatter(x=m["Month"], y=m["Posts"], mode="lines+markers+text", text=[f"{v:,}" for v in m["Posts"]],
                               textposition="top center", line=dict(color=PURPLE, width=3), marker=dict(size=8, color=MAGENTA),
                               hovertemplate="%{x|%b %Y}: %{y:,} posts<extra></extra>"))
    fig.update_xaxes(tickformat="%b %y", dtick="M1" if len(m) <= 14 else "M2")
    fig.update_yaxes(rangemode="tozero", title="Posts")
    return style(fig, h, legend=False)


def fig_post_type(d, h=300, selectable=False):
    p = an.post_type_perf(d)
    metrics = [("AvgLikes", "Avg Likes"), ("AvgComments", "Avg Comments"), ("AvgSaves", "Avg Saves")]
    fig = make_subplots(rows=1, cols=3, subplot_titles=[m[1] for m in metrics], horizontal_spacing=0.08)
    cols = sel_colors(list(p["Post Type"]), "x_type") if selectable else [PURPLE, CYAN, PINK, MAGENTA]
    for i, (c, name) in enumerate(metrics, start=1):
        fig.add_trace(go.Bar(x=p["Post Type"], y=p[c], marker_color=cols, text=p[c].round(0).astype(int).map("{:,}".format),
                             textposition="outside", name=name, showlegend=False,
                             hovertemplate="%{x}: %{y:,.1f}<extra>" + name + "</extra>"), row=1, col=i)
        fig.update_yaxes(range=[0, p[c].max() * 1.25], row=1, col=i)
    fig.update_annotations(font=dict(color=INK, size=12, family=FONT))
    return style(fig, h, legend=False)


def fig_post_type_er(d, h=300):
    p = an.post_type_perf(d)
    fig = go.Figure(go.Bar(x=p["Post Type"], y=p["AvgER"], marker_color=SERIES[: len(p)],
                           text=p["AvgER"].map("{:.2f}%".format), textposition="outside"))
    fig.update_yaxes(range=[0, p["AvgER"].max() * 1.25], title="Avg engagement rate (%)")
    return style(fig, h, legend=False)


def fig_dow(d, metric="AvgER", h=300, selectable=False):
    g = an.dow_perf(d)
    best = g[metric].idxmax()
    cols = sel_colors(list(g["Day Name"]), "x_day") if selectable and st.session_state.get("x_day") else \
        [MAGENTA if i == best else PURPLE for i in g.index]
    txt = g[metric].map("{:.2f}%".format) if metric == "AvgER" else g[metric].map("{:,.0f}".format)
    fig = go.Figure(go.Bar(x=g["Day Name"], y=g[metric], marker_color=cols, text=txt, textposition="outside",
                           hovertemplate="%{x}: %{y:,.2f}<extra></extra>"))
    fig.update_xaxes(categoryorder="array", categoryarray=an.DAY_ORDER, tickangle=-30)
    fig.update_yaxes(range=[0, g[metric].max() * 1.2], title="Avg engagement rate (%)" if metric == "AvgER" else "Avg engagements / post")
    return style(fig, h, legend=False)


def fig_funnel(d, h=340):
    f = an.funnel(d)
    fig = go.Figure(go.Funnel(y=f["Stage"], x=f["Total"], textinfo="value+percent initial",
                              marker=dict(color=[PURPLE, VIOLET, MAGENTA, PINK, "#2aa6a6", "#d65db1"]),
                              textfont=dict(color="white")))
    return style(fig, h, legend=False)


def fig_campaign_donut(d, h=300):
    c = an.category_perf(d, "Campaign Type")
    fig = go.Figure(go.Pie(labels=c["Campaign Type"], values=c["TotalEng"], hole=0.55, marker=dict(colors=SERIES),
                           textinfo="percent", hovertemplate="%{label}: %{value:,} engagements<extra></extra>"))
    fig.update_layout(legend=dict(orientation="v", x=1.0))
    return style(fig, h)


def fig_hashtag(d, metric="AvgER", h=300, selectable=False, kind="bar"):
    t = an.hashtag_perf(d).sort_values(metric, ascending=False)
    label = {"AvgER": "Avg engagement rate (%)", "AvgReach": "Avg reach", "Posts": "Posts using tag", "AvgLikes": "Avg likes"}[metric]
    if kind == "pie":
        return style(go.Figure(go.Pie(labels=t["Hashtag"], values=t[metric], hole=0.4, marker=dict(colors=SERIES))), h)
    cols = sel_colors(list(t["Hashtag"]), "x_tag") if selectable else [PURPLE] * len(t)
    txt = t[metric].map("{:.2f}".format) if metric == "AvgER" else t[metric].map("{:,.0f}".format)
    fig = go.Figure(go.Bar(x=t["Hashtag"], y=t[metric], marker_color=cols, text=txt, textposition="outside"))
    fig.update_yaxes(range=[0, t[metric].max() * 1.2], title=label)
    fig.update_xaxes(tickangle=-25)
    return style(fig, h, legend=False)


def fig_top(d, by, h=330):
    t = an.top_posts(d, by).iloc[::-1]
    is_er = by == "Engagement Rate"
    fig = go.Figure(go.Bar(y=t["Post Label"], x=t[by], orientation="h", marker_color=MAGENTA if is_er else PURPLE,
                           text=t[by].map("{:.1f}%".format if is_er else "{:,.0f}".format), textposition="inside",
                           textfont=dict(color="white"), hovertemplate="%{y}<br>%{x:,.2f}<extra></extra>"))
    fig.update_yaxes(tickfont=dict(size=10))
    return style(fig, h, legend=False).update_layout(margin=dict(l=8, r=8, t=8, b=8))


def fig_source_type(d, h=300):
    g = d.groupby(["Post Type", "Engagement Source"])["Total Engagement"].sum().reset_index()
    fig = go.Figure()
    for i, s in enumerate(sorted(g["Engagement Source"].unique())):
        x = g[g["Engagement Source"] == s]
        fig.add_trace(go.Bar(y=x["Post Type"], x=x["Total Engagement"], name=s, orientation="h", marker_color=SERIES[i % 6]))
    fig.update_layout(barmode="stack")
    return style(fig, h)


def fig_emotion(d, h=300):
    c = an.category_perf(d, "Audience Emotion")
    fig = go.Figure()
    for i, k in enumerate(["Likes", "Comments", "Shares", "Saves"]):
        fig.add_trace(go.Bar(x=c["Audience Emotion"], y=c[k], name=k, marker_color=SERIES[i]))
    fig.update_layout(barmode="relative", barnorm="percent")
    fig.update_yaxes(title="% of engagements")
    return style(fig, h)


def fig_growth(d, h=300):
    g = an.monthly_growth(d)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=g["Month"], y=g["Follows"], name="New follows", marker_color=PURPLE), secondary_y=False)
    fig.add_trace(go.Scatter(x=g["Month"], y=g["ProfileVisits"], name="Profile visits", mode="lines+markers",
                             line=dict(color=MAGENTA, width=3)), secondary_y=True)
    fig.update_xaxes(tickformat="%b %y")
    fig.update_yaxes(title_text="Follows", secondary_y=False, rangemode="tozero")
    fig.update_yaxes(title_text="Profile visits", secondary_y=True, rangemode="tozero", showgrid=False)
    return style(fig, h)


def fig_er_trend(d, h=300):
    g = an.monthly_growth(d)
    fig = go.Figure(go.Scatter(x=g["Month"], y=g["ER"], mode="lines+markers", line=dict(color=PURPLE, width=3),
                               marker=dict(color=MAGENTA, size=8)))
    fig.update_xaxes(tickformat="%b %y")
    fig.update_yaxes(range=[0, g["ER"].max() * 1.3], title="Avg engagement rate (%)")
    return style(fig, h, legend=False)


def fig_category_er(d, col, h=280):
    c = an.category_perf(d, col).sort_values("AvgER", ascending=False)
    fig = go.Figure(go.Bar(x=c[col], y=c["AvgER"], marker_color=SERIES[: len(c)], text=c["AvgER"].map("{:.2f}%".format),
                           textposition="outside"))
    fig.update_yaxes(range=[0, c["AvgER"].max() * 1.25], title="Avg ER (%)")
    return style(fig, h, legend=False)


# ----------------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------------
st.markdown('<div class="title-pill">Instagram Performance Analytics for Sugar Cosmetics</div>', unsafe_allow_html=True)

K = an.kpis(df)
TABS = ["Dashboard", "KPI Overview", "Monthly Posting Trend", "Top 10 by Likes", "Top 10 by Engagement Rate",
        "Post Type Performance", "Day of Week", "Engagement Funnel", "Hashtag Analysis", "Audience & Growth",
        "Insights & Strategy"]
tabs = st.tabs(TABS)

# ============================== DASHBOARD ====================================
with tabs[0]:
    cols = st.columns(6)
    for c, (v, l) in zip(cols, [(f"{K['posts']:,}", "Total Posts"), (an.human(K["likes"]), "Total Likes"),
                                (an.human(K["comments"]), "Total Comments"), (an.human(K["reach"]), "Total Reach"),
                                (an.human(K["impressions"]), "Total Impressions"), (f"{K['avg_er']:.1f}%", "Avg Engagement Rate")]):
        c.markdown(kpi(v, l), unsafe_allow_html=True)
    st.caption("Tip: click a bar in **Post Type**, **Day of Week** or **Hashtag** charts to cross-filter the whole dashboard. "
               "Click it again, or use *Clear chart selections* in the sidebar, to reset.")

    c1, c2, c3 = st.columns([1.1, 1.3, 1])
    with c1, st.container(border=True):
        title("Monthly Posting Trend", "Posts per month")
        show(fig_monthly(df), "d_monthly")
    with c2, st.container(border=True):
        title("Post Type Performance", "Average likes, comments and saves per post - click a bar to filter")
        click_chart(fig_post_type(apply_cross(base, ("x_type",)), selectable=True), "d_ptype", "x_type")
    with c3, st.container(border=True):
        title("Engagement Funnel", "Impressions to saves (all posts in view)")
        show(fig_funnel(df), "d_funnel")

    c1, c2, c3 = st.columns([1, 1, 1.1])
    with c1, st.container(border=True):
        title("Avg Engagement Rate by Day of Week", "Best day highlighted - click to filter")
        click_chart(fig_dow(apply_cross(base, ("x_day",)), selectable=True), "d_dow", "x_day")
    with c2, st.container(border=True):
        title("Total Engagements by Campaign Type")
        show(fig_campaign_donut(df), "d_camp")
    with c3, st.container(border=True):
        title("Hashtag Performance", "Avg engagement rate per hashtag - click to filter")
        click_chart(fig_hashtag(apply_cross(base, ("x_tag",)), selectable=True), "d_tag", "x_tag")

    c1, c2 = st.columns(2)
    with c1, st.container(border=True):
        title("Top 10 Posts by Likes")
        show(fig_top(df, "Likes"), "d_toplikes")
    with c2, st.container(border=True):
        title("Top 10 Posts by Engagement Rate")
        show(fig_top(df, "Engagement Rate"), "d_toper")

    c1, c2, c3 = st.columns(3)
    with c1, st.container(border=True):
        title("Engagements by Post Type and Source")
        show(fig_source_type(df), "d_srctype")
    with c2, st.container(border=True):
        title("Engagement Mix by Audience Emotion", "Share of likes / comments / shares / saves")
        show(fig_emotion(df), "d_emotion")
    with c3, st.container(border=True):
        title("Follower Growth Signals", "New follows vs profile visits per month")
        show(fig_growth(df), "d_growth")

# ============================== TASK 1: KPI ==================================
with tabs[1]:
    st.subheader("KPI Overview - how is the account performing overall?")
    r1 = st.columns(5)
    for c, (v, l) in zip(r1, [(f"{K['posts']:,}", "Total Posts"), (f"{K['likes']:,}", "Total Likes"),
                              (f"{K['comments']:,}", "Total Comments"), (f"{K['reach']:,}", "Total Reach"),
                              (f"{K['avg_er']:.2f}%", "Avg Engagement Rate")]):
        c.markdown(kpi(v, l), unsafe_allow_html=True)
    st.write("")
    r2 = st.columns(5)
    for c, (v, l) in zip(r2, [(an.human(K["impressions"]), "Total Impressions"), (an.human(K["shares"]), "Total Shares"),
                              (an.human(K["saves"]), "Total Saves"), (an.human(K["profile_visits"]), "Profile Visits"),
                              (an.human(K["follows"]), "New Follows")]):
        c.markdown(kpi(v, l), unsafe_allow_html=True)
    st.write("")
    r3 = st.columns(3)
    for c, (v, l) in zip(r3, [(f"{K['weighted_er']:.2f}%", "Weighted ER (total engagement / total reach)"),
                              (f"{K['visit_rate']:.2f}%", "Profile visits per reach"),
                              (f"{K['follow_conv']:.1f}%", "Follows per profile visit")]):
        c.markdown(kpi(v, l), unsafe_allow_html=True)
    st.markdown('<div class="note"><b>Definitions</b> - Engagement = Likes + Comments + Shares + Saves. '
                'Engagement Rate (per post) = Engagement / Reach x 100; the headline figure is the average across posts.</div>',
                unsafe_allow_html=True)

# ============================== TASK 2: MONTHLY ==============================
with tabs[2]:
    st.subheader("Monthly Posting Trend")
    with st.container(border=True):
        show(fig_monthly(df, 420), "t_monthly")
    st.markdown('<div class="note">Apr 2024 (starts 19 Apr) and Apr 2025 (ends 19 Apr) are partial months, '
                'so their lower counts reflect data coverage, not a drop in activity.</div>', unsafe_allow_html=True)

# ============================== TASK 3: TOP LIKES ============================
with tabs[3]:
    st.subheader("Top 10 Posts by Likes")
    with st.container(border=True):
        show(fig_top(df, "Likes", 400), "t_toplikes")
    with st.container(border=True):
        t = an.top_posts(df, "Likes")[["Post Label", "Hashtags", "Reach", "Likes", "Comments", "Shares", "Saves", "Engagement Rate"]]
        show(table_fig(t, {"Reach": "{:,}".format, "Likes": "{:,}".format, "Comments": "{:,}".format, "Shares": "{:,}".format,
                           "Saves": "{:,}".format, "Engagement Rate": "{:.1f}%".format}, 340, [3, 3, 1, 1, 1, 1, 1, 1.2]), "t_toplikes_tbl")
    st.caption("The dataset has no caption column, so each post is identified by format | campaign | date | post ID.")

# ============================== TASK 4: TOP ER ===============================
with tabs[4]:
    st.subheader("Top 10 Posts by Engagement Rate")
    min_reach = st.slider("Minimum reach (filters out tiny-audience posts)", 0, 20000, 0, 500)
    dr = df[df["Reach"] >= min_reach]
    if dr.empty:
        st.warning("No posts meet the minimum reach.")
    else:
        with st.container(border=True):
            show(fig_top(dr, "Engagement Rate", 400), "t_toper")
        with st.container(border=True):
            t = an.top_posts(dr, "Engagement Rate")[["Post Label", "Hashtags", "Reach", "Likes", "Comments", "Shares", "Saves", "Engagement Rate"]]
            show(table_fig(t, {"Reach": "{:,}".format, "Likes": "{:,}".format, "Comments": "{:,}".format, "Shares": "{:,}".format,
                               "Saves": "{:,}".format, "Engagement Rate": "{:.1f}%".format}, 340, [3, 3, 1, 1, 1, 1, 1, 1.2]), "t_toper_tbl")
        st.caption("'Hidden gems' = high engagement relative to reach. Compare with the likes ranking: the two lists barely overlap.")

# ============================== TASK 5: POST TYPE ============================
with tabs[5]:
    st.subheader("Post Type Performance Comparison")
    c1, c2 = st.columns(2)
    with c1, st.container(border=True):
        title("Average likes, comments and saves per post")
        show(fig_post_type(df, 360), "t_ptype")
    with c2, st.container(border=True):
        title("Average engagement rate by post type")
        show(fig_post_type_er(df, 360), "t_ptype_er")
    p = an.post_type_perf(df).rename(columns={"AvgLikes": "Avg Likes", "AvgComments": "Avg Comments", "AvgSaves": "Avg Saves",
                                              "AvgShares": "Avg Shares", "AvgER": "Avg ER (%)"})
    with st.container(border=True):
        show(table_fig(p, {"Posts": "{:,}".format, "Avg Likes": "{:,.1f}".format, "Avg Comments": "{:,.1f}".format,
                           "Avg Saves": "{:,.1f}".format, "Avg Shares": "{:,.1f}".format, "Avg ER (%)": "{:.2f}".format}, 200), "t_ptype_tbl")
    st.caption("This dataset contains Image, Reel, Story and Video posts (no Carousel).")

# ============================== TASK 6: DAY OF WEEK ==========================
with tabs[6]:
    st.subheader("Day of Week Analysis")
    m = st.radio("Metric", ["Avg engagement rate", "Avg engagements per post"], horizontal=True)
    metric = "AvgER" if m.startswith("Avg engagement rate") else "AvgEngagement"
    with st.container(border=True):
        show(fig_dow(df, metric, 420), "t_dow")
    g = an.dow_perf(df)
    with st.container(border=True):
        show(table_fig(g.rename(columns={"Day Name": "Day", "AvgER": "Avg ER (%)", "AvgEngagement": "Avg engagements"}),
                       {"Posts": "{:,}".format, "Avg ER (%)": "{:.2f}".format, "Avg engagements": "{:,.0f}".format}, 290), "t_dow_tbl")

# ============================== TASK 7: FUNNEL ===============================
with tabs[7]:
    st.subheader("Engagement Funnel")
    c1, c2 = st.columns([1.2, 1])
    with c1, st.container(border=True):
        show(fig_funnel(df, 430), "t_funnel")
    with c2, st.container(border=True):
        f = an.funnel(df)
        show(table_fig(f, {"Total": "{:,}".format, "% of previous": lambda v: "-" if v != v else f"{v:.1f}%",
                           "% of impressions": "{:.2f}%".format}, 240), "t_funnel_tbl")
    st.markdown('<div class="note">Likes, comments, shares and saves are parallel actions rather than strict sequential steps, '
                'so "% of previous" after Reach is a comparison, not a drop-off (saves can exceed shares). '
                '"% of impressions" is the cleanest read.</div>', unsafe_allow_html=True)

# ============================== TASK 8: HASHTAGS =============================
with tabs[8]:
    st.subheader("Hashtag Analysis")
    metric_lbl = st.selectbox("Metric", ["Avg engagement rate", "Avg reach", "Posts using hashtag", "Avg likes"])
    metric = {"Avg engagement rate": "AvgER", "Avg reach": "AvgReach", "Posts using hashtag": "Posts", "Avg likes": "AvgLikes"}[metric_lbl]
    c1, c2 = st.columns(2)
    with c1, st.container(border=True):
        title(f"{metric_lbl} by hashtag")
        show(fig_hashtag(df, metric, 360), "t_tag_bar")
    with c2, st.container(border=True):
        title(f"Share of {metric_lbl.lower()}")
        show(fig_hashtag(df, metric, 360, kind="pie"), "t_tag_pie")
    min_posts = st.slider("Minimum posts per hashtag combination", 20, 400, 100, 10)
    combos = an.combo_perf(df, min_posts)
    with st.container(border=True):
        title("Hashtag combinations ranked by avg engagement rate")
        if combos.empty:
            st.info("No combinations meet that minimum.")
        else:
            show(table_fig(combos.head(12).rename(columns={"AvgER": "Avg ER (%)", "AvgReach": "Avg reach"}),
                           {"Posts": "{:,}".format, "Avg ER (%)": "{:.2f}".format, "Avg reach": "{:,.0f}".format}, 400, [4, 1, 1, 1]),
                 "t_combo_tbl")
    st.caption("Small gaps between combinations are within normal variation - treat them as hypotheses to A/B test, not proven winners.")

# ============================== AUDIENCE & GROWTH ============================
with tabs[9]:
    st.subheader("Audience & Growth")
    c1, c2 = st.columns(2)
    with c1, st.container(border=True):
        title("Follows vs profile visits by month")
        show(fig_growth(df, 340), "t_growth")
    with c2, st.container(border=True):
        title("Average engagement rate by month")
        show(fig_er_trend(df, 340), "t_ertrend")
    dim = st.selectbox("Compare engagement rate by", ["Campaign Type", "Audience Emotion", "Engagement Source", "Post Type"])
    c1, c2 = st.columns([1.2, 1])
    with c1, st.container(border=True):
        show(fig_category_er(df, dim, 330), "t_catER")
    with c2, st.container(border=True):
        cp = an.category_perf(df, dim)[[dim, "Posts", "AvgER", "Follows per 1K reach"]].rename(columns={"AvgER": "Avg ER (%)"})
        show(table_fig(cp, {"Posts": "{:,}".format, "Avg ER (%)": "{:.2f}".format, "Follows per 1K reach": "{:.2f}".format}, 250), "t_cat_tbl")

# ============================== INSIGHTS =====================================
with tabs[10]:
    st.subheader("Insights & Strategy (updates with the filters)")
    pt, dw, hp = an.post_type_perf(df), an.dow_perf(df), an.hashtag_perf(df)
    bt, wt = pt.loc[pt["AvgER"].idxmax()], pt.loc[pt["AvgER"].idxmin()]
    bd, wd = dw.loc[dw["AvgER"].idxmax()], dw.loc[dw["AvgER"].idxmin()]
    bh = hp.loc[hp["AvgER"].idxmax()]
    spread_pt = (bt["AvgER"] / wt["AvgER"] - 1) * 100
    spread_dw = (bd["AvgER"] / wd["AvgER"] - 1) * 100

    items = [
        f"<b>Overall:</b> {K['posts']:,} posts reached {an.human(K['reach'])} accounts and earned {an.human(K['likes'])} likes "
        f"at an average engagement rate of {K['avg_er']:.1f}%. Likes make up roughly {K['likes'] / (K['likes'] + K['comments'] + K['shares'] + K['saves']) * 100:.0f}% of all engagement.",
        f"<b>Format:</b> {bt['Post Type']} has the highest engagement rate ({bt['AvgER']:.2f}%) and {wt['Post Type']} the lowest "
        f"({wt['AvgER']:.2f}%) - a gap of only {spread_pt:.1f}%. Format alone is not a strong lever in this data.",
        f"<b>Timing:</b> {bd['Day Name']} performs best ({bd['AvgER']:.2f}%) and {wd['Day Name']} weakest ({wd['AvgER']:.2f}%), "
        f"a {spread_dw:.1f}% gap - posting day is a minor lever too.",
        f"<b>Hashtags:</b> {bh['Hashtag']} leads on engagement rate ({bh['AvgER']:.2f}%), but all single hashtags sit within a very narrow band.",
        f"<b>Conversion:</b> {K['visit_rate']:.1f}% of reached accounts visit the profile and {K['follow_conv']:.0f}% of visitors follow - "
        f"{an.human(K['follows'])} new follows in this view. Profile visits are the strongest lever for follower growth.",
    ]
    for it in items:
        st.markdown(f'<div class="insight">{it}</div>', unsafe_allow_html=True)

    st.markdown("### Recommended strategy")
    st.markdown(
        """
- **Timing & frequency:** keep the steady ~4,100 posts/month cadence; shift a little extra volume to the best-performing weekday
  and test (A/B) rather than overhaul the calendar - weekday differences are small.
- **Content mix:** keep all four formats in rotation (in the full dataset they perform within ~1% of each other); use Reels/Stories for reach and
  Images/Video for saves-led education content, and measure with the engagement funnel.
- **Engagement:** add comment-driving prompts (polls, questions, giveaways) - comments are only ~10% of engagement and
  shares/saves ~4-5% each, so there is headroom beyond likes.
- **Follower growth:** put calls-to-action on profile visit (bio link, "follow for tutorials"); lifting visit-to-follow
  conversion is cheaper than buying more reach.
- **Hashtags:** brand + community tags are used almost equally; test 3-tag sets that pair #CrueltyFree / #VeganBeauty / #BoldLooks.
- **Gaps:** no caption, creative or cost data - add them to analyse messaging themes and true ROI.
"""
    )
