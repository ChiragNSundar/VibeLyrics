"""
References package initialization
"""
from .folder_manager import FolderManager
from .txt_parser import TxtParser
from .structured_parser import StructuredParser
from .genius_scraper import GeniusScraper

__all__ = [
    'FolderManager',
    'TxtParser',
    'StructuredParser',
    'GeniusScraper'
]
