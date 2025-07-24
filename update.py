import csv
import requests
import os
import re
from urllib.parse import urlparse
from pathlib import Path
import time

DOMAIN = "https://swag.swarsel.win"
WISH_ENDPOINT = f"{DOMAIN}/api/wishes"
AUTH_ENDPOINT = f"{DOMAIN}/api/authentication_token"
IMAGE_UPLOAD_ENDPOINT_TEMPLATE = "{DOMAIN}/api/wishes/{wish_id}/image"
collection_url = input("Enter collection url: ")
match = re.search(r'/collections/([a-f0-9\-]{36})', wishlist_url)
collection = match.group(1)
print(f"got {collection}")
collection_ID = f"/api/wishlists/{collection}"
CURRENCY = "EUR"
VISIBILITY = "public"
csv_input = input("Enter csv filename: ")
CSV_INPUT = csv_input
CSV_OUTPUT = "posted_cards.csv"
IMAGE_DIR = "image"

json_headers_min = {
    "Content-Type": "application/json",
}


def read_credentials(filepath="credentials.txt"):
    username = password = None

    with open(filepath, "r") as file:
        for line in file:
            if line.startswith("username:"):
                username = line.split(":", 1)[1].strip()
            elif line.startswith("password:"):
                password = line.split(":", 1)[1].strip()

    if not username or not password:
        raise ValueError("Credentials file is missing username or password.")

    return username, password

def sanitize_filename(name):
    return re.sub(r'[^a-zA-Z0-9]', '_', name).strip('_')

def get_extension_from_url(url):
    parsed = urlparse(url)
    if '.' in parsed.path:
        return os.path.splitext(parsed.path)[1]
    return ".jpg"

def download_image(url, name):
    if not url:
        print(f"[WARN] No image URL for {name}")
        return None

    Path(IMAGE_DIR).mkdir(parents=True, exist_ok=True)
    filename = sanitize_filename(name) + get_extension_from_url(url)
    filepath = os.path.join(IMAGE_DIR, filename)

    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"[INFO] Downloaded image for {name} -> {filepath}")
        return filepath
    except requests.RequestException as e:
        print(f"[ERROR] Failed to download image for {name}: {e}")
        return None

def load_cards_from_csv(csv_file):
    with open(csv_file, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def auth_self(username, password):
    payload = {
        "username": username,
        "password": password,
    }

    try:
        response = requests.post(AUTH_ENDPOINT, headers=json_headers_min, json=payload)
        response.raise_for_status()
        data = response.json()
        token = data.get("token")
        print(f"Authenticated")
        return token
    except requests.RequestException as e:
        print(f"[ERROR] {e}")
        try:
            print(response.content.decode())
        except Exception:
            pass
        return None

def post_card(card, auth):
    payload = {
        "name": card["Name"],
        "url": card["URL"],
        "comment": card["URL"],
        "wishlist": WISHLIST_ID,
        "price": card["Price"],
        "currency": CURRENCY,
        "visibility": VISIBILITY
    }

    try:
        json_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {auth}",
        }
        response = requests.post(WISH_ENDPOINT, headers=json_headers, json=payload)
        response.raise_for_status()
        data = response.json()
        card_id = data.get("id")
        print(f"[SUCCESS] {card['Name']} added with ID: {card_id}")
        return card_id
    except requests.RequestException as e:
        print(f"[ERROR] Failed to add {card['Name']}: {e}")
        try:
            print(response.content.decode())
        except Exception:
            pass
        return None

def upload_image(wish_id, image_path, name, auth):
    if not image_path or not os.path.isfile(image_path):
        print(f"[WARN] No image to upload for {name}")
        return False

    upload_url = IMAGE_UPLOAD_ENDPOINT_TEMPLATE.format(DOMAIN=DOMAIN,wish_id=wish_id)
    try:
        multipart_headers = {
            "Authorization": f"Bearer {auth}",
        }
        with open(image_path, 'rb') as img_file:
            files = {'file': img_file}
            response = requests.post(upload_url, headers=multipart_headers, files=files)
            response.raise_for_status()
            print(f"[UPLOAD] Image uploaded for {name}")
            return True
    except requests.RequestException as e:
        print(f"[ERROR] Upload failed for {name}: {e}")
        try:
            print(response.content.decode())
        except Exception:
            pass
        return False

def save_posted_cards(cards, output_file):
    with open(output_file, mode="w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Name", "URL", "Price", "ID", "Image File"])
        writer.writeheader()
        writer.writerows(cards)

def main():
    cards = load_cards_from_csv(CSV_INPUT)
    print(f"[INFO] Found {len(cards)} card(s) to process.")

    posted = []
    count = 0
    username, password = read_credentials()

    for card in cards:
        if count == 0 or count > 20:
            auth = auth_self(username, password)
            count = 0
        time.sleep(1)

        # Step 1: Get list of items
        image_path = download_image(card.get("Image URL", ""), card["Name"])
        card["DownloadedImage"] = image_path or ""

        # Step 2: Create wish
        wish_id = post_card(card, auth)
        if not wish_id:
            continue

        # Step 3: Upload image
        upload_image(wish_id, image_path, card["Name"], auth)

        posted.append({
            "Name": card["Name"],
            "URL": card["URL"],
            "Price": card["Price"],
            "ID": wish_id,
            "Image File": image_path or ""
        })
        count += 1

    if posted:
        save_posted_cards(posted, CSV_OUTPUT)
        print(f"[INFO] Saved {len(posted)} posted card(s) to {CSV_OUTPUT}")
    else:
        print("[WARN] No cards were successfully posted.")

if __name__ == "__main__":
    main()
