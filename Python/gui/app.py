# File: gui/app.py
import tkinter as tk
from tkinter import ttk
import threading
import time

# Importar managers
from core.serial_manager import SerialManager
from core.access_manager import AccessManager
from core.file_manager import FileManager
from core.access_logger import AccessLogger

# Importar tabs
from gui.monitor_tab import MonitorTab
from gui.gestion_tab import GestionTab
from gui.registro_tab import RegistroTab
from gui.buscador_tab import BuscadorTab

class AplicacionControlAcceso:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Control de Acceso RFID")
        self.root.geometry("900x700")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Inicializar managers
        self.file_manager = FileManager()
        self.access_manager = AccessManager(self.file_manager)
        self.access_logger = AccessLogger(self.file_manager)
        self.serial_manager = SerialManager(self.access_manager, self.access_logger)

        # Configurar GUI
        self.configurar_gui()

        # Iniciar hilo de limpieza automática de tarjetas caducadas
        self.start_cleanup_thread()

    def configurar_gui(self):
        # Crear el notebook (pestañas)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Crear las pestañas - CORRECCIÓN: Pasar access_logger a MonitorTab
        self.monitor_tab = MonitorTab(self.notebook, self.root, self.serial_manager, self.access_manager, self.file_manager, self.access_logger)
        self.notebook.add(self.monitor_tab, text="Monitor")

        self.gestion_tab = GestionTab(self.notebook, self.root, self.serial_manager, self.access_manager, self.file_manager)
        self.notebook.add(self.gestion_tab, text="Gestión")

        self.registro_tab = RegistroTab(self.notebook, self.root, self.serial_manager, self.access_manager, self.file_manager)
        self.notebook.add(self.registro_tab, text="Registro")

        self.buscador_tab = BuscadorTab(self.notebook, self.root, self.serial_manager, self.access_manager, self.file_manager, self.access_logger)
        self.notebook.add(self.buscador_tab, text="Buscador")

        # Barra de estado
        self.status_bar = ttk.Label(self.root, text="Sistema iniciado", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Actualizar estado de conexión periódicamente
        self.update_status()

    def start_cleanup_thread(self):
        """Inicia un hilo para limpiar automáticamente las tarjetas caducadas cada hora."""
        def cleanup_worker():
            while True:
                try:
                    time.sleep(3600)  # Esperar 1 hora
                    expired_count = self.access_manager.cleanup_expired_cards()
                    if expired_count > 0:
                        print(f"AplicacionControlAcceso: Limpieza automática - {expired_count} tarjetas caducadas eliminadas.")
                        # Actualizar la lista en GestionTab si está visible
                        if hasattr(self, 'gestion_tab'):
                            self.root.after(0, self.gestion_tab.cargar_tarjetas)
                except Exception as e:
                    print(f"AplicacionControlAcceso: Error en limpieza automática - {str(e)}")

        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()

    def update_status(self):
        """Actualiza la barra de estado con información de conexión."""
        try:
            if self.serial_manager and self.serial_manager.is_connected:
                port_info = getattr(self.serial_manager, 'port', 'Desconocido')
                status_text = f"Conectado a {port_info} | UIDs registrados: {len(self.access_manager.registered_uids)}"
            else:
                status_text = "Desconectado | Sin comunicación serial"
            
            self.status_bar.config(text=status_text)
        except Exception as e:
            self.status_bar.config(text=f"Error en estado: {str(e)}")
        
        # Programar la próxima actualización
        self.root.after(5000, self.update_status)  # Actualizar cada 5 segundos

    def on_closing(self):
        """Maneja el cierre de la aplicación."""
        print("Cerrando aplicación...")
        
        # Cerrar conexión serial si existe
        if hasattr(self, 'serial_manager') and self.serial_manager:
            self.serial_manager.disconnect()
        
        # Cerrar la ventana
        self.root.destroy()
