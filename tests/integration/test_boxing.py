#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple test for boxing equipment mapping
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.fastcentrik_woocommerce.mappers.category_mapper import CategoryMapper

def test_boxing():
    """Test boxing equipment mapping"""
    mapper = CategoryMapper()
    
    # Test boxing equipment
    test_cases = [
        {
            "name": "boxerske rukavice",
            "params": {"sport": "box", "typ": "rukavice"},
        },
        {
            "name": "boxerska helma",
            "params": {"sport": "box", "typ": "helma"},
        },
        {
            "name": "cyklotrenazer nordictrack",
            "params": {"typ": "fitness stroj", "znacka": "nordictrack"},
        }
    ]
    
    for test in test_cases:
        print(f"Testing: {test['name']}")
        print(f"Params: {test['params']}")
        
        category, mapping_type = mapper.map_product_to_category(
            test["name"],
            test["params"]
        )
        
        print(f"Result: {category} ({mapping_type})")
        print("-" * 40)

if __name__ == "__main__":
    test_boxing()