# Instagram Performance Analytics for Sugar Cosmetics (Streamlit)

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```
Opens at http://localhost:8501. The dataset is read from `data/sugar_cosmetics_instagram_data.xlsx`
(or upload another .xlsx in the sidebar).

## Files
| File | Purpose |
|---|---|
| `app.py` | Streamlit dashboard (UI, charts, filters, cross-filtering) |
| `analytics.py` | Pure-pandas KPI / aggregation functions (also used by the report) |
| `data_prep.py` | Loading, cleaning, calculated fields. `python data_prep.py` exports a cleaned CSV |
| `make_report_charts.py`, `build_report.js` | Regenerate the report charts and Word report |
| `.streamlit/config.toml` | Purple theme |
| `Sugar_Cosmetics_Business_Insights_Report.docx` | Business-insights report (Task 10) |

## Task coverage (tabs)
1 KPI Overview | 2 Monthly Posting Trend | 3 Top 10 by Likes | 4 Top 10 by Engagement Rate |
5 Post Type Performance | 6 Day of Week | 7 Engagement Funnel | 8 Hashtag Analysis |
9 Dashboard (all-in-one, filters + click cross-filtering) | 10 Insights & Strategy.

Engagement Rate = (Likes + Comments + Shares + Saves) / Reach x 100 per post; KPI = mean across posts.
