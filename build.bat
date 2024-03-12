call D:\Dev\Workspace\Python\CSV-Table-Editor\.venv\Scripts\activate.bat

pyinstaller --noconfirm --windowed --hidden-import=fastparquet --hidden-import=dbfread --hidden-import=dbf --icon "D:\Dev\Workspace\Python\CSV-Table-Editor\icon.ico" --name "CSV Table Editor" "D:\Dev\Workspace\Python\CSV-Table-Editor\gui.py"