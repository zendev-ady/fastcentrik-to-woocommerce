#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validátor kategorií pro WooCommerce import
==========================================

Ověřuje správnost přiřazení kategorií a generuje reporty.

Autor: FastCentrik Migration Tool
Verze: 1.0
"""

import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class CategoryValidator:
    """Validuje přiřazení kategorií a generuje reporty."""
    
    def __init__(self, products_file: str = "woocommerce_output/woocommerce_products.csv",
                 categories_file: str = "woocommerce_output/woocommerce_categories.csv"):
        """
        Inicializace validátoru.
        
        Args:
            products_file: Cesta k CSV souboru s produkty
            categories_file: Cesta k CSV souboru s kategoriemi
        """
        self.products_file = Path(products_file)
        self.categories_file = Path(categories_file)
        self.validation_results = {
            'total_products': 0,
            'products_with_category': 0,
            'products_without_category': 0,
            'invalid_categories': [],
            'category_distribution': {},
            'unmapped_products': [],
            'warnings': []
        }
    
    def validate(self) -> Dict:
        """
        Provede kompletní validaci kategorií.
        
        Returns:
            Slovník s výsledky validace
        """
        logger.info("Zahajuji validaci kategorií...")
        
        # Načtení dat
        products_df = self._load_products()
        categories_df = self._load_categories()
        
        if products_df is None or categories_df is None:
            return self.validation_results
        
        # Získání seznamu platných kategorií
        valid_categories = self._get_valid_categories(categories_df)
        
        # Validace produktů
        self._validate_products(products_df, valid_categories)
        
        # Analýza distribuce kategorií
        self._analyze_category_distribution(products_df)
        
        # Kontrola hierarchie kategorií
        self._check_category_hierarchy(products_df, categories_df)
        
        return self.validation_results
    
    def _load_products(self) -> pd.DataFrame:
        """Načte produkty z CSV souboru."""
        try:
            if not self.products_file.exists():
                logger.error(f"Soubor s produkty neexistuje: {self.products_file}")
                return None
            
            df = pd.read_csv(self.products_file)
            self.validation_results['total_products'] = len(df)
            logger.info(f"Načteno {len(df)} produktů")
            return df
        except Exception as e:
            logger.error(f"Chyba při načítání produktů: {e}")
            return None
    
    def _load_categories(self) -> pd.DataFrame:
        """Načte kategorie z CSV souboru."""
        try:
            if not self.categories_file.exists():
                logger.error(f"Soubor s kategoriemi neexistuje: {self.categories_file}")
                return None
            
            df = pd.read_csv(self.categories_file)
            logger.info(f"Načteno {len(df)} kategorií")
            return df
        except Exception as e:
            logger.error(f"Chyba při načítání kategorií: {e}")
            return None
    
    def _get_valid_categories(self, categories_df: pd.DataFrame) -> set:
        """Vytvoří seznam všech platných kategorií včetně hierarchických cest."""
        valid_categories = set()
        
        # Přidat jednotlivé kategorie
        for _, cat in categories_df.iterrows():
            if pd.notna(cat.get('Category Name')):
                valid_categories.add(cat['Category Name'])
        
        # Přidat hierarchické cesty (pokud jsou v produktech)
        # Toto bude doplněno při validaci produktů
        
        return valid_categories
    
    def _validate_products(self, products_df: pd.DataFrame, valid_categories: set):
        """Validuje kategorie přiřazené produktům."""
        # Načíst nastavení multi-kategorií
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
        from config.config import CATEGORY_MAPPING_SETTINGS
        multi_category_enabled = CATEGORY_MAPPING_SETTINGS.get('enable_multi_category', False)
        max_categories = CATEGORY_MAPPING_SETTINGS.get('max_categories_per_product', 2)
        separator = CATEGORY_MAPPING_SETTINGS.get('multi_category_separator', ' | ')
        
        for idx, product in products_df.iterrows():
            sku = product.get('SKU', f'row_{idx}')
            name = product.get('Name', 'Neznámý produkt')
            categories = product.get('Categories', '')
            
            # Kontrola, zda má produkt kategorii
            if pd.isna(categories) or categories == '':
                self.validation_results['products_without_category'] += 1
                self.validation_results['unmapped_products'].append({
                    'sku': sku,
                    'name': name,
                    'type': product.get('Type', 'simple')
                })
            else:
                self.validation_results['products_with_category'] += 1
                
                # Rozdělit kategorie pokud je multi-category povoleno
                if multi_category_enabled and separator in str(categories):
                    category_list = [cat.strip() for cat in str(categories).split(separator)]
                    
                    # Kontrola počtu kategorií
                    if len(category_list) > max_categories:
                        self.validation_results['warnings'].append({
                            'type': 'too_many_categories',
                            'message': f"Produkt {sku} má {len(category_list)} kategorií, ale limit je {max_categories}",
                            'sku': sku,
                            'name': name,
                            'categories': category_list
                        })
                    
                    # Validace každé kategorie
                    for category_path in category_list:
                        self._validate_single_category(category_path, valid_categories, sku, name)
                else:
                    # Single category validation
                    category_path = str(categories).strip()
                    self._validate_single_category(category_path, valid_categories, sku, name)
    
    def _validate_single_category(self, category_path: str, valid_categories: set, sku: str, name: str):
        """Validuje jednu kategorii."""
        # Přidat hierarchickou cestu do platných kategorií
        if ' > ' in category_path:
            parts = category_path.split(' > ')
            for i in range(len(parts)):
                partial_path = ' > '.join(parts[:i+1])
                valid_categories.add(partial_path)
        
        # Kontrola, zda kategorie existuje
        if category_path not in valid_categories:
            # Zkontrolovat, zda alespoň poslední část cesty existuje
            last_part = category_path.split(' > ')[-1]
            if last_part not in valid_categories:
                self.validation_results['invalid_categories'].append({
                    'sku': sku,
                    'name': name,
                    'category': category_path
                })
    
    def _analyze_category_distribution(self, products_df: pd.DataFrame):
        """Analyzuje distribuci produktů v kategoriích."""
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
        from config.config import CATEGORY_MAPPING_SETTINGS
        multi_category_enabled = CATEGORY_MAPPING_SETTINGS.get('enable_multi_category', False)
        separator = CATEGORY_MAPPING_SETTINGS.get('multi_category_separator', ' | ')
        
        category_counts = {}
        multi_category_stats = {
            'products_with_single_category': 0,
            'products_with_multiple_categories': 0,
            'category_combinations': {}
        }
        
        for _, product in products_df.iterrows():
            categories = product.get('Categories', '')
            if pd.notna(categories) and categories != '':
                categories_str = str(categories).strip()
                
                if multi_category_enabled and separator in categories_str:
                    # Multi-category product
                    category_list = [cat.strip() for cat in categories_str.split(separator)]
                    multi_category_stats['products_with_multiple_categories'] += 1
                    
                    # Count individual categories
                    for cat in category_list:
                        category_counts[cat] = category_counts.get(cat, 0) + 1
                    
                    # Track category combinations
                    combo_key = " + ".join(sorted(category_list))
                    multi_category_stats['category_combinations'][combo_key] = \
                        multi_category_stats['category_combinations'].get(combo_key, 0) + 1
                else:
                    # Single category product
                    multi_category_stats['products_with_single_category'] += 1
                    category_counts[categories_str] = category_counts.get(categories_str, 0) + 1
        
        # Seřadit podle počtu produktů
        self.validation_results['category_distribution'] = dict(
            sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        )
        
        # Přidat multi-category statistiky
        if multi_category_enabled:
            self.validation_results['multi_category_stats'] = multi_category_stats
    
    def _check_category_hierarchy(self, products_df: pd.DataFrame, categories_df: pd.DataFrame):
        """Kontroluje konzistenci hierarchie kategorií."""
        # Získat všechny použité kategorie z produktů
        used_categories = set()
        for _, product in products_df.iterrows():
            categories = product.get('Categories', '')
            if pd.notna(categories) and categories != '':
                category_path = str(categories).strip()
                if ' > ' in category_path:
                    parts = category_path.split(' > ')
                    for part in parts:
                        used_categories.add(part.strip())
                else:
                    used_categories.add(category_path)
        
        # Kontrola, zda všechny použité kategorie existují v definici
        defined_categories = set(categories_df['Category Name'].dropna())
        
        missing_categories = used_categories - defined_categories
        if missing_categories:
            self.validation_results['warnings'].append({
                'type': 'missing_category_definition',
                'message': f"Následující kategorie jsou použity v produktech, ale nejsou definovány: {', '.join(missing_categories)}"
            })
    
    def generate_report(self, output_file: str = "category_validation_report.json"):
        """
        Generuje validační report.
        
        Args:
            output_file: Název výstupního souboru
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_products': self.validation_results['total_products'],
                'products_with_category': self.validation_results['products_with_category'],
                'products_without_category': self.validation_results['products_without_category'],
                'percentage_mapped': (
                    self.validation_results['products_with_category'] / 
                    self.validation_results['total_products'] * 100
                ) if self.validation_results['total_products'] > 0 else 0
            },
            'details': self.validation_results
        }
        
        # Uložit JSON report
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Validační report uložen do: {output_file}")
        
        # Vytisknout souhrn
        self._print_summary()
    
    def _print_summary(self):
        """Vytiskne souhrn validace."""
        print("\n" + "="*60)
        print("SOUHRN VALIDACE KATEGORIÍ")
        print("="*60)
        
        total = self.validation_results['total_products']
        with_cat = self.validation_results['products_with_category']
        without_cat = self.validation_results['products_without_category']
        
        print(f"Celkem produktů: {total}")
        print(f"Produkty s kategorií: {with_cat} ({with_cat/total*100:.1f}%)")
        print(f"Produkty bez kategorie: {without_cat} ({without_cat/total*100:.1f}%)")
        
        if self.validation_results['invalid_categories']:
            print(f"\n⚠️  Produkty s neplatnou kategorií: {len(self.validation_results['invalid_categories'])}")
            for item in self.validation_results['invalid_categories'][:5]:
                print(f"   - {item['name']} (SKU: {item['sku']}) -> {item['category']}")
            if len(self.validation_results['invalid_categories']) > 5:
                print(f"   ... a {len(self.validation_results['invalid_categories']) - 5} dalších")
        
        if self.validation_results['unmapped_products']:
            print(f"\n❌ Produkty bez kategorie: {len(self.validation_results['unmapped_products'])}")
            for item in self.validation_results['unmapped_products'][:5]:
                print(f"   - {item['name']} (SKU: {item['sku']})")
            if len(self.validation_results['unmapped_products']) > 5:
                print(f"   ... a {len(self.validation_results['unmapped_products']) - 5} dalších")
        
        print("\nTOP 10 kategorií podle počtu produktů:")
        for category, count in list(self.validation_results['category_distribution'].items())[:10]:
            print(f"   {category}: {count} produktů")
        
        # Multi-category statistiky
        if 'multi_category_stats' in self.validation_results:
            stats = self.validation_results['multi_category_stats']
            print(f"\nMulti-category statistiky:")
            print(f"   Produkty s jednou kategorií: {stats['products_with_single_category']}")
            print(f"   Produkty s více kategoriemi: {stats['products_with_multiple_categories']}")
            
            if stats['category_combinations']:
                print("\n   TOP 5 kombinací kategorií:")
                sorted_combos = sorted(stats['category_combinations'].items(),
                                     key=lambda x: x[1], reverse=True)
                for combo, count in sorted_combos[:5]:
                    print(f"      {combo}: {count} produktů")
        
        if self.validation_results['warnings']:
            print("\n⚠️  Varování:")
            for warning in self.validation_results['warnings']:
                print(f"   - {warning['message']}")
        
        print("="*60)
    
    def export_unmapped_products(self, output_file: str = "unmapped_products.csv"):
        """
        Exportuje seznam produktů bez kategorie do CSV.
        
        Args:
            output_file: Název výstupního souboru
        """
        if not self.validation_results['unmapped_products']:
            logger.info("Žádné nenamapované produkty k exportu")
            return
        
        df = pd.DataFrame(self.validation_results['unmapped_products'])
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        logger.info(f"Seznam nenamapovaných produktů exportován do: {output_file}")


def main():
    """Hlavní funkce pro spuštění validace."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    validator = CategoryValidator()
    validator.validate()
    validator.generate_report()
    validator.export_unmapped_products()


if __name__ == "__main__":
    main()