#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to debug image processing for a specific product.
"""

import sys
import pandas as pd
import logging
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.fastcentrik_woocommerce.loaders.data_loader import DataLoader
from src.fastcentrik_woocommerce.core.webtoffee_transformer import WebToffeeTransformer
from src.fastcentrik_woocommerce.utils.logging_config import setup_logging

# Set up logging with new configuration
logger = setup_logging(__name__, console_level=logging.DEBUG)

def main():
    """Main function to test image processing for a specific product."""
    # Constants
    INPUT_FILE = "Export_Excel_Lite.xls"
    TARGET_SKU = "10756308"  # The problematic SKU
    
    logger.info(f"Testing image processing for SKU: {TARGET_SKU}")
    
    try:
        # 1. Load data
        loader = DataLoader(INPUT_FILE)
        data = loader.load_data()
        
        products_df = data['products']
        categories_df = data['categories']
        
        # 2. Print column names to verify structure
        logger.info(f"Column names in products DataFrame: {list(products_df.columns)}")
        
        # 3. Filter for the target product
        target_product = products_df[products_df['KodZbozi'] == TARGET_SKU]
        if len(target_product) == 0:
            # Try with KodMasterVyrobku
            target_product = products_df[products_df['KodMasterVyrobku'] == TARGET_SKU]
            
        if len(target_product) == 0:
            logger.error(f"Product with SKU {TARGET_SKU} not found!")
            # Print all SKUs to help identify the correct one
            all_skus = products_df['KodZbozi'].tolist()
            logger.info(f"Available SKUs: {all_skus[:20]}...")
            return
        
        logger.info(f"Found {len(target_product)} products with SKU/MasterCode {TARGET_SKU}")
        
        # 4. Print the product data to see what we're working with
        for idx, row in target_product.iterrows():
            logger.info(f"Product {idx}:")
            for col in row.index:
                # Check if the column might contain image paths
                val = row[col]
                if pd.notna(val) and isinstance(val, str) and ('/images/' in val or '.jpg' in val or '.png' in val):
                    logger.info(f"  {col} (POTENTIAL IMAGE): {val}")
                else:
                    logger.info(f"  {col}: {val}")
        
        # 5. Create a small dataset with just this product and its variants
        if 'KodMasterVyrobku' in products_df.columns:
            # Find all variants with this master code
            variants = products_df[products_df['KodMasterVyrobku'] == TARGET_SKU]
            if len(variants) > 0:
                logger.info(f"Found {len(variants)} variants with master code {TARGET_SKU}")
                
                # CRITICAL FIX: Make sure to include the parent product in the test dataset
                # First, check if the target product is already in the variants DataFrame
                target_in_variants = False
                for _, row in variants.iterrows():
                    if row['KodZbozi'] == TARGET_SKU:
                        target_in_variants = True
                        break
                
                if not target_in_variants and len(target_product) > 0:
                    logger.info(f"Adding parent product with SKU {TARGET_SKU} to the test dataset")
                    # Combine the target product and variants
                    test_products = pd.concat([target_product, variants])
                else:
                    test_products = variants
            else:
                # If no variants found, just use the target product
                logger.info(f"No variants found, using just the target product")
                test_products = target_product
        else:
            # If no KodMasterVyrobku column, just use the target product
            test_products = target_product
        
        # 6. Run the transformation on this small dataset
        transformer = WebToffeeTransformer(test_products, categories_df)
        woo_products, _ = transformer.run_transformation()
        
        # 7. Check the results
        logger.info("\nTransformation Results:")
        for product in woo_products:
            logger.info(f"Product ID: {product['ID']}")
            logger.info(f"SKU: {product['sku']}")
            logger.info(f"Type: {product['tax:product_type']}")
            logger.info(f"Images: {product['images']}")
            logger.info("-" * 50)
        
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()