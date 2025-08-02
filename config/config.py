"""
Konfigurační soubor pro FastCentrik to WooCommerce transformaci
Verze 2.0 - s vylepšeními pro variabilní produkty a skladové zásoby
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

# NOVÉ: Nastavení pro inteligentní mapování kategorií
CATEGORY_MAPPING_SETTINGS = {
    "use_intelligent_mapping": True,  # Použít nový inteligentní systém mapování
    "fallback_to_original": True,    # Použít původní kategorii jako fallback
    "default_category": "",           # Výchozí kategorie pro nenamapované produkty
    "log_unmapped_products": True,    # Logovat produkty, které nebyly namapovány
    "export_mapping_report": True,    # Exportovat report mapování
    "mapping_priority": [             # Priorita zdrojů pro mapování
        "intelligent",                # 1. Inteligentní mapování podle pravidel
        "manual_override",            # 2. Manuální přepisy
        "original_category"           # 3. Původní kategorie
    ],
    "parameter_weights": {            # Váhy parametrů pro mapování
        "pohlavi": 10,
        "sport": 9,
        "typ": 8,
        "povrch": 7,
        "znacka": 5
    },
    # Nastavení pro multi-kategorie
    "enable_multi_category": True,    # Povolit přiřazení do více kategorií
    "max_categories_per_product": 3,  # Maximální počet kategorií na produkt (zvýšeno pro unisex produkty)
    "multi_category_separator": " | ", # Oddělovač pro více kategorií v CSV (WooCommerce standard)
    "validate_categories": True,      # Validovat existenci kategorií před přiřazením
    "multi_category_strategy": "complementary",  # Strategie: "complementary" nebo "all_matches"
    "use_leaf_category_only": False  # Použít celou cestu kategorie pro lepší rozlišení
}

# Mapování atributů - DŮLEŽITÉ pro správné zobrazení variant
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
    "strih": "Střih",
    "vyrobce": "Výrobce",
    "znacka": "Značka"
}

# SEO nastavení
SEO_SETTINGS = {
    "title_suffix": " | Váš SportShop",
    "meta_desc_template": "Kvalitní {product_name} v kategorii {category}. ✓ Rychlé dodání ✓ Skvělé ceny ✓ Zákaznická podpora",
    "focus_keyword_words": 3  # Počet slov pro focus keyword
}

# URL nastavení pro obrázky
IMAGE_BASE_URL = "https://storage.googleapis.com/sportovni-eshop-produkty-fotky"

# Nastavení exportu
EXPORT_SETTINGS = {
    "encoding": "utf-8-sig",
    "separator": ",",
    "include_empty_attributes": False,
    "max_attributes_per_product": 3
}

# Nastavení variant - KLÍČOVÉ pro správnou funkci variabilních produktů
VARIANT_SETTINGS = {
    "create_parent_products": True,
    "variant_attributes": ["velikost", "barva"],  # Hlavní atributy pro varianty
    "parent_name_remove_attrs": ["velikost", "barva"],  # Atributy k odstranění z názvu parent produktu
    "inherit_parent_data": True,  # Varianty zdědí data z parent produktu
    "sync_stock_status": True,  # Synchronizovat stock status mezi parent a variantami
}

# NOVÉ: Nastavení skladových zásob
STOCK_SETTINGS = {
    "enable_backorders": False,  # Povolit objednávky při vyprodání
    "low_stock_threshold": 5,     # Práh pro nízké zásoby
    "manage_stock_for_variations": True,  # Řídit zásoby pro varianty
    "manage_stock_for_simple": True,      # Řídit zásoby pro jednoduché produkty
    "default_stock_status": "instock",    # Výchozí stav skladu
    "stock_status_mapping": {
        0: "outofstock",
        1: "onbackorder",  # pokud backorders povoleny
        "default": "instock"
    },
    "notify_on_low_stock": True,  # Notifikace při nízkých zásobách
    "hide_out_of_stock": False,   # Skrýt vyprodané produkty
}

# Nastavení kategorií
CATEGORY_SETTINGS = {
    "create_hierarchy": True,
    "max_depth": 4,
    "default_parent": "",
    "auto_create_missing": True,  # Automaticky vytvořit chybějící kategorie
    "category_separator": " > ",  # Oddělovač pro hierarchii kategorií
}

# Nastavení tagů
TAG_SETTINGS = {
    "auto_generate_tags": True,
    "tag_attributes": ["pohlavi", "sport", "material", "znacka"],
    "max_tags_per_product": 5,
    "tag_separator": ", ",
    "normalize_tags": True,  # Normalizovat tagy (malá písmena, bez diakritiky)
}

# Nastavení validace
VALIDATION_SETTINGS = {
    "validate_before_export": True,
    "stop_on_errors": False,  # Zastavit při nalezení chyb
    "max_errors_to_display": 20,
    "validate_images": True,
    "validate_prices": True,
    "validate_stock": True,
    "min_price": 0,
    "max_price": 999999,
}

# Pokročilá nastavení
ADVANCED_SETTINGS = {
    "skip_empty_products": True,
    "validate_prices": True,
    "generate_seo_automatically": True,
    "create_product_variations": True,
    "log_level": "INFO",  # DEBUG, INFO, WARNING, ERROR
    "batch_size": 1000,  # Počet produktů zpracovaných najednou
    "memory_optimization": True,  # Optimalizace paměti pro velké soubory
}

# Nastavení pro import do WooCommerce
WOOCOMMERCE_IMPORT_SETTINGS = {
    "update_existing": True,  # Aktualizovat existující produkty
    "skip_existing": False,   # Přeskočit existující produkty
    "matching_field": "sku",  # Pole pro párování (sku, id, slug)
    "import_images": True,
    "download_images": False,  # Stáhnout obrázky lokálně
    "recalculate_attributes": True,
    "create_taxonomies": True,  # Vytvořit chybějící taxonomie
}

# Debug nastavení
DEBUG_SETTINGS = {
    "save_intermediate_files": False,  # Ukládat mezivýsledky
    "print_product_structure": True,   # Vypsat strukturu produktů
    "export_validation_report": True,  # Exportovat validační report
    "sample_size": 10,  # Počet produktů pro debug výpis
}