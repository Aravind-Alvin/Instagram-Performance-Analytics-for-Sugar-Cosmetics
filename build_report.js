const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, HeadingLevel, AlignmentType,
  WidthType, ShadingType, BorderStyle, LevelFormat, PageBreak, Footer, PageNumber,
} = require("docx");

const PURPLE = "5A3EA6", INK = "3B1A5A", PINKBG = "F6E6F5", FONT = "Calibri";
const W = 9360; // content width, US Letter w/ 1" margins

const p = (text, o = {}) => new Paragraph({ spacing: { after: 120, line: 276 }, ...o,
  children: Array.isArray(text) ? text : [new TextRun({ text, font: FONT, size: 22, ...(o.run || {}) })] });
const runs = (parts) => parts.map(([t, b]) => new TextRun({ text: t, bold: !!b, font: FONT, size: 22 }));
const h1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 280, after: 120 },
  children: [new TextRun({ text: t, bold: true, font: FONT, size: 32, color: PURPLE })] });
const h2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 200, after: 80 },
  children: [new TextRun({ text: t, bold: true, font: FONT, size: 26, color: INK })] });
const bullet = (parts) => new Paragraph({ numbering: { reference: "bul", level: 0 }, spacing: { after: 80 },
  children: typeof parts === "string" ? [new TextRun({ text: parts, font: FONT, size: 22 })] : runs(parts) });
const img = (file, w, h) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 },
  children: [new ImageRun({ type: "png", data: fs.readFileSync("report_assets/" + file),
    transformation: { width: w, height: h }, altText: { title: file, description: file, name: file } })] });
const cap = (t) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 160 },
  children: [new TextRun({ text: t, italics: true, font: FONT, size: 18, color: "666666" })] });
const callout = (label, text) => new Paragraph({ spacing: { before: 60, after: 160 },
  shading: { type: ShadingType.CLEAR, fill: PINKBG }, border: { left: { style: BorderStyle.SINGLE, size: 24, color: PURPLE, space: 8 } },
  indent: { left: 160 }, children: [new TextRun({ text: label + " ", bold: true, font: FONT, size: 22, color: PURPLE }),
    new TextRun({ text, font: FONT, size: 22 })] });

const border = { style: BorderStyle.SINGLE, size: 4, color: "CCB3D6" };
const borders = { top: border, bottom: border, left: border, right: border };
function table(widths, header, rows) {
  const cell = (t, w, hd) => new TableCell({ width: { size: w, type: WidthType.DXA }, borders,
    shading: { type: ShadingType.CLEAR, fill: hd ? PURPLE : "FFFFFF" }, margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({ children: [new TextRun({ text: String(t), bold: hd, font: FONT, size: 20, color: hd ? "FFFFFF" : INK })] })] });
  return new Table({ width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: widths,
    rows: [new TableRow({ tableHeader: true, children: header.map((t, i) => cell(t, widths[i], true)) }),
      ...rows.map((r) => new TableRow({ children: r.map((t, i) => cell(t, widths[i], false)) }))] });
}
const gap = () => new Paragraph({ spacing: { after: 120 }, children: [] });

const body = [];
// ---------- Title ----------
body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 600, after: 80 },
  children: [new TextRun({ text: "Instagram Performance Analytics", bold: true, font: FONT, size: 52, color: PURPLE })] }));
body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 },
  children: [new TextRun({ text: "for Sugar Cosmetics", bold: true, font: FONT, size: 40, color: INK })] }));
body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 360 },
  children: [new TextRun({ text: "Business Insights & Strategic Recommendations  |  Data: 19 Apr 2024 - 19 Apr 2025  |  50,000 posts", font: FONT, size: 20, color: "666666" })] }));

// ---------- Exec summary ----------
body.push(h1("1. Executive summary"));
body.push(p("Sugar Cosmetics' Instagram account is large, consistent and highly engaged. Over the 12-month window the 50,000 posts reached " +
  "about 987 million accounts (1.28 billion impressions), collected 147.7 million likes and 18.5 million comments, and generated 8.9 million new follows. " +
  "The average post earns an engagement rate of 18.5% of its reach."));
body.push(p([...runs([["The most important finding is about what does not matter. ", true],
  ["Engagement rate is almost identical across post formats (a 1.0% gap between best and worst), weekdays (1.2%), hashtags (0.5%), campaign types, " +
   "audience emotions and engagement sources. Reach and impressions are also unrelated to engagement rate (correlation 0.00). " +
   "The account performs evenly across its content mix, so the biggest growth opportunities lie in scale, conversion and testing - not in swapping one format or day for another.", false]])]));
body.push(table([3000, 1700, 4660], ["Headline KPI", "Value", "Reading"], [
  ["Total posts", "50,000", "~4,100 per month, a steady cadence"],
  ["Total likes / comments", "147.7M / 18.5M", "Likes are 81% of all engagement; comments 10%"],
  ["Total reach", "987.4M", "Reach is 77% of impressions"],
  ["Avg engagement rate", "18.5%", "Engagement (likes+comments+shares+saves) / reach"],
  ["Profile visits / new follows", "29.6M / 8.9M", "3.0% of reach visits; ~30% of visitors follow"],
]));
body.push(gap());

// ---------- Data & method ----------
body.push(h1("2. Data and method"));
body.push(p("The dataset (sugar_cosmetics_instagram_data.xlsx) holds one row per post with date, post type, campaign type, hashtags, audience emotion, " +
  "engagement source, impressions, reach, likes, comments, shares, saves, profile visits and follows. Cleaning checks found no missing values, " +
  "duplicates or rows where reach exceeded impressions, so no records were removed."));
body.push(bullet([["Engagement rate (ER) ", true], ["= (likes + comments + shares + saves) / reach x 100, calculated per post; the KPI is the mean across posts.", false]]));
body.push(bullet([["Month / weekday ", true], ["are derived from Post Date. Apr 2024 (starts 19 Apr) and Apr 2025 (ends 19 Apr) are partial months.", false]]));
body.push(bullet([["Hashtags ", true], ["are split into individual tags (each post counts once per tag); full tag combinations are analysed separately.", false]]));
body.push(callout("Data caveats.", "(1) There is no caption column, so posts are labelled by format | campaign | date | post ID. " +
  "(2) The dataset has Image, Reel, Story and Video posts - no Carousel. (3) ~137 posts per day is far higher than a normal brand account and category averages are " +
  "unusually uniform, which suggests the data is sampled or synthetic; conclusions below are about this dataset and should be validated on live Instagram Insights before large budget decisions."));

// ---------- Findings ----------
body.push(h1("3. Findings by analysis"));

body.push(h2("3.1 Posting consistency (Task 2)"));
body.push(img("monthly.png", 520, 222));
body.push(p("Volume is remarkably stable: 3,930 to 4,296 posts every full month, with February the lightest (3,930, a shorter month) and December the busiest (4,296). " +
  "The dips in Apr 2024 and Apr 2025 are due to partial coverage, not a change in activity."));

body.push(h2("3.2 Top 10 posts by likes (Task 3)"));
body.push(img("top_likes.png", 520, 250));
body.push(p("All ten posts earned 11,043-11,392 likes and each reached 44,000-47,000 accounts - i.e. the biggest reach in the data. " +
  "Six of the ten are Influencer Collab (3) or Giveaway (3) campaigns, and all four formats appear. Likes mostly reward reach, so this list mainly shows which posts were widely distributed."));

body.push(h2("3.3 Top 10 posts by engagement rate (Task 4)"));
body.push(img("top_er.png", 520, 250));
body.push(p("The ER ranking tells a different story: the top posts reach 33.8-34.1% ER with reach ranging from 7,181 to 44,299. " +
  "No post appears in both top-10 lists, confirming that likes-based rankings hide efficient content. Giveaway, Influencer Collab, Tutorial, Festive and Launch posts all appear. " +
  "Hidden gems such as the 7,181-reach Video launch (34.0% ER) show strong content can win without a big audience."));

body.push(h2("3.3b Post type performance (Task 5)"));
body.push(img("post_type.png", 540, 202));
body.push(table([1800, 1400, 1400, 1500, 1500, 1760], ["Post type", "Avg likes", "Avg comments", "Avg saves", "Avg shares", "Avg ER"], [
  ["Image", "2,954", "367", "177", "161", "18.43%"], ["Reel", "2,960", "369", "178", "162", "18.61%"],
  ["Story", "2,964", "371", "178", "165", "18.60%"], ["Video", "2,941", "370", "176", "162", "18.51%"],
]));
body.push(gap());
body.push(p("Reels (18.61%) and Stories (18.60%) lead and Images (18.43%) trail, but the full spread is under 1% - formats are effectively tied. " +
  "Story posts lead on likes, comments and shares; Reels lead on saves and ER."));

body.push(h2("3.4 Day-of-week analysis (Task 6)"));
body.push(img("dow.png", 520, 222));
body.push(p("Wednesday has the highest average ER (18.63%) followed by Saturday (18.60%) and Tuesday (18.57%); Sunday is lowest (18.42%). " +
  "The whole range is 1.2%, and posting volume is also near-flat across days (7,028-7,355), so timing is a mild tiebreaker only."));

body.push(h2("3.5 Engagement funnel (Task 7)"));
body.push(img("funnel.png", 520, 236));
body.push(p("Of 1.28 billion impressions, 77.4% were unique reach. Likes equal 11.6% of impressions, comments 1.4%, shares 0.64% and saves 0.69%. " +
  "Comments, shares and saves are parallel actions rather than a strict sequence, so compare them as shares of impressions. The clear weak spots are the 'deep' actions: " +
  "only about 1 in 70 impressions becomes a comment and about 1 in 150 a share or save."));

body.push(h2("3.6 Hashtag analysis (Task 8)"));
body.push(img("hashtag.png", 520, 222));
body.push(p("The five hashtags are used almost equally (about 20,000 posts each). Average ER ranges only from 18.51% (#MakeupGoals) to 18.61% (#VeganBeauty). " +
  "Combination analysis (combinations with at least 100 posts) ranges from 17.5% to 19.5%, with #BoldLooks + #CrueltyFree + #VeganBeauty at the top (19.5% across 293 posts). " +
  "Given ~290 posts per combination, differences of about 1 point are close to normal sampling variation, so treat these as test hypotheses, not proven winners."));

body.push(h2("3.7 Audience and growth signals"));
body.push(img("growth.png", 520, 222));
body.push(p("Monthly follows (about 700-760K in full months) track profile visits closely (post-level correlation 0.84): roughly 3% of reached accounts visit the profile, and about 30% of visitors follow. " +
  "Follows per 1,000 reached accounts are flat at ~9 across formats, campaigns and sources. Growth is therefore steady rather than accelerating - and driven by how many people reach the profile, so the lever is " +
  "reach-to-visit conversion."));
body.push(p("Engagement by source is also tight: Collab (18.59%) and Influencer (18.58%) edge Paid (18.53%) and Organic (18.44%), a gap of 0.8% that does not justify shifting spend on its own."));

// ---------- Dashboard ----------
body.push(h1("4. The interactive dashboard (Task 9)"));
body.push(p("The Streamlit app combines all analyses in one purple-and-pink dashboard styled after the reference design, with an individual tab per analysis:"));
body.push(bullet("Sidebar filters: Post Type, Month, Hashtag, Campaign Type, Engagement Source and Audience Emotion; every chart and KPI responds."));
body.push(bullet("Chart actions: click a bar in Post Type, Day of Week or Hashtag charts to cross-filter the whole dashboard; click again or press 'Clear chart selections' to reset."));
body.push(bullet("Tabs for KPI Overview, Monthly Trend, Top 10 by Likes, Top 10 by ER (with minimum-reach slider), Post Type, Day of Week, Funnel, Hashtags, Audience & Growth, and live Insights."));
body.push(bullet("Download button for the filtered data (CSV)."));

// ---------- Strategy ----------
body.push(new Paragraph({ children: [new PageBreak()] }));
body.push(h1("5. Strategic recommendations (Task 10)"));

body.push(h2("5.1 Key takeaways"));
body.push(bullet("The account is healthy: 18.5% average ER and ~4,100 posts a month with no seasonality or decline."));
body.push(bullet("Performance is uniform across format, weekday, hashtag, campaign and source - none is a decisive winner (all gaps are about 1% or less)."));
body.push(bullet("Likes dominate engagement (81%); comments (10%), shares (4.4%) and saves (4.8%) are under-developed."));
body.push(bullet("Reach is not linked to ER, and likes rankings differ from ER rankings - so judge content on ER as well as likes."));
body.push(bullet("Follower growth is steady (~0.7M per month) and driven by profile visits: 3% visit, 30% of those follow."));

body.push(h2("5.2 Recommended posting strategy"));
body.push(table([1900, 7460], ["Area", "Recommendation"], [
  ["Timing", "Keep the daily cadence but weight a bit more volume to Wednesday, Tuesday and Saturday (best ER); treat Sunday as the lowest priority. Run a 6-8 week test before reshaping the calendar, since the gaps are small."],
  ["Frequency", "Hold the current ~4,100 posts/month. Monthly ER stayed within 18.4-18.7% whatever the volume, so extra posts are not a proven lever."],
  ["Content mix", "Lean slightly toward Reels and Stories (highest ER and the most engagement per post) while keeping Image and Video for tutorials and product education. Do not cut any format."],
  ["Measurement", "Rank content by ER and saves, not just likes, to surface efficient content like the high-ER, mid-reach posts in section 3.3."],
]));
body.push(gap());

body.push(h2("5.3 Improving engagement and follower growth"));
body.push(bullet([["Lift comments, shares and saves. ", true], ["Add polls, 'tag a friend', quiz and shade-match prompts; comments are only 1.4% of impressions, so this is the biggest headroom.", false]]));
body.push(bullet([["Fix the profile-visit step. ", true], ["Only 3% of reached accounts visit the profile. Use 'follow for tutorials' cues, pinned posts, and bio links to lift visits; each +0.1 pt on visit rate is about +1M visits per year.", false]]));
body.push(bullet([["Improve visit-to-follow conversion ", true], ["(currently ~30%) with a stronger bio, highlights and consistent grid so visitors see a reason to follow.", false]]));
body.push(bullet([["Scale what works through collabs. ", true], ["Influencer Collab and Giveaway posts occupy the top-likes list; Collab/Influencer sources lead on ER vs Paid and Organic.", false]]));

body.push(h2("5.4 Gaps identified and how to address them"));
body.push(table([3000, 6360], ["Gap", "How to address it"], [
  ["No captions or creative data", "Capture caption text, creative theme, CTA and product tags to analyse messaging, not just metrics."],
  ["No cost / revenue data", "Add spend for paid and collab posts and link-clicks/sales to calculate true ROI per campaign."],
  ["No audience demographics", "Pull age, gender and city from Instagram Insights to segment performance (the brief asks for demographic analysis)."],
  ["Partial months & no follower totals", "Use full-month windows and record total followers to compute true growth rate."],
  ["Very uniform data", "Validate against live Insights; if real, run structured A/B tests to find genuine differences."],
]));
body.push(gap());

body.push(h2("5.5 Content and campaign ideas"));
body.push(bullet([["'Shade-Match Saturday' Reels series ", true], ["- quick-tip tutorials with a comment prompt ('Which shade are you?') to lift comments and saves.", false]]));
body.push(bullet([["Mid-week Collab spotlight (Wednesday) ", true], ["- creator takeovers and Stories polls, built on the best-ER day and the highest-ER source.", false]]));
body.push(bullet([["Giveaway with a follow-and-save mechanic ", true], ["- rewards the actions that are under-represented (saves, shares) and drives profile follows.", false]]));
body.push(bullet([["'Cruelty-free, bold-looks' hashtag test ", true], ["- A/B the #BoldLooks + #CrueltyFree + #VeganBeauty set vs current sets for 6 weeks.", false]]));
body.push(bullet([["Festive and launch calendar ", true], ["- pair product launches with a tutorial post the same week so launch reach converts to saves.", false]]));

body.push(h2("5.6 Suggested KPIs to track"));
body.push(p("Engagement rate, comment-to-impression %, share+save rate, profile-visit rate, visit-to-follow conversion, and follows per 1,000 reach - reviewed monthly in the dashboard."));

const doc = new Document({
  styles: { default: { document: { run: { font: FONT, size: 22 } } } },
  numbering: { config: [{ reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT,
    style: { paragraph: { indent: { left: 600, hanging: 300 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1300, right: 1440, bottom: 1200, left: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: "Sugar Cosmetics - Instagram Analytics  |  Page ", font: FONT, size: 18, color: "888888" }),
        new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 18, color: "888888" })] })] }) },
    children: body,
  }],
});
Packer.toBuffer(doc).then((b) => { fs.writeFileSync("Sugar_Cosmetics_Business_Insights_Report.docx", b); console.log("ok"); });
