# FastCentrik → WooCommerce

Převede Excel export z FastCentrik na CSV soubory pro WooCommerce import.

## Rychlý start

```bash
# 1. Instalace
pip install -r requirements.txt

# 2. Umístěte soubor Export_Excel_Lite.xls do složky

# 3. Spuštění
python run_transformation.py

# 4. Výsledek ve složce woocommerce_output/
```

## Co to dělá

**Vstup:** `Export_Excel_Lite.xls` z FastCentrik  
**Výstup:** 
- `woocommerce_products.csv` 
- `woocommerce_categories.csv`

### Automatické funkce
- **Kategorie:** Pánské běžecké tričko → `Muži > Oblečení` + `Sport > Běh`
- **Varianty:** Velikosti a barvy jako WooCommerce varianty
- **SEO:** Auto-generování meta title/description

## Import do WooCommerce

1. **Kategorie:** WooCommerce → Produkty → Import → `woocommerce_categories.csv`
2. **Produkty:** WooCommerce → Produkty → Import → `woocommerce_products.csv`

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

```bash
# Vlastní soubor
python run_transformation.py --input muj_export.xls

# Debug
python run_transformation.py --log-level DEBUG

# Validace kategorií
python validate_categories.py
```

## Řešení problémů

| Problém | Řešení |
|---------|--------|
| FileNotFoundError | Soubor musí být `Export_Excel_Lite.xls` |
| Chybí kategorie | `python validate_categories.py` |
| Špatné ceny | Zkontrolujte `transformation.log` |

## Požadavky

- Python 3.8+
- Excel soubor z FastCentrik export