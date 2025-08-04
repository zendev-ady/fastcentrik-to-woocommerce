# FastCentrik → WooCommerce

Převede Excel export z FastCentrik na CSV soubory pro WooCommerce import.

## Rychlý start

```bash
# 1. Instalace
pip install -r requirements.txt

# 2. Umístěte soubor Export_Excel_Lite.xls do složky

# 3. Spuštění - Standardní WooCommerce formát
python run_transformation.py

# 3. Spuštění - WebToffee formát
python run_webtoffee_transformation.py

# 4. Výsledek ve složce woocommerce_output/ nebo webtoffee_output/
```

## Podporované formáty

### 1. Standardní WooCommerce formát
**Vstup:** `Export_Excel_Lite.xls` z FastCentrik
**Výstup:**
- `woocommerce_products.csv`
- `woocommerce_categories.csv`

### 2. WebToffee formát
**Vstup:** `Export_Excel_Lite.xls` z FastCentrik
**Výstup ve složce `webtoffee_output/`:**
- `webtoffee_products_all.csv` - Všechny produkty
- `webtoffee_products_simple.csv` - Jednoduché produkty
- `webtoffee_products_variable.csv` - Variable produkty a varianty
- `webtoffee_sample.csv` - Ukázka prvních 20 produktů
- `webtoffee_import_template.csv` - Šablona pro import

### Automatické funkce
- **Kategorie:** Pánské běžecké tričko → `Muži > Oblečení` + `Sport > Běh`
- **Varianty:** Velikosti a barvy jako WooCommerce varianty
- **SEO:** Auto-generování meta title/description

## Import do WooCommerce

### Standardní WooCommerce import
1. **Kategorie:** WooCommerce → Produkty → Import → `woocommerce_categories.csv`
2. **Produkty:** WooCommerce → Produkty → Import → `woocommerce_products.csv`

### WebToffee import
1. **Instalace pluginu:** "Product Import Export for WooCommerce" od WebToffee
2. **Import:** WooCommerce → WebToffee Import Export → Import
3. **Nahrajte soubor:** `webtoffee_products_all.csv`

## Konfigurace

Upravte `config/config.py`:

```python
# URL obrázků
IMAGE_BASE_URL = "https://vasedomena.cz/images/"

# SEO šablona
"title_suffix": " | Váš obchod"

# Multi-kategorie (doporučeno)
"enable_multi_category": True
```

## Pokročilé použití

### Standardní formát
```bash
# Vlastní soubor
python run_transformation.py --input muj_export.xls

# Debug
python run_transformation.py --log-level DEBUG

# Validace kategorií
python validate_categories.py
```

### WebToffee formát
```bash
# Spuštění (automaticky vytvoří všechny soubory včetně ukázky a šablony)
python run_webtoffee_transformation.py
```

## Řešení problémů

| Problém | Řešení |
|---------|--------|
| FileNotFoundError | Soubor musí být `Export_Excel_Lite.xls` |
| Chybí kategorie | `python validate_categories.py` |
| Špatné ceny | Zkontrolujte `transformation.log` |
| Varianty nejsou propojené (WebToffee) | Zkontrolujte parent_sku |
| Atributy se nezobrazují (WebToffee) | Ověřte formát attribute: sloupců |

## Dokumentace

- [Multi-kategorie dokumentace](docs/MULTI_CATEGORY_DOCUMENTATION.md)
- [WebToffee formát dokumentace](docs/WEBTOFFEE_FORMAT_DOCUMENTATION.md)

## Požadavky

- Python 3.8+
- Excel soubor z FastCentrik export
- Pro WebToffee: Plugin "Product Import Export for WooCommerce"