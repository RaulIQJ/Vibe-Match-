"""Pull my Spotify top tracks and check how many are in the Kaggle catalog."""
import os
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()

# Permissions we ask the user for (shown on Spotify's login screen)
SCOPES = "user-top-read user-read-recently-played user-library-read"

# Spotify's three windows for "top" listening
TIME_RANGES = {
    "short_term": "last ~4 weeks",
    "medium_term": "last ~6 months",
    "long_term": "last ~1 year",
}


def get_client():
    """Log in to Spotify. The first run opens a browser; later runs reuse the saved token."""
    return spotipy.Spotify(auth_manager=SpotifyOAuth(scope=SCOPES))


def fetch_top_tracks(sp):
    """Return a table of the user's top 50 tracks for each time range."""
    rows = []
    for time_range in TIME_RANGES:
        results = sp.current_user_top_tracks(limit=50, time_range=time_range)
        for rank, track in enumerate(results["items"], start=1):
            rows.append({
                "time_range": time_range,
                "rank": rank,
                "track_id": track["id"],
                "track_name": track["name"],
                "artist": track["artists"][0]["name"],
                "isrc": track.get("external_ids", {}).get("isrc"),
            })
    return pd.DataFrame(rows)


def normalize(text):
    """Lowercase and trim so 'Blinding Lights ' matches 'blinding lights'."""
    return str(text).lower().strip()


def check_catalog_match(top, catalog):
    """Mark each top track as found in the catalog by Spotify ID or by name + artist."""
    catalog_ids = set(catalog["track_id"])

    first_artist = catalog["artists"].astype(str).str.split(";").str[0]
    catalog_keys = set(zip(catalog["track_name"].map(normalize), first_artist.map(normalize)))

    top["id_match"] = top["track_id"].isin(catalog_ids)
    top["name_match"] = [
        (normalize(name), normalize(artist)) in catalog_keys
        for name, artist in zip(top["track_name"], top["artist"])
    ]
    top["in_catalog"] = top["id_match"] | top["name_match"]
    return top


def main():
    sp = get_client()
    me = sp.current_user()
    print(f"Logged in as: {me['display_name']}\n")

    top = fetch_top_tracks(sp)
    catalog = pd.read_csv("data/raw/dataset.csv")
    top = check_catalog_match(top, catalog)

    print("Catalog coverage of your top tracks:")
    for time_range, label in TIME_RANGES.items():
        subset = top[top["time_range"] == time_range]
        print(f"  {time_range:12} ({label}): "
              f"{subset['in_catalog'].sum()}/{len(subset)} found "
              f"({subset['id_match'].sum()} by ID, "
              f"{(subset['name_match'] & ~subset['id_match']).sum()} by name only)")

    missing = top[~top["in_catalog"]].drop_duplicates("track_id").head(5)
    print("\nA few songs NOT in the catalog:")
    for _, row in missing.iterrows():
        print(f"  - {row['track_name']} — {row['artist']}")

    os.makedirs("data/user", exist_ok=True)
    top.to_csv("data/user/top_tracks.csv", index=False)
    print("\nSaved to data/user/top_tracks.csv")


if __name__ == "__main__":
    main()