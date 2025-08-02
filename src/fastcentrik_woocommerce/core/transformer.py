#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastCentrik to WooCommerce CSV Transformer - Vylepšená verze
============================================================

Transformuje data z FastCentrik platformy do WooCommerce kompatibilního CSV formátu.
Podporuje variabilní produkty, kategorie, atributy a SEO optimalizaci.

Autor: FastCentrik Migration Tool
Verze: 2.0
"""

import pandas as pd
import re
from pathlib import Path
from typing import Dict, List, Tuple, Set
import logging
import sys

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.fastcentrik_woocommerce.utils.utils import create_slug, parse_parameters
from config.config import (
    SEO_SETTINGS,
    TAG_SETTINGS,
    VARIANT_SETTINGS,
    IMAGE_BASE_URL,
    ATTRIBUTE_MAPPING,
    STOCK_SETTINGS,
    CATEGORY_MAPPING_SETTINGS
)
from src.fastcentrik_woocommerce.mappers.category_mapper import CategoryMapper

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
        self.validation_errors = []
        
        # Inicializace inteligentního category mapperu
        if CATEGORY_MAPPING_SETTINGS.get('use_intelligent_mapping', False):
            self.category_mapper = CategoryMapper()
            logger.info("Inteligentní mapování kategorií aktivováno")
        else:
            self.category_mapper = None
    
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
    
    def _get_stock_data(self, row: pd.Series, product_type: str = 'simple') -> Dict:
        """Vrátí kompletní data o skladových zásobách"""
        stock_quantity = row.get('NaSklade', 0)
        
        # Základní stock data
        stock_data = {
            'In stock?': '1' if stock_quantity > 0 else '0',
            'Stock': str(stock_quantity) if product_type != 'variable' else '',
            'Low stock amount': str(STOCK_SETTINGS.get('low_stock_threshold', 5)),
            'Backorders allowed?': '1' if STOCK_SETTINGS.get('enable_backorders', False) else '0',
            'Manage stock?': '1' if product_type != 'variable' else ''
        }
        
        # Pro varianty přidat stock status
        if product_type == 'variation':
            if stock_quantity <= 0 and STOCK_SETTINGS.get('enable_backorders', False):
                stock_data['Stock status'] = 'onbackorder'
            elif stock_quantity <= 0:
                stock_data['Stock status'] = 'outofstock'
            else:
                stock_data['Stock status'] = 'instock'
        
        return stock_data
    
    def _create_parent_attributes(self, variants_group: pd.DataFrame) -> Dict:
        """Vytvoří souhrnné atributy pro parent produkt ze všech variant"""
        all_attributes = {}
        
        # Shromáždíme všechny unikátní hodnoty atributů ze všech variant
        for _, variant in variants_group.iterrows():
            params = parse_parameters(variant.get('HodnotyParametru', ''))
            
            for attr_name in VARIANT_SETTINGS.get('variant_attributes', ['velikost', 'barva']):
                if attr_name in params:
                    if attr_name not in all_attributes:
                        all_attributes[attr_name] = set()
                    all_attributes[attr_name].add(params[attr_name])
        
        # Převod na WooCommerce formát
        woo_attributes = {}
        attr_counter = 1
        
        for attr_name, values in all_attributes.items():
            mapped_name = ATTRIBUTE_MAPPING.get(attr_name, attr_name.title())
            woo_attributes[f'Attribute {attr_counter} name'] = mapped_name
            woo_attributes[f'Attribute {attr_counter} value(s)'] = ', '.join(sorted(values))
            woo_attributes[f'Attribute {attr_counter} visible'] = '1'
            woo_attributes[f'Attribute {attr_counter} global'] = '1'
            attr_counter += 1
        
        return woo_attributes
    
    def _calculate_parent_stock(self, variants_group: pd.DataFrame) -> Tuple[str, str]:
        """Vypočítá skladové zásoby pro parent produkt"""
        any_in_stock = False
        
        for _, variant in variants_group.iterrows():
            variant_stock = variant.get('NaSklade', 0)
            if variant_stock > 0:
                any_in_stock = True
                break
        
        # WooCommerce parent produkty nemají vlastní stock
        in_stock = '1' if any_in_stock else '0'
        stock_quantity = ''  # Vždy prázdné pro variable produkty
        
        return in_stock, stock_quantity
    
    def _get_stock_data(self, row: pd.Series, product_type: str = 'simple') -> Dict:
        """Vrátí kompletní data o skladových zásobách"""
        stock_quantity = row.get('NaSklade', 0)
        
        # Základní stock data
        stock_data = {
            'In stock?': '1' if stock_quantity > 0 else '0',
            'Stock': str(stock_quantity) if product_type != 'variable' else '',
            'Low stock amount': str(STOCK_SETTINGS.get('low_stock_threshold', 5)),
            'Backorders allowed?': '1' if STOCK_SETTINGS.get('enable_backorders', False) else '0',
            'Manage stock?': '1' if product_type != 'variable' else ''
        }
        
        # Pro varianty přidat stock status
        if product_type == 'variation':
            if stock_quantity <= 0 and STOCK_SETTINGS.get('enable_backorders', False):
                stock_data['Stock status'] = 'onbackorder'
            elif stock_quantity <= 0:
                stock_data['Stock status'] = 'outofstock'
            else:
                stock_data['Stock status'] = 'instock'
        
        return stock_data
    
    def _create_parent_attributes(self, variants_group: pd.DataFrame) -> Dict:
        """Vytvoří souhrnné atributy pro parent produkt ze všech variant"""
        all_attributes = {}
        
        # Shromáždíme všechny unikátní hodnoty atributů ze všech variant
        for _, variant in variants_group.iterrows():
            params = parse_parameters(variant.get('HodnotyParametru', ''))
            
            for attr_name in VARIANT_SETTINGS.get('variant_attributes', ['velikost', 'barva']):
                if attr_name in params:
                    if attr_name not in all_attributes:
                        all_attributes[attr_name] = set()
                    all_attributes[attr_name].add(params[attr_name])
        
        # Převod na WooCommerce formát
        woo_attributes = {}
        attr_counter = 1
        
        for attr_name, values in all_attributes.items():
            mapped_name = ATTRIBUTE_MAPPING.get(attr_name, attr_name.title())
            woo_attributes[f'Attribute {attr_counter} name'] = mapped_name
            woo_attributes[f'Attribute {attr_counter} value(s)'] = ', '.join(sorted(values))
            woo_attributes[f'Attribute {attr_counter} visible'] = '1'
            woo_attributes[f'Attribute {attr_counter} global'] = '1'
            attr_counter += 1
        
        return woo_attributes
    
    def _calculate_parent_stock(self, variants_group: pd.DataFrame) -> Tuple[str, str]:
        """Vypočítá skladové zásoby pro parent produkt"""
        any_in_stock = False
        
        for _, variant in variants_group.iterrows():
            variant_stock = variant.get('NaSklade', 0)
            if variant_stock > 0:
                any_in_stock = True
                break
        
        # WooCommerce parent produkty nemají vlastní stock
        in_stock = '1' if any_in_stock else '0'
        stock_quantity = ''  # Vždy prázdné pro variable produkty
        
        return in_stock, stock_quantity
    
    def _create_woo_product(self, row: pd.Series, product_type: str = 'simple', parent_sku: str = '') -> Dict:
        """Vytvoří WooCommerce produkt ze záznamu."""
        params = parse_parameters(row.get('HodnotyParametru', ''))
        
        # Základní informace
        sku = str(row['KodZbozi'])
        name = str(row['JmenoZbozi'])
        
        # Kategorie - použití inteligentního mapování
        category_path = ""
        
        if self.category_mapper and CATEGORY_MAPPING_SETTINGS.get('use_intelligent_mapping', False):
            # Kontrola, zda je povoleno multi-category mapování
            if CATEGORY_MAPPING_SETTINGS.get('enable_multi_category', False):
                # Multi-category mapování
                categories, mapping_type = self.category_mapper.map_product_to_multiple_categories(
                    product_name=name,
                    product_params=params,
                    original_category=self._get_category_path(row.get('InetrniKodyKategorii', '')),
                    max_categories=CATEGORY_MAPPING_SETTINGS.get('max_categories_per_product', 2),
                    strategy=CATEGORY_MAPPING_SETTINGS.get('multi_category_strategy', 'complementary')
                )
                
                # Spojit kategorie pomocí definovaného oddělovače
                if categories:
                    separator = CATEGORY_MAPPING_SETTINGS.get('multi_category_separator', ', ')
                    # Pokud je nastaveno použití pouze koncové kategorie
                    if CATEGORY_MAPPING_SETTINGS.get('use_leaf_category_only', True):
                        # Extrahovat pouze název koncové kategorie z každé cesty
                        leaf_categories = []
                        for cat_path in categories:
                            # Získat poslední část cesty (za posledním ' > ')
                            leaf_name = cat_path.split(' > ')[-1].strip()
                            leaf_categories.append(leaf_name)
                        category_path = separator.join(leaf_categories)
                    else:
                        # Použít celou cestu
                        category_path = separator.join(categories)
                
                # Logování nenamapovaných produktů
                if mapping_type == "unmapped" and CATEGORY_MAPPING_SETTINGS.get('log_unmapped_products', True):
                    logger.warning(f"Produkt '{name}' (SKU: {sku}) nebyl namapován do žádné kategorie")
            else:
                # Single-category mapování (zpětná kompatibilita)
                category_path, mapping_type = self.category_mapper.map_product_to_category(
                    product_name=name,
                    product_params=params,
                    original_category=self._get_category_path(row.get('InetrniKodyKategorii', ''))
                )
                
                # Logování nenamapovaných produktů
                if mapping_type == "unmapped" and CATEGORY_MAPPING_SETTINGS.get('log_unmapped_products', True):
                    logger.warning(f"Produkt '{name}' (SKU: {sku}) nebyl namapován do žádné kategorie")
        else:
            # Původní mapování
            if pd.notna(row.get('InetrniKodyKategorii')):
                category_path = self._get_category_path(row['InetrniKodyKategorii'])
                # Pokud je nastaveno použití pouze koncové kategorie
                if CATEGORY_MAPPING_SETTINGS.get('use_leaf_category_only', True) and category_path:
                    category_path = category_path.split(' > ')[-1].strip()
        
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
        
        # Skladové zásoby
        stock_data = self._get_stock_data(row, product_type)
        
        # Atributy
        attributes = {}
        if product_type == 'variation':
            # Pro varianty přidáme pouze atributy, které jsou variant attributes
            attr_counter = 1
            for attr_name in VARIANT_SETTINGS.get('variant_attributes', ['velikost', 'barva']):
                if attr_name in params:
                    mapped_name = ATTRIBUTE_MAPPING.get(attr_name, attr_name.title())
                    attributes[f'Attribute {attr_counter} name'] = mapped_name
                    attributes[f'Attribute {attr_counter} value(s)'] = params[attr_name]
                    attributes[f'Attribute {attr_counter} visible'] = '1'
                    attributes[f'Attribute {attr_counter} global'] = '1'
                    attr_counter += 1
        elif product_type == 'simple':
            # Pro jednoduché produkty přidáme všechny atributy
            attr_counter = 1
            for attr_name, attr_value in params.items():
                if attr_counter > 3:
                    break
                mapped_name = ATTRIBUTE_MAPPING.get(attr_name, attr_name.title())
                attributes[f'Attribute {attr_counter} name'] = mapped_name
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
            'In stock?': stock_data['In stock?'],
            'Stock': stock_data['Stock'],
            'Low stock amount': stock_data['Low stock amount'],
            'Backorders allowed?': stock_data['Backorders allowed?'],
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
        
        # Přidání stock status pro varianty
        if product_type == 'variation' and 'Stock status' in stock_data:
            woo_product['Stock status'] = stock_data['Stock status']
        
        return woo_product
    
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
            
            # Vytvoření parent produktu
            parent_product = self._create_woo_product(main_product, 'variable')
            parent_product['SKU'] = f"{master_code}_parent"
            
            # Přidání souhrnných atributů
            parent_attributes = self._create_parent_attributes(group)
            parent_product.update(parent_attributes)
            
            # Výpočet skladových zásob
            in_stock, stock = self._calculate_parent_stock(group)
            parent_product['In stock?'] = in_stock
            parent_product['Stock'] = stock
            parent_product['Manage stock?'] = ''  # Variable produkty neřídí stock přímo
            
            self.woo_products.append(parent_product)
            
            # Varianty
            for _, variant in group.iterrows():
                variant_product = self._create_woo_product(variant, 'variation', f"{master_code}_parent")
                self.woo_products.append(variant_product)
        
        logger.info(f"Vytvořeno celkem {len(self.woo_products)} WooCommerce produktů")
        
        # Debug výstup pokud je povoleno
        self._debug_product_structure()
        
        # Debug výstup pokud je povoleno
        self._debug_product_structure()

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
    
    def _debug_product_structure(self):
        """Vypíše debug informace o struktuře produktů"""
        if logging.getLogger().level == logging.DEBUG:
            print("\n=== DEBUG: Struktura produktů ===")
            
            variable_products = [p for p in self.woo_products if p['Type'] == 'variable']
            print(f"Variable produkty: {len(variable_products)}")
            
            for vp in variable_products[:5]:  # Omezit na prvních 5 pro přehlednost
                print(f"\nParent: {vp['SKU']}")
                print(f"  Název: {vp['Name']}")
                print(f"  Stock: {vp['Stock']} (měl by být prázdný)")
                print(f"  In stock?: {vp['In stock?']}")
                
                # Vypsat atributy
                attrs = []
                for i in range(1, 4):
                    attr_name = vp.get(f'Attribute {i} name')
                    attr_values = vp.get(f'Attribute {i} value(s)')
                    if attr_name:
                        attrs.append(f"{attr_name}: {attr_values}")
                print(f"  Atributy: {', '.join(attrs)}")
                
                # Najít varianty
                variants = [p for p in self.woo_products if p['Type'] == 'variation' and p['Parent'] == vp['SKU']]
                print(f"  Počet variant: {len(variants)}")
                for v in variants[:3]:  # Zobrazit max 3 varianty
                    print(f"    - {v['SKU']}: Stock={v['Stock']}, In stock={v['In stock?']}")
    
    def validate_products(self) -> List[str]:
        """Validuje vytvořené produkty před exportem"""
        errors = []
        parent_skus = set()
        
        # Najít všechny parent produkty
        for product in self.woo_products:
            if product['Type'] == 'variable':
                parent_skus.add(product['SKU'])
        
        # Zkontrolovat varianty
        for product in self.woo_products:
            if product['Type'] == 'variation':
                if product['Parent'] not in parent_skus:
                    errors.append(f"Varianta {product['SKU']} nemá parent produkt {product['Parent']}")
                
                # Kontrola atributů
                has_attributes = any(
                    product.get(f'Attribute {i} name') 
                    for i in range(1, 4)
                )
                if not has_attributes:
                    errors.append(f"Varianta {product['SKU']} nemá žádné atributy")
        
        # Kontrola parent produktů
        for product in self.woo_products:
            if product['Type'] == 'variable':
                # Musí mít atributy
                has_attributes = any(
                    product.get(f'Attribute {i} name') 
                    for i in range(1, 4)
                )
                if not has_attributes:
                    errors.append(f"Parent produkt {product['SKU']} nemá žádné atributy")
                
                # Neměl by mít stock
                if product.get('Stock'):
                    errors.append(f"Variable produkt {product['SKU']} má vyplněný stock: {product['Stock']}")
        
        return errors
    
    def _debug_product_structure(self):
        """Vypíše debug informace o struktuře produktů"""
        if logging.getLogger().level == logging.DEBUG:
            print("\n=== DEBUG: Struktura produktů ===")
            
            variable_products = [p for p in self.woo_products if p['Type'] == 'variable']
            print(f"Variable produkty: {len(variable_products)}")
            
            for vp in variable_products[:5]:  # Omezit na prvních 5 pro přehlednost
                print(f"\nParent: {vp['SKU']}")
                print(f"  Název: {vp['Name']}")
                print(f"  Stock: {vp['Stock']} (měl by být prázdný)")
                print(f"  In stock?: {vp['In stock?']}")
                
                # Vypsat atributy
                attrs = []
                for i in range(1, 4):
                    attr_name = vp.get(f'Attribute {i} name')
                    attr_values = vp.get(f'Attribute {i} value(s)')
                    if attr_name:
                        attrs.append(f"{attr_name}: {attr_values}")
                print(f"  Atributy: {', '.join(attrs)}")
                
                # Najít varianty
                variants = [p for p in self.woo_products if p['Type'] == 'variation' and p['Parent'] == vp['SKU']]
                print(f"  Počet variant: {len(variants)}")
                for v in variants[:3]:  # Zobrazit max 3 varianty
                    print(f"    - {v['SKU']}: Stock={v['Stock']}, In stock={v['In stock?']}")
    
    def validate_products(self) -> List[str]:
        """Validuje vytvořené produkty před exportem"""
        errors = []
        parent_skus = set()
        
        # Najít všechny parent produkty
        for product in self.woo_products:
            if product['Type'] == 'variable':
                parent_skus.add(product['SKU'])
        
        # Zkontrolovat varianty
        for product in self.woo_products:
            if product['Type'] == 'variation':
                if product['Parent'] not in parent_skus:
                    errors.append(f"Varianta {product['SKU']} nemá parent produkt {product['Parent']}")
                
                # Kontrola atributů
                has_attributes = any(
                    product.get(f'Attribute {i} name') 
                    for i in range(1, 4)
                )
                if not has_attributes:
                    errors.append(f"Varianta {product['SKU']} nemá žádné atributy")
        
        # Kontrola parent produktů
        for product in self.woo_products:
            if product['Type'] == 'variable':
                # Musí mít atributy
                has_attributes = any(
                    product.get(f'Attribute {i} name') 
                    for i in range(1, 4)
                )
                if not has_attributes:
                    errors.append(f"Parent produkt {product['SKU']} nemá žádné atributy")
                
                # Neměl by mít stock
                if product.get('Stock'):
                    errors.append(f"Variable produkt {product['SKU']} má vyplněný stock: {product['Stock']}")
        
        return errors
    
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
        
        # Validace
        validation_errors = self.validate_products()
        if validation_errors:
            logger.warning(f"Nalezeno {len(validation_errors)} validačních chyb:")
            for error in validation_errors[:10]:  # Zobrazit max 10 chyb
                logger.warning(f"  - {error}")
        
        self._print_transformation_stats()
        
        # Vytisknout report mapování kategorií
        if self.category_mapper and CATEGORY_MAPPING_SETTINGS.get('export_mapping_report', True):
            self.category_mapper.print_mapping_report()
        
        logger.info("=== TRANSFORMACE DAT DOKONČENA ===")
        return self.woo_products, self.woo_categories
    
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
        if self.validation_errors:
            print(f"⚠️  Validační chyby: {len(self.validation_errors)}")
        print("="*50)