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
import unicodedata
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

# Nastavení logování
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FastCentrikToWooCommerce:
    """Hlavní třída pro transformaci FastCentrik dat do WooCommerce formátu."""
    
    def __init__(self, excel_file_path: str):
        """
        Inicializace transformátoru.
        
        Args:
            excel_file_path (str): Cesta k FastCentrik Excel souboru
        """
        self.excel_file_path = excel_file_path
        self.products_data = None
        self.categories_data = None
        self.parameters_data = None
        self.category_mapping = {}
        self.woo_products = []
        
        # WooCommerce mapping
        self.woo_columns = [
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
    
    def load_data(self) -> None:
        """Načte data ze všech listů Excel souboru."""
        logger.info(f"Načítám data z {self.excel_file_path}")
        
        try:
            # Načtení produktů
            self.products_data = pd.read_excel(self.excel_file_path, sheet_name='Zbozi')
            logger.info(f"Načteno {len(self.products_data)} produktů")
            
            # Načtení kategorií
            self.categories_data = pd.read_excel(self.excel_file_path, sheet_name='Kategorie')
            logger.info(f"Načteno {len(self.categories_data)} kategorií")
            
            # Načtení parametrů
            self.parameters_data = pd.read_excel(self.excel_file_path, sheet_name='Parametry')
            logger.info(f"Načteno {len(self.parameters_data)} parametrů")
            
            # Vytvoření mapování kategorií
            self._create_category_mapping()
            
        except Exception as e:
            logger.error(f"Chyba při načítání dat: {e}")
            raise
    
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
                    'slug': self._create_slug(cat['JmenoKategorie'])
                }
        
        logger.info(f"Vytvořeno mapování pro {len(self.category_mapping)} kategorií")
    
    def _create_slug(self, text: str) -> str:
        """Vytvoří URL-friendly slug z textu."""
        if pd.isna(text):
            return ""
        
        # Převod na malá písmena a normalizace
        text = str(text).lower()
        text = unicodedata.normalize('NFKD', text)
        text = text.encode('ascii', 'ignore').decode('ascii')
        
        # Nahrazení mezer a speciálních znaků pomlčkami
        text = re.sub(r'[^a-z0-9]+', '-', text)
        text = text.strip('-')
        
        return text
    
    def _parse_parameters(self, param_string: str) -> Dict[str, str]:
        """Parsuje parametry z FastCentrik formátu."""
        if pd.isna(param_string) or not param_string:
            return {}
        
        params = {}
        param_pairs = param_string.split('##')
        
        for pair in param_pairs:
            if '||' in pair:
                key, value = pair.split('||', 1)
                params[key.strip()] = value.strip()
        
        return params
    
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
        """Generuje SEO pole pro produkt."""
        # SEO title (max 60 znaků)
        seo_title = product_name[:57] + "..." if len(product_name) > 60 else product_name
        
        # Meta description
        meta_desc = f"Kvalitní {product_name.lower()} v kategorii {category}. ✓ Rychlé dodání ✓ Skvělé ceny ✓ Zákaznická podpora"
        if len(meta_desc) > 155:
            meta_desc = meta_desc[:152] + "..."
        
        # Focus keyword (první 2-3 slova)
        focus_keyword = ' '.join(product_name.split()[:3]).lower()
        
        return seo_title, meta_desc, focus_keyword
    
    def _get_product_images(self, main_image: str, additional_images: str) -> str:
        """Sestaví seznam obrázků produktu."""
        images = []
        
        if pd.notna(main_image) and main_image:
            images.append(main_image.strip())
        
        if pd.notna(additional_images) and additional_images:
            additional = [img.strip() for img in additional_images.split(';') if img.strip()]
            images.extend(additional)
        
        return ','.join(images)
    
    def _create_woo_product(self, row: pd.Series, product_type: str = 'simple', parent_sku: str = '') -> Dict:
        """Vytvoří WooCommerce produkt ze záznamu."""
        params = self._parse_parameters(row.get('HodnotyParametru', ''))
        
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
        important_attrs = ['velikost', 'barva', 'pohlavi', 'sport', 'material']
        for attr in important_attrs:
            if attr in params and attr_counter <= 3:
                attributes[f'Attribute {attr_counter} name'] = attr.title()
                attributes[f'Attribute {attr_counter} value(s)'] = params[attr]
                attributes[f'Attribute {attr_counter} visible'] = '1'
                attributes[f'Attribute {attr_counter} global'] = '1'
                attr_counter += 1
        
        # Tagy
        tags = []
        if 'pohlavi' in params:
            tags.append(params['pohlavi'])
        if 'sport' in params:
            tags.append(params['sport'])
        if 'material' in params:
            tags.append(params['material'])
        
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
    
    def transform_products(self) -> None:
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
        """Vytvoří název pro hlavní variabilní produkt."""
        first_product = variants_group.iloc[0]
        name = str(first_product['JmenoZbozi'])
        
        # Odstranění specifických variant z názvu
        params = self._parse_parameters(first_product.get('HodnotyParametru', ''))
        
        # Odstranění velikosti a barvy z názvu
        if 'velikost' in params:
            name = re.sub(r'\b' + re.escape(params['velikost']) + r'\b', '', name, flags=re.IGNORECASE)
        if 'barva' in params:
            name = re.sub(r'\b' + re.escape(params['barva']) + r'\b', '', name, flags=re.IGNORECASE)
        
        # Vyčištění názvu
        name = re.sub(r'\s+', ' ', name).strip()
        
        return name
    
    def export_to_csv(self, output_file: str = 'woocommerce_products.csv') -> None:
        """Exportuje produkty do WooCommerce CSV."""
        logger.info(f"Exportuji produkty do {output_file}")
        
        # Vytvoření DataFrame
        df = pd.DataFrame(self.woo_products)
        
        # Zajištění všech sloupců
        for col in self.woo_columns:
            if col not in df.columns:
                df[col] = ''
        
        # Řazení sloupců podle WooCommerce standardu
        df = df.reindex(columns=self.woo_columns)
        
        # Export do CSV
        df.to_csv(output_file, index=False, encoding='utf-8-sig', sep=',')
        
        logger.info(f"Export dokončen: {len(df)} produktů uloženo do {output_file}")
    
    def generate_categories_csv(self, output_file: str = 'woocommerce_categories.csv') -> None:
        """Generuje samostatný CSV soubor s kategoriemi."""
        logger.info("Generuji CSV s kategoriemi")
        
        categories = []
        for cat_id, cat_data in self.category_mapping.items():
            if cat_data['name'] and cat_data['name'] != 'ROOT_1':
                category = {
                    'Category ID': cat_id,
                    'Category Name': cat_data['name'],
                    'Category Slug': cat_data['slug'],
                    'Category Parent': cat_data['parent'] if cat_data['parent'] != 'ROOT_1' else '',
                    'Category Description': cat_data['description']
                }
                categories.append(category)
        
        df_categories = pd.DataFrame(categories)
        df_categories.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        logger.info(f"Kategorie exportovány do {output_file}")
    
    def run_transformation(self, output_dir: str = './output/') -> None:
        """Spustí kompletní transformaci."""
        logger.info("=== SPUŠTĚNÍ FASTCENTRIK TO WOOCOMMERCE TRANSFORMACE ===")
        
        # Vytvoření výstupní složky
        Path(output_dir).mkdir(exist_ok=True)
        
        try:
            # 1. Načtení dat
            self.load_data()
            
            # 2. Transformace produktů
            self.transform_products()
            
            # 3. Export produktů
            products_file = Path(output_dir) / 'woocommerce_products.csv'
            self.export_to_csv(str(products_file))
            
            # 4. Export kategorií
            categories_file = Path(output_dir) / 'woocommerce_categories.csv'
            self.generate_categories_csv(str(categories_file))
            
            # 5. Statistiky
            self._print_transformation_stats()
            
            logger.info("=== TRANSFORMACE ÚSPĚŠNĚ DOKONČENA ===")
            
        except Exception as e:
            logger.error(f"Chyba během transformace: {e}")
            raise
    
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


def main():
    """Hlavní funkce pro spuštění transformace."""
    # Konfigurace
    EXCEL_FILE = "Export_Excel_Lite 1.xls"  # Cesta k vašemu souboru
    OUTPUT_DIR = "./woocommerce_output/"
    
    # Spuštění transformace
    transformer = FastCentrikToWooCommerce(EXCEL_FILE)
    transformer.run_transformation(OUTPUT_DIR)
    
    print(f"\n✅ Transformace dokončena!")
    print(f"📁 Výstupní soubory jsou v: {OUTPUT_DIR}")
    print(f"📄 woocommerce_products.csv - produkty pro import")
    print(f"📄 woocommerce_categories.csv - kategorie pro import")


if __name__ == "__main__":
    main()