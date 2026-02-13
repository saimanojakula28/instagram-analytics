from load_clean import load_data
from features import add_features

def main():
    df = load_data()
    df = add_features(df)

    print("Rows:", len(df))
    print("\nTop 5 posts by engagement_rate:")
    print(df.sort_values("engagement_rate", ascending=False)[
        ["impressions","likes","comments","shares","saves","engagement_rate","hashtag_count","caption_length"]
    ].head(5))

    print("\nAverage engagement_rate:", round(df["engagement_rate"].mean(), 2))

if __name__ == "__main__":
    main()
