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
        "Image URL": safe_xpath("//img[@class='card shadow resp-w']/@src"),
        "Name": safe_xpath("/html[1]/body[1]/main[1]/div[1]/section[1]/div[1]/div[2]/div[1]/div[1]/div[1]/p[1]/span[1]/a[1]/text()"),
        "Number": safe_xpath("/html[1]/body[1]/main[1]/div[1]/section[1]/div[2]/div[1]/a[1]/div[1]/span[2]/text()"),
        "Set": safe_xpath("//span[@class='text-lg']/text()"),
        "Price": safe_xpath("/html/body/main/div/section[2]/div[2]/a[2]/span/text()")[1:]
    }

def main():
    set = input("set set url handle: ")
    size = int(input("how many things are in the set? "))
    urls = [ f"https://limitlesstcg.com/cards/{set}/{item}" for item in range(1,size + 1) ]

    all_data = []

    for url in urls:
        print(f"[INFO] Processing: {url}")
        data = fetch_and_extract(url)
        if data:
            all_data.append(data)

    if not all_data:
        print("[WARN] No data fetched.")
        return

    csv_file = f"{set}.csv"
    with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=all_data[0].keys())
        writer.writeheader()
        writer.writerows(all_data)

    print(f"[SUCCESS] Wrote {len(all_data)} entries to {csv_file}")

if __name__ == "__main__":
    main()

