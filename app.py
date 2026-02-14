import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from io import StringIO

st.set_page_config(page_title="Instagram Analytics", layout="wide")
st.title("📊 Instagram Performance Dashboard")

uploaded_file = st.sidebar.file_uploader("Upload your instagram_data file", type=["csv", "txt"])

if uploaded_file is None:
    st.warning("Upload your file from the left sidebar.")
    st.stop()

# ----- Read raw bytes safely -----
raw_bytes = uploaded_file.getvalue()

# 1) Empty file check
if raw_bytes is None or len(raw_bytes) == 0:
    st.error("❌ The uploaded file is EMPTY (0 bytes). Please export/download again and upload a proper CSV.")
    st.stop()

# 2) Decode preview to identify file type
preview = raw_bytes[:600].decode("latin1", errors="replace")
st.sidebar.caption("File details")
st.sidebar.write({"name": uploaded_file.name, "size_bytes": len(raw_bytes)})

with st.expander("🔍 File preview (first 600 characters)"):
    st.code(preview)

# If it looks like JSON, stop and tell user clearly
if preview.lstrip().startswith("{") or preview.lstrip().startswith("["):
    st.error("❌ This looks like JSON, not CSV. Please convert JSON → CSV first (Instagram ZIP download gives JSON).")
    st.info("Tip: If you only have Instagram ZIP, share the JSON file name (like posts.json) and I’ll give you the converter script.")
    st.stop()

# ----- Robust CSV parse: encodings + separators -----
def try_parse(text: str):
    # Try common separators
    for sep in [",", ";", "\t", "|"]:
        try:
            df_try = pd.read_csv(StringIO(text), sep=sep)
            # valid if it has at least 2 columns or at least 1 column with rows
            if df_try.shape[1] >= 1 and df_try.shape[0] >= 1:
                return df_try, sep
        except Exception:
            continue
    return None, None

df = None
used_sep = None

for enc in ["utf-8", "utf-8-sig", "latin1", "cp1252"]:
    try:
        text = raw_bytes.decode(enc, errors="replace")
        if text.strip() == "":
            continue
        df, used_sep = try_parse(text)
        if df is not None:
            break
    except Exception:
        continue

if df is None:
    st.error("❌ Could not parse this file as a CSV table.")
    st.info("Make sure the file is a real CSV export (with headers). The preview above shows what was uploaded.")
    st.stop()

st.success(f"✅ File loaded successfully (separator detected: `{used_sep}`)")

# ----- Standardize columns -----
df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
st.caption("Detected columns:")
st.write(df.columns.tolist())

# ----- Ensure numeric columns exist -----
def ensure_numeric(col, aliases=None):
    aliases = aliases or []
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        return
    for a in aliases:
        a2 = a.strip().lower().replace(" ", "_")
        if a2 in df.columns:
            df[col] = pd.to_numeric(df[a2], errors="coerce").fillna(0)
            return
    df[col] = 0

ensure_numeric("impressions", aliases=["impression", "views", "total_impressions"])
ensure_numeric("likes")
ensure_numeric("comments")
ensure_numeric("shares")
ensure_numeric("saves")

# ----- Features -----
df["engagement"] = df["likes"] + df["comments"] + df["shares"] + df["saves"]
df["engagement_rate"] = np.where(df["impressions"] > 0, (df["engagement"] / df["impressions"]) * 100, 0)

# ----- Filters -----
st.sidebar.header("🔎 Filters")
min_imp = int(df["impressions"].min()) if len(df) else 0
max_imp = int(df["impressions"].max()) if len(df) else 0
min_impressions = st.sidebar.slider("Minimum Impressions", min_value=min_imp, max_value=max_imp, value=min_imp)
df = df[df["impressions"] >= min_impressions].copy()

# ----- KPIs -----
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Posts", len(df))
c2.metric("Total Impressions", int(df["impressions"].sum()))
c3.metric("Avg Engagement Rate (%)", round(df["engagement_rate"].mean(), 2) if len(df) else 0)
c4.metric("Total Engagement", int(df["engagement"].sum()))

st.divider()

# ----- Charts -----
st.subheader("📈 Engagement Rate Distribution")
st.plotly_chart(px.histogram(df, x="engagement_rate", nbins=20), use_container_width=True)

st.subheader("🏆 Top 10 Posts by Engagement Rate")
top_posts = df.sort_values("engagement_rate", ascending=False).head(10)

show_cols = [c for c in ["impressions", "likes", "comments", "shares", "saves", "engagement_rate"] if c in top_posts.columns]
st.dataframe(top_posts[show_cols], use_container_width=True)
