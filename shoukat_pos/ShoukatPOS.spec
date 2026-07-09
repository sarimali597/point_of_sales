# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Specification for Shoukat POS

Usage:
    pyinstaller ShoukatPOS.spec

This spec file configures:
- Single executable output
- Asset inclusion (icons, fonts, default templates)
- Hidden imports for dynamic loads (PIL, matplotlib, customtkinter)
- Windows-specific settings (icon, console behavior)
"""

from PyInstaller.building.build_main import Analysis
from PyInstaller.building.datastruct import TOC
from PyInstaller.building.utils import _check_guts_eq
from PyInstaller.building.api import PYZ, EXE, COLLECT
import os

block_cipher = None

# Define data files to include
# Format: (source_path, target_path_in_bundle)
datas = [
    ('assets', 'assets'),
    ('shoukat_pos/assets', 'assets'),  # Fallback for different root contexts
]

# Add database schema if it exists as a file (optional, usually embedded in code)
if os.path.exists('shoukat_pos/database/schema.sql'):
    datas.append(('shoukat_pos/database/schema.sql', 'database'))

a = Analysis(
    ['shoukat_pos/main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        # GUI Frameworks
        'customtkinter',
        'customtkinter.windows.widgets.core_widget_classes',
        'customtkinter.windows.widgets.font',
        
        # Imaging
        'PIL',
        'PIL._imagingtk',
        'PIL._tkinter_finder',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        
        # Cryptography & Security
        'bcrypt',
        'cryptography',
        'cryptography.fernet',
        
        # Plotting & PDF
        'matplotlib.backends.backend_tkagg',
        'matplotlib.pyplot',
        'fpdf',
        
        # Database
        'sqlite3',
        
        # Hardware (optional drivers)
        'win32print',
        'win32api',
        'serial',
        'serial.tools.list_ports',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter.test',
        'matplotlib.tests',
        'numpy.random._examples',
        'pytest',
        'pylint',
        'unittest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ShoukatPOS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True for debugging startup issues
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='shoukat_pos/assets/logo.ico' if os.path.exists('shoukat_pos/assets/logo.ico') else None,
)

COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ShoukatPOS',
)
