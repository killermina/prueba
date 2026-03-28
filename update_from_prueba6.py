import json
import requests
import unicodedata
import re

TARGET_FILE = "comunJakare.json"
SOURCE_URL = "https://raw.githubusercontent.com/elvioladordemark/cijefcji/refs/heads/main/prueba6.json"

CATEGORY_MAPPING = {
    "Argentina": "CANALES DE ARGENTINA",
    "INFANTILES 👦": "INFANTILES 👦",
}

def normalize_name(name):
    if not name: return ""
    name = name.lower().strip()
    name = unicodedata.normalize('NFD', name)
    name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
    name = re.sub(r'[^a-z0-9]', '', name) 
    return name

# 1. Descargar y LIMPIAR el JSON (Evita el Invalid control character)
try:
    response = requests.get(SOURCE_URL)
    response.raise_for_status()
    # Limpiamos saltos de línea que rompen el formato
    raw_data = response.text.replace('\n', '').replace('\r', '')
    source_data = json.loads(raw_data)
except Exception as e:
    print(f"❌ Error fuente: {e}")
    exit()

# 2. Crear mapa de actualizaciones
source_map = {}
for src_cat in source_data:
    if not isinstance(src_cat, dict): continue
    src_name = src_cat.get("name", "").strip()
    target_title = next((t for t, s in CATEGORY_MAPPING.items() if s.lower() in src_name.lower() or t.lower() in src_name.lower()), None)
    
    if target_title:
        for item in src_cat.get("samples", []):
            name_raw = item.get("name", "")
            if name_raw:
                norm_name = normalize_name(name_raw)
                # IMPORTANTE: Guardamos con el nombre exacto de la llave
                source_map[norm_name] = {
                    "url": item.get("url", "").strip(),
                    "drm_license_uri": item.get("drm_license_uri", "").strip()
                }

# 3. Cargar y actualizar local
try:
    with open(TARGET_FILE, 'r', encoding='utf-8') as f:
        target = json.load(f)
except Exception as e:
    print(f"❌ Error local: {e}")
    exit()

updated_count = 0
for category in target:
    title = category.get("title")
    if title not in CATEGORY_MAPPING:
        continue

    items = category.get("items", [])
    for item in items:
        norm_local = normalize_name(item.get("name", ""))
        if norm_local in source_map:
            new_data = source_map[norm_local]
            changed = False

            # Actualizar URL
            if new_data.get("url") and new_data["url"] != item.get("url", ""):
                item["url"] = new_data["url"]
                changed = True

            # Actualizar DRM (usando .get para evitar el KeyError)
            new_drm = new_data.get("drm_license_uri", "")
            if new_drm and new_drm != item.get("drm_license_uri", ""):
                item["drm_license_uri"] = new_drm
                changed = True

            if changed:
                updated_count += 1

# 4. Guardar
if updated_count > 0:
    with open(TARGET_FILE, 'w', encoding='utf-8') as f:
        json.dump(target, f, ensure_ascii=False, indent=2)
    print(f"✅ Éxito: Se actualizaron {updated_count} canales.")
else:
    print("⚠️ No hubo cambios.")
