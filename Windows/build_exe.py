# build_exe.py
"""
Script to build a one-file executable for the Weatherite Windows app using PyInstaller.
Run this script in PowerShell:
    python build_exe.py
"""

import PyInstaller.__main__

# Main script to package
main_script = "main.py"

print("Running PyInstaller...")
PyInstaller.__main__.run([
    main_script,
    '--name', 'Weatherite'
])
print("Build complete. Check the 'dist' folder for Weatherite.exe.")

