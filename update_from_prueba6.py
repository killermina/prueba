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
    # Limpieza extra para nombres con variaciones
    name = re.sub(r'[^a-z0-9]', '', name) # Solo dejamos letras y números para cruce ciego
    return name

# 1. Descargar fuente
try:
    response = requests.get(SOURCE_URL)
    source_data = response.json()
except Exception as e:
    print(f"❌ Error descarga: {e}")
    exit()

# 2. Crear mapa
source_map = {}
for src_cat in source_data:
    src_name_raw = src_cat.get("name", "")
    # Buscamos si esta categoría está en nuestro mapeo
    target_title = next((t for t, s in CATEGORY_MAPPING.items() if s.lower() in src_name_raw.lower() or t.lower() in src_name_raw.lower()), None)
    
    if target_title:
        print(f"🔍 Fuente detectada: '{src_name_raw}' mapeada a '{target_title}'")
        for item in src_cat.get("samples", []):
            name_raw = item.get("name", "")
            norm_name = normalize_name(name_raw)
            if norm_name:
                source_map[norm_name] = {
                    "url": item.get("url", "").strip(),
                    "drm": item.get("drm_license_uri", "").strip(),
                    "orig_name": name_raw
                }

# 3. Procesar Local
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

    print(f"\n--- Revisando Categoría Local: {title} ---")
    items = category.get("items", [])
    
    for item in items:
        local_name = item.get("name", "")
        norm_local = normalize_name(local_name)
        
        # DEBUG: Ver qué está comparando
        # print(f"Comparando: {norm_local}") 
        
        if norm_local in source_map:
            new_data = source_map[norm_local]
            changed = False

            if new_data["url"] and new_data["url"] != item.get("url", ""):
                item["url"] = new_data["url"]
                changed = True

            if new_data["drm"] and new_data["drm"] != item.get("drm_license_uri", ""):
                item["drm_license_uri"] = new_data["drm_license_uri"]
                changed = True

            if changed:
                updated_count += 1
                print(f"✅ ¡MATCH! Actualizado: {local_name}")
        else:
            # Descomenta la siguiente línea para ver qué canales NO están encontrando pareja:
            # print(f"❌ No se encontró en fuente: {local_name} (ID: {norm_local})")
            pass

# 4. Guardar
if updated_count > 0:
    with open(TARGET_FILE, 'w', encoding='utf-8') as f:
        json.dump(target, f, ensure_ascii=False, indent=2)
    print(f"\n🚀 Total actualizado: {updated_count} canales.")
else:
    print("\n⚠️ No hubo cambios. Posibles causas:")
    print("1. Los nombres en 'comunJakare.json' no coinciden con 'prueba6.json'.")
    print("2. Las categorías en CATEGORY_MAPPING no coinciden exactamente con los 'title' de tu local.")
    print("3. Las URLs ya eran idénticas.")
