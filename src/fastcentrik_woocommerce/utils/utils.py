#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pomocné funkce pro transformaci dat.
"""

import pandas as pd
import re
import unicodedata
from typing import Dict

def create_slug(text: str) -> str:
    """
    Vytvoří URL-friendly slug z textu.

    Args:
        text (str): Vstupní text.

    Returns:
        str: Normalizovaný slug.
    """
    if pd.isna(text):
        return ""
    
    # Převod na malá písmena a normalizace
    text = str(text).lower()
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    
    # Nahrazení mezer a speciálních znaků pomlčkami
    text = re.sub(r'[^a-z0-9]+', '-', text)
    text = text.strip('-')
    
    return text

def parse_parameters(param_string: str) -> Dict[str, str]:
    """
    Parsuje parametry z FastCentrik formátu (např. "barva||modrá##velikost||XL").
    Je navržen tak, aby byl odolný vůči chybám.

    Args:
        param_string (str): Řetězec s parametry.

    Returns:
        Dict[str, str]: Slovník s naparsovanými parametry.
    """
    if pd.isna(param_string) or not param_string:
        return {}
    
    params = {}
    # Rozdělení podle '##' a odstranění prázdných řetězců
    param_pairs = filter(None, param_string.split('##'))
    
    for pair in param_pairs:
        if '||' in pair:
            parts = pair.split('||', 1)
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()
                if key and value:
                    params[key] = value
    
    return params