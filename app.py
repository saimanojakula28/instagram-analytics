import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="Instagram Analytics", layout="wide")
st.title("📊 Instagram Performance Dashboard")

# ---- Load data ----
df = pd.read_csv("data/instagram_data.csv", encoding="latin1")

# Standardize column names (IMPORTANT)
df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

st.caption("Detected columns:")
st.write(df.columns.tolist())

# ---- Helper: ensure a numeric column exists ----
def ensure_numeric(col_name, aliases=None):
    aliases = aliases or []
    if col_name in df.columns:
        df[col_name] = pd.to_numeric(df[col_name], errors="coerce").fillna(0)
        return col_name

    # try aliases
    for a in aliases:
        a2 = a.strip().lower().replace(" ", "_")
        if a2 in df.columns:
            df[col_name] = pd.to_numeric(df[a2], errors="coerce").fillna(0)
            return col_name

    # if not found, create it
    df[col_name] = 0
    return col_name

# ---- Map your metrics safely ----
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

# ---- Create engagement metrics ----
df["engagement"] = df["likes"] + df["comments"] + df["shares"] + df["saves"]
df["engagement_rate"] = np.where(df["impressions"] > 0,
                                 (df["engagement"] / df["impressions"]) * 100,
                                 0)

# ---- KPIs ----
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Posts", len(df))
c2.metric("Total Impressions", int(df["impressions"].sum()))
c3.metric("Avg Engagement Rate (%)", round(df["engagement_rate"].mean(), 2))
c4.metric("Total Engagement", int(df["engagement"].sum()))

st.divider()

# ---- Engagement distribution ----
st.subheader("📈 Engagement Rate Distribution")
fig1 = px.histogram(df, x="engagement_rate", nbins=20)
st.plotly_chart(fig1, use_container_width=True)

# ---- Sources breakdown ----
st.subheader("🧭 Where impressions came from")
source_data = df[["from_home","from_hashtags","from_explore","from_other"]].sum().reset_index()
source_data.columns = ["Source","Total"]
fig2 = px.pie(source_data, names="Source", values="Total")
st.plotly_chart(fig2, use_container_width=True)

# ---- Optional: caption + hashtags analysis ----
if "hashtags" in df.columns:
    df["hashtag_count"] = df["hashtags"].fillna("").astype(str).apply(lambda x: x.count("#"))
    st.subheader("🔖 Hashtag Count vs Engagement Rate")
    fig3 = px.scatter(df, x="hashtag_count", y="engagement_rate")
    st.plotly_chart(fig3, use_container_width=True)

if "caption" in df.columns:
    df["caption_length"] = df["caption"].fillna("").astype(str).apply(len)
    st.subheader("✍️ Caption Length vs Engagement Rate")
    fig4 = px.scatter(df, x="caption_length", y="engagement_rate")
    st.plotly_chart(fig4, use_container_width=True)
