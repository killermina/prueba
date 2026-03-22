import json
import requests
import re
import unicodedata

TARGET_FILE = "comunJakare.json"  # tu archivo
SOURCE_URL  = "https://raw.githubusercontent.com/elvioladordemark/cijefcji/refs/heads/main/prueba6.json"

def normalize_name(name):
    if not name:
        return ""
    name = unicodedata.normalize('NFD', name.lower().strip())
    name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
    name = re.sub(r'\s+', ' ', name)
    name = name.replace("tv publica", "television publica").replace("america tv", "america television")
    return name

# Descargar fuente
response = requests.get(SOURCE_URL)
response.raise_for_status()
source_data = response.json()

# Cargar tu JSON
with open(TARGET_FILE, 'r', encoding='utf-8') as f:
    target = json.load(f)

source_map = {}
for cat in source_data:
    cat_name = cat.get("name", "")
    samples = cat.get("samples", [])
    for item in samples:
        norm_name = normalize_name(item.get("name", ""))
        if norm_name:
            source_map[norm_name] = {
                "url": item.get("url", ""),
                "drm_license_uri": item.get("drm_license_uri", ""),
                "headers": item.get("headers", None)
            }

updated_count = 0

for cat in target:
    if cat.get("type") == "category" and "items" in cat:
        for item in cat["items"]:
            norm_name = normalize_name(item.get("name", ""))
            if norm_name in source_map:
                new_data = source_map[norm_name]
                changed = False

                if new_data["url"] and new_data["url"] != item.get("url", ""):
                    item["url"] = new_data["url"]
                    changed = True

                if new_data["drm_license_uri"] and new_data["drm_license_uri"] != item.get("drm_license_uri", ""):
                    item["drm_license_uri"] = new_data["drm_license_uri"]
                    changed = True

                if new_data["headers"] and new_data["headers"] != item.get("headers"):
                    item["headers"] = new_data["headers"]
                    changed = True

                if changed:
                    updated_count += 1
                    print(f"Actualizado: {item['name']} en {cat.get('title', 'sin título')}")

if updated_count > 0:
    with open(TARGET_FILE, 'w', encoding='utf-8') as f:
        json.dump(target, f, ensure_ascii=False, indent=2)
    print(f"✅ {updated_count} items actualizados")
else:
    print("No se encontraron coincidencias para actualizar")
