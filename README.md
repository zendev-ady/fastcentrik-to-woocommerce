# FastCentrik to WooCommerce Transformátor

🚀 Nástroj pro převod dat z FastCentrik exportu do formátu kompatibilního s WooCommerce.

## 📋 Co budete potřebovat

### 1. Instalace Dockeru (Ubuntu/Debian)

```bash
# Aktualizace systému
sudo apt update

# Instalace závislostí
sudo apt install apt-transport-https ca-certificates curl software-properties-common

# Přidání Docker GPG klíče
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Přidání Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalace Dockeru
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io

# Přidání uživatele do docker skupiny (aby nebylo potřeba sudo)
sudo usermod -aG docker $USER

# Restart systému nebo odhlášení/přihlášení
```

### 2. Instalace Docker Compose

```bash
# Stažení Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Nastavení práv
sudo chmod +x /usr/local/bin/docker-compose

# Ověření instalace
docker-compose --version
```

### 3. Pro ostatní Linux distribuce

**CentOS/RHEL/Fedora:**
```bash
# Instalace Dockeru
sudo dnf install docker docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
```

**Arch Linux:**
```bash
# Instalace Dockeru
sudo pacman -S docker docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
```

## 🚀 Spuštění projektu

### Krok 1: Stažení projektu
```bash
# Pokud máte git
git clone <URL_VAŠEHO_REPOZITÁŘE>
cd fastcentrik-to-woocommerce

# Nebo si stáhněte ZIP a rozbalte
```

### Krok 2: Příprava vstupních dat
```bash
# Umístěte váš Excel soubor z FastCentrik do složky projektu
# Soubor musí být pojmenován: Export_Excel_Lite.xls
cp /cesta/k/vašemu/souboru.xls ./Export_Excel_Lite.xls
```

### Krok 3: Spuštění transformace

**Možnost A - Pomocí skriptu (doporučeno):**
```bash
# Nastavení práv pro skript
chmod +x run.sh

# Spuštění
./run.sh
```

**Možnost B - Manuálně pomocí Docker Compose:**
```bash
# Build Docker image
docker-compose build

# Spuštění transformace
docker-compose --profile transform up transform

# Vyčištění po dokončení
docker-compose --profile transform down
```

**Možnost C - Přímé použití Dockeru:**
```bash
# Build image
docker build -t fastcentrik-transformer .

# Spuštění s mapováním souborů
docker run --rm \
  -v $(pwd)/Export_Excel_Lite.xls:/app/Export_Excel_Lite.xls:ro \
  -v $(pwd)/woocommerce_output:/app/woocommerce_output \
  -v $(pwd)/transformation.log:/app/transformation.log \
  fastcentrik-transformer python run_transformation.py
```

## 📁 Výsledky

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

## ⚙️ Pokročilé možnosti

### Vlastní vstupní soubor
```bash
# Spuštění s vlastním souborem
docker run --rm \
  -v $(pwd)/muj_soubor.xls:/app/Export_Excel_Lite.xls:ro \
  -v $(pwd)/woocommerce_output:/app/woocommerce_output \
  fastcentrik-transformer python run_transformation.py
```

### Vlastní výstupní složka
```bash
# Spuštění s vlastní výstupní složkou
docker run --rm \
  -v $(pwd)/Export_Excel_Lite.xls:/app/Export_Excel_Lite.xls:ro \
  -v $(pwd)/moje_vystupy:/app/woocommerce_output \
  fastcentrik-transformer python run_transformation.py --output /app/woocommerce_output
```

### Debug režim
```bash
# Spuštění s debug logováním
docker run --rm \
  -v $(pwd)/Export_Excel_Lite.xls:/app/Export_Excel_Lite.xls:ro \
  -v $(pwd)/woocommerce_output:/app/woocommerce_output \
  -v $(pwd)/transformation.log:/app/transformation.log \
  fastcentrik-transformer python run_transformation.py --log-level DEBUG
```

## 🔧 Konfigurace

Upravte soubor `config.py` pro:
- Mapování kategorií
- SEO nastavení
- URL obrázků
- Nastavení variant produktů

## 📝 Logování

Všechny operace jsou logovány do souboru `transformation.log`. V případě problémů zkontrolujte tento soubor.

## ❗ Řešení problémů

### Docker není nainstalován
```bash
# Ověření instalace
docker --version
docker-compose --version

# Pokud příkazy nefungují, Docker není správně nainstalován
```

### Chyba oprávnění
```bash
# Přidání uživatele do docker skupiny
sudo usermod -aG docker $USER

# Odhlášení a přihlášení nebo restart
```

### Soubor neexistuje
```bash
# Zkontrolujte, že máte soubor Export_Excel_Lite.xls v aktuální složce
ls -la Export_Excel_Lite.xls
```

### Chyba při buildu
```bash
# Vyčištění Docker cache
docker system prune -a

# Nový build
docker-compose build --no-cache
```

## 📞 Podpora

V případě problémů:
1. Zkontrolujte log soubor `transformation.log`
2. Ověřte, že máte správný formát vstupního Excel souboru
3. Zkontrolujte Docker logy: `docker-compose logs`

## 🎯 Rychlý start (TL;DR)

```bash
# 1. Nainstalujte Docker a Docker Compose
# 2. Stáhněte projekt
# 3. Umístěte Excel soubor jako Export_Excel_Lite.xls
# 4. Spusťte:
chmod +x run.sh && ./run.sh
# 5. Výsledky najdete ve složce woocommerce_output/