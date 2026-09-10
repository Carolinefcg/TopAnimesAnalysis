from datetime import datetime
import glob
import json
import os
import time
import requests

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


def fetch_airing_light_novels(max_pages: int = 3):
    """Fetch currently airing anime filtered strictly for Light Novel adaptations."""
    collected_light_novels = []

    for page in range(1, max_pages + 1):
        url = f"{BASE_URL}/top/anime?filter=airing&page={page}&limit=25"
        print(f"Fetching page {page} from: {url}")

        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code == 200:
                data = response.json().get("data", [])
                if not data:
                    break

                # Filter strictly for Light Novel adaptations
                page_light_novels = [
                    anime
                    for anime in data
                    if anime.get("source") == "Light novel"
                ]
                collected_light_novels.extend(page_light_novels)
                print(
                    f"  -> Page {page}: Found {len(page_light_novels)} Light Novel entries."
                )

            elif response.status_code == 429:
                print("Rate limited by Jikan. Sleeping for 2 seconds...")
                time.sleep(2)
            else:
                print(
                    f"Failed to fetch page {page}. Status Code: {response.status_code}"
                )
                break

        except Exception as e:
            print(f"Request error on page {page}: {e}")
            break

        # Respect Jikan rate limits (max 3 req/sec)
        time.sleep(1)

    return collected_light_novels


def manage_file_rotation(new_file_name):
    """1.

    Moves any existing file in 'current' to 'history'
    2. Keeps only the last 3 files in 'history', deleting older ones.
    """
    # Move existing current file(s) to history
    existing_current_files = glob.glob(os.path.join(CURRENT_DIR, "*.json"))
    for file_path in existing_current_files:
        file_name = os.path.basename(file_path)
        dest_path = os.path.join(HISTORY_DIR, file_name)
        os.rename(file_path, dest_path)
        print(f"Rotated previous 'current' file to history: {file_name}")

    # Cleanup history: retain latest 3 files
    history_files = sorted(glob.glob(os.path.join(HISTORY_DIR, "*.json")))
    if len(history_files) > 3:
        files_to_delete = history_files[:-3]
        for old_file in files_to_delete:
            os.remove(old_file)
            print(f"Deleted old historical file: {os.path.basename(old_file)}")


def main():
    light_novel_anime = fetch_airing_light_novels(max_pages=3)
    print(
        f"\nTotal extracted Airing Light Novel entries: {len(light_novel_anime)}"
    )

    if not light_novel_anime:
        print("No Light Novel data extracted. Skipping rotation.")
        return

    # File Rotation Logic
    filename = f"airing_light_novels_raw_{execution_time}.json"
    manage_file_rotation(filename)

    # Save fresh file to 'current' directory
    current_file_path = os.path.join(CURRENT_DIR, filename)
    with open(current_file_path, "w", encoding="utf-8") as f:
        json.dump(light_novel_anime, f, indent=4, ensure_ascii=False)

    print(f"\n--- Extraction Complete ---")
    print(f"Saved latest data to: {current_file_path}")


if __name__ == "__main__":
    main()
