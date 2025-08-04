# WebToffee Format Documentation

## Přehled

Tento dokument popisuje implementaci transformace FastCentrik dat do formátu kompatibilního s WebToffee pluginem "Product Import Export for WooCommerce".

## Hlavní rozdíly oproti standardnímu WooCommerce formátu

### 1. Parent-Child vztahy
- **WebToffee**: Používá `parent_sku` pro označení parent produktu
- **Standard WooCommerce**: Používá `post_parent` s ID produktu

```csv
# WebToffee formát
parent_sku,sku,post_title,tax:product_type
,SHOE001_parent,"Běžecké boty",variable
SHOE001_parent,SHOE001_42,"Běžecké boty - 42",variation
```

### 2. Formát atributů
WebToffee používá specifický formát pro atributy s několika sloupci:

- `attribute:název` - Hodnoty atributu
- `attribute_data:název` - Viditelnost atributu (1 = viditelný)
- `attribute_default:název` - Výchozí hodnota pro variable produkty
- `meta:attribute_název` - Metadata atributu

```csv
# Variable produkt
attribute:color,attribute_data:color,attribute_default:color,meta:attribute_color
"Red|Blue|Green",1,"Red",""

# Varianta
attribute:color,attribute_data:color,meta:attribute_color
"Red",1,"Red"
```

### 3. Taxonomie
Všechny taxonomie používají prefix `tax:`:

- `tax:product_type` - Typ produktu (simple, variable, variation)
- `tax:product_cat` - Kategorie produktu
- `tax:product_tag` - Tagy produktu
- `tax:product_visibility` - Viditelnost produktu

### 4. Oddělování hodnot
- **Obrázky**: Oddělené pipe symbolem `|`
- **Kategorie**: Oddělené pipe symbolem `|` pro více kategorií
- **Atributy**: Oddělené pipe symbolem `|` pro více hodnot

## Struktura CSV souboru

### Povinné sloupce

| Sloupec | Popis | Příklad |
|---------|-------|---------|
| `sku` | SKU produktu | PROD001 |
| `post_title` | Název produktu | Běžecké boty |
| `tax:product_type` | Typ produktu | simple/variable/variation |
| `post_status` | Status produktu | publish/draft |
| `regular_price` | Běžná cena | 1000 |

### Sloupce pro varianty

| Sloupec | Popis | Příklad |
|---------|-------|---------|
| `parent_sku` | SKU parent produktu | SHOE001_parent |
| `attribute:size` | Hodnota atributu velikost | 42 |
| `attribute:color` | Hodnota atributu barva | Red |

### Sloupce pro skladové zásoby

| Sloupec | Popis | Příklad |
|---------|-------|---------|
| `stock` | Počet kusů na skladě | 50 |
| `stock_status` | Status skladu | instock/outofstock |
| `manage_stock` | Řídit skladové zásoby | yes/no |
| `backorders` | Povolit objednávky při vyprodání | yes/no |

## Příklady produktů

### Jednoduchý produkt
```csv
sku,post_title,post_status,tax:product_type,regular_price,stock,manage_stock
PROD001,"Jednoduchý produkt",publish,simple,1000,50,yes
```

### Variable produkt (parent)
```csv
parent_sku,sku,post_title,tax:product_type,attribute:size,attribute_data:size,attribute_default:size
,SHOE001_parent,"Běžecké boty",variable,"40|41|42",1,41
```

### Varianty
```csv
parent_sku,sku,post_title,tax:product_type,attribute:size,regular_price,stock
SHOE001_parent,SHOE001_40,"Běžecké boty - 40",variation,40,2500,10
SHOE001_parent,SHOE001_41,"Běžecké boty - 41",variation,41,2500,15
SHOE001_parent,SHOE001_42,"Běžecké boty - 42",variation,42,2500,5
```

## Použití transformačního skriptu

### Spuštění
```bash
# Umístěte soubor Export_Excel_Lite.xls do aktuální složky
python run_webtoffee_transformation.py
```

Skript automaticky:
- Načte soubor `Export_Excel_Lite.xls`
- Vytvoří složku `webtoffee_output/`
- Vygeneruje všechny potřebné CSV soubory
- Vytvoří ukázkový soubor s prvními 20 produkty
- Vytvoří import šablonu

### Výstupní soubory
Ve složce `webtoffee_output/` najdete:
- `webtoffee_products_all.csv` - Všechny produkty
- `webtoffee_products_simple.csv` - Pouze jednoduché produkty
- `webtoffee_products_variable.csv` - Variable produkty a jejich varianty
- `webtoffee_sample.csv` - Ukázka prvních 20 produktů
- `webtoffee_import_template.csv` - Šablona s příklady

## Import do WooCommerce

1. **Instalace pluginu**
   - Nainstalujte "Product Import Export for WooCommerce" od WebToffee
   - Plugin je dostupný zdarma na WordPress.org

2. **Příprava importu**
   - V administraci: WooCommerce → WebToffee Import Export → Import
   - Vyberte "Product" jako typ importu
   - Nahrajte CSV soubor

3. **Mapování sloupců**
   - Plugin by měl automaticky rozpoznat sloupce díky správným názvům
   - Zkontrolujte mapování atributů
   - Ujistěte se, že `parent_sku` je správně namapován

4. **Pořadí importu**
   - Pro variable produkty importujte v tomto pořadí:
     1. Nejprve soubor obsahující všechny produkty (`_all.csv`)
     2. Nebo nejprve variable produkty, pak varianty

5. **Kontrola po importu**
   - Zkontrolujte správné propojení variant s parent produkty
   - Ověřte atributy a jejich hodnoty
   - Zkontrolujte skladové zásoby

## Řešení problémů

### Varianty nejsou propojené s parent produktem
- Zkontrolujte, že `parent_sku` odpovídá `sku` parent produktu
- Ujistěte se, že parent produkt byl importován před variantami

### Atributy se nezobrazují
- Ověřte formát sloupců `attribute:`, `attribute_data:`, atd.
- Zkontrolujte, že `attribute_data:název` obsahuje hodnotu `1`

### Chybné kódování znaků
- Soubory jsou exportovány s UTF-8 BOM pro správné zobrazení v Excelu
- Při importu vyberte UTF-8 kódování

### Variable produkty mají skladové zásoby
- Variable produkty by neměly mít vlastní stock
- Stock je řízen pouze na úrovni variant

## Technické detaily implementace

### Třída WebToffeeTransformer
Hlavní transformační třída, která:
- Detekuje varianty podle `KodMasterVyrobku` nebo SKU vzoru
- Vytváří parent produkty s agregovanými atributy
- Formátuje atributy podle WebToffee specifikace
- Přidává taxonomie s prefixem `tax:`

### Třída WebToffeeCSVExporter
Exportní třída, která:
- Vytváří CSV soubory ve správném formátu
- Rozděluje produkty podle typu (simple, variable)
- Přidává UTF-8 BOM pro Excel kompatibilitu
- Generuje import šablony

### Validace
Transformace obsahuje validaci pro:
- Kontrolu parent-child vztahů
- Ověření přítomnosti atributů u variant
- Kontrolu stock nastavení pro variable produkty
- Validaci povinných polí

## Rozšíření a úpravy

### Přidání nových atributů
1. Upravte `VARIANT_SETTINGS` v `config/config.py`
2. Přidejte mapování do `ATTRIBUTE_MAPPING`
3. Atributy budou automaticky zpracovány

### Změna formátu kategorií
- Upravte oddělovač v metodě `_get_category_path_for_product()`
- WebToffee standardně používá pipe `|`

### Vlastní validační pravidla
- Přidejte nová pravidla do metody `validate_products()`
- Logujte varování pro nekritické problémy