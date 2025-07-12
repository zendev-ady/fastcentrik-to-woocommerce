# ============================================================================
# Dockerfile pro FastCentrik to WooCommerce transformátor
# ============================================================================

FROM python:3.11-slim

# Nastavení pracovního adresáře
WORKDIR /app

# Instalace systémových závislostí
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Kopírování requirements a instalace Python závislostí
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopírování zdrojového kódu
COPY . .

# Vytvoření výstupní složky
RUN mkdir -p /app/woocommerce_output

# Nastavení práv
RUN chmod +x run_transformation.py

# Výchozí příkaz
CMD ["python", "run_transformation.py", "--help"]