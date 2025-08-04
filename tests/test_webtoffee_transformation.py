#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test WebToffee Transformation
=============================

Testuje správnost transformace do WebToffee formátu.

Autor: FastCentrik Migration Tool
"""

import sys
from pathlib import Path
import pandas as pd
import logging

# Přidání projektu do Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.fastcentrik_woocommerce.core.webtoffee_transformer import WebToffeeTransformer
from src.fastcentrik_woocommerce.exporters.webtoffee_csv_exporter import WebToffeeCSVExporter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_test_data():
    """Vytvoří testovací data pro transformaci."""
    
    # Testovací produkty
    products_data = {
        'KodZbozi': ['PROD001', 'SHOE001', 'SHOE001_2', 'SHOE001_3', 'TSHIRT001'],
        'JmenoZbozi': ['Jednoduchý produkt', 'Běžecké boty', 'Běžecké boty 42', 'Běžecké boty 43', 'Tričko modré'],
        'KodMasterVyrobku': ['', 'SHOE001', 'SHOE001', 'SHOE001', ''],
        'Popis': ['Popis produktu', 'Kvalitní běžecké boty', 'Kvalitní běžecké boty', 'Kvalitní běžecké boty', 'Bavlněné tričko'],
        'KratkyPopis': ['Krátký popis', 'Běžecké boty pro sport', 'Běžecké boty pro sport', 'Běžecké boty pro sport', 'Pohodlné tričko'],
        'CenaBezna': [1000, 2500, 2500, 2500, 500],
        'ZakladniCena': [900, 2200, 2200, 2200, 500],
        'NaSklade': [50, 0, 10, 5, 100],
        'Vypnuto': [0, 0, 0, 0, 1],
        'HlavniObrazek': ['prod001.jpg', 'shoe001.jpg', 'shoe001.jpg', 'shoe001.jpg', 'tshirt001.jpg'],
        'DalsiObrazky': ['prod001_2.jpg;prod001_3.jpg', '', '', '', 'tshirt001_2.jpg'],
        'InetrniKodyKategorii': ['CAT001', 'CAT002', 'CAT002', 'CAT002', 'CAT003'],
        'HodnotyParametru': ['material||bavlna##barva||černá', '', 'velikost||42', 'velikost||43', 'barva||modrá##velikost||L'],
        'Hmotnost': ['0,5', '0,8', '0,8', '0,8', '0,2']
    }
    
    # Testovací kategorie
    categories_data = {
        'InterniKod': ['CAT001', 'CAT002', 'CAT003', 'CAT004'],
        'JmenoKategorie': ['Elektronika', 'Obuv', 'Oblečení', 'Sport'],
        'KodNadrizeneKategorie': ['ROOT_1', 'CAT004', 'ROOT_1', 'ROOT_1'],
        'PopisKategorie': ['Elektronické produkty', 'Sportovní obuv', 'Oblečení a móda', 'Sportovní potřeby']
    }
    
    products_df = pd.DataFrame(products_data)
    categories_df = pd.DataFrame(categories_data)
    
    return products_df, categories_df


def test_webtoffee_format():
    """Testuje správnost WebToffee formátu."""
    logger.info("=== TEST WEBTOFFEE FORMÁTU ===")
    
    # Vytvoření testovacích dat
    products_df, categories_df = create_test_data()
    
    # Transformace
    transformer = WebToffeeTransformer(products_df, categories_df)
    woo_products, validation_errors = transformer.run_transformation()
    
    # Testy
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Počet produktů
    logger.info("\nTest 1: Kontrola počtu produktů")
    expected_count = 6  # 2 simple + 1 variable + 3 variations
    if len(woo_products) == expected_count:
        logger.info(f"✓ Správný počet produktů: {len(woo_products)}")
        tests_passed += 1
    else:
        logger.error(f"✗ Nesprávný počet produktů: {len(woo_products)}, očekáváno: {expected_count}")
        tests_failed += 1
    
    # Test 2: Kontrola parent_sku
    logger.info("\nTest 2: Kontrola parent_sku pro varianty")
    variations = [p for p in woo_products if p['tax:product_type'] == 'variation']
    parent_sku_ok = all(p.get('parent_sku') == 'SHOE001_parent' for p in variations)
    if parent_sku_ok:
        logger.info("✓ Všechny varianty mají správný parent_sku")
        tests_passed += 1
    else:
        logger.error("✗ Některé varianty nemají správný parent_sku")
        tests_failed += 1
    
    # Test 3: Kontrola taxonomií s prefixem
    logger.info("\nTest 3: Kontrola taxonomy prefixů")
    taxonomy_ok = all(
        'tax:product_type' in p and 
        'tax:product_cat' in p 
        for p in woo_products
    )
    if taxonomy_ok:
        logger.info("✓ Všechny produkty mají správné taxonomy prefixy")
        tests_passed += 1
    else:
        logger.error("✗ Některé produkty nemají správné taxonomy prefixy")
        tests_failed += 1
    
    # Test 4: Kontrola atributů
    logger.info("\nTest 4: Kontrola formátu atributů")
    variable_product = next((p for p in woo_products if p['tax:product_type'] == 'variable'), None)
    if variable_product:
        has_correct_attrs = (
            'attribute:velikost' in variable_product and
            'attribute_data:velikost' in variable_product and
            'attribute_default:velikost' in variable_product
        )
        if has_correct_attrs:
            logger.info("✓ Variable produkt má správný formát atributů")
            tests_passed += 1
        else:
            logger.error("✗ Variable produkt nemá správný formát atributů")
            tests_failed += 1
    
    # Test 5: Kontrola obrázků
    logger.info("\nTest 5: Kontrola formátu obrázků")
    simple_product = next((p for p in woo_products if p['sku'] == 'PROD001'), None)
    if simple_product and '|' in simple_product.get('Images', ''):
        logger.info("✓ Obrázky jsou správně oddělené pipe symbolem")
        tests_passed += 1
    else:
        logger.error("✗ Obrázky nejsou správně formátované")
        tests_failed += 1
    
    # Test 6: Kontrola cen
    logger.info("\nTest 6: Kontrola formátu cen")
    price_ok = all(
        ',' not in str(p.get('regular_price', '')) and
        ',' not in str(p.get('sale_price', ''))
        for p in woo_products
    )
    if price_ok:
        logger.info("✓ Všechny ceny mají správný formát (tečka místo čárky)")
        tests_passed += 1
    else:
        logger.error("✗ Některé ceny mají nesprávný formát")
        tests_failed += 1
    
    # Test 7: Kontrola stock management
    logger.info("\nTest 7: Kontrola stock management")
    variable_stock_ok = all(
        p.get('manage_stock') == 'no' and p.get('stock') == ''
        for p in woo_products if p['tax:product_type'] == 'variable'
    )
    if variable_stock_ok:
        logger.info("✓ Variable produkty nemají vlastní stock")
        tests_passed += 1
    else:
        logger.error("✗ Variable produkty mají nesprávné stock nastavení")
        tests_failed += 1
    
    # Test 8: Export do CSV
    logger.info("\nTest 8: Test exportu do CSV")
    try:
        exporter = WebToffeeCSVExporter('test_output')
        exported_files = exporter.export_products(woo_products, 'test_webtoffee')
        if exported_files:
            logger.info(f"✓ Export úspěšný, vytvořeno {len(exported_files)} souborů")
            tests_passed += 1
            
            # Načteme a zkontrolujeme CSV
            for file in exported_files:
                if 'all' in file:
                    df = pd.read_csv(file)
                    logger.info(f"  - Soubor {Path(file).name}: {len(df)} řádků, {len(df.columns)} sloupců")
        else:
            logger.error("✗ Export selhal")
            tests_failed += 1
    except Exception as e:
        logger.error(f"✗ Export selhal s chybou: {e}")
        tests_failed += 1
    
    # Souhrn
    logger.info("\n" + "="*50)
    logger.info("SOUHRN TESTŮ")
    logger.info("="*50)
    logger.info(f"Úspěšné testy: {tests_passed}")
    logger.info(f"Neúspěšné testy: {tests_failed}")
    logger.info(f"Celkem testů: {tests_passed + tests_failed}")
    
    if validation_errors:
        logger.warning(f"\nValidační chyby: {len(validation_errors)}")
        for error in validation_errors[:5]:
            logger.warning(f"  - {error}")
    
    # Ukázka výstupu
    logger.info("\n=== UKÁZKA TRANSFORMOVANÝCH DAT ===")
    for i, product in enumerate(woo_products[:3]):
        logger.info(f"\nProdukt {i+1}:")
        logger.info(f"  SKU: {product.get('sku')}")
        logger.info(f"  Název: {product.get('post_title')}")
        logger.info(f"  Typ: {product.get('tax:product_type')}")
        logger.info(f"  Parent SKU: {product.get('parent_sku', 'N/A')}")
        logger.info(f"  Cena: {product.get('regular_price')}")
        logger.info(f"  Kategorie: {product.get('tax:product_cat')}")
        
        # Zobrazit atributy
        attrs = []
        for key in product:
            if key.startswith('attribute:') and product[key]:
                attr_name = key.replace('attribute:', '')
                attrs.append(f"{attr_name}={product[key]}")
        if attrs:
            logger.info(f"  Atributy: {', '.join(attrs)}")
    
    return tests_passed, tests_failed


def test_edge_cases():
    """Testuje okrajové případy."""
    logger.info("\n\n=== TEST OKRAJOVÝCH PŘÍPADŮ ===")
    
    # Test s prázdnými daty
    logger.info("\nTest s prázdnými daty:")
    empty_products = pd.DataFrame()
    empty_categories = pd.DataFrame()
    
    try:
        transformer = WebToffeeTransformer(empty_products, empty_categories)
        products, errors = transformer.run_transformation()
        logger.info(f"✓ Transformace prázdných dat proběhla bez chyby, produktů: {len(products)}")
    except Exception as e:
        logger.error(f"✗ Transformace prázdných dat selhala: {e}")
    
    # Test s chybějícími sloupci
    logger.info("\nTest s chybějícími sloupci:")
    incomplete_products = pd.DataFrame({
        'KodZbozi': ['TEST001'],
        'JmenoZbozi': ['Test produkt']
        # Chybí ostatní sloupce
    })
    
    try:
        transformer = WebToffeeTransformer(incomplete_products, pd.DataFrame())
        products, errors = transformer.run_transformation()
        logger.info(f"✓ Transformace neúplných dat proběhla, produktů: {len(products)}")
    except Exception as e:
        logger.error(f"✗ Transformace neúplných dat selhala: {e}")


if __name__ == "__main__":
    # Spuštění testů
    logger.info("SPOUŠTÍM TESTY WEBTOFFEE TRANSFORMACE")
    logger.info("="*60)
    
    # Hlavní testy
    passed, failed = test_webtoffee_format()
    
    # Okrajové případy
    test_edge_cases()
    
    # Závěr
    logger.info("\n" + "="*60)
    if failed == 0:
        logger.info("✓ VŠECHNY TESTY PROŠLY ÚSPĚŠNĚ!")
    else:
        logger.error(f"✗ NĚKTERÉ TESTY SELHALY ({failed} z {passed + failed})")
    logger.info("="*60)