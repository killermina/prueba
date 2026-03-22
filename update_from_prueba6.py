import json
import requests
import re
import unicodedata

TARGET_FILE = "comunJakare.json"
SOURCE_URL = "https://raw.githubusercontent.com/elvioladordemark/cijefcji/refs/heads/main/prueba6.json"

def normalize_name(name):
    if not name:
        return ""
    name = name.lower().strip()
    name = unicodedata.normalize('NFD', name)
    name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
    name = re.sub(r'\s+', ' ', name)
    # Reglas mínimas y estrictas
    name = name.replace("tv pública", "televisión pública")
    name = name.replace("américa tv", "america tv")
    return name

# Descargar fuente
response = requests.get(SOURCE_URL)
response.raise_for_status()
source_data = response.json()

# Mapa solo con nombres normalizados → nuevos url y drm
source_map = {}
for cat in source_data:
    for item in cat.get("samples", []):
        orig_name = item.get("name", "")
        norm_name = normalize_name(orig_name)
        if norm_name:
            source_map[norm_name] = {
                "url": item.get("url"),
                "drm_license_uri": item.get("drm_license_uri")
            }

# Cargar tu JSON
with open(TARGET_FILE, 'r', encoding='utf-8') as f:
    target = json.load(f)

updated = False
updated_items = []

for category in target:
    if category.get("type") == "category" and "items" in category:
        for item in category["items"]:
            orig_name = item.get("name", "")
            norm_name = normalize_name(orig_name)
            
            if norm_name in source_map:
                new_data = source_map[norm_name]
                changed = False
                
                current_url = item.get("url")
                current_drm = item.get("drm_license_uri")
                
                if new_data["url"] and new_data["url"] != current_url:
                    item["url"] = new_data["url"]
                    changed = True
                
                if new_data["drm_license_uri"] and new_data["drm_license_uri"] != current_drm:
                    item["drm_license_uri"] = new_data["drm_license_uri"]
                    changed = True
                
                if changed:
                    updated = True
                    updated_items.append(orig_name)

# Guardar SOLO si hubo cambios reales
if updated:
    with open(TARGET_FILE, 'w', encoding='utf-8') as f:
        json.dump(target, f, ensure_ascii=False, indent=2, sort_keys=False)  # sort_keys=False para no cambiar orden
    print(f"✅ Actualizados {len(updated_items)} items: {', '.join(updated_items)}")
else:
    print("No se encontraron cambios válidos")
