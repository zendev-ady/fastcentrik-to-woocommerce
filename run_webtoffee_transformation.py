#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebToffee Transformation Runner
===============================

Skript pro spuštění transformace FastCentrik dat do WebToffee CSV formátu.

Použití:
    python run_webtoffee_transformation.py

Vstupní soubor: Export_Excel_Lite.xls (musí být v aktuální složce)
Výstup: webtoffee_output/

Autor: FastCentrik Migration Tool
"""

import sys
from pathlib import Path
from datetime import datetime

# Přidání projektu do Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.fastcentrik_woocommerce.loaders.data_loader import DataLoader
from src.fastcentrik_woocommerce.core.webtoffee_transformer import WebToffeeTransformer
from src.fastcentrik_woocommerce.exporters.webtoffee_csv_exporter import WebToffeeCSVExporter
from src.fastcentrik_woocommerce.utils.logging_config import get_transformation_logger

# Nastavení logování s novou konfigurací
logger = get_transformation_logger(__name__, "webtoffee")

# Konstanty
INPUT_FILE = "Export_Excel_Lite.xls"
OUTPUT_DIR = "webtoffee_output"


def main():
    """Hlavní funkce pro spuštění transformace."""
    # Kontrola vstupního souboru
    input_path = Path(INPUT_FILE)
    if not input_path.exists():
        logger.error(f"Vstupní soubor neexistuje: {INPUT_FILE}")
        logger.error("Umístěte soubor Export_Excel_Lite.xls do aktuální složky a spusťte znovu.")
        sys.exit(1)
    
    logger.info("="*60)
    logger.info("WEBTOFFEE TRANSFORMACE - START")
    logger.info("="*60)
    logger.info(f"Vstupní soubor: {input_path}")
    logger.info(f"Výstupní adresář: {OUTPUT_DIR}")
    
    try:
        # 1. Načtení dat
        logger.info("\n1. NAČÍTÁNÍ DAT")
        logger.info("-" * 40)
        loader = DataLoader(str(input_path))
        data = loader.load_data()
        
        products_df = data['products']
        categories_df = data['categories']
        # parameters_df = data['parameters']  # Není potřeba pro WebToffee transformaci
        
        logger.info(f"Načteno {len(products_df)} produktů")
        logger.info(f"Načteno {len(categories_df)} kategorií")
        
        # 2. Transformace dat
        logger.info("\n2. TRANSFORMACE DAT")
        logger.info("-" * 40)
        transformer = WebToffeeTransformer(products_df, categories_df)
        woo_products, validation_errors = transformer.run_transformation()
        
        # 3. Export dat
        logger.info("\n3. EXPORT DAT")
        logger.info("-" * 40)
        exporter = WebToffeeCSVExporter(OUTPUT_DIR)
        
        # Export produktů
        exported_files = exporter.export_products(woo_products)
        
        logger.info("\nVytvořené soubory:")
        for file in exported_files:
            logger.info(f"  - {file}")
        
        # Vždy vytvoříme ukázkový soubor
        sample_file = exporter.export_sample(woo_products, sample_size=20)
        logger.info(f"\nUkázkový soubor (prvních 20 produktů): {sample_file}")
        
        # Vytvoření šablony
        template_file = exporter.create_import_template()
        logger.info(f"\nImport šablona: {template_file}")
        
        # 4. Souhrn
        logger.info("\n" + "="*60)
        logger.info("SOUHRN TRANSFORMACE")
        logger.info("="*60)
        
        # Statistiky produktů
        simple_count = len([p for p in woo_products if p['tax:product_type'] == 'simple'])
        variable_count = len([p for p in woo_products if p['tax:product_type'] == 'variable'])
        variation_count = len([p for p in woo_products if p['tax:product_type'] == 'variation'])
        
        logger.info(f"Celkem produktů: {len(woo_products)}")
        logger.info(f"  - Jednoduché: {simple_count}")
        logger.info(f"  - Variable: {variable_count}")
        logger.info(f"  - Varianty: {variation_count}")
        
        # Validační chyby
        if validation_errors:
            logger.warning(f"\nValidační chyby: {len(validation_errors)}")
            for i, error in enumerate(validation_errors[:10], 1):
                logger.warning(f"  {i}. {error}")
            if len(validation_errors) > 10:
                logger.warning(f"  ... a dalších {len(validation_errors) - 10} chyb")
        else:
            logger.info("\n✓ Žádné validační chyby")
        
        # Instrukce pro import
        logger.info("\n" + "="*60)
        logger.info("INSTRUKCE PRO IMPORT DO WOOCOMMERCE")
        logger.info("="*60)
        logger.info("1. Nainstalujte plugin 'Product Import Export for WooCommerce' od WebToffee")
        logger.info("2. V administraci WooCommerce přejděte na: WooCommerce > WebToffee Import Export > Import")
        logger.info("3. Vyberte 'Product' jako typ importu")
        logger.info("4. Nahrajte vytvořený CSV soubor")
        logger.info("5. Mapování sloupců by mělo být automatické díky správným názvům")
        logger.info("6. Pro variable produkty importujte nejdříve soubor s '_all' nebo '_variable'")
        logger.info("\nTIP: Nejprve vyzkoušejte import s ukázkovým souborem!")
        
        logger.info("\n" + "="*60)
        logger.info("TRANSFORMACE DOKONČENA ÚSPĚŠNĚ")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"\nCHYBA: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()