import json
import requests
import unicodedata
import re

TARGET_FILE = "comunJakare.json"
SOURCE_URL = "https://raw.githubusercontent.com/elvioladordemark/cijefcji/refs/heads/main/prueba6.json"

CATEGORY_MAPPING = {
    "Argentina": "CANALES DE ARGENTINA",
    "INFANTILES 👦": "INFANTILES 👦",
    "⚽ FOX SPORTS ⚽": "⚽DEPORTES ESPN Y FOX SPORTS ​🇦🇷",
    "⚽TyC SPORTS⚽": "⚽🇦🇷PACK FUTBOL ARGENTINO",
    "🎬 Cultura y Cocina": "CULTURA Y COCINA 🐢",
    "⚽EVENTOS FLOW COPA DEL REY⚽": "⚽EVENTOS FLOW COPA DEL REY⚽",
}

def normalize_name(name):
    if not name: return ""
    name = name.lower().strip()
    name = unicodedata.normalize('NFD', name)
    name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
    name = re.sub(r'[^a-z0-9]', '', name) 
    return name

# 1. Descargar y LIMPIAR el JSON
try:
    response = requests.get(SOURCE_URL)
    response.raise_for_status()
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
                source_map[norm_name] = {
                    "url": item.get("url", "").strip(),
                    "drm_license_uri": item.get("drm_license_uri", "").strip()
                }

# 3. Cargar local
try:
    with open(TARGET_FILE, 'r', encoding='utf-8') as f:
        target = json.load(f)
except Exception as e:
    print(f"❌ Error local: {e}")
    exit()

# --- CAMBIO AQUÍ: Lista para guardar nombres actualizados ---
updated_count = 0
list_updated_names = [] 

for category in target:
    title = category.get("title")
    if title not in CATEGORY_MAPPING:
        continue

    items = category.get("items", [])
    for item in items:
        original_name = item.get("name", "Desconocido")
        norm_local = normalize_name(original_name)
        
        if norm_local in source_map:
            new_data = source_map[norm_local]
            changed = False

            if new_data.get("url") and new_data["url"] != item.get("url", ""):
                item["url"] = new_data["url"]
                changed = True

            new_drm = new_data.get("drm_license_uri", "")
            if new_drm and new_drm != item.get("drm_license_uri", ""):
                item["drm_license_uri"] = new_drm
                changed = True

            if changed:
                updated_count += 1
                list_updated_names.append(original_name)

# 4. Guardar y Reportar
if updated_count > 0:
    with open(TARGET_FILE, 'w', encoding='utf-8') as f:
        json.dump(target, f, ensure_ascii=False, indent=2)
    
    # Este formato lo leerá el bot de Telegram perfectamente
    print(f"✅ *Actualización Exitosa*")
    print(f"Total: {updated_count} canales.")
    print("-------------------------")
    for name in list_updated_names:
        print(f"📺 {name}")
else:
    print("⚠️ *Sin cambios detectados*")
    print("Todos los canales coinciden con la fuente.")
