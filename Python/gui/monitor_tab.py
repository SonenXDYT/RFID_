# File: gui/monitor_tab.py
import tkinter as tk
from tkinter import ttk
import threading
import time
from datetime import datetime

# Importar managers
from core.serial_manager import SerialManager
from core.access_manager import AccessManager
from core.file_manager import FileManager
from core.access_logger import AccessLogger

class MonitorTab(ttk.Frame):
    def __init__(self, parent, root, serial_manager, access_manager, file_manager, access_logger):
        super().__init__(parent, padding="10")
        self.root = root
        self.serial_manager = serial_manager
        self.access_manager = access_manager
        self.file_manager = file_manager
        self.access_logger = access_logger
        
        self.reading_active = False
        self.reading_thread = None

        self.configurar_gui()
        self.iniciar_lectura()

    def configurar_gui(self):
        # Configurar el layout para que se expanda
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Frame principal para el historial de intentos
        history_frame = ttk.LabelFrame(self, text="Historial de Intentos de Acceso", padding="10")
        history_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(0, weight=1)

        # Treeview para mostrar el historial de intentos
        columns = ("Fecha", "Hora", "UID", "Nombre", "Estado", "Mensaje")
        self.history_tree = ttk.Treeview(history_frame, columns=columns, show="headings", height=20)
        
        # Configurar encabezados
        self.history_tree.heading("Fecha", text="Fecha")
        self.history_tree.heading("Hora", text="Hora")
        self.history_tree.heading("UID", text="UID")
        self.history_tree.heading("Nombre", text="Nombre")
        self.history_tree.heading("Estado", text="Estado")
        self.history_tree.heading("Mensaje", text="Mensaje")
        
        # Configurar ancho de columnas
        self.history_tree.column("Fecha", width=100)
        self.history_tree.column("Hora", width=80)
        self.history_tree.column("UID", width=100)
        self.history_tree.column("Nombre", width=150)
        self.history_tree.column("Estado", width=100)
        self.history_tree.column("Mensaje", width=200)

        # Configurar colores para las filas
        self.history_tree.tag_configure("permitido", background="#e8f5e8")
        self.history_tree.tag_configure("denegado", background="#ffe8e8")

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        h_scrollbar = ttk.Scrollbar(history_frame, orient=tk.HORIZONTAL, command=self.history_tree.xview)
        self.history_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Grid del Treeview y scrollbars
        self.history_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))

        # Frame para controles y estadísticas
        control_frame = ttk.Frame(self)
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        control_frame.columnconfigure(2, weight=1)

        # Botones de control
        ttk.Button(control_frame, text="Actualizar", command=self.cargar_historial).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(control_frame, text="Limpiar Historial", command=self.limpiar_historial).grid(row=0, column=1, padx=(0, 10))

        # Estadísticas en tiempo real
        self.stats_label = ttk.Label(control_frame, text="Esperando datos...")
        self.stats_label.grid(row=0, column=2, sticky=tk.E)

        # Cargar historial inicial
        self.cargar_historial()

        print("MonitorTab: Configuración de GUI completa.")

    def iniciar_lectura(self):
        """Inicia el hilo de lectura serial si no está activo."""
        if not self.reading_active:
            print("MonitorTab: Intentando iniciar lectura...")
            self.reading_active = True
            self.reading_thread = threading.Thread(target=self.read_from_serial, daemon=True)
            self.reading_thread.start()
            print("MonitorTab: Hilo de lectura iniciado.")
        else:
            print("MonitorTab: La lectura ya está activa.")

    def detener_lectura(self):
        """Detiene el hilo de lectura serial."""
        if self.reading_active:
            print("MonitorTab: Solicitando detener lectura...")
            self.reading_active = False
            print("MonitorTab: reading_active establecido a False.")

    def read_from_serial(self):
        """Lee datos del puerto serial en un hilo separado."""
        print("MonitorTab: Hilo de lectura activo. Esperando datos del serial real...")
        while self.reading_active:
            try:
                if self.serial_manager and self.serial_manager.is_connected:
                    serial_data = self.serial_manager.read_continuous_data()
                    if serial_data:
                        print(f"MonitorTab: Datos serial válidos leídos: '{serial_data}'.")
                        self.root.after(0, self.process_reading, serial_data)
                else:
                    time.sleep(0.5)
            except Exception as e:
                print(f"MonitorTab: Error en hilo de lectura serial - {str(e)}")
                time.sleep(1)

        print("MonitorTab: Hilo de lectura terminado.")

    def process_reading(self, serial_data):
        """Procesa los datos leídos del serial y actualiza el historial."""
        print(f"MonitorTab: process_reading llamado con datos seriales: '{serial_data}'")
        
        # Limpiar y parsear los datos recibidos
        cleaned_data = serial_data.strip()
        
        # Solo procesar datos de registro (intentos de acceso)
        if cleaned_data.startswith('REGISTRO:'):
            # Formato: REGISTRO:UID|Timestamp|Estado
            parts = cleaned_data.split(':', 1)[1].split('|')
            if len(parts) >= 3:
                uid = parts[0]
                timestamp_arduino = parts[1]
                estado_arduino = parts[2]
                
                print(f"MonitorTab: Intento de acceso detectado - UID: {uid}")
                
                # Verificar acceso usando el AccessManager
                access_granted, access_message = self.access_manager.check_access(uid)
                registered_name = self.access_manager.get_registered_name(uid)
                
                # Crear entrada para el historial
                now = datetime.now()
                fecha = now.strftime("%Y-%m-%d")
                hora = now.strftime("%H:%M:%S")
                estado = "PERMITIDO" if access_granted else "DENEGADO"
                
                # Agregar al historial visual
                self.root.after(0, self.agregar_intento_historial, fecha, hora, uid, registered_name, estado, access_message)
                
                # Enviar respuesta al Arduino
                if access_granted:
                    command_to_send = f"ACCESO:PERMITIDO|{registered_name}"
                else:
                    command_to_send = f"ACCESO:DENEGADO|{access_message}"
                
                if self.serial_manager and self.serial_manager.is_connected:
                    self.serial_manager.send_command(command_to_send)
                    print(f"MonitorTab: Comando enviado al Arduino: '{command_to_send}'")
                
                # Registrar en el log
                if self.access_logger:
                    self.access_logger.log_attempt(uid, registered_name, estado)

    def agregar_intento_historial(self, fecha, hora, uid, nombre, estado, mensaje):
        """Agrega un intento de acceso al historial visual."""
        # Determinar el tag para el color de fila
        tag = "permitido" if estado == "PERMITIDO" else "denegado"
        
        # Insertar al inicio del Treeview (más recientes primero)
        self.history_tree.insert("", 0, values=(fecha, hora, uid, nombre, estado, mensaje), tags=(tag,))
        
        # Mantener solo los últimos 100 intentos para rendimiento
        children = self.history_tree.get_children()
        if len(children) > 100:
            for item in children[100:]:
                self.history_tree.delete(item)
        
        # Actualizar estadísticas
        self.actualizar_estadisticas()
        
        print(f"MonitorTab: Intento agregado al historial - {uid} - {nombre} - {estado}")

    def cargar_historial(self):
        """Carga el historial desde el archivo de log."""
        print("MonitorTab: Cargando historial desde archivo...")
        
        # Limpiar el Treeview
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        try:
            # Cargar las últimas 50 líneas del historial
            history_lines = self.file_manager.load_history(50)
            
            for line in history_lines:
                parsed_entry = self.parse_log_line(line.strip())
                if parsed_entry:
                    fecha, hora, uid, nombre, estado, mensaje = parsed_entry
                    tag = "permitido" if "PERMITIDO" in estado else "denegado"
                    self.history_tree.insert("", 0, values=parsed_entry, tags=(tag,))
            
            self.actualizar_estadisticas()
            print(f"MonitorTab: {len(history_lines)} entradas cargadas desde el historial.")
            
        except Exception as e:
            print(f"MonitorTab: Error al cargar historial - {str(e)}")

    def parse_log_line(self, line):
        """Parsea una línea del log y extrae la información."""
        try:
            if not line.strip() or not line.startswith('['):
                return None
            
            # Extraer timestamp
            timestamp_end = line.find(']')
            if timestamp_end == -1:
                return None
            
            timestamp_str = line[1:timestamp_end]
            try:
                datetime_obj = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                fecha = datetime_obj.strftime("%Y-%m-%d")
                hora = datetime_obj.strftime("%H:%M:%S")
            except ValueError:
                return None
            
            # Extraer el resto de la información usando regex
            import re
            rest = line[timestamp_end + 1:].strip()
            
            uid_match = re.search(r'UID:\s*([^|]+)', rest)
            name_match = re.search(r'Nombre:\s*([^|]+)', rest)
            status_match = re.search(r'Estado:\s*([^|]+)', rest)
            message_match = re.search(r'Mensaje:\s*(.+)', rest)
            
            uid = uid_match.group(1).strip() if uid_match else "N/A"
            nombre = name_match.group(1).strip() if name_match else "N/A"
            estado = status_match.group(1).strip() if status_match else "N/A"
            mensaje = message_match.group(1).strip() if message_match else ""
            
            return (fecha, hora, uid, nombre, estado, mensaje)
            
        except Exception as e:
            print(f"MonitorTab: Error al parsear línea '{line}': {str(e)}")
            return None

    def limpiar_historial(self):
        """Limpia el historial visual."""
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        self.actualizar_estadisticas()
        print("MonitorTab: Historial visual limpiado.")

    def actualizar_estadisticas(self):
        """Actualiza las estadísticas mostradas."""
        children = self.history_tree.get_children()
        total = len(children)
        
        if total == 0:
            self.stats_label.config(text="Sin intentos registrados")
            return
        
        permitidos = 0
        denegados = 0
        
        for child in children:
            values = self.history_tree.item(child, "values")
            if len(values) >= 5:
                estado = values[4]  # Columna Estado
                if "PERMITIDO" in estado:
                    permitidos += 1
                elif "DENEGADO" in estado:
                    denegados += 1
        
        stats_text = f"Total: {total} | Permitidos: {permitidos} | Denegados: {denegados}"
        if total > 0:
            permitidos_pct = (permitidos / total) * 100
            denegados_pct = (denegados / total) * 100
            stats_text += f" | Éxito: {permitidos_pct:.1f}% | Fallos: {denegados_pct:.1f}%"
        
        self.stats_label.config(text=stats_text)
