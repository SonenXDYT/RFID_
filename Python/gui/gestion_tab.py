# File: gui/gestion_tab.py
import tkinter as tk
from tkinter import ttk, messagebox
import re # Importar re para parsear
# Importar managers necesarios
from core.serial_manager import SerialManager
from core.access_manager import AccessManager
from core.file_manager import FileManager

class GestionTab(ttk.Frame):
    def __init__(self, parent, root, serial_manager, access_manager, file_manager):
        super().__init__(parent, padding="10")
        self.root = root # Referencia a la ventana principal
        self.serial_manager = serial_manager
        self.access_manager = access_manager
        self.file_manager = file_manager

        self.configurar_gui()
        self.cargar_tarjetas() # Cargar tarjetas al inicializar

    def configurar_gui(self):
        # Configurar el layout para que se expanda
        self.columnconfigure(0, weight=1) # La columna principal se expandirá

        # Frame para la lista de tarjetas
        list_frame = ttk.LabelFrame(self, text="Tarjetas Registradas", padding="10")
        list_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        # Treeview para mostrar las tarjetas
        columns = ("UID", "Nombre", "Tipo", "Caducidad")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
        
        # Configurar encabezados
        self.tree.heading("UID", text="UID")
        self.tree.heading("Nombre", text="Nombre")
        self.tree.heading("Tipo", text="Tipo")
        self.tree.heading("Caducidad", text="Caducidad")
        
        # Configurar ancho de columnas
        self.tree.column("UID", width=120)
        self.tree.column("Nombre", width=150)
        self.tree.column("Tipo", width=100)
        self.tree.column("Caducidad", width=150)
        
        # Scrollbar para el Treeview
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Grid del Treeview y scrollbar
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # Frame para botones de gestión
        button_frame = ttk.Frame(self)
        button_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        # Botones de gestión
        ttk.Button(button_frame, text="Actualizar Lista", command=self.cargar_tarjetas).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(button_frame, text="Eliminar Seleccionada", command=self.eliminar_tarjeta_seleccionada).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Limpiar Caducadas", command=self.limpiar_caducadas).grid(row=0, column=2, padx=5)

        # Frame para eliminar por UID manual
        manual_frame = ttk.LabelFrame(self, text="Eliminar por UID", padding="10")
        manual_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))
        manual_frame.columnconfigure(1, weight=1)

        ttk.Label(manual_frame, text="UID:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.uid_entry = ttk.Entry(manual_frame, width=20)
        self.uid_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(manual_frame, text="Eliminar", command=self.eliminar_por_uid_manual).grid(row=0, column=2, padx=(5, 0))

        # Configurar expansión de filas
        self.rowconfigure(0, weight=1)

    def cargar_tarjetas(self):
        """Carga y muestra todas las tarjetas registradas en el Treeview."""
        print("GestionTab: Cargando tarjetas registradas...") # Debug
        
        # Limpiar el Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            # Recargar los UIDs desde el archivo
            self.access_manager.load_registered_uids() # Usar el método correcto
            
            # Obtener todos los UIDs registrados
            registered_uids = self.access_manager.registered_uids
            
            # Agregar cada tarjeta al Treeview
            for uid, card_data in registered_uids.items():
                if isinstance(card_data, str):
                    # Formato antiguo: solo nombre
                    name = card_data
                    card_type = "Permanente"
                    expiry = "N/A"
                elif isinstance(card_data, dict):
                    # Formato nuevo: diccionario con información completa
                    name = card_data.get("name", "N/A")
                    card_type = "Temporal" if card_data.get("temporal", False) else "Permanente"
                    expiry = card_data.get("expiry_datetime", "N/A")
                else:
                    name = "Error"
                    card_type = "Desconocido"
                    expiry = "N/A"
                
                self.tree.insert("", tk.END, values=(uid, name, card_type, expiry))
            
            print(f"GestionTab: {len(registered_uids)} tarjetas cargadas en la lista.") # Debug
            
        except Exception as e:
            print(f"GestionTab: Error al cargar tarjetas - {str(e)}") # Debug
            messagebox.showerror("Error", f"Error al cargar las tarjetas: {str(e)}")

    def limpiar_caducadas(self):
        """Elimina automáticamente las tarjetas temporales caducadas."""
        try:
            expired_count = self.access_manager.cleanup_expired_cards()
            if expired_count > 0:
                messagebox.showinfo("Limpieza Completada", f"Se eliminaron {expired_count} tarjetas caducadas.")
                self.cargar_tarjetas()  # Recargar la lista
            else:
                messagebox.showinfo("Limpieza Completada", "No se encontraron tarjetas caducadas.")
        except Exception as e:
            print(f"GestionTab: Error al limpiar tarjetas caducadas - {str(e)}")
            messagebox.showerror("Error", f"Error al limpiar tarjetas caducadas: {str(e)}")

    def eliminar_tarjeta_seleccionada(self):
        """Elimina la tarjeta seleccionada en el Treeview."""
        selected_item = self.tree.selection()
        
        if not selected_item:
            messagebox.showwarning("Advertencia", "Por favor, seleccione una tarjeta de la lista.")
            return
        
        # Obtener el UID de la tarjeta seleccionada
        item_values = self.tree.item(selected_item[0], "values")
        uid_to_delete = item_values[0]
        name_to_delete = item_values[1]
        card_type = item_values[2]
        
        # Confirmar eliminación
        confirm = messagebox.askyesno("Confirmar Eliminación", 
                                    f"¿Está seguro de que desea eliminar la tarjeta?\n\nUID: {uid_to_delete}\nNombre: {name_to_delete}\nTipo: {card_type}")
        
        if confirm:
            self.eliminar_tarjeta(uid_to_delete)

    def eliminar_por_uid_manual(self):
        """Elimina una tarjeta por UID ingresado manualmente."""
        uid_to_delete = self.uid_entry.get().strip()
        
        if not uid_to_delete:
            messagebox.showwarning("Advertencia", "Por favor, ingrese un UID.")
            return
        
        # Verificar si el UID existe
        if uid_to_delete not in self.access_manager.registered_uids:
            messagebox.showwarning("Advertencia", f"El UID '{uid_to_delete}' no está registrado.")
            return
        
        card_data = self.access_manager.registered_uids[uid_to_delete]
        if isinstance(card_data, str):
            name_to_delete = card_data
        elif isinstance(card_data, dict):
            name_to_delete = card_data.get("name", "Usuario")
        else:
            name_to_delete = "Desconocido"
        
        # Confirmar eliminación
        confirm = messagebox.askyesno("Confirmar Eliminación", 
                                    f"¿Está seguro de que desea eliminar la tarjeta?\n\nUID: {uid_to_delete}\nNombre: {name_to_delete}")
        
        if confirm:
            self.eliminar_tarjeta(uid_to_delete)
            self.uid_entry.delete(0, tk.END) # Limpiar el campo de entrada

    def eliminar_tarjeta(self, uid):
        """
        Elimina una tarjeta del sistema.
        
        Args:
            uid (str): UID de la tarjeta a eliminar
        """
        print(f"GestionTab: Intentando eliminar tarjeta con UID: {uid}") # Debug
        
        try:
            # Usar el método del AccessManager para eliminar
            success = self.access_manager.remove_uid(uid)
            
            if success:
                print(f"GestionTab: Tarjeta eliminada exitosamente - UID: {uid}") # Debug
                messagebox.showinfo("Éxito", f"Tarjeta eliminada exitosamente.\n\nUID: {uid}")
                
                # Recargar la lista
                self.cargar_tarjetas()
            else:
                print(f"GestionTab: Error al eliminar tarjeta - UID: {uid}") # Debug
                
        except Exception as e:
            print(f"GestionTab: Error al eliminar tarjeta {uid} - {str(e)}") # Debug
            messagebox.showerror("Error", f"Error al eliminar la tarjeta: {str(e)}")
