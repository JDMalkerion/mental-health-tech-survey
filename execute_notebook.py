#!/usr/bin/env python3
"""
execute_notebook.py
Executes eda_notebook.ipynb top-to-bottom and saves the executed cells back to disk,
confirming zero errors.
"""
import sys
import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError

print("Loading eda_notebook.ipynb...")
nb = nbformat.read("eda_notebook.ipynb", as_version=4)

client = NotebookClient(nb, timeout=300, kernel_name="python3")
print("Executing notebook top-to-bottom...")

try:
    client.execute()
    print("Notebook executed successfully with ZERO errors!")
    with open("eda_notebook.ipynb", "w", encoding="utf-8") as f:
        nbformat.write(nb, f)
    print("Executed notebook written back to eda_notebook.ipynb.")
except CellExecutionError as e:
    print(f"Execution failed with error: {e}")
    sys.exit(1)
