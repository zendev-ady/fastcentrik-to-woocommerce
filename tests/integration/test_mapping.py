#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for improved category mapping
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.fastcentrik_woocommerce.mappers.category_mapper import CategoryMapper

def test_improved_mapping():
    """Test the improved category mapping"""
    mapper = CategoryMapper()
    
    # Test cases based on the log issues
    test_cases = [
        {
            "name": "Unisex trekove boty Palladium Pallabrousse Tact kremove",
            "params": {"pohlavi": "unisex", "znacka": "Palladium"},
            "description": "Palladium unisex shoes - should map to both male and female outdoor shoes"
        },
        {
            "name": "Unisex turisticka obuv Palladium Pampa Hi Supply Lth cerna",
            "params": {"pohlavi": "unisex", "znacka": "Palladium"},
            "description": "Palladium unisex tourist shoes - should map to outdoor categories"
        },
        {
            "name": "Boxerske rukavice IQ Cross The Line Boxeo cerno-cervene",
            "params": {"sport": "box", "typ": "rukavice"},
            "description": "Boxing gloves - should map to boxing category"
        },
        {
            "name": "Boxerska helma Adidas Hybrid 50 cerna",
            "params": {"sport": "box", "typ": "helma", "znacka": "Adidas"},
            "description": "Boxing helmet - should map to boxing category"
        },
        {
            "name": "Hokejka Bauer Supreme 1S GripTac 17 Composite cerna",
            "params": {"sport": "hokej", "typ": "hokejka", "znacka": "Bauer"},
            "description": "Hockey stick - should map to hockey equipment"
        },
        {
            "name": "Cyklotrenažer Nordictrack Commercial S27i",
            "params": {"typ": "fitness stroj", "znacka": "Nordictrack"},
            "description": "Exercise bike - should map to fitness equipment"
        },
        {
            "name": "Divci perova vesta 4F s vyplni ze syntetickeho peri cerna",
            "params": {"pohlavi": "divci", "typ": "vesta"},
            "description": "Girls down vest - should map to winter clothing"
        }
    ]
    
    print("Testing Improved Category Mapping")
    print("=" * 60)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['description']}")
        print(f"Product: {test['name']}")
        print(f"Params: {test['params']}")
        
        # Test single category mapping
        category, mapping_type = mapper.map_product_to_category(
            test["name"],
            test["params"]
        )
        print(f"Single mapping: {category} (type: {mapping_type})")
        
        # Test multi-category mapping
        categories, mapping_type = mapper.map_product_to_multiple_categories(
            test["name"],
            test["params"],
            max_categories=2,
            strategy="complementary"
        )
        print(f"Multi mapping: {categories} (type: {mapping_type})")
        print("-" * 40)
    
    # Print mapping statistics
    mapper.print_mapping_report()

if __name__ == "__main__":
    test_improved_mapping()