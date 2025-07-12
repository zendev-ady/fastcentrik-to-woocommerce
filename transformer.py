#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastCentrik to WooCommerce CSV Transformer
==========================================

Transformuje data z FastCentrik platformy do WooCommerce kompatibilního CSV formátu.
Podporuje variabilní produkty, kategorie, atributy a SEO optimalizaci.

Autor: FastCentrik Migration Tool
Verze: 1.0
"""

import pandas as pd
import re
from pathlib import Path
from typing import Dict, List, Tuple
import logging
from utils import create_slug, parse_parameters
from config import (
    SEO_SETTINGS,
    TAG_SETTINGS,
    VARIANT_SETTINGS,
    IMAGE_BASE_URL
)

# Nastavení logování
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataTransformer:
    """
    Zodpovídá za transformaci načtených FastCentrik dat do WooCommerce formátu.
    """
    def __init__(self, products_df: pd.DataFrame, categories_df: pd.DataFrame):
        """
        Inicializace transformátoru.

        Args:
            products_df (pd.DataFrame): DataFrame s produkty.
            categories_df (pd.DataFrame): DataFrame s kategoriemi.
        """
        self.products_data = products_df
        self.categories_data = categories_df
        self.category_mapping = {}
        self.woo_products = []
        self.woo_categories = []
    
    def _create_category_mapping(self) -> None:
        """Vytvoří mapování kategorií s hierarchickou strukturou."""
        logger.info("Vytvářím mapování kategorií")
        
        # Základní mapování ID -> název
        for _, cat in self.categories_data.iterrows():
            if pd.notna(cat['InterniKod']) and pd.notna(cat['JmenoKategorie']):
                self.category_mapping[cat['InterniKod']] = {
                    'name': cat['JmenoKategorie'],
                    'parent': cat.get('KodNadrizeneKategorie', ''),
                    'description': cat.get('PopisKategorie', ''),
                    'slug': create_slug(cat['JmenoKategorie'])
                }
        
        logger.info(f"Vytvořeno mapování pro {len(self.category_mapping)} kategorií")
    
    
    def _get_category_path(self, category_id: str) -> str:
        """Získá hierarchickou cestu kategorie."""
        if not category_id or category_id not in self.category_mapping:
            return ""
        
        category = self.category_mapping[category_id]
        path = [category['name']]
        
        # Projdeme hierarchii nahoru
        parent_id = category['parent']
        while parent_id and parent_id != 'ROOT_1' and parent_id in self.category_mapping:
            parent = self.category_mapping[parent_id]
            path.insert(0, parent['name'])
            parent_id = parent['parent']
        
        return ' > '.join(path)
    
    def _generate_seo_fields(self, product_name: str, category: str) -> Tuple[str, str, str]:
        """Generuje SEO pole pro produkt na základě nastavení v config.py."""
        # SEO title
        title_template = f"{{product_name}}{SEO_SETTINGS.get('title_suffix', '')}"
        seo_title = title_template.format(product_name=product_name)
        
        # Meta description
        meta_desc = SEO_SETTINGS.get('meta_desc_template', '{product_name}').format(
            product_name=product_name,
            category=category
        )
        
        # Focus keyword
        word_count = SEO_SETTINGS.get('focus_keyword_words', 3)
        focus_keyword = ' '.join(product_name.split()[:word_count]).lower()
        
        return seo_title, meta_desc, focus_keyword
    
    def _get_product_images(self, main_image: str, additional_images: str) -> str:
        """Sestaví seznam obrázků produktu s použitím base URL z configu."""
        images = []
        base_url = IMAGE_BASE_URL.strip('/')
        
        if pd.notna(main_image) and main_image.strip():
            # Odstraníme počáteční lomítko z cesty k obrázku, pokud existuje
            image_path = main_image.strip().lstrip('/')
            images.append(f"{base_url}/{image_path}")
        
        if pd.notna(additional_images) and additional_images.strip():
            additional = []
            for img in additional_images.split(';'):
                if img.strip():
                    # Odstraníme počáteční lomítko z cesty k obrázku, pokud existuje
                    image_path = img.strip().lstrip('/')
                    additional.append(f"{base_url}/{image_path}")
            images.extend(additional)
        
        return ', '.join(images)
    
    def _create_woo_product(self, row: pd.Series, product_type: str = 'simple', parent_sku: str = '') -> Dict:
        """Vytvoří WooCommerce produkt ze záznamu."""
        params = parse_parameters(row.get('HodnotyParametru', ''))
        
        # Základní informace
        sku = str(row['KodZbozi'])
        name = str(row['JmenoZbozi'])
        
        # Kategorie
        category_path = ""
        if pd.notna(row.get('InetrniKodyKategorii')):
            category_path = self._get_category_path(row['InetrniKodyKategorii'])
        
        # Ceny
        regular_price = str(row.get('CenaBezna', '')).replace(',', '.')
        sale_price = str(row.get('ZakladniCena', '')).replace(',', '.')
        
        # Popis
        description = str(row.get('Popis', ''))
        short_description = str(row.get('KratkyPopis', ''))
        
        # SEO
        seo_title, meta_desc, focus_keyword = self._generate_seo_fields(name, category_path.split(' > ')[-1] if category_path else '')
        
        # Obrázky
        images = self._get_product_images(row.get('HlavniObrazek'), row.get('DalsiObrazky'))
        
        # Atributy
        attributes = {}
        attr_counter = 1
        
        # Přidání hlavních atributů
        for attr_name, attr_value in params.items():
            if attr_counter > 3:
                break
            attributes[f'Attribute {attr_counter} name'] = attr_name.title()
            attributes[f'Attribute {attr_counter} value(s)'] = attr_value
            attributes[f'Attribute {attr_counter} visible'] = '1'
            attributes[f'Attribute {attr_counter} global'] = '1'
            attr_counter += 1

        # Tagy
        tags = []
        if TAG_SETTINGS.get('auto_generate_tags', False):
            tag_attributes = TAG_SETTINGS.get('tag_attributes', [])
            for tag_attr in tag_attributes:
                if tag_attr in params:
                    tags.append(params[tag_attr])
            tags = tags[:TAG_SETTINGS.get('max_tags_per_product', 5)]
        
        # WooCommerce produkt
        woo_product = {
            'ID': '',
            'Type': product_type,
            'SKU': sku,
            'Name': name,
            'Published': '1' if row.get('Vypnuto', 0) == 0 else '0',
            'Is featured?': '0',
            'Visibility in catalog': 'visible',
            'Short description': short_description,
            'Description': description,
            'Date sale price starts': '',
            'Date sale price ends': '',
            'Tax status': 'taxable',
            'Tax class': '',
            'In stock?': '1' if row.get('NaSklade', 0) > 0 else '0',
            'Stock': str(row.get('NaSklade', 0)),
            'Low stock amount': '',
            'Backorders allowed?': '0',
            'Sold individually?': '0',
            'Weight (kg)': str(row.get('Hmotnost', '')).replace(',', '.'),
            'Length (cm)': '',
            'Width (cm)': '',
            'Height (cm)': '',
            'Allow customer reviews?': '1',
            'Purchase note': '',
            'Sale price': sale_price if sale_price != regular_price else '',
            'Regular price': regular_price,
            'Categories': category_path,
            'Tags': ', '.join(tags),
            'Shipping class': '',
            'Images': images,
            'Download limit': '',
            'Download expiry days': '',
            'Parent': parent_sku,
            'Grouped products': '',
            'Upsells': '',
            'Cross-sells': '',
            'External URL': '',
            'Button text': '',
            'Position': '0',
            'Meta: _yoast_wpseo_title': seo_title,
            'Meta: _yoast_wpseo_metadesc': meta_desc,
            'Meta: _yoast_wpseo_focuskw': focus_keyword
        }
        
        # Přidání atributů
        woo_product.update(attributes)
        
        return woo_product
    
    def run_transformation(self) -> Tuple[List[Dict], List[Dict]]:
        """
        Spustí kompletní transformaci dat a vrátí produkty a kategorie.

        Returns:
            Tuple[List[Dict], List[Dict]]: Dvojice obsahující seznam produktů a seznam kategorií.
        """
        logger.info("=== SPUŠTĚNÍ TRANSFORMACE DAT ===")
        self._create_category_mapping()
        self._transform_products()
        self._transform_categories()
        self._print_transformation_stats()
        logger.info("=== TRANSFORMACE DAT DOKONČENA ===")
        return self.woo_products, self.woo_categories

    def _transform_products(self) -> None:
        """Hlavní metoda pro transformaci produktů."""
        logger.info("Zahajuji transformaci produktů")
        
        # Seskupení produktů podle master kódu
        master_groups = self.products_data.groupby('KodMasterVyrobku')
        simple_products = self.products_data[self.products_data['KodMasterVyrobku'].isna()]
        
        # Zpracování jednoduchých produktů
        logger.info(f"Zpracovávám {len(simple_products)} jednoduchých produktů")
        for _, product in simple_products.iterrows():
            woo_product = self._create_woo_product(product, 'simple')
            self.woo_products.append(woo_product)
        
        # Zpracování variabilních produktů
        variable_groups = master_groups.size()
        variable_groups = variable_groups[variable_groups > 1]
        
        logger.info(f"Zpracovávám {len(variable_groups)} skupin variabilních produktů")
        
        for master_code, group in master_groups:
            if pd.isna(master_code) or len(group) <= 1:
                continue
            
            # Hlavní variabilní produkt
            main_product = group.iloc[0].copy()
            main_product['JmenoZbozi'] = self._create_parent_name(group)
            
            parent_product = self._create_woo_product(main_product, 'variable')
            parent_product['SKU'] = f"{master_code}_parent"
            parent_product['Stock'] = ''  # Variabilní produkty nemají stock
            
            self.woo_products.append(parent_product)
            
            # Varianty
            for _, variant in group.iterrows():
                variant_product = self._create_woo_product(variant, 'variation', f"{master_code}_parent")
                self.woo_products.append(variant_product)
        
        logger.info(f"Vytvořeno celkem {len(self.woo_products)} WooCommerce produktů")

    def _create_parent_name(self, variants_group: pd.DataFrame) -> str:
        """Vytvoří název pro hlavní variabilní produkt na základě configu."""
        first_product = variants_group.iloc[0]
        name = str(first_product['JmenoZbozi'])
        
        # Odstranění specifických variant z názvu
        params = parse_parameters(first_product.get('HodnotyParametru', ''))
        attrs_to_remove = VARIANT_SETTINGS.get('parent_name_remove_attrs', [])
        
        for attr in attrs_to_remove:
            if attr in params:
                # Použijeme word boundary \b, aby se nemazaly části slov
                name = re.sub(r'\b' + re.escape(params[attr]) + r'\b', '', name, flags=re.IGNORECASE)
        
        # Vyčištění názvu od dvojitých mezer
        name = re.sub(r'\s+', ' ', name).strip()
        
        return name

    def _transform_categories(self) -> None:
        """Transformuje kategorie do formátu pro export."""
        logger.info("Transformuji kategorie...")
        
        for cat_id, cat_data in self.category_mapping.items():
            if cat_data['name'] and cat_data['name'] != 'ROOT_1':
                category = {
                    'Category ID': cat_id,
                    'Category Name': cat_data['name'],
                    'Category Slug': cat_data['slug'],
                    'Category Parent': cat_data['parent'] if cat_data['parent'] != 'ROOT_1' else '',
                    'Category Description': cat_data['description']
                }
                self.woo_categories.append(category)
        logger.info(f"Zpracováno {len(self.woo_categories)} kategorií.")
    
    def _print_transformation_stats(self) -> None:
        """Vypíše statistiky transformace."""
        simple_count = len([p for p in self.woo_products if p['Type'] == 'simple'])
        variable_count = len([p for p in self.woo_products if p['Type'] == 'variable'])
        variation_count = len([p for p in self.woo_products if p['Type'] == 'variation'])
        
        print("\n" + "="*50)
        print("STATISTIKY TRANSFORMACE")
        print("="*50)
        print(f"Celkem FastCentrik produktů: {len(self.products_data)}")
        print(f"Celkem WooCommerce produktů: {len(self.woo_products)}")
        print(f"  - Jednoduché produkty: {simple_count}")
        print(f"  - Variabilní produkty: {variable_count}")
        print(f"  - Varianty: {variation_count}")
        print(f"Celkem kategorií: {len(self.category_mapping)}")
        print("="*50)

