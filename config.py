"""
Konfigurační soubor pro FastCentrik to WooCommerce transformaci
"""

# Cesty k souborům
INPUT_EXCEL_FILE = "Export_Excel_Lite.xls"
OUTPUT_DIRECTORY = "./woocommerce_output/"

# Mapování kategorií - můžete přidat vlastní mapování
CATEGORY_MAPPING_OVERRIDES = {
    # "fastcentrik_category_name": "woocommerce_category_name"
    # "Sporty": "Sport a outdoor",
    # "Pánské": "Muži",
}

# Mapování atributů
ATTRIBUTE_MAPPING = {
    "velikost": "Velikost",
    "barva": "Barva", 
    "pohlavi": "Pohlaví",
    "sport": "Sport",
    "material": "Materiál",
    "zapinani": "Zapínání",
    "technologie": "Technologie",
    "povrch": "Povrch",
    "kategorie_bot": "Kategorie bot",
    "typ_kopacek": "Typ kopaček",
    "kolekce": "Kolekce",
    "trida_kopacek": "Třída kopaček",
    "hmotnost": "Hmotnost",
    "delka_rukavu": "Délka rukávu",
    "strih": "Střih"
}

# SEO nastavení
SEO_SETTINGS = {
    "title_suffix": " | Váš SportShop",
    "meta_desc_template": "Kvalitní {product_name} v kategorii {category}. ✓ Rychlé dodání ✓ Skvělé ceny ✓ Zákaznická podpora",
    "focus_keyword_words": 3  # Počet slov pro focus keyword
}

# URL nastavení pro obrázky
IMAGE_BASE_URL = "https://vase-domena.cz"  # Změňte na vaši doménu

# Nastavení exportu
EXPORT_SETTINGS = {
    "encoding": "utf-8-sig",
    "separator": ",",
    "include_empty_attributes": False,
    "max_attributes_per_product": 3
}

# Nastavení variant
VARIANT_SETTINGS = {
    "create_parent_products": True,
    "variant_attributes": ["velikost", "barva"],  # Hlavní atributy pro varianty
    "parent_name_remove_attrs": ["velikost", "barva"]  # Atributy k odstranění z názvu parent produktu
}

# Nastavení kategorií
CATEGORY_SETTINGS = {
    "create_hierarchy": True,
    "max_depth": 4,
    "default_parent": ""
}

# Nastavení tagů
TAG_SETTINGS = {
    "auto_generate_tags": True,
    "tag_attributes": ["pohlavi", "sport", "material"],
    "max_tags_per_product": 5
}

# Pokročilá nastavení
ADVANCED_SETTINGS = {
    "skip_empty_products": True,
    "validate_prices": True,
    "generate_seo_automatically": True,
    "create_product_variations": True,
    "log_level": "INFO"  # DEBUG, INFO, WARNING, ERROR
}