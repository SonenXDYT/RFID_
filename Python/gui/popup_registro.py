# File: gui/popup_registro.py
import tkinter as tk
from tkinter import ttk, messagebox

class PopupRegistro(tk.Toplevel):
    def __init__(self, parent, access_manager, file_manager, uid_to_register):
        super().__init__(parent)
        self.parent = parent
        self.access_manager = access_manager
        self.file_manager = file_manager
        self.uid_to_register = uid_to_register

        self.title("Registrar Nuevo UID")
        self.geometry("350x180") # Ajustar tamaño
        self.transient(parent) # La ventana emergente aparece encima de la principal
        self.grab_set() # Bloquea la interacción con la ventana principal
        self.protocol("WM_DELETE_WINDOW", self.on_closing) # Manejar cierre con la X

        self.configurar_gui()

    def configurar_gui(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(1, weight=1) # La columna de entrada se expande

        # Mostrar el UID a registrar
        ttk.Label(main_frame, text="UID a Registrar:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Label(main_frame, text=self.uid_to_register, font=('Arial', 10, 'bold')).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)

        # Campo para el nombre
        ttk.Label(main_frame, text="Nombre:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.name_entry = ttk.Entry(main_frame, width=40)
        self.name_entry.grid
