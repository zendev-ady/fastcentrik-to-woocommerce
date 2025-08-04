#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for variant detection based on SKU patterns
"""

import pandas as pd
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.fastcentrik_woocommerce.core.transformer import DataTransformer

def create_test_data():
    """Create test data with variant products"""
    
    # Test products with variants
    products_data = {
        'KodZbozi': ['033201', '033201_2', '033201_3', '033201_4', '019228', '019310'],
        'JmenoZbozi': [
            'Pánské kopačky lisovky Adidas Kaiser 5 Liga FG černé',
            'Pánské kopačky lisovky Adidas Kaiser 5 Liga FG černé 39 1/3',
            'Pánské kopačky lisovky Adidas Kaiser 5 Liga FG černé 40',
            'Pánské kopačky lisovky Adidas Kaiser 5 Liga FG černé 41 1/3',
            'Pánské kopačky turfy Adidas Mundial Team TF černé',
            'Pánské sálové kopačky Adidas Mundial Goal IN černé'
        ],
        'HodnotyParametru': [
            '',
            'velikost=39 1/3;barva=černá',
            'velikost=40;barva=černá',
            'velikost=41 1/3;barva=černá',
            'velikost=42;barva=černá',
            'velikost=43;barva=černá'
        ],
        'NaSklade': [0, 15, 20, 10, 50, 30],
        'CenaBezna': [3153.35, 3153.35, 3153.35, 3153.35, 3503.87, 3600.06],
        'ZakladniCena': [2546.27, 2546.27, 2546.27, 2546.27, 3236.76, 3449.67],
        'KodMasterVyrobku': [None, None, None, None, None, None],
        'InetrniKodyKategorii': ['CAT123', 'CAT123', 'CAT123', 'CAT123', 'CAT456', 'CAT789'],
        'Vypnuto': [0, 0, 0, 0, 0, 0],
        'Popis': ['Test popis'] * 6,
        'KratkyPopis': ['Test krátký popis'] * 6,
        'HlavniObrazek': ['test.jpg'] * 6,
        'DalsiObrazky': ['test2.jpg;test3.jpg'] * 6,
        'Hmotnost': [0.9] * 6
    }
    
    categories_data = {
        'InterniKod': ['CAT123', 'CAT456', 'CAT789'],
        'JmenoKategorie': ['Kopačky lisovky', 'Kopačky turfy', 'Sálové kopačky'],
        'KodNadrizeneKategorie': ['ROOT_1', 'ROOT_1', 'ROOT_1'],
        'PopisKategorie': ['Test kategorie'] * 3
    }
    
    products_df = pd.DataFrame(products_data)
    categories_df = pd.DataFrame(categories_data)
    
    return products_df, categories_df

def test_variant_detection():
    """Test the variant detection functionality"""
    
    print("=== TEST DETEKCE VARIANT ===\n")
    
    # Create test data
    products_df, categories_df = create_test_data()
    
    print("Testovací data:")
    print(f"Počet produktů: {len(products_df)}")
    print("\nSKU produktů:")
    for sku in products_df['KodZbozi']:
        print(f"  - {sku}")
    
    # Create transformer
    transformer = DataTransformer(products_df, categories_df)
    
    # Test SKU grouping
    print("\n=== TEST SESKUPOVÁNÍ PODLE SKU ===")
    sku_groups = transformer._group_products_by_sku_pattern()
    
    print(f"\nDetekované skupiny variant: {len(sku_groups['parent_groups'])}")
    for parent_sku, variants in sku_groups['parent_groups'].items():
        print(f"\nSkupina {parent_sku}:")
        print(f"  Parent SKU: {parent_sku}")
        print(f"  Varianty: {variants}")
    
    print(f"\nVšechny SKU které jsou součástí variant: {sku_groups['all_variant_skus']}")
    
    # Run transformation
    print("\n=== SPUŠTĚNÍ TRANSFORMACE ===")
    woo_products, woo_categories = transformer.run_transformation()
    
    # Analyze results
    print("\n=== VÝSLEDKY TRANSFORMACE ===")
    print(f"Celkem WooCommerce produktů: {len(woo_products)}")
    
    # Count by type
    types_count = {}
    for product in woo_products:
        product_type = product['Type']
        types_count[product_type] = types_count.get(product_type, 0) + 1
    
    print("\nPočet produktů podle typu:")
    for product_type, count in types_count.items():
        print(f"  - {product_type}: {count}")
    
    # Show variable products
    print("\n=== VARIABILNÍ PRODUKTY ===")
    for product in woo_products:
        if product['Type'] == 'variable':
            print(f"\nParent produkt: {product['SKU']}")
            print(f"  Název: {product['Name']}")
            print(f"  Stock: '{product['Stock']}' (měl by být prázdný)")
            print(f"  In stock?: {product['In stock?']}")
            
            # Show attributes
            attrs = []
            for i in range(1, 4):
                attr_name = product.get(f'Attribute {i} name')
                attr_values = product.get(f'Attribute {i} value(s)')
                if attr_name:
                    attrs.append(f"{attr_name}: {attr_values}")
            print(f"  Atributy: {', '.join(attrs)}")
            
            # Show variants
            print("  Varianty:")
            for variant in woo_products:
                if variant['Type'] == 'variation' and variant['Parent'] == product['SKU']:
                    variant_attrs = []
                    for i in range(1, 4):
                        attr_name = variant.get(f'Attribute {i} name')
                        attr_value = variant.get(f'Attribute {i} value(s)')
                        if attr_name:
                            variant_attrs.append(f"{attr_name}={attr_value}")
                    print(f"    - {variant['SKU']}: {', '.join(variant_attrs)}, Stock={variant['Stock']}")
    
    # Show simple products
    print("\n=== JEDNODUCHÉ PRODUKTY ===")
    for product in woo_products:
        if product['Type'] == 'simple':
            print(f"  - {product['SKU']}: {product['Name']}")
    
    print("\n=== TEST DOKONČEN ===")

if __name__ == "__main__":
    test_variant_detection()