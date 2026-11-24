import os
import re
from pathlib import Path
from typing import Optional
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader


class DocumentLoader:
    @staticmethod
    def load_pdf(file_path: str) -> str:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text

    @staticmethod
    def load_html(file_path: str) -> str:
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        return soup.get_text(separator='\n')

    @staticmethod
    def load_txt(file_path: str) -> str:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    @staticmethod
    def load(file_path: str) -> str:
        ext = Path(file_path).suffix.lower()
        if ext == '.pdf':
            return DocumentLoader.load_pdf(file_path)
        elif ext in ['.html', '.htm']:
            return DocumentLoader.load_html(file_path)
        elif ext in ['.txt', '.md']:
            return DocumentLoader.load_txt(file_path)
        else:
            raise ValueError(f"Formato no soportado: {ext}")