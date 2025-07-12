#!/bin/bash
# ============================================================================
# run.sh - Spouštěcí skript pro FastCentrik transformátor
# ============================================================================

set -e

# Barvy pro výstup
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 FastCentrik to WooCommerce Transformátor${NC}"
echo "=" * 50

# Kontrola Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker není nainstalován!${NC}"
    echo "Nainstalujte Docker podle instrukcí na: https://docs.docker.com/engine/install/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose není nainstalován!${NC}"
    echo "Nainstalujte Docker Compose podle instrukcí na: https://docs.docker.com/compose/install/"
    exit 1
fi

# Kontrola vstupního souboru
if [ ! -f "Export_Excel_Lite.xls" ]; then
    echo -e "${RED}❌ Vstupní soubor 'Export_Excel_Lite.xls' neexistuje!${NC}"
    echo "Umístěte váš Excel soubor do této složky a pojmenujte ho 'Export_Excel_Lite.xls'"
    exit 1
fi

echo -e "${GREEN}✅ Všechny požadavky splněny${NC}"

# Vytvoření výstupní složky
mkdir -p woocommerce_output

echo -e "${YELLOW}📦 Buildování Docker image...${NC}"
docker-compose build

echo -e "${YELLOW}🔄 Spouštění transformace...${NC}"
docker-compose --profile transform up transform

echo -e "${GREEN}🎉 Transformace dokončena!${NC}"
echo -e "${BLUE}📁 Výsledky najdete ve složce: woocommerce_output/${NC}"
echo -e "${BLUE}📄 Log soubor: transformation.log${NC}"

# Vyčištění
docker-compose --profile transform down