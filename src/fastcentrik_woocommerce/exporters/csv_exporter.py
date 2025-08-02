#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modul pro export dat do WooCommerce CSV formátu.
"""

import pandas as pd
import logging
from pathlib import Path
from typing import List, Dict
import sys

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from config.config import EXPORT_SETTINGS

logger = logging.getLogger(__name__)

class CsvExporter:
    """
    Zodpovídá za export transformovaných dat do CSV souborů.
    """
    
    WOO_COLUMNS = [
        'ID', 'Type', 'SKU', 'Name', 'Published', 'Is featured?',
        'Visibility in catalog', 'Short description', 'Description', 
        'Date sale price starts', 'Date sale price ends', 'Tax status',
        'Tax class', 'In stock?', 'Stock', 'Low stock amount', 'Backorders allowed?',
        'Sold individually?', 'Weight (kg)', 'Length (cm)', 'Width (cm)', 'Height (cm)',
        'Allow customer reviews?', 'Purchase note', 'Sale price', 'Regular price',
        'Categories', 'Tags', 'Shipping class', 'Images', 'Download limit',
        'Download expiry days', 'Parent', 'Grouped products', 'Upsells', 'Cross-sells',
        'External URL', 'Button text', 'Position', 'Attribute 1 name', 'Attribute 1 value(s)',
        'Attribute 1 visible', 'Attribute 1 global', 'Attribute 2 name', 'Attribute 2 value(s)',
        'Attribute 2 visible', 'Attribute 2 global', 'Attribute 3 name', 'Attribute 3 value(s)',
        'Attribute 3 visible', 'Attribute 3 global', 'Meta: _yoast_wpseo_title',
        'Meta: _yoast_wpseo_metadesc', 'Meta: _yoast_wpseo_focuskw'
    ]

    def export_products(self, products: List[Dict], output_dir: str):
        """
        Exportuje seznam produktů do CSV souboru.

        Args:
            products (List[Dict]): Seznam slovníků reprezentujících produkty.
            output_dir (str): Cílová složka pro export.
        """
        if not products:
            logger.warning("Nebyly nalezeny žádné produkty k exportu.")
            return

        output_file = Path(output_dir) / 'woocommerce_products.csv'
        logger.info(f"Exportuji {len(products)} produktů do {output_file}...")

        df = pd.DataFrame(products)
        
        # Zajistí, že všechny sloupce existují
        for col in self.WOO_COLUMNS:
            if col not in df.columns:
                df[col] = ''
        
        df = df.reindex(columns=self.WOO_COLUMNS)
        
        df.to_csv(
            output_file, 
            index=False, 
            encoding=EXPORT_SETTINGS.get('encoding', 'utf-8-sig'), 
            sep=EXPORT_SETTINGS.get('separator', ',')
        )
        logger.info("Export produktů dokončen.")

    def export_categories(self, categories: List[Dict], output_dir: str):
        """
        Exportuje seznam kategorií do CSV souboru.

        Args:
            categories (List[Dict]): Seznam slovníků reprezentujících kategorie.
            output_dir (str): Cílová složka pro export.
        """
        if not categories:
            logger.warning("Nebyly nalezeny žádné kategorie k exportu.")
            return

        output_file = Path(output_dir) / 'woocommerce_categories.csv'
        logger.info(f"Exportuji {len(categories)} kategorií do {output_file}...")

        df = pd.DataFrame(categories)
        df.to_csv(
            output_file, 
            index=False, 
            encoding=EXPORT_SETTINGS.get('encoding', 'utf-8-sig'),
            sep=EXPORT_SETTINGS.get('separator', ',')
        )
        logger.info("Export kategorií dokončen.")