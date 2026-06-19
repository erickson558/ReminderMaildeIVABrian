# -*- mode: python ; coding: utf-8 -*-
# reminderfactura.spec — PyInstaller spec para compilar Reminder IVA Brian
#
# Uso:
#   pyinstaller reminderfactura.spec
#
# Genera: dist/reminderIVABrian.exe (sin ventana de consola)

block_cipher = None

a = Analysis(
    ['reminderfactura.py'],
    pathex=[],
    binaries=[],
    # Incluir archivos de traducción JSON y el icono en el ejecutable
    datas=[
        ('src/i18n/es.json', 'src/i18n'),
        ('src/i18n/en.json', 'src/i18n'),
        ('reminderagua.ico', '.'),
    ],
    # pywin32 necesita que sus módulos se especifiquen explícitamente
    hiddenimports=[
        'win32com',
        'win32com.client',
        'pywintypes',
        'win32api',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='reminderIVABrian',        # Nombre del ejecutable final
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,                  # Sin ventana de consola negra
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='reminderagua.ico',        # Icono de la aplicación
)
