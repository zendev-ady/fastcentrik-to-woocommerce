# ============================================================================
# install_dependencies.py - Instalátor závislostí
# ============================================================================

#!/usr/bin/env python3
"""
Instalátor závislostí pro FastCentrik to WooCommerce transformátor
"""

import subprocess
import sys

def install_package(package):
    """Instaluje Python balíček"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} úspěšně nainstalován")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ Chyba při instalaci {package}")
        return False

def main():
    """Hlavní funkce pro instalaci"""
    print("🔧 Instalace závislostí pro FastCentrik transformátor")
    print("=" * 50)
    
    required_packages = [
        "pandas>=1.5.0",
        "openpyxl>=3.0.0", 
        "xlrd>=2.0.0"
    ]
    
    failed_packages = []
    
    for package in required_packages:
        print(f"📦 Instaluji {package}...")
        if not install_package(package):
            failed_packages.append(package)
    
    if failed_packages:
        print(f"\n❌ Nepodařilo se nainstalovat: {', '.join(failed_packages)}")
        print("Zkuste ruční instalaci pomocí: pip install pandas openpyxl xlrd")
        sys.exit(1)
    else:
        print("\n🎉 Všechny závislosti úspěšně nainstalovány!")
        print("Nyní můžete spustit transformaci pomocí: python run_transformation.py")

if __name__ == "__main__":
    main()