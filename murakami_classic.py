import requests
import lxml.html
import csv
import re

# Config
url = "https://mfctc.kaikaikiki.com/cardlist.html"
img_base = "https://mfctc.kaikaikiki.com"
sets = ["PR", "SP", "TKPR", "CMAPR", "TCB", "FGW", "MKJW"]

# Fetch and parse
response = requests.get(url)
response.raise_for_status()
doc = lxml.html.fromstring(response.text)

# Store results: {set_prefix: {card_id: card_data_dict}}
cards_by_set = {s: {} for s in sets}

# Loop through all modal divs
modal_divs = doc.xpath("//div[starts-with(@id, '')]")

for div in modal_divs:
    full_id = div.attrib.get("id")  # e.g., PR-001R, JP_PR-001
    if not full_id:
        continue

    # Extract set prefix and canonical card ID
    match = re.search(r"(PR|SP|TKPR|CMAPR|TCB|FGW|MKJW)-\d{3}", full_id)
    if not match:
        continue

    canonical_id = match.group(0)
    set_prefix = canonical_id.split("-")[0]

    if canonical_id in cards_by_set[set_prefix]:
        continue

    # Get image
    img_elem = div.xpath('.//img')
    if not img_elem:
        continue
    img_src = img_elem[0].attrib.get("src")
    if img_src and not img_src.startswith("http"):
        img_src = img_base + img_src

    # Get name (Japanese preferred)
    jp_xpath = f"//div[@id='{full_id}']//div[@class='p-modalHead']//div[@class='p-modalHeadTitle is-jp']"
    fallback_xpath = f"//div[@id='{full_id}']//div[@class='p-modalHead']//div[@class='p-modalHeadTitle']"
    title_elem = doc.xpath(jp_xpath) or doc.xpath(fallback_xpath)
    title_text = title_elem[0].text_content().strip() if title_elem else "N/A"

    # Get description
    desc_xpath_jp = f"//div[@id='{full_id}']//div[@class='p-modalContent']/p[1]"
    desc_xpath_fallback = f"//div[@id='{full_id}']//div[@class='p-modalInner']//div[@class='p-modalImg']//p[@class='p-modalContent__txt is-jp']"
    desc_elem = doc.xpath(desc_xpath_jp) or doc.xpath(desc_xpath_fallback)

    import re

    if desc_elem:
        desc_html = lxml.html.tostring(desc_elem[0], encoding="unicode", method="html")
        desc_html = desc_html.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
        desc_text = lxml.html.fromstring(desc_html).text_content()

        # Normalize line breaks and strip each line
        lines = desc_text.splitlines()
        cleaned_lines = [line.strip() for line in lines if line.strip() != '']
        desc_text = "\n".join(cleaned_lines)
    else:
        desc_text = ""

     # Get rarity
    rarity_xpath = f"//div[@id='{full_id}']//div[@class='p-modalHead']//div[@class='p-modalHeadInfo']//div[contains(@class, 'p-modalHeadInfo__rare')]"
    rarity_elem = doc.xpath(rarity_xpath)
    rarity_text = rarity_elem[0].text_content().strip() if rarity_elem else "n/a"

    # Store card data
    cards_by_set[set_prefix][canonical_id] = {
        "id": canonical_id,
        "name": title_text,
        "image_url": img_src,
        "description": desc_text,
        "rarity": rarity_text
    }

# Output to CSV per set
for set_prefix, cards in cards_by_set.items():
    if not cards:
        continue
    filename = f"{set_prefix}.csv"
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "name", "image_url", "description", "rarity"])
        writer.writeheader()
        writer.writerows(cards.values())
    print(f"✅ Wrote {len(cards)} cards to {filename}")
