import pandas as pd

def load_data(path="data/instagram_data.csv"):
    
    try:
        df = pd.read_csv(path, encoding="utf-8")
    except:
        df = pd.read_csv(path, encoding="latin1")

    df.columns = [c.strip().replace(" ", "_").lower() for c in df.columns]

    return df
