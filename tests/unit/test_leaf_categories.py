#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test pro ověření, že se používají pouze názvy koncových kategorií
"""

import sys
from pathlib import Path
# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.fastcentrik_woocommerce.mappers.category_mapper import CategoryMapper
from config.config import CATEGORY_MAPPING_SETTINGS

def test_leaf_categories():
    mapper = CategoryMapper()
    
    test_products = [
        {
            "name": "Pánské běžecké tričko Nike",
            "params": {"pohlavi": "pánské", "typ": "tričko", "sport": "běh"}
        },
        {
            "name": "Dětské fotbalové kopačky Adidas FG",
            "params": {"pohlavi": "dětské", "typ": "kopačky", "sport": "fotbal", "povrch": "FG"}
        },
        {
            "name": "Dámské outdoorové boty",
            "params": {"pohlavi": "dámské", "typ": "boty", "sport": "outdoor"}
        }
    ]
    
    print("Test koncových kategorií (leaf categories)")
    print("=" * 60)
    print(f"use_leaf_category_only: {CATEGORY_MAPPING_SETTINGS.get('use_leaf_category_only', True)}")
    print(f"separator: '{CATEGORY_MAPPING_SETTINGS.get('multi_category_separator', ' | ')}'")
    print("=" * 60)
    
    for product in test_products:
        print(f"\nProdukt: {product['name']}")
        
        # Získat kategorie
        categories, _ = mapper.map_product_to_multiple_categories(
            product['name'],
            product['params'],
            max_categories=2
        )
        
        if categories:
            # Ukázat plné cesty
            print(f"Plné cesty kategorií:")
            for i, cat in enumerate(categories, 1):
                print(f"  {i}. {cat}")
            
            # Ukázat pouze koncové kategorie
            leaf_categories = []
            for cat_path in categories:
                leaf_name = cat_path.split(' > ')[-1].strip()
                leaf_categories.append(leaf_name)
            
            print(f"Koncové kategorie:")
            for i, cat in enumerate(leaf_categories, 1):
                print(f"  {i}. {cat}")
            
            # CSV formát
            separator = CATEGORY_MAPPING_SETTINGS.get('multi_category_separator', ' | ')
            csv_format = separator.join(leaf_categories)
            print(f"CSV formát: {csv_format}")
        else:
            print("Žádné kategorie nebyly přiřazeny")
        
        print("-" * 60)

if __name__ == "__main__":
    test_leaf_categories()