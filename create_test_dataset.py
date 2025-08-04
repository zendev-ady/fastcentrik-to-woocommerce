#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skript pro vytvoření testovacího datasetu s omezeným počtem produktů
který pokrývá různé druhy produktů a kategorie.
"""

import pandas as pd
import sys
from pathlib import Path
import logging
import shutil

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from config.config import INPUT_EXCEL_FILE

# Nastavení logování
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_dataset(input_file: str, output_file: str, target_count: int = 50):
    """
    Vytvoří testovací dataset s omezeným počtem produktů.
    
    Args:
        input_file: Cesta k původnímu Excel souboru
        output_file: Cesta pro uložení testovacího souboru
        target_count: Cílový počet produktů (default: 50)
    """
    logger.info(f"Načítám data z {input_file}")
    
    # Načtení všech listů
    excel_file = pd.ExcelFile(input_file)
    sheets_data = {}
    
    # Načtení listu s produkty
    products_df = pd.read_excel(excel_file, sheet_name='Zbozi')
    logger.info(f"Načteno {len(products_df)} produktů")
    
    # Analýza produktů
    logger.info("Analyzuji strukturu produktů...")
    
    # 1. Detekce variant (produkty s podtržítkem v SKU)
    products_df['is_variant'] = products_df['KodZbozi'].astype(str).str.contains('_\d+$', regex=True)
    products_df['base_sku'] = products_df['KodZbozi'].astype(str).str.replace('_\d+$', '', regex=True)
    
    # 2. Skupiny variant
    variant_groups = products_df[products_df['is_variant']].groupby('base_sku').size()
    logger.info(f"Nalezeno {len(variant_groups)} skupin variant")
    
    # 3. Jednoduché produkty (nejsou součástí variant)
    simple_products = products_df[~products_df['is_variant'] & ~products_df['KodZbozi'].isin(variant_groups.index)]
    logger.info(f"Nalezeno {len(simple_products)} jednoduchých produktů")
    
    # 4. Analýza kategorií
    categories_in_products = products_df['InetrniKodyKategorii'].dropna().unique()
    logger.info(f"Produkty jsou v {len(categories_in_products)} různých kategoriích")
    
    # 5. Analýza parametrů pro zjištění druhů produktů
    params_sample = products_df['HodnotyParametru'].dropna().head(100)
    sports = set()
    types = set()
    
    for params in params_sample:
        if 'sport:' in str(params):
            sport = str(params).split('sport:')[1].split(';')[0].strip()
            sports.add(sport)
        if 'typ:' in str(params):
            typ = str(params).split('typ:')[1].split(';')[0].strip()
            types.add(typ)
    
    logger.info(f"Nalezené sporty: {list(sports)[:10]}")
    logger.info(f"Nalezené typy: {list(types)[:10]}")
    
    # Výběr produktů pro testovací dataset
    selected_products = []
    
    # 1. Vybereme několik skupin variant (cca 20 produktů)
    variant_groups_sorted = variant_groups.sort_values(ascending=False)
    selected_variant_groups = 0
    
    for base_sku, count in variant_groups_sorted.items():
        if selected_variant_groups >= 5:  # Max 5 skupin variant
            break
        
        # Přidáme všechny produkty této skupiny
        group_products = products_df[
            (products_df['base_sku'] == base_sku) | 
            (products_df['KodZbozi'] == base_sku)
        ]
        selected_products.extend(group_products.index.tolist())
        selected_variant_groups += 1
        logger.info(f"Přidána skupina variant {base_sku} ({len(group_products)} produktů)")
    
    # 2. Vybereme jednoduché produkty z různých kategorií
    remaining_slots = target_count - len(selected_products)
    
    # Pokusíme se vybrat produkty rovnoměrně z různých kategorií
    if remaining_slots > 0:
        # Seskupíme jednoduché produkty podle kategorie
        simple_by_category = simple_products.groupby('InetrniKodyKategorii')
        
        # Vybereme po jednom produktu z každé kategorie
        for category, group in simple_by_category:
            if len(selected_products) >= target_count:
                break
            if len(group) > 0:
                # Vybereme první produkt z kategorie
                selected_products.append(group.index[0])
        
        # Pokud stále nemáme dost produktů, přidáme zbývající
        if len(selected_products) < target_count:
            remaining_simple = simple_products[~simple_products.index.isin(selected_products)]
            additional_count = min(target_count - len(selected_products), len(remaining_simple))
            if additional_count > 0:
                selected_products.extend(remaining_simple.head(additional_count).index.tolist())
    
    # Vytvoření finálního datasetu
    test_products = products_df.loc[selected_products].copy()
    logger.info(f"Vybráno celkem {len(test_products)} produktů")
    
    # Statistiky výběru
    logger.info("\n=== STATISTIKY TESTOVACÍHO DATASETU ===")
    logger.info(f"Celkem produktů: {len(test_products)}")
    logger.info(f"Jednoduché produkty: {len(test_products[~test_products['is_variant'] & ~test_products['KodZbozi'].isin(variant_groups.index)])}")
    logger.info(f"Varianty: {len(test_products[test_products['is_variant']])}")
    logger.info(f"Parent produkty variant: {len(test_products[test_products['KodZbozi'].isin(variant_groups.index)])}")
    logger.info(f"Počet kategorií: {len(test_products['InetrniKodyKategorii'].dropna().unique())}")
    
    # Odstranění pomocných sloupců
    test_products = test_products.drop(columns=['is_variant', 'base_sku'])
    
    # Načtení ostatních listů (kategorie, parametry)
    for sheet_name in excel_file.sheet_names:
        if sheet_name != 'Zbozi':
            sheets_data[sheet_name] = pd.read_excel(excel_file, sheet_name=sheet_name)
    
    # Uložení testovacího datasetu
    logger.info(f"\nUkládám testovací dataset do {output_file}")
    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        # Uložit produkty
        test_products.to_excel(writer, sheet_name='Zbozi', index=False)
        
        # Uložit ostatní listy
        for sheet_name, df in sheets_data.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    logger.info("Testovací dataset úspěšně vytvořen!")
    
    # Vytvoření zálohy původního souboru
    backup_file = f"{INPUT_EXCEL_FILE}.backup"
    if not Path(backup_file).exists():
        shutil.copy(INPUT_EXCEL_FILE, backup_file)
        logger.info(f"Vytvořena záloha původního souboru: {backup_file}")
    
    return test_products

def main():
    """Hlavní funkce"""
    # Cesty k souborům
    input_file = INPUT_EXCEL_FILE
    output_file = "test_dataset_50_products.xls"
    
    # Kontrola existence vstupního souboru
    if not Path(input_file).exists():
        logger.error(f"Vstupní soubor {input_file} neexistuje!")
        sys.exit(1)
    
    # Vytvoření testovacího datasetu
    test_products = create_test_dataset(input_file, output_file, target_count=50)
    
    print("\n" + "="*60)
    print("TESTOVACÍ DATASET PŘIPRAVEN!")
    print("="*60)
    print(f"Soubor: {output_file}")
    print(f"Počet produktů: {len(test_products)}")
    print("\nNyní můžete spustit transformaci s testovacím datasetem:")
    print(f"python run_transformation.py --input {output_file}")
    print("="*60)

if __name__ == "__main__":
    main()