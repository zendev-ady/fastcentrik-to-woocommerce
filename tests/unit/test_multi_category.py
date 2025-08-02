#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script pro multi-category mapování
=======================================

Testuje funkčnost přiřazování produktů do více kategorií.
"""

import sys
from pathlib import Path
# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.fastcentrik_woocommerce.mappers.category_mapper import CategoryMapper
from config.config import CATEGORY_MAPPING_SETTINGS
import json


def test_multi_category_mapping():
    """Testuje multi-category mapování s různými produkty."""
    
    # Inicializace mapperu
    mapper = CategoryMapper()
    
    # Testovací produkty
    test_products = [
        {
            "name": "Pánské běžecké tričko Nike Dri-FIT",
            "params": {
                "pohlavi": "pánské",
                "typ": "tričko",
                "sport": "běh",
                "znacka": "Nike",
                "material": "polyester"
            },
            "description": "Sportovní tričko vhodné jak pro běh, tak pro běžné nošení"
        },
        {
            "name": "Dámské outdoorové boty Salomon",
            "params": {
                "pohlavi": "dámské",
                "typ": "boty",
                "sport": "outdoor",
                "znacka": "Salomon",
                "povrch": "trek"
            },
            "description": "Univerzální boty pro outdoor aktivity"
        },
        {
            "name": "Dětské fotbalové kopačky Adidas FG",
            "params": {
                "pohlavi": "dětské",
                "typ": "kopačky",
                "sport": "fotbal",
                "povrch": "FG",
                "znacka": "Adidas"
            },
            "description": "Dětské kopačky na přírodní trávu"
        },
        {
            "name": "Fitness rukavice Reebok",
            "params": {
                "typ": "rukavice",
                "sport": "fitness",
                "znacka": "Reebok",
                "pohlavi": "unisex"
            },
            "description": "Univerzální fitness rukavice"
        },
        {
            "name": "Pánská zimní bunda Nike Sportswear",
            "params": {
                "pohlavi": "pánské",
                "typ": "bunda",
                "sezona": "zima",
                "znacka": "Nike"
            },
            "description": "Zimní bunda vhodná pro sport i běžné nošení"
        }
    ]
    
    print("="*80)
    print("TEST MULTI-CATEGORY MAPOVÁNÍ")
    print("="*80)
    print(f"\nNastavení:")
    print(f"  Multi-category povoleno: {CATEGORY_MAPPING_SETTINGS.get('enable_multi_category', False)}")
    print(f"  Max kategorií na produkt: {CATEGORY_MAPPING_SETTINGS.get('max_categories_per_product', 2)}")
    print(f"  Strategie: {CATEGORY_MAPPING_SETTINGS.get('multi_category_strategy', 'complementary')}")
    print(f"  Oddělovač: '{CATEGORY_MAPPING_SETTINGS.get('multi_category_separator', ', ')}'")
    print("\n" + "-"*80)
    
    # Test každého produktu
    for i, product in enumerate(test_products, 1):
        print(f"\n{i}. Produkt: {product['name']}")
        print(f"   Popis: {product['description']}")
        print(f"   Parametry: {json.dumps(product['params'], ensure_ascii=False, indent=6)}")
        
        # Single category mapping
        single_cat, single_type = mapper.map_product_to_category(
            product['name'],
            product['params']
        )
        print(f"\n   Single-category výsledek:")
        print(f"     Kategorie: {single_cat}")
        print(f"     Typ: {single_type}")
        
        # Multi-category mapping
        multi_cats, multi_type = mapper.map_product_to_multiple_categories(
            product['name'],
            product['params'],
            max_categories=CATEGORY_MAPPING_SETTINGS.get('max_categories_per_product', 2),
            strategy=CATEGORY_MAPPING_SETTINGS.get('multi_category_strategy', 'complementary')
        )
        print(f"\n   Multi-category výsledek:")
        print(f"     Kategorie: {multi_cats}")
        print(f"     Počet kategorií: {len(multi_cats)}")
        print(f"     Typ: {multi_type}")
        
        # Spojené kategorie pro CSV
        if multi_cats:
            separator = CATEGORY_MAPPING_SETTINGS.get('multi_category_separator', ', ')
            csv_categories = separator.join(multi_cats)
            print(f"     CSV formát: {csv_categories}")
        
        print("-"*80)
    
    # Vytisknout report
    print("\n")
    mapper.print_mapping_report()


def test_category_limit_validation():
    """Testuje validaci limitu kategorií."""
    print("\n\n")
    print("="*80)
    print("TEST VALIDACE LIMITU KATEGORIÍ")
    print("="*80)
    
    mapper = CategoryMapper()
    
    # Test s různými limity
    test_limits = [1, 2, 3, 5]
    
    product = {
        "name": "Univerzální sportovní produkt Nike",
        "params": {
            "pohlavi": "pánské",
            "typ": "oblečení",
            "sport": "fitness",
            "znacka": "Nike"
        }
    }
    
    print(f"\nTestovaný produkt: {product['name']}")
    print(f"Parametry: {json.dumps(product['params'], ensure_ascii=False)}")
    
    for limit in test_limits:
        categories, _ = mapper.map_product_to_multiple_categories(
            product['name'],
            product['params'],
            max_categories=limit,
            strategy='all_matches'
        )
        print(f"\nLimit {limit}: Přiřazeno {len(categories)} kategorií")
        for cat in categories:
            print(f"  - {cat}")


def test_backward_compatibility():
    """Testuje zpětnou kompatibilitu se single-category systémem."""
    print("\n\n")
    print("="*80)
    print("TEST ZPĚTNÉ KOMPATIBILITY")
    print("="*80)
    
    mapper = CategoryMapper()
    
    # Produkt, který by měl mít jednu kategorii
    product = {
        "name": "Fotbalový míč Adidas",
        "params": {
            "typ": "míč",
            "sport": "fotbal",
            "znacka": "Adidas"
        }
    }
    
    print(f"\nProdukt: {product['name']}")
    
    # Single category (původní systém)
    single_cat, _ = mapper.map_product_to_category(
        product['name'],
        product['params']
    )
    
    # Multi-category s limitem 1
    multi_cats, _ = mapper.map_product_to_multiple_categories(
        product['name'],
        product['params'],
        max_categories=1
    )
    
    print(f"\nSingle-category: {single_cat}")
    print(f"Multi-category (limit 1): {multi_cats[0] if multi_cats else 'None'}")
    print(f"Kompatibilní: {'✓ ANO' if single_cat == (multi_cats[0] if multi_cats else None) else '✗ NE'}")


if __name__ == "__main__":
    # Spustit všechny testy
    test_multi_category_mapping()
    test_category_limit_validation()
    test_backward_compatibility()