import json
import requests
import unicodedata
import re

TARGET_FILE = "comunJakare.json"
SOURCE_URL = "https://raw.githubusercontent.com/elvioladordemark/cijefcji/refs/heads/main/prueba6.json"

# ================== AGREGA AQUÍ LAS CATEGORÍAS QUE QUIERES ACTUALIZAR ==================
CATEGORY_MAPPING = {
    "Argentina": "CANALES DE ARGENTINA",
    "INFANTILES 👦": "INFANTILES 👦",           # ← Agregada aquí
    # "Paraguay": "PARAGUAY GLOBAL 🇵🇾",
    # "LANC TV": "⚽LANC TV⚽",
}

def normalize_name(name):
    if not name:
        return ""
    name = name.lower().strip()
    name = unicodedata.normalize('NFD', name)
    name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
    name = re.sub(r'\s+', ' ', name)
    name = name.replace("tv pública", "televisión pública").replace("tv publica", "televisión pública")
    name = name.replace("américa tv", "america tv").replace("america television", "america tv")
    name = name.replace("el trece", "trece")
    return name

# Descargar fuente
response = requests.get(SOURCE_URL)
response.raise_for_status()
source_data = response.json()

# Crear mapa de actualizaciones
source_map = {}
for src_cat in source_data:
    src_name = src_cat.get("name", "").strip()
    target_title = next((t for t, s in CATEGORY_MAPPING.items() if s.lower() in src_name.lower() or t.lower() in src_name.lower()), None)
    
    if target_title:
        print(f"✓ Categoría encontrada en fuente: {src_name} → se actualizará '{target_title}'")
        for item in src_cat.get("samples", []):
            norm_name = normalize_name(item.get("name", ""))
            if norm_name:
                source_map[norm_name] = {
                    "url": item.get("url", ""),
                    "drm_license_uri": item.get("drm_license_uri", "")
                }

# Cargar tu JSON
with open(TARGET_FILE, 'r', encoding='utf-8') as f:
    target = json.load(f)

updated_count = 0
updated_categories = []

for category in target:
    title = category.get("title")
    if title not in CATEGORY_MAPPING:
        continue

    print(f"\nProcesando categoría: {title}")
    items = category.get("items", [])
    cat_updated = 0

    for item in items:
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

            if changed:
                updated_count += 1
                cat_updated += 1
                print(f"   → Actualizado: {item.get('name')}")

    if cat_updated > 0:
        updated_categories.append(f"{title} ({cat_updated} items)")

# Guardar cambios
if updated_count > 0:
    with open(TARGET_FILE, 'w', encoding='utf-8') as f:
        json.dump(target, f, ensure_ascii=False, indent=2, sort_keys=False)
    print(f"\n✅ ¡Éxito! Se actualizaron {updated_count} items en total:")
    for cat in updated_categories:
        print(f"   • {cat}")
else:
    print("\nNo se encontraron cambios en las categorías configuradas.")
