# FastCentrik to WooCommerce Transformátor

🚀 Nástroj pro převod dat z FastCentrik exportu do formátu kompatibilního s WooCommerce.

## 📋 Požadavky

- Python 3.8 nebo vyšší
- pip (správce balíčků pro Python)

## 📁 Struktura projektu

```
fastcentrik-to-woocommerce/
├── src/
│   └── fastcentrik_woocommerce/
│       ├── core/           # Hlavní transformační logika
│       ├── exporters/      # CSV exportéry
│       ├── loaders/        # Načítání dat
│       ├── mappers/        # Mapování kategorií
│       ├── utils/          # Pomocné funkce
│       └── validators/     # Validátory dat
├── tests/
│   ├── unit/              # Unit testy
│   └── integration/       # Integrační testy
├── config/                # Konfigurační soubory
├── docs/                  # Dokumentace
├── scripts/               # Pomocné skripty
├── woocommerce_output/    # Výstupní soubory
└── requirements.txt       # Python závislosti
```

## 🚀 Instalace

### 1. Klonování repozitáře

```bash
git clone <URL_VAŠEHO_REPOZITÁŘE>
cd fastcentrik-to-woocommerce
```

### 2. Instalace závislostí

```bash
pip install -r requirements.txt
```

Nebo použijte instalační skript:

```bash
python scripts/install_dependencies.py
```

## ✨ Funkce

### Inteligentní mapování kategorií
Systém automaticky přiřazuje produkty do správných WooCommerce kategorií na základě:
- Pohlaví (muži, ženy, děti)
- Typu produktu (oblečení, boty, doplňky)
- Sportu (fotbal, tenis, běh, atd.)
- Dalších atributů produktu

### Multi-Category systém
Produkty mohou být přiřazeny do více kategorií současně:
- **Výchozí limit**: 2 kategorie na produkt
- **Komplementární strategie**: výběr kategorií z různých větví
- **Plně konfigurovatelné** limity a strategie
- **Zpětná kompatibilita** se single-category systémem

**Příklad**: Pánské běžecké tričko může být zařazeno do:
1. Muži > Pánské oblečení > Pánská trička
2. Sporty > Běh > Běžecké oblečení

## 📊 Použití

### Základní transformace

```bash
# Umístěte váš Excel soubor z FastCentrik do kořenové složky projektu
# Soubor musí být pojmenován: Export_Excel_Lite.xls

# Spusťte transformaci
python run_transformation.py
```

### Pokročilé možnosti

```bash
# Vlastní vstupní soubor
python run_transformation.py --input muj_soubor.xls

# Vlastní výstupní složka
python run_transformation.py --output ./moje_vystupy/

# Debug režim
python run_transformation.py --log-level DEBUG

# Pouze validace
python run_transformation.py --validate-only
```

### Dávkové zpracování

Pro zpracování více souborů najednou:

```bash
python scripts/batch_transform.py /cesta/ke/slozce/s/excel/soubory --output ./batch_output/
```

## 🧪 Testování

### Spuštění testů

```bash
# Test multi-category systému
python tests/unit/test_multi_category.py

# Test leaf categories
python tests/unit/test_leaf_categories.py

# Validace kategorií
python validate_categories.py
```

## ⚙️ Konfigurace

Upravte soubor `config/config.py` pro:

### Multi-category nastavení
```python
CATEGORY_MAPPING_SETTINGS = {
    "enable_multi_category": True,
    "max_categories_per_product": 2,
    "multi_category_strategy": "complementary",
    "multi_category_separator": " | ",
    "use_leaf_category_only": True
}
```

### SEO nastavení
```python
SEO_SETTINGS = {
    "title_suffix": " | Váš SportShop",
    "meta_desc_template": "Kvalitní {product_name} v kategorii {category}",
    "focus_keyword_words": 3
}
```

### Další nastavení
- Mapování kategorií
- URL obrázků
- Nastavení variant produktů
- Skladové zásoby
- Atributy a tagy

## 📁 Výstupní soubory

Po úspěšném dokončení najdete ve složce `woocommerce_output/`:

- **woocommerce_products.csv** - Produkty připravené pro import do WooCommerce
- **woocommerce_categories.csv** - Kategorie připravené pro import do WooCommerce

## 📊 Import do WooCommerce

### 1. Import kategorií
1. Přihlaste se do WP Admin
2. Jděte na **WooCommerce → Produkty → Kategorie**
3. Použijte plugin pro CSV import nebo importujte manuálně

### 2. Import produktů
1. Jděte na **WooCommerce → Produkty**
2. Klikněte na **Import**
3. Nahrajte soubor `woocommerce_products.csv`
4. Namapujte sloupce podle potřeby
5. Spusťte import

## 📝 Logování

Všechny operace jsou logovány do souboru `transformation.log`. V případě problémů zkontrolujte tento soubor.

## ❗ Řešení problémů

### Python není nainstalován
```bash
# Ověření instalace
python --version
python3 --version
```

### Chybí závislosti
```bash
# Reinstalace závislostí
pip install -r requirements.txt --force-reinstall
```

### Soubor neexistuje
```bash
# Zkontrolujte, že máte soubor Export_Excel_Lite.xls v aktuální složce
ls -la Export_Excel_Lite.xls
```

## 📚 Dokumentace

- [Multi-Category dokumentace](docs/MULTI_CATEGORY_DOCUMENTATION.md) - Podrobný návod k multi-category systému
- [Konfigurace](config/config.py) - Všechna nastavení transformace

## 🎯 Rychlý start

```bash
# 1. Nainstalujte závislosti
pip install -r requirements.txt

# 2. Umístěte Excel soubor jako Export_Excel_Lite.xls

# 3. Spusťte transformaci
python run_transformation.py

# 4. Výsledky najdete ve složce woocommerce_output/
```

## 📞 Podpora

V případě problémů:
1. Zkontrolujte log soubor `transformation.log`
2. Ověřte, že máte správný formát vstupního Excel souboru
3. Pro problémy s kategoriemi spusťte: `python validate_categories.py`
4. Zkontrolujte [dokumentaci](docs/)

## 🤝 Přispívání

Příspěvky jsou vítány! Prosím:
1. Forkněte repozitář
2. Vytvořte feature branch (`git checkout -b feature/AmazingFeature`)
3. Commitněte změny (`git commit -m 'Add some AmazingFeature'`)
4. Pushněte do branch (`git push origin feature/AmazingFeature`)
5. Otevřete Pull Request

## 📄 Licence

Tento projekt je licencován pod MIT licencí.