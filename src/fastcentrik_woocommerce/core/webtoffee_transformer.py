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
import sys
import html
import logging
from html.parser import HTMLParser

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.fastcentrik_woocommerce.utils.utils import create_slug, parse_parameters
from src.fastcentrik_woocommerce.utils.logging_config import setup_logging
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

# Nastavení logování s novou konfigurací
logger = setup_logging(__name__, log_level=logging.DEBUG)


class HTMLStripper(HTMLParser):
    """
    Pomocná třída pro odstranění HTML tagů.
    Zachovává strukturální elementy jako <ul>, <li>, <h1>-<h6>, a tagy pro ztučnění textu (<b> a <strong>),
    ale odstraňuje inline CSS.
    """
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.result = []
        self.tag_stack = []  # Stack to track nested tags
        
    def handle_starttag(self, tag, attrs):
        # List of allowed structural tags
        allowed_tags = ('b', 'strong', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p')
        
        if tag in allowed_tags:
            self.tag_stack.append(tag)
            
            # Filter out style attributes
            filtered_attrs = [(name, value) for name, value in attrs if name.lower() != 'style']
            
            # Construct tag with remaining attributes
            if filtered_attrs:
                attr_str = ' '.join(f'{name}="{value}"' for name, value in filtered_attrs)
                self.result.append(f'<{tag} {attr_str}>')
            else:
                self.result.append(f'<{tag}>')
            
    def handle_endtag(self, tag):
        if tag in ('b', 'strong', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p'):
            if self.tag_stack and self.tag_stack[-1] == tag:
                self.tag_stack.pop()
                self.result.append(f'</{tag}>')
        
    def handle_data(self, data):
        self.result.append(data)
        
    def get_text(self):
        return ''.join(self.result)


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
    
    def _get_product_images(self, row: pd.Series) -> str:
        """
        Sestaví seznam obrázků produktu z řádku DataFrame s použitím base URL.
        WebToffee používá pipe | jako oddělovač.
        """
        # DEBUG: Log all column names to identify potential image columns
        logger.debug(f"DEBUG: Dostupné sloupce v DataFrame: {list(row.index)}")
        
        main_image = row.get('HlavniObrazek')
        additional_images = row.get('DalsiObrazky')
        sku = row.get('KodZbozi', 'N/A')
        
        # DEBUG: Log the values of potential image columns
        logger.debug(f"DEBUG: SKU: {sku}, HlavniObrazek: {main_image}, DalsiObrazky: {additional_images}")
        
        images = []
        base_url = IMAGE_BASE_URL.strip('/')
        
        if pd.notna(main_image) and main_image.strip():
            image_path = main_image.strip().lstrip('/')
            images.append(f"{base_url}/{image_path}")
            logger.debug(f"DEBUG: Přidán hlavní obrázek: {image_path}")
        else:
            logger.debug(f"DEBUG: Hlavní obrázek je prázdný nebo None")
        
        if pd.notna(additional_images) and additional_images.strip():
            for img in additional_images.split(';'):
                if img.strip():
                    image_path = img.strip().lstrip('/')
                    images.append(f"{base_url}/{image_path}")
                    logger.debug(f"DEBUG: Přidán další obrázek: {image_path}")
        else:
            logger.debug(f"DEBUG: Další obrázky jsou prázdné nebo None")
        
        if not images:
            logger.debug(f"Pro SKU {sku} nebyly nalezeny žádné cesty k obrázkům.")

        return '|'.join(images)

    # Metoda _get_all_variant_images byla odstraněna - není potřeba
    # Používáme konzistentně _get_product_images pro všechny typy produktů
    
    def _format_price(self, price: any) -> str:
        """Formátuje cenu - převede čárku na tečku."""
        if pd.isna(price) or price == '':
            return ''
        return str(price).replace(',', '.')
    
    def _clean_html(self, html_content: str) -> str:
        """
        Odstraní HTML tagy a entity z textu, kromě strukturálních elementů a tagů pro ztučnění textu.
        Zachovává tagy <ul>, <ol>, <li>, <h1>-<h6>, <p>, <b> a <strong>, ale odstraňuje inline CSS.
        
        Args:
            html_content (str): Text s HTML formátováním
            
        Returns:
            str: Text s odstraněnými HTML tagy kromě povolených strukturálních elementů
        """
        if not html_content or pd.isna(html_content):
            return ''
            
        # Odstranění HTML tagů kromě <b> a <strong>
        stripper = HTMLStripper()
        stripper.feed(html_content)
        text = stripper.get_text()
        
        # Dekódování HTML entit
        text = html.unescape(text)
        
        # Odstranění nadbytečných mezer a prázdných řádků
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
        
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
            
            # SKU pro variantu bude doplněno později při zpracování skupiny variant
            woo_product = {
                'ID': product_id,
                'post_parent': parent_id,
                'parent_sku': parent_sku,
                'sku': '',  # bude doplněno jako {parentSKU}_{index}
                'post_title': str(row['JmenoZbozi']),
                'post_excerpt': short_description,
                'post_content': self._clean_html(str(row.get('Popis', '')) if pd.notna(row.get('Popis')) else ''),
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
            images = self._get_product_images(row)
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
                'post_content': self._clean_html(description),
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
        if not variant_groups:
            logger.info("KodMasterVyrobku nenalezen, zkouším detekci podle SKU vzoru")
            variant_groups = self._group_products_by_sku_pattern()

        # --> ENHANCED DIAGNOSTIC BLOCK
        if variant_groups:
            logger.info("\n" + "="*80)
            logger.info("DIAGNOSTIKA ZPRACOVÁNÍ VARIANT A OBRÁZKŮ")
            logger.info("="*80)
            
            # Analyzujeme první skupinu variant
            first_master_code = next(iter(variant_groups))
            if first_master_code in variant_groups:
                first_group = variant_groups[first_master_code]
                logger.info(f"\nAnalýza první skupiny variant:")
                logger.info(f"Master Code: {first_master_code}")
                logger.info(f"Počet variant: {len(first_group)}")
                logger.info("-" * 70)
                
                # Detailní výpis dat každé varianty
                for i, product_row in enumerate(first_group):
                    sku = product_row.get('KodZbozi', 'N/A')
                    name = product_row.get('JmenoZbozi', 'N/A')
                    main_img = product_row.get('HlavniObrazek', 'N/A')
                    add_imgs = product_row.get('DalsiObrazky', 'N/A')
                    params = product_row.get('HodnotyParametru', 'N/A')
                    
                    logger.info(f"\nVarianta {i}:")
                    logger.info(f"  SKU: '{sku}'")
                    logger.info(f"  Název: '{name}'")
                    logger.info(f"  Hlavní obrázek: '{main_img}'")
                    logger.info(f"  Další obrázky: '{add_imgs}'")
                    logger.info(f"  Parametry: '{params}'")
                    
                    # Extrakce variant atributů pro diagnostiku
                    variant_attrs = self._extract_variant_attributes(product_row)
                    if variant_attrs:
                        logger.info(f"  Variantní atributy: {variant_attrs}")
                    else:
                        logger.info(f"  -> Toto je pravděpodobně MASTER produkt (žádné variantní atributy)")
                
                logger.info("-" * 70)
                logger.info("Nyní bude následovat agregace obrázků pro tuto skupinu...")
                logger.info("="*80 + "\n")
        # <-- END ENHANCED DIAGNOSTIC BLOCK

        processed_skus = set()
        variable_count = 0
        variation_count = 0
        
        # 1. Zpracování všech variabilních produktů
        logger.info(f"Zpracovávám {len(variant_groups)} skupin variant...")
        for master_code, variants in variant_groups.items():
            # Přidání SKU všech variant do `processed_skus`, aby se nevytvořily jako Simple
            for v in variants:
                processed_skus.add(str(v['KodZbozi']))
            
            if not variants:
                logger.warning(f"Skupina variant pro master_code '{master_code}' je prázdná, přeskakuji.")
                continue

            # KRITICKÁ OPRAVA: Nejprve zkontrolujeme, zda existuje produkt s KodZbozi = master_code
            # Tento produkt by měl být použit jako parent, protože obsahuje obrázky
            logger.info(f"Hledám produkt s KodZbozi={master_code} pro použití jako parent...")
            
            # Vytvoříme kopii celého DataFrame pro vyhledávání
            all_products_df = self.products_data.copy()
            
            # Hledáme produkt s KodZbozi = master_code
            parent_product_rows = all_products_df[all_products_df['KodZbozi'] == master_code]
            
            if len(parent_product_rows) > 0:
                # Použijeme existující produkt jako parent
                logger.info(f"Nalezen existující produkt s KodZbozi={master_code}, použiji ho jako parent")
                parent_data = parent_product_rows.iloc[0].copy()
                parent_sku = master_code
                
                # Vypíšeme informace o obrázcích pro diagnostiku
                logger.info(f"Parent produkt má tyto obrázky:")
                logger.info(f"  HlavniObrazek: {parent_data.get('HlavniObrazek', 'N/A')}")
                logger.info(f"  DalsiObrazky: {parent_data.get('DalsiObrazky', 'N/A')}")
            else:
                # Fallback na původní logiku - použijeme první variantu
                logger.info(f"Nenalezen existující produkt s KodZbozi={master_code}, použiji první variantu jako parent")
                first_variant = variants[0]
                parent_sku = master_code
                parent_data = first_variant.copy()
                parent_data['JmenoZbozi'] = self._create_parent_name(variants)
            
            variants_df = pd.DataFrame(variants)
            parent_attributes = self._create_parent_attributes(variants_df)

            parent_product = self._create_woo_product(
                parent_data,
                'variable',
                parent_attributes=parent_attributes
            )
            parent_product['sku'] = parent_sku
            parent_product['post_parent'] = ''

            # FIX: Use the standard _get_product_images method instead of _get_all_variant_images
            # Since variants don't have their own images, we use the parent_data which is based on first_variant
            # This ensures consistent image URL formatting with simple products
            logger.info(f"\n>>> Získávám obrázky pro parent SKU: {parent_sku}")
            
            # DEBUG: Log parent_data columns and values
            logger.debug(f"DEBUG: parent_data sloupce: {list(parent_data.index)}")
            logger.debug(f"DEBUG: parent_data KodZbozi: {parent_data.get('KodZbozi', 'N/A')}")
            
            # Check if the product has the expected image columns
            if 'HlavniObrazek' not in parent_data or 'DalsiObrazky' not in parent_data:
                logger.warning(f"DEBUG: Produkt nemá očekávané sloupce s obrázky!")
                # Try to identify image columns by looking at all columns
                for col in parent_data.index:
                    val = parent_data.get(col)
                    if pd.notna(val) and isinstance(val, str) and ('/images/' in val or '.jpg' in val or '.png' in val):
                        logger.info(f"DEBUG: Potenciální sloupec s obrázkem: {col} = {val[:100]}...")
            
            # Explicitně zkontrolujeme hodnoty obrázků
            hlavni_obrazek = parent_data.get('HlavniObrazek')
            dalsi_obrazky = parent_data.get('DalsiObrazky')
            
            logger.info(f"Hodnoty obrázků v parent_data:")
            logger.info(f"  HlavniObrazek: {hlavni_obrazek}")
            logger.info(f"  DalsiObrazky: {dalsi_obrazky}")
            
            # Kontrola, zda jsou hodnoty NaN
            if pd.isna(hlavni_obrazek) and pd.isna(dalsi_obrazky):
                logger.warning(f"Obě hodnoty obrázků jsou NaN, zkusím najít produkt s obrázky v celém DataFrame")
                
                # Hledáme produkt s KodZbozi = master_code v celém DataFrame
                all_products_with_images = self.products_data[
                    (self.products_data['KodZbozi'] == master_code) &
                    (self.products_data['HlavniObrazek'].notna() | self.products_data['DalsiObrazky'].notna())
                ]
                
                if len(all_products_with_images) > 0:
                    logger.info(f"Nalezen produkt s obrázky v celém DataFrame, použiji ho pro obrázky")
                    image_product = all_products_with_images.iloc[0]
                    parent_data['HlavniObrazek'] = image_product['HlavniObrazek']
                    parent_data['DalsiObrazky'] = image_product['DalsiObrazky']
                    
                    logger.info(f"Nové hodnoty obrázků:")
                    logger.info(f"  HlavniObrazek: {parent_data['HlavniObrazek']}")
                    logger.info(f"  DalsiObrazky: {parent_data['DalsiObrazky']}")
            
            parent_images = self._get_product_images(parent_data)
            parent_product['images'] = parent_images
            
            # Detailní diagnostika přiřazených obrázků
            if parent_images:
                image_count = len(parent_images.split('|'))
                logger.info(f"<<< Parent {parent_sku}: přiřazeno {image_count} obrázků")
                logger.info(f"    Obrázky: {parent_images[:300]}...")
            else:
                # If first variant has no images, try other variants
                logger.warning(f"První varianta nemá obrázky, zkouším další varianty...")
                for i, variant in enumerate(variants[1:]):
                    logger.debug(f"DEBUG: Zkouším variantu {i+2}, SKU: {variant.get('KodZbozi', 'N/A')}")
                    # Log variant columns
                    logger.debug(f"DEBUG: Sloupce varianty: {list(variant.index)}")
                    
                    variant_images = self._get_product_images(variant)
                    if variant_images:
                        parent_product['images'] = variant_images
                        image_count = len(variant_images.split('|'))
                        logger.info(f"<<< Nalezeny obrázky ve variantě {variant.get('KodZbozi')}: {image_count} obrázků")
                        break
                
                if not parent_product['images']:
                    logger.warning(f"<<< Parent {parent_sku} nemá žádné obrázky v žádné variantě")
            
            # Uložíme si obrázky parent produktu pro pozdější použití u variant
            parent_images_for_variants = parent_product.get('images', '')
            
            parent_id = parent_product['ID']
            self.parent_id_mapping[parent_sku] = parent_id
            
            self.woo_products.append(parent_product)
            variable_count += 1
            processed_skus.add(parent_sku)

            # Seřazení variant
            def natural_sort_key(s):
                if isinstance(s, str):
                    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]
                return [s]

            primary_attr_name = VARIANT_SETTINGS.get('variant_attributes', ['velikost'])[0]
            
            for v in variants:
                attrs = self._extract_variant_attributes(v)
                v['sort_key'] = attrs.get(primary_attr_name, '')
            
            variants_sorted = sorted(variants, key=lambda v: natural_sort_key(v['sort_key']))

            # Zpracování jednotlivých variant
            all_current_skus = {p['sku'] for p in self.woo_products}
            
            for i, variant in enumerate(variants_sorted):
                variant_index = i + 1
                base_variant_sku = f"{parent_sku}_{variant_index}"
                unique_variant_sku = base_variant_sku
                
                bump = 1
                while unique_variant_sku in all_current_skus:
                    bump += 1
                    unique_variant_sku = f"{parent_sku}_{variant_index}_v{bump}"
                
                variant_product = self._create_woo_product(
                    variant,
                    'simple',
                    parent_id=parent_id,
                    is_variation=True,
                    parent_sku=parent_sku,
                    menu_order=variant_index
                )
                variant_product['sku'] = unique_variant_sku
                all_current_skus.add(unique_variant_sku)
                
                # Přidáme obrázky z parent produktu i do variant
                if parent_images_for_variants:
                    variant_product['images'] = parent_images_for_variants
                    logger.debug(f"Kopíruji obrázky z parent produktu do varianty {unique_variant_sku}")

                self.woo_products.append(variant_product)
                variation_count += 1
        
        logger.info(f"Vytvořeno {variable_count} variable produktů a {variation_count} variant.")
        logger.info(f"{len(processed_skus)} SKU označeno jako zpracované (varianty a jejich rodiče).")

        # 2. Zpracování jednoduchých produktů
        simple_count = 0
        logger.info("Zpracovávám jednoduché produkty...")
        for _, product in self.products_data.iterrows():
            sku = str(product['KodZbozi'])
            if sku not in processed_skus:
                woo_product = self._create_woo_product(product, 'simple')
                if woo_product['sku'] not in processed_skus:
                    self.woo_products.append(woo_product)
                    simple_count += 1
                    processed_skus.add(woo_product['sku'])

        logger.info(f"Zpracováno {simple_count} jednoduchých produktů.")
        logger.info(f"Celkem vytvořeno {len(self.woo_products)} produktů (včetně variant).")
    
    def validate_products(self) -> List[str]:
        """Validuje vytvořené produkty."""
        errors = []
        
        # Najít všechny parent produkty a jejich SKUs
        parent_ids = set()
        parent_skus_from_parents = set()
        seen_skus = set()
        for product in self.woo_products:
            sku_val = product.get('sku', '')
            if sku_val:
                if sku_val in seen_skus:
                    errors.append(f"Duplicita SKU: '{sku_val}' se vyskytuje vícekrát.")
                seen_skus.add(sku_val)

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
 
                # Kontrola, že varianta má vyplněné SKU podle pravidla
                if not product.get('sku'):
                    errors.append(f"Varianta '{product['post_title']}' (parent_sku: {product['parent_sku']}) nemá přiřazené SKU.")
                else:
                    # Formát {parentSKU}_<cislo>
                    if not re.match(rf"^{re.escape(product['parent_sku'])}_\d+$", product['sku']):
                        errors.append(f"Varianta '{product['post_title']}' má SKU '{product['sku']}', které neodpovídá formátu {product['parent_sku']}_<číslo>.")
 
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
        
        logger.info("\n" + "="*50)
        logger.info("STATISTIKY WEBTOFFEE TRANSFORMACE")
        logger.info("="*50)
        logger.info(f"Celkem FastCentrik produktů: {len(self.products_data)}")
        logger.info(f"Celkem WebToffee produktů: {len(self.woo_products)}")
        logger.info(f"  - Jednoduché produkty: {simple_count}")
        logger.info(f"  - Variable produkty: {variable_count}")
        logger.info(f"  - Varianty: {variation_count}")
        logger.info(f"Celkem kategorií: {len(self.category_mapping)}")
        if self.validation_errors:
            logger.warning(f"⚠️  Validační chyby: {len(self.validation_errors)}")
        logger.info("="*50)