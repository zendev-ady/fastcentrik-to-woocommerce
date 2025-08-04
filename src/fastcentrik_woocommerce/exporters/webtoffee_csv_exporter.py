#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebToffee CSV Exporter
======================

Exportuje transformovaná data do CSV formátu kompatibilního s WebToffee pluginem.

Autor: FastCentrik Migration Tool
Verze: 1.0
"""

import pandas as pd
from pathlib import Path
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class WebToffeeCSVExporter:
    """
    Exportuje data do WebToffee CSV formátu.
    
    WebToffee má specifické požadavky na pořadí a názvy sloupců.
    """
    
    # Definice sloupců ve správném pořadí pro WebToffee
    WEBTOFFEE_COLUMNS = [
        'ID',
        'post_parent',
        'sku',
        'post_title',
        'post_excerpt',
        'post_content',
        'post_status',
        'regular_price',
        'sale_price',
        'stock_status',
        'stock',
        'manage_stock',
        'weight',
        'length',
        'width',
        'height',
        'images',
        'tax:product_type',
        'tax:product_cat',
        'tax:product_tag',
        'visibility',
        'featured',
        'downloadable',
        'virtual',
        'backorders',
        'sold_individually',
        'low_stock_amount',
        'reviews_allowed',
        'purchase_note',
        'menu_order',
        'tax_status',
        'tax_class',
        'shipping_class'
    ]
    
    def __init__(self, output_dir: str = 'output'):
        """
        Inicializace exportéru.
        
        Args:
            output_dir: Adresář pro výstupní soubory
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def _prepare_dataframe(self, products: List[Dict]) -> pd.DataFrame:
        """
        Připraví DataFrame s produkty ve správném formátu.
        
        Args:
            products: Seznam produktů k exportu
            
        Returns:
            DataFrame připravený k exportu
        """
        # Vytvoříme DataFrame
        df = pd.DataFrame(products)
        
        # Přidáme chybějící sloupce s výchozími hodnotami
        default_values = {
            'length': '',
            'width': '',
            'height': '',
            'featured': 'no',
            'tax_status': 'taxable',
            'tax_class': '',
            'shipping_class': ''
        }
        
        for col, default_val in default_values.items():
            if col not in df.columns:
                df[col] = default_val
        
        # Získáme všechny atributové sloupce
        attribute_columns = []
        for col in df.columns:
            if col.startswith(('attribute:', 'attribute_data:', 'attribute_default:', 'meta:attribute_')):
                attribute_columns.append(col)
        
        # Seřadíme atributové sloupce
        attribute_columns.sort()
        
        # Vytvoříme finální seznam sloupců
        final_columns = []
        
        # Nejprve základní sloupce
        for col in self.WEBTOFFEE_COLUMNS:
            if col in df.columns:
                final_columns.append(col)
        
        # Pak atributové sloupce
        final_columns.extend(attribute_columns)
        
        # Nakonec jakékoliv další sloupce které nejsou v našem seznamu
        for col in df.columns:
            if col not in final_columns:
                final_columns.append(col)
        
        # Seřadíme DataFrame podle finálních sloupců
        df = df[final_columns]
        
        # Vyčistíme NaN hodnoty
        df = df.fillna('')
        
        return df
    
    def _split_by_product_type(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Rozdělí DataFrame podle typu produktu.
        
        WebToffee někdy vyžaduje oddělený import pro různé typy produktů.
        
        Args:
            df: DataFrame s produkty
            
        Returns:
            Dict s DataFrames podle typu
        """
        splits = {}
        
        # Simple produkty (typ Simple)
        simple_df = df[df['tax:product_type'] == 'Simple'].copy()
        if not simple_df.empty:
            splits['simple'] = simple_df
        
        # Variable produkty a jejich varianty (Variable nebo prázdný typ)
        variable_df = df[df['tax:product_type'].isin(['Variable', ''])].copy()
        if not variable_df.empty:
            # Seřadíme tak, aby parent produkty byly před variantami
            variable_df['_sort_order'] = variable_df.apply(
                lambda x: 0 if x['tax:product_type'] == 'Variable' else 1, axis=1
            )
            variable_df = variable_df.sort_values(['_sort_order', 'ID'])
            variable_df = variable_df.drop('_sort_order', axis=1)
            splits['variable'] = variable_df
        
        return splits
    
    def export_products(self, products: List[Dict], filename_prefix: str = 'webtoffee_products') -> List[str]:
        """
        Exportuje produkty do CSV souborů.
        
        Args:
            products: Seznam produktů k exportu
            filename_prefix: Prefix pro názvy souborů
            
        Returns:
            Seznam cest k vytvořeným souborům
        """
        logger.info(f"Exportuji {len(products)} produktů do WebToffee CSV formátu")
        
        # Připravíme DataFrame
        df = self._prepare_dataframe(products)
        
        # Rozdělíme podle typu produktu
        splits = self._split_by_product_type(df)
        
        exported_files = []
        
        # Export jednotlivých typů
        for product_type, type_df in splits.items():
            output_file = self.output_dir / f"{filename_prefix}_{product_type}.csv"
            
            # Export do CSV
            type_df.to_csv(
                output_file,
                index=False,
                encoding='utf-8-sig',  # BOM pro Excel
                sep=',',
                quotechar='"',
                escapechar='\\'
            )
            
            exported_files.append(str(output_file))
            logger.info(f"Exportováno {len(type_df)} {product_type} produktů do {output_file}")
        
        # Vytvoříme také kompletní soubor se všemi produkty
        all_products_file = self.output_dir / f"{filename_prefix}_all.csv"
        df.to_csv(
            all_products_file,
            index=False,
            encoding='utf-8-sig',
            sep=',',
            quotechar='"',
            escapechar='\\'
        )
        exported_files.append(str(all_products_file))
        logger.info(f"Exportován kompletní soubor se všemi produkty: {all_products_file}")
        
        return exported_files
    
    def export_sample(self, products: List[Dict], sample_size: int = 10) -> str:
        """
        Exportuje ukázkový soubor s omezeným počtem produktů.
        
        Args:
            products: Seznam produktů
            sample_size: Počet produktů v ukázce
            
        Returns:
            Cesta k ukázkovému souboru
        """
        logger.info(f"Vytvářím ukázkový soubor s {sample_size} produkty")
        
        # Vezmeme ukázku produktů
        sample_products = products[:sample_size]
        
        # Připravíme DataFrame
        df = self._prepare_dataframe(sample_products)
        
        # Export
        sample_file = self.output_dir / "webtoffee_sample.csv"
        df.to_csv(
            sample_file,
            index=False,
            encoding='utf-8-sig',
            sep=',',
            quotechar='"',
            escapechar='\\'
        )
        
        logger.info(f"Ukázkový soubor vytvořen: {sample_file}")
        
        return str(sample_file)
    
    def create_import_template(self) -> str:
        """
        Vytvoří prázdnou šablonu pro WebToffee import.
        
        Returns:
            Cesta k souboru šablony
        """
        logger.info("Vytvářím WebToffee import šablonu")
        
        # Vytvoříme prázdný DataFrame se všemi sloupci
        template_data = {}
        
        # Základní sloupce
        for col in self.WEBTOFFEE_COLUMNS:
            template_data[col] = ['']
        
        # Příkladové atributové sloupce s pa_ prefix
        template_data['attribute:pa_color'] = ['']
        template_data['attribute_data:pa_color'] = ['0|1|1']
        template_data['attribute_default:pa_color'] = ['']
        template_data['meta:attribute_pa_color'] = ['']
        
        template_data['attribute:pa_size'] = ['']
        template_data['attribute_data:pa_size'] = ['1|1|1']
        template_data['attribute_default:pa_size'] = ['']
        template_data['meta:attribute_pa_size'] = ['']
        
        # Vytvoříme DataFrame
        df = pd.DataFrame(template_data)
        
        # Přidáme příkladové řádky
        example_rows = [
            {
                'ID': '1001',
                'post_parent': '',
                'sku': 'EXAMPLE-001',
                'post_title': 'Example Simple Product',
                'post_status': 'publish',
                'tax:product_type': 'Simple',
                'regular_price': '100',
                'stock': '50',
                'manage_stock': 'yes',
                'tax:product_cat': 'Category 1 > Subcategory',
                'visibility': 'visible',
                'backorders': 'no',
                'downloadable': 'no',
                'virtual': 'no',
                'menu_order': '0'
            },
            {
                'ID': '1002',
                'post_parent': '',
                'sku': 'EXAMPLE-VAR',
                'post_title': 'Example Variable Product',
                'post_status': 'publish',
                'tax:product_type': 'Variable',
                'regular_price': '150',
                'manage_stock': 'yes',
                'attribute:pa_color': 'Red|Blue|Green',
                'attribute_data:pa_color': '0|1|1',
                'attribute_default:pa_color': 'Red',
                'attribute:pa_size': 'S|M|L',
                'attribute_data:pa_size': '1|1|1',
                'attribute_default:pa_size': 'M',
                'visibility': 'visible',
                'backorders': 'no',
                'downloadable': 'no',
                'virtual': 'no',
                'menu_order': '0'
            },
            {
                'ID': '1003',
                'post_parent': '1002',
                'sku': 'EXAMPLE-VAR-RED-S',
                'post_title': '',  # Varianty nemají název
                'post_status': 'publish',
                'tax:product_type': '',  # Varianty mají prázdný typ
                'regular_price': '150',
                'stock': '10',
                'manage_stock': 'yes',
                'meta:attribute_pa_color': 'Red',
                'meta:attribute_pa_size': 'S',
                'visibility': 'visible',
                'backorders': 'no',
                'downloadable': 'no',
                'virtual': 'no',
                'menu_order': '0'
            }
        ]
        
        # Přidáme příklady
        for example in example_rows:
            for col in df.columns:
                if col not in example:
                    example[col] = ''
            df = pd.concat([df, pd.DataFrame([example])], ignore_index=True)
        
        # Export
        template_file = self.output_dir / "webtoffee_import_template.csv"
        df.to_csv(
            template_file,
            index=False,
            encoding='utf-8-sig',
            sep=',',
            quotechar='"',
            escapechar='\\'
        )
        
        logger.info(f"Šablona vytvořena: {template_file}")
        
        return str(template_file)