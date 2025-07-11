# ============================================================================
# run_transformation.py - Spouštěcí skript
# ============================================================================

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Spouštěcí skript pro FastCentrik to WooCommerce transformaci

Použití:
    python run_transformation.py
    python run_transformation.py --input "jiný_soubor.xls" --output "./custom_output/"
"""

import argparse
import sys
from pathlib import Path
import logging
from config import INPUT_EXCEL_FILE, OUTPUT_DIRECTORY, ADVANCED_SETTINGS
from data_loader import DataLoader
from transformer import DataTransformer
from csv_exporter import CsvExporter

def setup_logging(level: str = "INFO"):
    """Nastavení logování"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('transformation.log', encoding='utf-8')
        ]
    )

def validate_input_file(file_path: str) -> bool:
    """Validace vstupního souboru"""
    path = Path(file_path)
    
    if not path.exists():
        print(f"❌ Soubor {file_path} neexistuje!")
        return False
    
    if not path.suffix.lower() in ['.xls', '.xlsx']:
        print(f"❌ Soubor {file_path} není Excel soubor!")
        return False
    
    return True

def main():
    """Hlavní funkce"""
    parser = argparse.ArgumentParser(description='FastCentrik to WooCommerce transformace')
    parser.add_argument('--input', '-i', default=INPUT_EXCEL_FILE, 
                       help='Cesta k vstupnímu Excel souboru')
    parser.add_argument('--output', '-o', default=OUTPUT_DIRECTORY,
                       help='Výstupní složka')
    parser.add_argument('--log-level', default=ADVANCED_SETTINGS['log_level'],
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Úroveň logování')
    parser.add_argument('--validate-only', action='store_true',
                       help='Pouze validace bez transformace')
    
    args = parser.parse_args()
    
    # Nastavení logování
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    print("🚀 FastCentrik to WooCommerce Transformátor")
    print("=" * 50)
    
    # Validace vstupního souboru
    if not validate_input_file(args.input):
        sys.exit(1)
    
    print(f"📁 Vstupní soubor: {args.input}")
    print(f"📁 Výstupní složka: {args.output}")
    
    if args.validate_only:
        print("✅ Validace dokončena - soubor je v pořádku")
        return
    
    try:
        # 1. Načtení dat
        loader = DataLoader(args.input)
        data = loader.load_data()
        
        # 2. Transformace dat
        transformer = DataTransformer(
            products_df=data['products'],
            categories_df=data['categories']
        )
        products, categories = transformer.run_transformation()
        
        # 3. Export do CSV
        exporter = CsvExporter()
        output_path = Path(args.output)
        output_path.mkdir(parents=True, exist_ok=True)
        
        exporter.export_products(products, str(output_path))
        exporter.export_categories(categories, str(output_path))
        
        print("\n🎉 TRANSFORMACE ÚSPĚŠNĚ DOKONČENA!")
        print(f"📄 Soubory jsou uloženy v: {args.output}")
        print("\n📋 Další kroky:")
        print("1. Zkontrolujte vygenerované CSV soubory v složce 'woocommerce_output'")
        print("2. Importujte kategorie do WooCommerce (woocommerce_categories.csv)")
        print("3. Importujte produkty do WooCommerce (woocommerce_products.csv)")
        
    except FileNotFoundError:
        # Chyba je již zalogována v DataLoaderu
        sys.exit(1)
    except Exception as e:
        logger.error(f"Došlo k neočekávané chybě během transformace: {e}", exc_info=True)
        print(f"\n❌ Transformace selhala. Zkontrolujte log soubor 'transformation.log' pro detaily.")
        sys.exit(1)
    finally:
        # Zajistí, že se logy vždy zapíší do souboru
        logging.shutdown()

if __name__ == "__main__":
    main()