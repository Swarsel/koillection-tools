import csv
import requests
import os
import re
from urllib.parse import urlparse
from pathlib import Path
import time

# MODE = "mmktc"
MODE = "mmktc"
DOMAIN = "https://swag.swarsel.win"
ITEM_ENDPOINT = f"{DOMAIN}/api/items"
DATA_ENDPOINT = f"{DOMAIN}/api/data"
AUTH_ENDPOINT = f"{DOMAIN}/api/authentication_token"
IMAGE_UPLOAD_ENDPOINT_TEMPLATE = "{DOMAIN}/api/items/{item_id}/image"
wishlist_url = input("Enter wishlist url: ")
match = re.search(r'/collections/([a-f0-9\-]{36})', wishlist_url)
wishlist = match.group(1)
print(f"got {wishlist}")
ITEMLIST_ID = f"/api/collections/{wishlist}"
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
    url = url.replace("comassets","com/assets")
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
        "name": card["name"],
        "collection": ITEMLIST_ID,
        "visibility": VISIBILITY
    }

    try:
        json_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {auth}",
        }
        response = requests.post(ITEM_ENDPOINT, headers=json_headers, json=payload)
        response.raise_for_status()
        data = response.json()
        card_id = data.get("id")
        print(f"[SUCCESS] {card['name']} added with ID: {card_id}")
        return card_id
    except requests.RequestException as e:
        print(f"[ERROR] Failed to add {card['name']}: {e}")
        try:
            print(response.content.decode())
        except Exception:
            pass
        return None

def upload_image(item_id, image_path, name, auth):
    if not image_path or not os.path.isfile(image_path):
        print(f"[WARN] No image to upload for {name}")
        return False

    upload_url = IMAGE_UPLOAD_ENDPOINT_TEMPLATE.format(DOMAIN=DOMAIN,item_id=item_id)
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

def post_set(card, auth, item_id):
    payload = {
        "item": f"/api/items/{item_id}",
        "type": "text",
        "label": "Set Number",
        "value": card["id"],
        "visibility": VISIBILITY
    }

    try:
        json_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {auth}",
        }
        response = requests.post(DATA_ENDPOINT, headers=json_headers, json=payload)
        response.raise_for_status()
        data = response.json()
        card_id = data.get("id")
        print(f"[SUCCESS] Set {card["id"]} added to ID: {card_id}")
        return
    except requests.RequestException as e:
        print(f"[ERROR] Failed to add Set to {card['name']}: {e}")
        try:
            print(response.content.decode())
        except Exception:
            pass
        return None

def post_desc(card, auth, item_id):
    payload = {
        "item": f"/api/items/{item_id}",
        "type": "text",
        "label": "Description",
        "value": card["description"],
        "visibility": VISIBILITY
    }

    try:
        json_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {auth}",
        }
        response = requests.post(DATA_ENDPOINT, headers=json_headers, json=payload)
        response.raise_for_status()
        data = response.json()
        card_id = data.get("id")
        print(f"[SUCCESS] Set {card["description"]} added to ID: {card_id}")
        return
    except requests.RequestException as e:
        print(f"[ERROR] Failed to add Desc to {card['name']}: {e}")
        try:
            print(response.content.decode())
        except Exception:
            pass
        return None

def post_rarity(card, auth, item_id):
    payload = {
        "item": f"/api/items/{item_id}",
        "type": "text",
        "label": "Rarity",
        "value": card["rarity"],
        "visibility": VISIBILITY
    }

    try:
        json_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {auth}",
        }
        response = requests.post(DATA_ENDPOINT, headers=json_headers, json=payload)
        response.raise_for_status()
        data = response.json()
        card_id = data.get("id")
        print(f"[SUCCESS] Set {card["rarity"]} added to ID: {card_id}")
        return
    except requests.RequestException as e:
        print(f"[ERROR] Failed to add Rarity to {card['name']}: {e}")
        try:
            print(response.content.decode())
        except Exception:
            pass
        return None

def save_posted_cards(cards, output_file):
        # i cant be bothered
        pass

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
        if not card.get("name") or not card.get("image_url"):
            print(f"[SKIP] Incomplete data for row: {card}")
            continue

        # Step 1: Download image
        image_path = download_image(card.get("image_url", ""), card["name"])
        card["DownloadedImage"] = image_path or ""

        # Step 2: Create wish
        item_id = post_card(card, auth)
        if not item_id:
            continue

        # Step 3: Create fields
        post_set(card, auth, item_id)
        post_desc(card, auth, item_id)
        post_rarity(card, auth, item_id)

        # Step 3: Upload image
        upload_image(item_id, image_path, card["name"], auth)

        count += 1

        print("finishhh")

if __name__ == "__main__":
    main()
