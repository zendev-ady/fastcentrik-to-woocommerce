# ============================================================================
# batch_transform.py - Dávkové zpracování více souborů
# ============================================================================

#!/usr/bin/env python3
"""
Dávkové zpracování více FastCentrik souborů
"""

import os
import glob
from pathlib import Path
import logging
from transformer import FastCentrikToWooCommerce

def batch_transform(input_dir: str, output_base_dir: str):
    """Dávkové zpracování všech Excel souborů ve složce"""
    
    logger = logging.getLogger(__name__)
    input_path = Path(input_dir)
    
    # Najdeme všechny Excel soubory
    excel_files = list(input_path.glob("*.xls")) + list(input_path.glob("*.xlsx"))
    
    if not excel_files:
        print(f"❌ Ve složce {input_dir} nejsou žádné Excel soubory")
        return
    
    print(f"📁 Nalezeno {len(excel_files)} Excel souborů")
    
    successful = 0
    failed = 0
    
    for excel_file in excel_files:
        try:
            print(f"\n🔄 Zpracovávám: {excel_file.name}")
            
            # Vytvoření výstupní složky pro každý soubor
            file_output_dir = Path(output_base_dir) / excel_file.stem
            file_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Transformace
            transformer = FastCentrikToWooCommerce(str(excel_file))
            transformer.run_transformation(str(file_output_dir))
            
            print(f"✅ {excel_file.name} - dokončeno")
            successful += 1
            
        except Exception as e:
            print(f"❌ {excel_file.name} - chyba: {e}")
            logger.error(f"Chyba při zpracování {excel_file}: {e}")
            failed += 1
    
    print(f"\n📊 SOUHRN DÁVKOVÉHO ZPRACOVÁNÍ:")
    print(f"✅ Úspěšně zpracováno: {successful}")
    print(f"❌ Chyby: {failed}")
    print(f"📁 Výstupní soubory: {output_base_dir}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Dávkové zpracování FastCentrik souborů')
    parser.add_argument('input_dir', help='Složka se vstupními Excel soubory')
    parser.add_argument('--output', '-o', default='./batch_output/', 
                       help='Základní výstupní složka')
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    batch_transform(args.input_dir, args.output)