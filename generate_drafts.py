import io
import os
import random
import time
import requests
from PIL import Image, ImageDraw

PRINTIFY_TOKEN = os.environ.get("PRINTIFY_API", "").strip()
GEMINI_KEY = os.environ.get("AI_API", "").strip()

BASE = "https://api.printify.com/v1"
PF_HEADERS = {
"Authorization": f"Bearer {PRINTIFY_TOKEN}",
"Content-Type": "application/json",
}

BLUEPRINTS = [
("Sweatshirt", 1292, 10),
("Hoodie", 77, 10),
("T-Shirt", 6, 10),
]

def get_shop_id():
r = requests.get(f"{BASE}/shops.json", headers=PF_HEADERS, timeout=30)
r.raise_for_status()
shops = r.json()
if not shops:
raise RuntimeError("Printify hesabinda magaza bulunamadi.")
return shops[0]["id"]

def get_provider_and_variants(blueprint_id):
pr_res = requests.get(
f"{BASE}/catalog/blueprints/{blueprint_id}/print_providers.json",
headers=PF_HEADERS,
timeout=30,
)
pr_res.raise_for_status()
providers = pr_res.json()
if not providers:
raise RuntimeError(f"Blueprint {blueprint_id} icin tedarikci bulunamadi.")
provider_id = providers[0]["id"]

var_res = requests.get(
    f"{BASE}/catalog/blueprints/{blueprint_id}/print_providers/{provider_id}/variants.json",
    headers=PF_HEADERS,
    timeout=30,
)
var_res.raise_for_status()
variants = var_res.json().get("variants", [])
variant_ids = [v["id"] for v in variants if v.get("id")]
return provider_id, variant_ids
def generate_design_bytes(category, idx):
prompts = [
f"Bold street fashion graphic print for a {category}, minimal high-contrast typography and geometric streetwear emblem, clean flat vector-style art on pure black background, sharp edges, no mockup, no text clutter",
f"Retro underground rap album cover inspired graphic design for a {category}, chrome and neon red accent lines, gritty halftone texture on solid black background, flat print artwork only",
f"Minimalist brutalist streetwear motif for a {category}, sharp emblem, white and crimson graphic art on solid black background, high contrast print design",
]
prompt = prompts[(idx - 1) % len(prompts)]

if GEMINI_KEY:
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"imagen-3.0-generate-002:predict?key={GEMINI_KEY}"
    )
    payload = {
        "instances": [{"prompt": prompt}],
        "parameters": {"sampleCount": 1, "aspectRatio": "1:1"},
    }
    try:
        res = requests.post(url, json=payload, timeout=60)
        if res.status_code == 200:
            preds = res.json().get("predictions", [])
            if preds and preds[0].get("bytesBase64Encoded"):
                import base64

                return base64.b64decode(preds[0]["bytesBase64Encoded"])
    except Exception as e:
        print(f"[WARN] Gemini gorsel hatasi ({category} #{idx}): {e}")

img = Image.new("RGB", (2400, 2400), color=(15, 15, 18))
draw = ImageDraw.Draw(img)
accent = (220, 38, 38) if idx % 2 == 0 else (245, 245, 245)
draw.rectangle([300, 300, 2100, 2100], outline=accent, width=24)
draw.line([(300, 1200), (2100, 1200)], fill=accent, width=12)
buf = io.BytesIO()
img.save(buf, format="PNG")
return buf.getvalue()
def upload_image_to_printify(img_bytes, filename):
res = requests.post(
f"{BASE}/uploads/images.json",
headers=PF_HEADERS,
json={
"file_name": filename,
"contents": import("base64").b64encode(img_bytes).decode("utf-8"),
},
timeout=60,
)
res.raise_for_status()
return res.json()["id"]

def create_draft_product(shop_id, title, description, bp_id, provider_id, variant_ids, image_id):
selected_variants = variant_ids[:12] if len(variant_ids) > 12 else variant_ids
variant_objs = [{"id": vid, "price": 2999, "is_enabled": True} for vid in selected_variants]

payload = {
    "title": title,
    "description": description,
    "blueprint_id": bp_id,
    "print_provider_id": provider_id,
    "variants": variant_objs,
    "print_areas": [
        {
            "variant_ids": selected_variants,
            "placeholders": [
                {
                    "position": "front",
                    "images": [
                        {
                            "id": image_id,
                            "x": 0.5,
                            "y": 0.5,
