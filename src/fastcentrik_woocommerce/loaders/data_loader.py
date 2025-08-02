#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modul pro načítání dat z FastCentrik exportu.
"""

import pandas as pd
import logging
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)

class DataLoader:
    """
    Zodpovídá za načítání a základní validaci dat z vstupního Excel souboru.
    """
    def __init__(self, file_path: str):
        """
        Inicializace DataLoaderu.

        Args:
            file_path (str): Cesta k vstupnímu Excel souboru.
        """
        self.file_path = Path(file_path)
        self.data = {}

    def load_data(self) -> Dict[str, pd.DataFrame]:
        """
        Načte data ze všech požadovaných listů v Excel souboru.

        Returns:
            Dict[str, pd.DataFrame]: Slovník s DataFrame pro každý list.
        
        Raises:
            FileNotFoundError: Pokud soubor neexistuje.
            Exception: Pro ostatní chyby při načítání.
        """
        if not self.file_path.exists():
            msg = f"Vstupní soubor nebyl nalezen: {self.file_path}"
            logger.error(msg)
            raise FileNotFoundError(msg)

        logger.info(f"Načítám data z {self.file_path}")
        try:
            sheets_to_load = {
                'products': 'Zbozi',
                'categories': 'Kategorie',
                'parameters': 'Parametry'
            }
            
            loaded_data = {}
            for key, sheet_name in sheets_to_load.items():
                logger.info(f"Načítám list '{sheet_name}'...")
                loaded_data[key] = pd.read_excel(self.file_path, sheet_name=sheet_name)
                logger.info(f"Načteno {len(loaded_data[key])} záznamů z listu '{sheet_name}'.")
            
            self.data = loaded_data
            return self.data

        except Exception as e:
            logger.error(f"Došlo k chybě při načítání Excel souboru: {e}")
            raise