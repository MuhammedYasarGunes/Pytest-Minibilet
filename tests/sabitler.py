"""Testlerde ortak sabitler. (conftest.py'den import yapma; ortak değerleri böyle bir modüle koy.)"""
from datetime import datetime

SIMDI = datetime(2026, 12, 1, 12, 0)  # testlerde "şu an" hep bu
