import glob
import json
import os
import requests
from datetime import datetime

# Execution timestamp
execution_time = datetime.now().strftime("%Y_%m_%d_%H%M%S")

# Base configuration
BASE_URL = "https://api.jikan.moe/v4"
HEADERS = {"User-Agent": "MAL-Analytics-Pipeline/1.0 (Portfolio Project)"}

# Directory Structure
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CURRENT_DIR = os.path.join(SCRIPT_DIR, "data", "raw", "current")
HISTORY_DIR = os.path.join(SCRIPT_DIR, "data", "raw", "history")

os.makedirs(CURRENT_DIR, exist_ok=True)
os.makedirs(HISTORY_DIR, exist_ok=True)


def fetch_current_season_anime():
    """Fetch currently airing anime from Jikan API."""
    url = f"{BASE_URL}/top/anime?filter=airing&limit=25"
    print(f"Fetching current seasonal anime from: {url}")

    response = requests.get(url, headers=HEADERS, timeout=10)

    if response.status_code == 200:
        return response.json().get("data", [])
    else:
        print(f"Failed to fetch. Status Code: {response.status_code}")
        return []


def manage_file_rotation(new_file_name):
    """
    1. Moves any existing file in 'current' to 'history'
    2. Keeps only the last 3 files in 'history', deleting older ones.
    """
    # 1. Move existing current file(s) to history
    existing_current_files = glob.glob(os.path.join(CURRENT_DIR, "*.json"))
    for file_path in existing_current_files:
        file_name = os.path.basename(file_path)
        dest_path = os.path.join(HISTORY_DIR, file_name)
        os.rename(file_path, dest_path)
        print(f"Rotated previous 'current' file to history: {file_name}")

    # 2. Cleanup history: keep only the latest 3 files
    history_files = sorted(glob.glob(os.path.join(HISTORY_DIR, "*.json")))
    if len(history_files) > 3:
        files_to_delete = history_files[:-3]  # All except last 3
        for old_file in files_to_delete:
            os.remove(old_file)
            print(f"Deleted old historical file: {os.path.basename(old_file)}")


def main():
    # Fetch Data
    seasonal_anime = fetch_current_season_anime()
    print(f"Successfully extracted {len(seasonal_anime)} seasonal anime entries.")

    if not seasonal_anime:
        print("No data extracted. Skipping rotation.")
        return

    # File Rotation Logic
    filename = f"airing_anime_raw_{execution_time}.json"
    manage_file_rotation(filename)

    # Save fresh file to 'current' directory
    current_file_path = os.path.join(CURRENT_DIR, filename)
    with open(current_file_path, "w", encoding="utf-8") as f:
        json.dump(seasonal_anime, f, indent=4, ensure_ascii=False)

    print(f"\n--- Extraction Complete ---")
    print(f"Saved latest data to: {current_file_path}")


if __name__ == "__main__":
    main()