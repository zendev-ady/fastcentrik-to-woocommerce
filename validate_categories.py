#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main script for category validation
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.fastcentrik_woocommerce.validators.validate_categories import main

if __name__ == "__main__":
    main()