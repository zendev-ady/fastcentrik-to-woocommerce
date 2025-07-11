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
from config import *

# Import hlavního transformátoru (předpokládáme, že je v souboru transformer.py)
try:
    from transformer import FastCentrikToWooCommerce
except ImportError:
    print("❌ Chyba: Nelze importovat FastCentrikToWooCommerce")
    print("   Ujistěte se, že máte soubor transformer.py ve stejné složce")
    sys.exit(1)

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
        # Vytvoření výstupní složky
        Path(args.output).mkdir(parents=True, exist_ok=True)
        
        # Spuštění transformace
        transformer = FastCentrikToWooCommerce(args.input)
        transformer.run_transformation(args.output)
        
        print("\n🎉 TRANSFORMACE ÚSPĚŠNĚ DOKONČENA!")
        print(f"📄 Soubory jsou uloženy v: {args.output}")
        print("\n📋 Další kroky:")
        print("1. Zkontrolujte vygenerované CSV soubory")
        print("2. Importujte kategorie do WooCommerce (woocommerce_categories.csv)")
        print("3. Importujte produkty do WooCommerce (woocommerce_products.csv)")
        
    except Exception as e:
        logger.error(f"Chyba během transformace: {e}")
        print(f"\n❌ Transformace selhala: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()