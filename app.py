import os
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

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

# ---------------- Load Data (works on Cloud) ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_PATH = os.path.join(BASE_DIR, "data", "instagram_data.csv")

st.sidebar.header("📂 Data Source")

use_uploaded = st.sidebar.checkbox("Use uploaded CSV (recommended for Cloud)", value=True)

@st.cache_data(show_spinner=False)
def read_csv_safely(file_or_path):
    # pandas encoding fallback
    try:
        return pd.read_csv(file_or_path, encoding="utf-8")
    except Exception:
        return pd.read_csv(file_or_path, encoding="latin1")

df = None

if use_uploaded:
    uploaded = st.sidebar.file_uploader("Upload instagram_data.csv", type=["csv"])
    if uploaded is not None:
        df = read_csv_safely(uploaded)
    else:
        st.warning("Upload your CSV to continue (left sidebar).")
        st.stop()
else:
    if os.path.exists(LOCAL_PATH):
        df = read_csv_safely(LOCAL_PATH)
    else:
        st.error("❌ Local dataset not found at: data/instagram_data.csv")
        st.info("Either upload the CSV from the sidebar, or add it to your GitHub repo inside `data/` folder.")
        st.stop()

# ---------------- Clean columns ----------------
df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

with st.expander("🧾 Detected columns"):
    st.write(df.columns.tolist())

# ---------------- Helpers ----------------
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

# Required metrics (based on your earlier columns)
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

# ---------------- Feature engineering ----------------
df["engagement"] = df["likes"] + df["comments"] + df["shares"] + df["saves"]
df["engagement_rate"] = np.where(df["impressions"] > 0, (df["engagement"] / df["impressions"]) * 100, 0)

# ---------------- Filters ----------------
st.sidebar.header("🔎 Filters")

min_imp = int(df["impressions"].min()) if len(df) else 0
max_imp = int(df["impressions"].max()) if len(df) else 0

min_impressions = st.sidebar.slider("Minimum Impressions", min_value=min_imp, max_value=max_imp, value=min_imp)
df = df[df["impressions"] >= min_impressions].copy()

# ---------------- KPIs ----------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Posts", len(df))
c2.metric("Total Impressions", int(df["impressions"].sum()))
c3.metric("Avg Engagement Rate (%)", round(df["engagement_rate"].mean(), 2) if len(df) else 0)
c4.metric("Total Engagement", int(df["engagement"].sum()))

st.divider()

# ---------------- Charts ----------------
st.subheader("📈 Engagement Rate Distribution")
st.plotly_chart(px.histogram(df, x="engagement_rate", nbins=20), use_container_width=True)

st.subheader("🧭 Where impressions came from")
source_data = df[["from_home", "from_hashtags", "from_explore", "from_other"]].sum().reset_index()
source_data.columns = ["Source", "Total"]
st.plotly_chart(px.pie(source_data, names="Source", values="Total"), use_container_width=True)

if "hashtags" in df.columns:
    df["hashtag_count"] = df["hashtags"].fillna("").astype(str).apply(lambda x: x.count("#"))
    st.subheader("🔖 Hashtag Count vs Engagement Rate")
    st.plotly_chart(px.scatter(df, x="hashtag_count", y="engagement_rate"), use_container_width=True)

if "caption" in df.columns:
    df["caption_length"] = df["caption"].fillna("").astype(str).apply(len)
    st.subheader("✍️ Caption Length vs Engagement Rate")
    st.plotly_chart(px.scatter(df, x="caption_length", y="engagement_rate"), use_container_width=True)

st.subheader("🏆 Top 10 Posts by Engagement Rate")
top_posts = df.sort_values("engagement_rate", ascending=False).head(10)
show_cols = [c for c in ["impressions", "likes", "comments", "shares", "saves", "engagement_rate"] if c in top_posts.columns]
st.dataframe(top_posts[show_cols], use_container_width=True)
