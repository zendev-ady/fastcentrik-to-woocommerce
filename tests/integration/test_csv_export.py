#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify the CSV export with separate image columns.
"""

import sys
import pandas as pd
import logging
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.fastcentrik_woocommerce.exporters.webtoffee_csv_exporter import WebToffeeCSVExporter
from src.fastcentrik_woocommerce.utils.logging_config import setup_logging

# Set up logging with new configuration
logger = setup_logging(__name__, console_level=logging.DEBUG)

def main():
    """Main function to test the CSV export with separate image columns."""
    # Create a test product with multiple images
    test_products = [
        {
            'ID': '1000',
            'post_parent': '',
            'sku': 'TEST-001',
            'post_title': 'Test Product with Multiple Images',
            'post_status': 'publish',
            'tax:product_type': 'Simple',
            'regular_price': '100',
            'stock': '50',
            'manage_stock': 'yes',
            'images': 'https://example.com/image1.jpg|https://example.com/image2.jpg|https://example.com/image3.jpg|https://example.com/image4.jpg'
        }
    ]
    
    # Create the exporter
    exporter = WebToffeeCSVExporter('test_output')
    
    # Export the test products
    logger.info("Exporting test products with separate image columns...")
    exporter.export_sample(test_products, sample_size=1)
    
    # Read the exported CSV file to verify the format
    sample_file = Path('test_output/webtoffee_sample.csv')
    if sample_file.exists():
        logger.info(f"Reading exported CSV file: {sample_file}")
        df = pd.read_csv(sample_file, encoding='utf-8-sig')
        
        # Check if the fifu_image_url_X columns exist
        image_columns = [col for col in df.columns if col.startswith('fifu_image_url_')]
        logger.info(f"Found {len(image_columns)} image columns: {image_columns}")
        
        # Check if the images column still exists
        if 'images' in df.columns:
            logger.warning("The 'images' column still exists in the output!")
        else:
            logger.info("The 'images' column has been replaced with separate image columns.")
        
        # Print the values of the image columns
        for col in image_columns:
            logger.info(f"{col}: {df[col].values[0]}")
    else:
        logger.error(f"Exported CSV file not found: {sample_file}")

if __name__ == "__main__":
    main()