#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastCentrik to WebToffee CSV Transformer
========================================

Transformuje data z FastCentrik platformy do WebToffee CSV formátu pro WooCommerce.
WebToffee formát má specifické požadavky na strukturu atributů a taxonomií.

Autor: FastCentrik Migration Tool
Verze: 1.0
"""

import pandas as pd
import re
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional
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


class WebToffeeTransformer:
    """
    Transformuje FastCentrik data do WebToffee CSV formátu.
    
    WebToffee formát specifika:
    - Používá post_parent s ID místo parent_sku
    - Atributy mají formát: attribute:Name, attribute_data:Name, meta:attribute_name
    - attribute_data obsahuje: position|visible|variation (např. "0|1|1")
    - Taxonomie používají prefix tax: (tax:product_type, tax:product_cat, tax:product_tag)
    - tax:product_type používá "Simple" nebo "Variable" (kapitalizované)
    - Obrázky jsou oddělené pipe symbolem |
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
        self.validation_errors = []
        self.product_id_counter = 1000  # Počáteční ID pro produkty
        self.parent_id_mapping = {}  # Mapování parent SKU na ID
        
        # Inicializace category mapperu
        if CATEGORY_MAPPING_SETTINGS.get('use_intelligent_mapping', False):
            self.category_mapper = CategoryMapper()
            logger.info("Inteligentní mapování kategorií aktivováno")
        else:
            self.category_mapper = None
    
    def _create_category_mapping(self) -> None:
        """Vytvoří mapování kategorií s hierarchickou strukturou."""
        logger.info("Vytvářím mapování kategorií")
        
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
    
    def _get_product_images(self, main_image: str, additional_images: str) -> str:
        """
        Sestaví seznam obrázků produktu s použitím base URL.
        WebToffee používá pipe | jako oddělovač.
        """
        images = []
        base_url = IMAGE_BASE_URL.strip('/')
        
        if pd.notna(main_image) and main_image.strip():
            image_path = main_image.strip().lstrip('/')
            images.append(f"{base_url}/{image_path}")
        
        if pd.notna(additional_images) and additional_images.strip():
            for img in additional_images.split(';'):
                if img.strip():
                    image_path = img.strip().lstrip('/')
                    images.append(f"{base_url}/{image_path}")
        
        return '|'.join(images)

    def _get_all_variant_images(self, variants_group: List[pd.Series]) -> str:
        """Sestaví seznam všech unikátních obrázků z dané skupiny variant."""
        all_image_paths = []
        seen_images = set()
        logger.info(f"Aggregating images for group of {len(variants_group)} variants.")

        for i, variant in enumerate(variants_group):
            main_image = variant.get('HlavniObrazek')
            additional_images = variant.get('DalsiObrazky')
            logger.debug(f"Variant {i} SKU {variant.get('KodZbozi')}: main='{main_image}', additional='{additional_images}'")

            # Zpracování hlavního obrázku
            if pd.notna(main_image) and main_image.strip():
                if main_image not in seen_images:
                    all_image_paths.append(main_image.strip())
                    seen_images.add(main_image)
                    logger.debug(f"Added main image: {main_image}")

            # Zpracování dalších obrázků
            if pd.notna(additional_images) and additional_images.strip():
                for img in additional_images.split(';'):
                    img_stripped = img.strip()
                    if img_stripped and img_stripped not in seen_images:
                        all_image_paths.append(img_stripped)
                        seen_images.add(img_stripped)
                        logger.debug(f"Added additional image: {img_stripped}")

        # Sestavení finálního řetězce obrázků
        base_url = IMAGE_BASE_URL.strip('/')
        image_urls = [f"{base_url}/{img.lstrip('/')}" for img in all_image_paths]
        
        final_image_string = '|'.join(image_urls)
        logger.info(f"Aggregated {len(image_urls)} unique images for the group: {final_image_string[:100]}...")
        return final_image_string
    
    def _format_price(self, price: any) -> str:
        """Formátuje cenu - převede čárku na tečku."""
        if pd.isna(price) or price == '':
            return ''
        return str(price).replace(',', '.')
    
    def _extract_variant_attributes(self, row: pd.Series) -> Dict[str, str]:
        """Extrahuje atributy varianty z parametrů nebo názvu."""
        params = parse_parameters(row.get('HodnotyParametru', ''))
        
        # Pokud nejsou parametry, zkusíme extrahovat velikost z názvu
        if not params and 'JmenoZbozi' in row:
            name = str(row['JmenoZbozi'])
            # Hledáme velikost na konci názvu (např. "39 1/3", "40", "41 1/3")
            size_match = re.search(r'\b(\d{2}(?:\s+\d/\d)?)\b$', name)
            if size_match:
                params['velikost'] = size_match.group(1)
        
        # Filtrujeme pouze variant atributy
        variant_attrs = {}
        for attr_name in VARIANT_SETTINGS.get('variant_attributes', ['velikost', 'barva']):
            if attr_name in params:
                variant_attrs[attr_name] = params[attr_name]
        
        return variant_attrs
    
    def _create_parent_attributes(self, variants_group: pd.DataFrame) -> Dict[str, str]:
        """
        Vytvoří atributy pro parent produkt ve WebToffee formátu.
        Shromáždí všechny unikátní hodnoty atributů ze všech variant.
        """
        all_attributes = {}
        
        # Shromáždíme všechny unikátní hodnoty atributů
        for _, variant in variants_group.iterrows():
            variant_attrs = self._extract_variant_attributes(variant)
            
            for attr_name, attr_value in variant_attrs.items():
                if attr_name not in all_attributes:
                    all_attributes[attr_name] = set()
                all_attributes[attr_name].add(attr_value)
        
        # Převod na WebToffee formát
        woo_attributes = {}
        position = 0
        
        for attr_name, values in all_attributes.items():
            mapped_name = ATTRIBUTE_MAPPING.get(attr_name, attr_name)
            sorted_values = sorted(values)
            
            # WebToffee formát pro atributy - používáme pa_ prefix
            attr_key = f'pa_{mapped_name.lower()}'
            
            # WebToffee formát pro atributy
            woo_attributes[f'attribute:{attr_key}'] = '|'.join(sorted_values)
            # position|visible|variation
            woo_attributes[f'attribute_data:{attr_key}'] = f'{position}|1|1'
            woo_attributes[f'attribute_default:{attr_key}'] = sorted_values[0] if sorted_values else ''
            
            position += 1
        
        return woo_attributes
    
    def _create_variant_attributes(self, row: pd.Series) -> Dict[str, str]:
        """Vytvoří atributy pro variantu ve WebToffee formátu."""
        variant_attrs = self._extract_variant_attributes(row)
        woo_attributes = {}
        position = 0
        
        for attr_name, attr_value in variant_attrs.items():
            mapped_name = ATTRIBUTE_MAPPING.get(attr_name, attr_name)
            
            # WebToffee formát pro varianty - používáme pa_ prefix
            attr_key = f'pa_{mapped_name.lower()}'
            
            # Pro varianty pouze meta atribut s hodnotou
            woo_attributes[f'meta:attribute_{attr_key}'] = attr_value
            
            position += 1
        
        return woo_attributes
    
    def _get_category_path_for_product(self, row: pd.Series) -> str:
        """Získá cestu kategorie pro produkt s podporou inteligentního mapování."""
        name = str(row['JmenoZbozi'])
        params = parse_parameters(row.get('HodnotyParametru', ''))
        
        if self.category_mapper and CATEGORY_MAPPING_SETTINGS.get('use_intelligent_mapping', False):
            if CATEGORY_MAPPING_SETTINGS.get('enable_multi_category', False):
                categories, _ = self.category_mapper.map_product_to_multiple_categories(
                    product_name=name,
                    product_params=params,
                    original_category=self._get_category_path(row.get('InetrniKodyKategorii', '')),
                    max_categories=CATEGORY_MAPPING_SETTINGS.get('max_categories_per_product', 2),
                    strategy=CATEGORY_MAPPING_SETTINGS.get('multi_category_strategy', 'complementary')
                )
                
                if categories:
                    separator = '|'  # WebToffee používá pipe pro více kategorií
                    if CATEGORY_MAPPING_SETTINGS.get('use_leaf_category_only', True):
                        leaf_categories = [cat.split(' > ')[-1].strip() for cat in categories]
                        return separator.join(leaf_categories)
                    else:
                        return separator.join(categories)
            else:
                category_path, _ = self.category_mapper.map_product_to_category(
                    product_name=name,
                    product_params=params,
                    original_category=self._get_category_path(row.get('InetrniKodyKategorii', ''))
                )
                return category_path
        else:
            # Původní mapování
            if pd.notna(row.get('InetrniKodyKategorii')):
                category_path = self._get_category_path(row['InetrniKodyKategorii'])
                if CATEGORY_MAPPING_SETTINGS.get('use_leaf_category_only', True) and category_path:
                    return category_path.split(' > ')[-1].strip()
                return category_path
        
        return ""
    
    def _create_woo_product(self, row: pd.Series, product_type: str = 'simple',
                           parent_id: str = '', parent_attributes: Dict = None,
                           is_variation: bool = False, parent_sku: str = '',
                           menu_order: int = 0) -> Dict:
        """
        Vytvoří WooCommerce produkt ve WebToffee formátu.
        
        Args:
            row: Data produktu
            product_type: Typ produktu (simple, variable)
            parent_id: ID parent produktu pro varianty
            parent_attributes: Atributy parent produktu (pro varianty)
            is_variation: True pokud je to varianta
            parent_sku: SKU parent produktu
            menu_order: Pořadí varianty
        """
        # Přiřadíme ID produktu
        product_id = str(self.product_id_counter)
        self.product_id_counter += 1
        
        # Základní informace
        sku = str(row['KodZbozi'])
        
        # Pro varianty používáme minimální data
        if is_variation:
            variant_attrs = self._extract_variant_attributes(row)
            first_attr_name = next(iter(variant_attrs.keys()), "").capitalize()
            first_attr_value = next(iter(variant_attrs.values()), "")
            short_description = f"{first_attr_name}: {first_attr_value}"
            
            woo_product = {
                'ID': product_id,
                'post_parent': parent_id,
                'parent_sku': parent_sku,
                'sku': '',  # Varianty mají prázdné SKU
                'post_title': str(row['JmenoZbozi']),
                'post_excerpt': short_description,
                'post_content': str(row.get('Popis', '')) if pd.notna(row.get('Popis')) else '',
                'post_status': 'publish' if row.get('Vypnuto', 0) == 0 else 'draft',
                'regular_price': self._format_price(row.get('CenaBezna', '')),
                'sale_price': self._format_price(row.get('ZakladniCena', '')) if pd.notna(row.get('ZakladniCena')) else '',
                'stock_status': 'instock' if row.get('NaSklade', 0) > 0 else 'outofstock',
                'stock': str(row.get('NaSklade', 0)),
                'manage_stock': 'yes',
                'weight': self._format_price(row.get('Hmotnost', '')),
                'images': '',  # Varianty nemají vlastní obrázky
                'tax:product_type': '',  # Prázdný typ pro varianty
                'tax:product_cat': '',
                'tax:product_tag': '',
                'visibility': 'visible',
                'backorders': 'no',
                'downloadable': 'no',
                'virtual': 'no',
                'menu_order': str(menu_order),
                'low_stock_amount': ''
            }
        else:
            # Plné informace pro simple a variable produkty
            name = str(row['JmenoZbozi'])
            category_path = self._get_category_path_for_product(row)
            regular_price = self._format_price(row.get('CenaBezna', ''))
            sale_price = self._format_price(row.get('ZakladniCena', ''))
            description = str(row.get('Popis', '')) if pd.notna(row.get('Popis')) else ''
            short_description = str(row.get('KratkyPopis', '')) if pd.notna(row.get('KratkyPopis')) else ''
            images = self._get_product_images(row.get('HlavniObrazek'), row.get('DalsiObrazky'))
            stock_quantity = row.get('NaSklade', 0)
            stock_status = 'instock' if stock_quantity > 0 else 'outofstock'
            post_status = 'publish' if row.get('Vypnuto', 0) == 0 else 'draft'
            
            # Tagy
            tags = []
            if TAG_SETTINGS.get('auto_generate_tags', False):
                params = parse_parameters(row.get('HodnotyParametru', ''))
                tag_attributes = TAG_SETTINGS.get('tag_attributes', [])
                for tag_attr in tag_attributes:
                    if tag_attr in params:
                        tags.append(params[tag_attr])
                tags = tags[:TAG_SETTINGS.get('max_tags_per_product', 5)]
            
            # Určení správného typu produktu pro WebToffee
            webtoffee_type = 'Simple' if product_type == 'simple' else 'Variable'
            
            woo_product = {
                'ID': product_id,
                'post_parent': '',
                'parent_sku': '',
                'sku': sku,
                'post_title': name,
                'post_excerpt': short_description,
                'post_content': description,
                'post_status': post_status,
                'regular_price': regular_price,
                'sale_price': sale_price if sale_price != regular_price else '',
                'stock_status': stock_status,
                'stock': str(stock_quantity),
                'manage_stock': 'yes',
                'weight': self._format_price(row.get('Hmotnost', '')),
                'images': images,
                'tax:product_type': webtoffee_type,
                'tax:product_cat': category_path,
                'tax:product_tag': '|'.join(tags) if tags else '',
                'visibility': 'visible',
                'backorders': 'no',
                'downloadable': 'no',
                'virtual': 'no',
                'menu_order': '0',
                'low_stock_amount': ''
            }
        # Přidání atributů podle typu produktu
        if product_type == 'variable' and not is_variation:
            # Parent produkt - agregované atributy ze všech variant
            if parent_attributes:
                woo_product.update(parent_attributes)
        elif is_variation:
            # Varianta - pouze specifické hodnoty atributů
            variant_attrs = self._create_variant_attributes(row)
            woo_product.update(variant_attrs)
        elif product_type == 'simple':
            # Jednoduchý produkt - všechny parametry jako atributy
            params = parse_parameters(row.get('HodnotyParametru', ''))
            position = 0
            for attr_name, attr_value in params.items():
                mapped_name = ATTRIBUTE_MAPPING.get(attr_name, attr_name)
                capitalized_name = mapped_name.capitalize()
                woo_product[f'attribute:{capitalized_name}'] = attr_value
                woo_product[f'attribute_data:{capitalized_name}'] = f'{position}|1|0'  # 0 na konci = není pro varianty
                woo_product[f'meta:attribute_{mapped_name.lower()}'] = ''
                position += 1
        
        return woo_product
    
    def _group_products_by_master_code(self) -> Dict[str, List[pd.Series]]:
        """
        Seskupí produkty podle KodMasterVyrobku pro detekci variant.
        
        Returns:
            Dict mapující master kód na seznam produktů
        """
        groups = {}
        
        for _, product in self.products_data.iterrows():
            master_code = product.get('KodMasterVyrobku', '')
            
            # Pokud má master kód, přidáme do skupiny
            if pd.notna(master_code) and master_code:
                if master_code not in groups:
                    groups[master_code] = []
                groups[master_code].append(product)
        
        # Filtrujeme skupiny s více než jedním produktem
        variant_groups = {k: v for k, v in groups.items() if len(v) > 1}
        
        logger.info(f"Detekováno {len(variant_groups)} skupin variant podle KodMasterVyrobku")
        
        return variant_groups
    
    def _group_products_by_sku_pattern(self) -> Dict[str, List[pd.Series]]:
        """
        Alternativní metoda - seskupí produkty podle SKU vzoru.
        Např. 033201, 033201_2, 033201_3
        
        Returns:
            Dict mapující base SKU na seznam produktů
        """
        groups = {}
        all_products = {}
        
        # Nejprve uložíme všechny produkty podle SKU
        for _, product in self.products_data.iterrows():
            sku = str(product['KodZbozi'])
            all_products[sku] = product
        
        # Najdeme base SKU které mají varianty
        for sku, product in all_products.items():
            # Pokud SKU končí _číslo, je to varianta
            match = re.match(r'^(.+?)_\d+$', sku)
            if match:
                base_sku = match.group(1)
                if base_sku not in groups:
                    groups[base_sku] = []
                groups[base_sku].append(product)
                
                # Přidáme také base SKU pokud existuje
                if base_sku in all_products:
                    if all_products[base_sku] not in groups[base_sku]:
                        groups[base_sku].append(all_products[base_sku])
        
        # Filtrujeme skupiny s více než jedním produktem
        variant_groups = {k: v for k, v in groups.items() if len(v) > 1}
        
        logger.info(f"Detekováno {len(variant_groups)} skupin variant podle SKU vzoru")
        
        return variant_groups
    
    def _create_parent_name(self, variants_group: List[pd.Series]) -> str:
        """Vytvoří název pro parent produkt."""
        first_product = variants_group[0]
        name = str(first_product['JmenoZbozi'])
        
        # Odstranění variant-specific částí z názvu
        variant_attrs = self._extract_variant_attributes(first_product)
        
        for attr_value in variant_attrs.values():
            # Odstranit hodnotu atributu z názvu
            name = re.sub(r'\b' + re.escape(str(attr_value)) + r'\b', '', name, flags=re.IGNORECASE)
        
        # Vyčištění názvu
        name = re.sub(r'\s+', ' ', name).strip()
        name = re.sub(r'\s*-\s*$', '', name)  # Odstranit pomlčku na konci
        
        return name
    
    def _transform_products(self) -> None:
        """Hlavní metoda pro transformaci produktů."""
        logger.info("Zahajuji transformaci produktů do WebToffee formátu")
        
        # Detekce variant - prioritně podle KodMasterVyrobku
        variant_groups = self._group_products_by_master_code()
        
        # Pokud nejsou master kódy, zkusíme SKU pattern
        if not variant_groups:
            logger.info("KodMasterVyrobku nenalezen, zkouším detekci podle SKU vzoru")
            variant_groups = self._group_products_by_sku_pattern()
        
        # Množina všech SKU které jsou součástí variant
        variant_skus = set()
        for group in variant_groups.values():
            for product in group:
                variant_skus.add(str(product['KodZbozi']))
        
        # Zpracování jednoduchých produktů
        simple_count = 0
        for _, product in self.products_data.iterrows():
            sku = str(product['KodZbozi'])
            if sku not in variant_skus:
                woo_product = self._create_woo_product(product, 'simple')
                self.woo_products.append(woo_product)
                simple_count += 1
        
        logger.info(f"Zpracováno {simple_count} jednoduchých produktů")
        
        # Zpracování variabilních produktů
        variable_count = 0
        variation_count = 0
        
        for master_code, variants in variant_groups.items():
            # Vytvoření parent produktu
            first_variant = variants[0]
            parent_sku = master_code  # SKU parenta je master_code
            
            # Upravíme název parent produktu
            parent_data = first_variant.copy()
            parent_data['JmenoZbozi'] = self._create_parent_name(variants)
            
            # Vytvoříme agregované atributy ze všech variant
            variants_df = pd.DataFrame(variants)
            parent_attributes = self._create_parent_attributes(variants_df)
            
            # Vytvoření parent produktu
            parent_product = self._create_woo_product(
                parent_data,
                'variable',
                parent_attributes=parent_attributes
            )
            parent_product['sku'] = parent_sku
            parent_product['post_parent'] = ''  # Parent nemá parent
            
            # Správné přiřazení obrázků k parent produktu
            aggregated_images = self._get_all_variant_images(variants)
            parent_product['images'] = aggregated_images
            logger.info(f"Assigned {len(aggregated_images.split('|')) if aggregated_images else 0} images to parent {parent_sku}")
            
            # Uložíme ID parent produktu pro varianty
            parent_id = parent_product['ID']
            self.parent_id_mapping[parent_sku] = parent_id
            
            self.woo_products.append(parent_product)
            variable_count += 1

            # Seřadit varianty pro správné menu_order
            def natural_sort_key(s):
                if isinstance(s, str):
                    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]
                return [s]

            primary_attr_name = VARIANT_SETTINGS.get('variant_attributes', ['velikost'])[0]
            
            # Dočasně přidáme klíč pro řazení
            for v in variants:
                attrs = self._extract_variant_attributes(v)
                v['sort_key'] = attrs.get(primary_attr_name, '')
            
            variants_sorted = sorted(variants, key=lambda v: natural_sort_key(v['sort_key']))

            # Zpracování jednotlivých variant
            for i, variant in enumerate(variants_sorted):
                variant_product = self._create_woo_product(
                    variant,
                    'simple',
                    parent_id=parent_id,
                    is_variation=True,
                    parent_sku=parent_sku,
                    menu_order=i + 1
                )
                self.woo_products.append(variant_product)
                variation_count += 1
        
        logger.info(f"Vytvořeno {variable_count} variable produktů a {variation_count} variant")
        logger.info(f"Celkem vytvořeno {len(self.woo_products)} produktů")
    
    def validate_products(self) -> List[str]:
        """Validuje vytvořené produkty."""
        errors = []
        
        # Najít všechny parent produkty a jejich SKUs
        parent_ids = set()
        parent_skus_from_parents = set()
        for product in self.woo_products:
            if product['tax:product_type'] == 'Variable':
                parent_ids.add(product['ID'])
                parent_skus_from_parents.add(product['sku'])
        
        # Kontrola variant
        for product in self.woo_products:
            if product.get('parent_sku'):  # Je to varianta
                # Kontrola post_parent
                if product['post_parent'] not in parent_ids:
                    errors.append(f"Varianta '{product['post_title']}' (parent_sku: {product['parent_sku']}) odkazuje на neexistující parent ID {product['post_parent']}")

                # Kontrola parent_sku
                if product['parent_sku'] not in parent_skus_from_parents:
                    errors.append(f"Varianta '{product['post_title']}' odkazuje na neexistující parent SKU {product['parent_sku']}.")

                # Kontrola prázdného SKU
                if product['sku'] != '':
                    errors.append(f"Varianta '{product['post_title']}' (parent_sku: {product['parent_sku']}) by měla mít prázdné SKU, ale má '{product['sku']}'.")

                # Kontrola meta atributů (varianty mají pouze meta:attribute_pa_*)
                has_meta_attributes = any(
                    key.startswith('meta:attribute_pa_') and product.get(key)
                    for key in product.keys()
                )
                if not has_meta_attributes:
                    errors.append(f"Varianta '{product['post_title']}' (parent_sku: {product['parent_sku']}) nemá žádné meta atributy")
        
        # Kontrola variable produktů
        for product in self.woo_products:
            if product['tax:product_type'] == 'Variable':
                # Musí mít agregované atributy
                has_attributes = any(
                    key.startswith('attribute:') and product.get(key)
                    for key in product.keys()
                )
                if not has_attributes:
                    errors.append(f"Variable produkt {product['sku']} nemá žádné atributy")
                
                # Variable produkty mohou mít stock ve WebToffee
                pass
        
        return errors
    
    def run_transformation(self) -> Tuple[List[Dict], List[str]]:
        """
        Spustí kompletní transformaci dat.
        
        Returns:
            Tuple[List[Dict], List[str]]: Seznam produktů a seznam validačních chyb
        """
        logger.info("=== SPUŠTĚNÍ WEBTOFFEE TRANSFORMACE ===")
        
        # Vytvoření mapování kategorií
        self._create_category_mapping()
        
        # Transformace produktů
        self._transform_products()
        
        # Validace
        self.validation_errors = self.validate_products()
        if self.validation_errors:
            logger.warning(f"Nalezeno {len(self.validation_errors)} validačních chyb:")
            for error in self.validation_errors[:10]:
                logger.warning(f"  - {error}")
        
        # Statistiky
        self._print_transformation_stats()
        
        logger.info("=== WEBTOFFEE TRANSFORMACE DOKONČENA ===")
        
        return self.woo_products, self.validation_errors
    
    def _print_transformation_stats(self) -> None:
        """Vypíše statistiky transformace."""
        simple_count = len([p for p in self.woo_products if p['tax:product_type'] == 'Simple'])
        variable_count = len([p for p in self.woo_products if p['tax:product_type'] == 'Variable'])
        variation_count = len([p for p in self.woo_products if p['tax:product_type'] == ''])  # Varianty mají prázdný typ
        
        print("\n" + "="*50)
        print("STATISTIKY WEBTOFFEE TRANSFORMACE")
        print("="*50)
        print(f"Celkem FastCentrik produktů: {len(self.products_data)}")
        print(f"Celkem WebToffee produktů: {len(self.woo_products)}")
        print(f"  - Jednoduché produkty: {simple_count}")
        print(f"  - Variable produkty: {variable_count}")
        print(f"  - Varianty: {variation_count}")
        print(f"Celkem kategorií: {len(self.category_mapping)}")
        if self.validation_errors:
            print(f"⚠️  Validační chyby: {len(self.validation_errors)}")
        print("="*50)