# File: main.py
import tkinter as tk
from gui.app import AplicacionControlAcceso

if __name__ == "__main__":
    root = tk.Tk()
    app = AplicacionControlAcceso(root)
    root.mainloop()
