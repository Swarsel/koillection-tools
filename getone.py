import requests
from lxml import html
import csv


def fetch_and_extract(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"[ERROR] Fetching {url}: {e}")
        return None

    tree = html.fromstring(response.content)

    def safe_xpath(xpath_expr, default=""):
        try:
            return tree.xpath(xpath_expr)[0].strip()
        except (IndexError, AttributeError):
            return default

    return {
        "URL": url,
        "Image URL": safe_xpath("(//img)[1]/@src"),
    }

def main():
    urls = [ "https://www.discogs.com/release/27856575-Akari-Kaida-Mega-Man-Battle-Network-Original-Video-Game-Soundtrack" ]

    all_data = []

    for url in urls:
        print(f"[INFO] Processing: {url}")
        data = fetch_and_extract(url)
        if data:
            all_data.append(data)

    if not all_data:
        print("[WARN] No data fetched.")
        return

    csv_file = f"one.csv"
    with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=all_data[0].keys())
        writer.writeheader()
        writer.writerows(all_data)

    print(f"[SUCCESS] Wrote {len(all_data)} entries to {csv_file}")

if __name__ == "__main__":
    main()
