import os
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# ---------------- Page + Style ----------------
st.set_page_config(page_title="Instagram Analytics", layout="wide")

st.markdown(
    """
    <style>
    body { background-color: #0e1117; color: white; }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("📊 Instagram Performance Dashboard")

# ---------------- Load Data (robust path) ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "instagram_data.csv")

if not os.path.exists(DATA_PATH):
    st.error("❌ Dataset not found at: data/instagram_data.csv")
    st.info(
        "Fix:\n"
        "1) Make sure your GitHub repo has a folder named `data`\n"
        "2) Put `instagram_data.csv` inside it\n"
        "3) Commit + push, then reboot the app on Streamlit Cloud"
    )
    st.stop()

df = pd.read_csv(DATA_PATH, encoding="latin1")

# Standardize column names
df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

# ---------------- Helper: ensure numeric columns exist ----------------
def ensure_numeric(col_name, aliases=None):
    aliases = aliases or []
    if col_name in df.columns:
        df[col_name] = pd.to_numeric(df[col_name], errors="coerce").fillna(0)
        return

    for a in aliases:
        a2 = a.strip().lower().replace(" ", "_")
        if a2 in df.columns:
            df[col_name] = pd.to_numeric(df[a2], errors="coerce").fillna(0)
            return

    df[col_name] = 0

# Map metrics safely
ensure_numeric("impressions", aliases=["impression", "views", "total_impressions"])
ensure_numeric("from_home", aliases=["home"])
ensure_numeric("from_hashtags", aliases=["hashtags"])
ensure_numeric("from_explore", aliases=["explore"])
ensure_numeric("from_other", aliases=["other"])
ensure_numeric("saves")
ensure_numeric("comments")
ensure_numeric("shares")
ensure_numeric("likes")
ensure_numeric("profile_visits", aliases=["visits", "profile_visit"])
ensure_numeric("follows", aliases=["followers"])

# ---------------- Feature Engineering ----------------
df["engagement"] = df["likes"] + df["comments"] + df["shares"] + df["saves"]
df["engagement_rate"] = np.where(
    df["impressions"] > 0,
    (df["engagement"] / df["impressions"]) * 100,
    0
)

# ---------------- Sidebar Filters (apply BEFORE charts) ----------------
st.sidebar.header("🔎 Filters")

# Protect slider if impressions is empty
min_imp = int(df["impressions"].min()) if len(df) else 0
max_imp = int(df["impressions"].max()) if len(df) else 0

min_impressions = st.sidebar.slider(
    "Minimum Impressions",
    min_value=min_imp,
    max_value=max_imp,
    value=min_imp
)

df_filtered = df[df["impressions"] >= min_impressions].copy()

# ---------------- Debug (optional) ----------------
with st.expander("🧾 Detected columns (click to view)"):
    st.write(df.columns.tolist())

# ---------------- KPIs ----------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Posts", len(df_filtered))
c2.metric("Total Impressions", int(df_filtered["impressions"].sum()))
c3.metric("Avg Engagement Rate (%)", round(df_filtered["engagement_rate"].mean(), 2) if len(df_filtered) else 0)
c4.metric("Total Engagement", int(df_filtered["engagement"].sum()))

st.divider()

# ---------------- Charts ----------------
st.subheader("📈 Engagement Rate Distribution")
fig1 = px.histogram(df_filtered, x="engagement_rate", nbins=20)
st.plotly_chart(fig1, use_container_width=True)

st.subheader("🧭 Where impressions came from")
source_data = df_filtered[["from_home", "from_hashtags", "from_explore", "from_other"]].sum().reset_index()
source_data.columns = ["Source", "Total"]
fig2 = px.pie(source_data, names="Source", values="Total")
st.plotly_chart(fig2, use_container_width=True)

# ---------------- Optional: hashtags + caption ----------------
if "hashtags" in df_filtered.columns:
    df_filtered["hashtag_count"] = df_filtered["hashtags"].fillna("").astype(str).apply(lambda x: x.count("#"))
    st.subheader("🔖 Hashtag Count vs Engagement Rate")
    fig3 = px.scatter(df_filtered, x="hashtag_count", y="engagement_rate")
    st.plotly_chart(fig3, use_container_width=True)

if "caption" in df_filtered.columns:
    df_filtered["caption_length"] = df_filtered["caption"].fillna("").astype(str).apply(len)
    st.subheader("✍️ Caption Length vs Engagement Rate")
    fig4 = px.scatter(df_filtered, x="caption_length", y="engagement_rate")
    st.plotly_chart(fig4, use_container_width=True)

# ---------------- Top 10 Table ----------------
st.subheader("🏆 Top 10 Posts by Engagement Rate")
top_posts = df_filtered.sort_values("engagement_rate", ascending=False).head(10)

cols_to_show = [c for c in ["impressions", "likes", "comments", "shares", "saves", "engagement_rate"] if c in top_posts.columns]
st.dataframe(top_posts[cols_to_show], use_container_width=True)
