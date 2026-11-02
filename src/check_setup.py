"""Sanity check: are keys loaded and is the dataset readable?"""
import os
from dotenv import load_dotenv
import pandas as pd

load_dotenv()  # reads .env into environment variables

# 1. Check each key exists (print only whether it's set, never the value)
for key in ["SPOTIPY_CLIENT_ID", "SPOTIPY_CLIENT_SECRET",
            "SPOTIPY_REDIRECT_URI", "LASTFM_API_KEY"]:
    status = "OK" if os.getenv(key) else "MISSING"
    print(f"{key:24} {status}")

# 2. Load the dataset and show its shape and columns
df = pd.read_csv("data/raw/dataset.csv")
print(f"\nDataset: {len(df):,} rows, {df['track_id'].nunique():,} unique tracks")
print("Columns:", list(df.columns))