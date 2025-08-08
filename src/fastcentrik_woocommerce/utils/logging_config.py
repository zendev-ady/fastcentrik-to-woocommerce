#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logging Configuration Module
===========================

Provides centralized logging configuration for the FastCentrik to WooCommerce migration tool.
Implements proper logging with file rotation and different log levels.

Usage:
    from src.fastcentrik_woocommerce.utils.logging_config import setup_logging
    
    # Setup logging with default configuration
    logger = setup_logging(__name__)
    
    # Or with custom configuration
    logger = setup_logging(
        name=__name__,
        log_level=logging.DEBUG,
        console_level=logging.INFO,
        file_level=logging.DEBUG
    )
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys
from datetime import datetime

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure logs directory exists
if not LOGS_DIR.exists():
    LOGS_DIR.mkdir(exist_ok=True)

def setup_logging(name, 
                 log_level=logging.INFO, 
                 console_level=logging.INFO, 
                 file_level=logging.DEBUG,
                 log_file=None,
                 max_file_size=10*1024*1024,  # 10 MB
                 backup_count=5):
    """
    Set up logging with console and file handlers.
    
    Args:
        name (str): Logger name, typically __name__
        log_level (int): Overall logger level
        console_level (int): Console handler log level
        file_level (int): File handler log level
        log_file (str, optional): Log file name. If None, a default name with timestamp will be used.
        max_file_size (int): Maximum size of each log file in bytes
        backup_count (int): Number of backup log files to keep
        
    Returns:
        logging.Logger: Configured logger
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Remove existing handlers if any
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Create file handler with rotation
    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        module_name = name.split('.')[-1]
        log_file = f"{module_name}_{timestamp}.log"
    
    log_path = LOGS_DIR / log_file
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=max_file_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(file_level)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    return logger

def get_transformation_logger(name, transformation_type="general"):
    """
    Get a logger specifically for transformation processes.
    
    Args:
        name (str): Logger name
        transformation_type (str): Type of transformation (e.g., "webtoffee", "general")
        
    Returns:
        logging.Logger: Configured logger for transformation
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"{transformation_type}_transformation_{timestamp}.log"
    
    return setup_logging(
        name=name,
        log_level=logging.DEBUG,
        console_level=logging.INFO,
        file_level=logging.DEBUG,
        log_file=log_file
    )