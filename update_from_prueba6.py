import json
import requests
import unicodedata
import re

TARGET_FILE = "comunJakare.json"
SOURCE_URL = "https://raw.githubusercontent.com/elvioladordemark/cijefcji/refs/heads/main/prueba6.json"
TARGET_CATEGORY_TITLE = "Argentina"  # ← Cambia aquí si quieres otra categoría, ej: "🇵🇾PARAGUAY🇵🇾"

def normalize_name(name):
    if not name:
        return ""
    name = name.lower().strip()
    name = unicodedata.normalize('NFD', name)
    name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
    name = re.sub(r'\s+', ' ', name)
    # Reglas para coincidir mejor (ajusta según necesites)
    name = name.replace("tv pública", "televisión pública").replace("tv publica", "televisión pública")
    name = name.replace("américa tv", "america tv").replace("america television", "america tv")
    name = name.replace("telefe", "telefe").replace("el trece", "trece")
    return name

# Descargar fuente
response = requests.get(SOURCE_URL)
response.raise_for_status()
source_data = response.json()

# Mapa solo de la categoría relevante en el fuente
source_map = {}
found_source_cat = False
for cat in source_data:
    cat_name = cat.get("name", "").strip()
    if "argentina" in cat_name.lower():  # Busca "CANALES DE ARGENTINA" o similar
        found_source_cat = True
        for item in cat.get("samples", []):
            norm_name = normalize_name(item.get("name", ""))
            if norm_name:
                source_map[norm_name] = {
                    "url": item.get("url", ""),
                    "drm_license_uri": item.get("drm_license_uri", "")
                }
        break  # Solo tomamos la primera categoría que coincida

if not found_source_cat:
    print("No se encontró categoría con 'argentina' en el fuente → no se actualiza nada")
else:
    print(f"Encontrada categoría fuente con {len(source_map)} items potenciales")

# Cargar tu JSON
with open(TARGET_FILE, 'r', encoding='utf-8') as f:
    target = json.load(f)

updated = False
updated_count = 0
updated_names = []

# Solo procesar la categoría específica
for category in target:
    if category.get("type") == "category" and category.get("title") == TARGET_CATEGORY_TITLE:
        print(f"Procesando categoría '{TARGET_CATEGORY_TITLE}' con {len(category.get('items', []))} items originales")
        for item in category.get("items", []):
            norm_name = normalize_name(item.get("name", ""))
            if norm_name in source_map:
                new_data = source_map[norm_name]
                changed = False

                if new_data["url"] and new_data["url"] != item.get("url", ""):
                    old_url = item.get("url", "ninguna")
                    item["url"] = new_data["url"]
                    changed = True
                    print(f"  - Actualizado url en '{item.get('name')}': {old_url[:50]}... → {new_data['url'][:50]}...")

                if new_data["drm_license_uri"] and new_data["drm_license_uri"] != item.get("drm_license_uri", ""):
                    old_drm = item.get("drm_license_uri", "ninguna")
                    item["drm_license_uri"] = new_data["drm_license_uri"]
                    changed = True
                    print(f"  - Actualizado drm en '{item.get('name')}': {old_drm[:50]}... → {new_data['drm_license_uri'][:50]}...")

                if changed:
                    updated = True
                    updated_count += 1
                    updated_names.append(item.get("name", "sin nombre"))

        break  # No necesitamos seguir buscando categorías

if updated:
    with open(TARGET_FILE, 'w', encoding='utf-8') as f:
        json.dump(target, f, ensure_ascii=False, indent=2, sort_keys=False)
    print(f"✅ Actualizados {updated_count} items en '{TARGET_CATEGORY_TITLE}': {', '.join(updated_names)}")
else:
    print(f"No hubo cambios válidos en '{TARGET_CATEGORY_TITLE}'")
