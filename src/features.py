import numpy as np
import pandas as pd
import re

def add_features(df: pd.DataFrame) -> pd.DataFrame:
    # Ensure numeric columns exist
    numeric_cols = [
        "impressions","from_home","from_hashtags","from_explore","from_other",
        "saves","comments","shares","likes","profile_visits","follows"
    ]
    for c in numeric_cols:
        if c not in df.columns:
            df[c] = 0

    # Convert to numeric safely
    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    # Engagement + rate
    df["engagement"] = df["likes"] + df["comments"] + df["shares"] + df["saves"]
    df["engagement_rate"] = np.where(df["impressions"] > 0,
                                     (df["engagement"] / df["impressions"]) * 100,
                                     0)

    # Source mix (where impressions came from)
    df["source_total"] = df["from_home"] + df["from_hashtags"] + df["from_explore"] + df["from_other"]
    for col in ["from_home","from_hashtags","from_explore","from_other"]:
        df[col + "_pct"] = np.where(df["source_total"] > 0,
                                    (df[col] / df["source_total"]) * 100,
                                    0)

    # Caption + hashtag features
    if "caption" in df.columns:
        df["caption"] = df["caption"].fillna("").astype(str)
        df["caption_length"] = df["caption"].str.len()
        df["caption_words"] = df["caption"].str.split().str.len()

    if "hashtags" in df.columns:
        df["hashtags"] = df["hashtags"].fillna("").astype(str)
        df["hashtag_count"] = df["hashtags"].apply(lambda x: len(re.findall(r"#\w+", x)))

    return df
