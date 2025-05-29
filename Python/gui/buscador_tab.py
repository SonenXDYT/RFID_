# File: gui/buscador_tab.py
import tkinter as tk
from tkinter import ttk, messagebox
import time
import re
from datetime import datetime, timedelta
# Importar managers necesarios
from core.serial_manager import SerialManager
from core.access_manager import AccessManager
from core.file_manager import FileManager
from core.access_logger import AccessLogger
from utils.email_sender import EmailSender
import io
import csv

class BuscadorTab(ttk.Frame):
    def __init__(self, parent, root, serial_manager, access_manager, file_manager, access_logger):
        super().__init__(parent, padding="10")
        self.root = root # Referencia a la ventana principal
        self.serial_manager = serial_manager
        self.access_manager = access_manager
        self.file_manager = file_manager
        self.access_logger = access_logger

        self.historial_completo = [] # Para almacenar todo el historial cargado
        self.resultados_busqueda = [] # Para almacenar los resultados de la búsqueda actual

        # Inicializar EmailSender
        self.email_sender = EmailSender(self.root)

        self.configurar_gui()
        self.cargar_historial() # Cargar historial al inicializar

    def configurar_gui(self):
        # Configurar el layout para que se expanda
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1) # La tabla de resultados se expandirá

        # Título
        title_frame = ttk.Frame(self)
        title_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        title_frame.columnconfigure(0, weight=1)
        
        ttk.Label(title_frame, text="Búsqueda en Historial de Accesos", font=('Arial', 14, 'bold')).grid(row=0, column=0)

        # Frame de búsqueda
        search_frame = ttk.LabelFrame(self, text="Criterios de Búsqueda", padding="10")
        search_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        search_frame.columnconfigure(1, weight=1)

        # Tipo de búsqueda
        ttk.Label(search_frame, text="Buscar por:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.search_type_var = tk.StringVar(value="UID")
        search_type_frame = ttk.Frame(search_frame)
        search_type_frame.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Radiobutton(search_type_frame, text="UID", variable=self.search_type_var, value="UID").grid(row=0, column=0, padx=5)
        ttk.Radiobutton(search_type_frame, text="Nombre", variable=self.search_type_var, value="Nombre").grid(row=0, column=1, padx=5)
        ttk.Radiobutton(search_type_frame, text="Ambos", variable=self.search_type_var, value="Ambos").grid(row=0, column=2, padx=5)

        # Campo de búsqueda
        ttk.Label(search_frame, text="Término de búsqueda:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.search_term_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_term_var, width=30)
        self.search_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        self.search_entry.bind('<Return>', lambda e: self.realizar_busqueda()) # Buscar al presionar Enter

        # Filtro por estado
        ttk.Label(search_frame, text="Estado:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.status_filter_var = tk.StringVar(value="Todos")
        status_frame = ttk.Frame(search_frame)
        status_frame.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Radiobutton(status_frame, text="Todos", variable=self.status_filter_var, value="Todos").grid(row=0, column=0, padx=5)
        ttk.Radiobutton(status_frame, text="Permitido", variable=self.status_filter_var, value="Permitido").grid(row=0, column=1, padx=5)
        ttk.Radiobutton(status_frame, text="Denegado", variable=self.status_filter_var, value="Denegado").grid(row=0, column=2, padx=5)

        # Filtro por fecha
        ttk.Label(search_frame, text="Filtro de fecha:").grid(row=3, column=0, sticky=tk.W, pady=2)
        date_frame = ttk.Frame(search_frame)
        date_frame.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        date_frame.columnconfigure(1, weight=1)
        date_frame.columnconfigure(3, weight=1)

        self.date_filter_var = tk.StringVar(value="Todos")
        date_filter_combo = ttk.Combobox(date_frame, textvariable=self.date_filter_var, width=15, state="readonly")
        date_filter_combo['values'] = ("Todos", "Hoy", "Ayer", "Última semana", "Último mes", "Rango personalizado")
        date_filter_combo.grid(row=0, column=0, padx=(0, 5))
        date_filter_combo.bind('<<ComboboxSelected>>', self.on_date_filter_change)

        # Campos para rango personalizado (inicialmente ocultos)
        ttk.Label(date_frame, text="Desde:").grid(row=0, column=1, sticky=tk.W, padx=5)
        self.date_from_var = tk.StringVar()
        self.date_from_entry = ttk.Entry(date_frame, textvariable=self.date_from_var, width=12, state='disabled')
        self.date_from_entry.grid(row=0, column=2, padx=2)

        ttk.Label(date_frame, text="Hasta:").grid(row=0, column=3, sticky=tk.W, padx=5)
        self.date_to_var = tk.StringVar()
        self.date_to_entry = ttk.Entry(date_frame, textvariable=self.date_to_var, width=12, state='disabled')
        self.date_to_entry.grid(row=0, column=4, padx=2)

        # Botones de búsqueda
        button_frame = ttk.Frame(search_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Buscar", command=self.realizar_busqueda).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Limpiar", command=self.limpiar_busqueda).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Actualizar Historial", command=self.cargar_historial).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="Enviar por Correo", command=self.enviar_por_correo).grid(row=0, column=3, padx=5)

        # Frame para resultados
        results_frame = ttk.LabelFrame(self, text="Resultados de Búsqueda", padding="5")
        results_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)

        # Tabla de resultados
        columns = ('Timestamp', 'UID', 'Nombre', 'Estado')
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=15)
        
        # Definir encabezados
        self.results_tree.heading('Timestamp', text='Fecha y Hora')
        self.results_tree.heading('UID', text='UID')
        self.results_tree.heading('Nombre', text='Nombre')
        self.results_tree.heading('Estado', text='Estado')
        
        # Configurar ancho de columnas
        self.results_tree.column('Timestamp', width=150, minwidth=120)
        self.results_tree.column('UID', width=150, minwidth=100)
        self.results_tree.column('Nombre', width=150, minwidth=100)
        self.results_tree.column('Estado', width=100, minwidth=80)
        
        self.results_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Scrollbars para la tabla
        v_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.results_tree.configure(yscrollcommand=v_scrollbar.set)

        h_scrollbar = ttk.Scrollbar(results_frame, orient=tk.HORIZONTAL, command=self.results_tree.xview)
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        self.results_tree.configure(xscrollcommand=h_scrollbar.set)

        # Etiqueta de estadísticas
        self.stats_label = ttk.Label(results_frame, text="")
        self.stats_label.grid(row=2, column=0, columnspan=2, pady=5)

    def on_date_filter_change(self, event=None):
        """Maneja el cambio en el filtro de fecha."""
        if self.date_filter_var.get() == "Rango personalizado":
            self.date_from_entry.config(state='normal')
            self.date_to_entry.config(state='normal')
            # Establecer fechas por defecto
            today = datetime.now()
            week_ago = today - timedelta(days=7)
            self.date_from_var.set(week_ago.strftime('%Y-%m-%d'))
            self.date_to_var.set(today.strftime('%Y-%m-%d'))
        else:
            self.date_from_entry.config(state='disabled')
            self.date_to_entry.config(state='disabled')
            self.date_from_var.set("")
            self.date_to_var.set("")

    def cargar_historial(self):
        """Carga todo el historial desde el archivo."""
        print("BuscadorTab: Cargando historial completo...") # Debug
        
        try:
            # Cargar líneas del historial
            history_lines = self.file_manager.load_history(1000)  # Cargar últimas 1000 líneas
            
            # Parsear las líneas a formato de diccionario
            self.historial_completo = []
            for line in history_lines:
                parsed_entry = self.parse_log_line(line.strip())
                if parsed_entry:
                    self.historial_completo.append(parsed_entry)
            
            print(f"BuscadorTab: Cargadas {len(self.historial_completo)} entradas del historial.") # Debug
            
            # Mostrar todas las entradas por defecto
            self.mostrar_resultados(self.historial_completo)
            
        except Exception as e:
            print(f"BuscadorTab: Error al cargar historial: {e}") # Debug
            messagebox.showerror("Error", f"No se pudo cargar el historial: {e}")

    def parse_log_line(self, line):
        """Parsea una línea del log y la convierte a diccionario."""
        try:
            if not line.strip() or not line.startswith('['):
                return None
            
            # Extraer timestamp
            timestamp_end = line.find(']')
            if timestamp_end == -1:
                return None
            
            timestamp_str = line[1:timestamp_end]
            
            # Extraer el resto de la información
            rest = line[timestamp_end + 1:].strip()
            
            uid_match = re.search(r'UID:\s*([^|]+)', rest)
            name_match = re.search(r'Nombre:\s*([^|]+)', rest)
            status_match = re.search(r'Estado:\s*([^|]+)', rest)
            
            uid = uid_match.group(1).strip() if uid_match else "N/A"
            nombre = name_match.group(1).strip() if name_match else "N/A"
            estado = status_match.group(1).strip() if status_match else "N/A"
            
            return {
                'timestamp': timestamp_str,
                'uid': uid,
                'name': nombre,
                'status': estado
            }
            
        except Exception as e:
            print(f"BuscadorTab: Error al parsear línea '{line}': {str(e)}")
            return None

    def realizar_busqueda(self):
        """Realiza la búsqueda basada en los criterios especificados."""
        search_term = self.search_term_var.get().strip().lower()
        search_type = self.search_type_var.get()
        status_filter = self.status_filter_var.get()
        date_filter = self.date_filter_var.get()

        print(f"BuscadorTab: Realizando búsqueda - Término: '{search_term}', Tipo: {search_type}, Estado: {status_filter}, Fecha: {date_filter}") # Debug

        # Filtrar por término de búsqueda
        resultados = []
        for entrada in self.historial_completo:
            uid = entrada.get('uid', '').lower()
            nombre = entrada.get('name', '').lower()
            
            # Aplicar filtro de búsqueda
            match = False
            if search_type == "UID":
                match = search_term in uid
            elif search_type == "Nombre":
                match = search_term in nombre
            elif search_type == "Ambos":
                match = search_term in uid or search_term in nombre
            
            # Si no hay término de búsqueda, incluir todas las entradas
            if not search_term:
                match = True
                
            if match:
                resultados.append(entrada)

        # Filtrar por estado
        if status_filter != "Todos":
            resultados = [r for r in resultados if r.get('status', '') == status_filter]

        # Filtrar por fecha
        resultados = self.aplicar_filtro_fecha(resultados, date_filter)

        # Guardar resultados para uso posterior (como envío por correo)
        self.resultados_busqueda = resultados

        # Mostrar resultados
        self.mostrar_resultados(resultados)
        
        print(f"BuscadorTab: Búsqueda completada. {len(resultados)} resultados encontrados.") # Debug

    def aplicar_filtro_fecha(self, resultados, date_filter):
        """Aplica el filtro de fecha a los resultados."""
        if date_filter == "Todos":
            return resultados

        try:
            today = datetime.now()
            
            if date_filter == "Hoy":
                fecha_inicio = today.replace(hour=0, minute=0, second=0, microsecond=0)
                fecha_fin = today.replace(hour=23, minute=59, second=59, microsecond=999999)
            elif date_filter == "Ayer":
                ayer = today - timedelta(days=1)
                fecha_inicio = ayer.replace(hour=0, minute=0, second=0, microsecond=0)
                fecha_fin = ayer.replace(hour=23, minute=59, second=59, microsecond=999999)
            elif date_filter == "Última semana":
                fecha_inicio = today - timedelta(days=7)
                fecha_fin = today
            elif date_filter == "Último mes":
                fecha_inicio = today - timedelta(days=30)
                fecha_fin = today
            elif date_filter == "Rango personalizado":
                try:
                    fecha_inicio = datetime.strptime(self.date_from_var.get(), '%Y-%m-%d')
                    fecha_fin = datetime.strptime(self.date_to_var.get(), '%Y-%m-%d')
                    fecha_fin = fecha_fin.replace(hour=23, minute=59, second=59) # Incluir todo el día final
                except ValueError:
                    messagebox.showerror("Error", "Formato de fecha incorrecto. Use YYYY-MM-DD")
                    return resultados
            else:
                return resultados

            # Filtrar resultados por fecha
            resultados_filtrados = []
            for entrada in resultados:
                try:
                    # Parsear el timestamp de la entrada
                    timestamp_str = entrada.get('timestamp', '')
                    entrada_fecha = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                    
                    if fecha_inicio <= entrada_fecha <= fecha_fin:
                        resultados_filtrados.append(entrada)
                except ValueError:
                    # Si no se puede parsear la fecha, incluir la entrada
                    print(f"BuscadorTab: No se pudo parsear fecha: {timestamp_str}") # Debug
                    resultados_filtrados.append(entrada)

            return resultados_filtrados

        except Exception as e:
            print(f"BuscadorTab: Error al aplicar filtro de fecha: {e}") # Debug
            messagebox.showerror("Error", f"Error al aplicar filtro de fecha: {e}")
            return resultados

    def mostrar_resultados(self, resultados):
        """Muestra los resultados en la tabla."""
        # Limpiar tabla actual
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        # Añadir resultados a la tabla (ordenados por fecha, más recientes primero)
        resultados_ordenados = sorted(resultados, key=lambda x: x.get('timestamp', ''), reverse=True)
        
        for entrada in resultados_ordenados:
            timestamp = entrada.get('timestamp', 'N/A')
            uid = entrada.get('uid', 'N/A')
            nombre = entrada.get('name', 'N/A')
            estado = entrada.get('status', 'N/A')
            
            # Añadir colores basados en el estado
            tags = []
            if estado == "PERMITIDO":
                tags = ['permitido']
            elif estado == "DENEGADO":
                tags = ['denegado']
            
            self.results_tree.insert('', tk.END, values=(timestamp, uid, nombre, estado), tags=tags)

        # Configurar colores para las etiquetas
        self.results_tree.tag_configure('permitido', foreground='green')
        self.results_tree.tag_configure('denegado', foreground='red')

        # Actualizar estadísticas
        total_resultados = len(resultados)
        permitidos = len([r for r in resultados if r.get('status') == 'PERMITIDO'])
        denegados = len([r for r in resultados if r.get('status') == 'DENEGADO'])
        
        stats_text = f"Total: {total_resultados} | Permitidos: {permitidos} | Denegados: {denegados}"
        self.stats_label.config(text=stats_text)

        print(f"BuscadorTab: Mostrando {total_resultados} resultados en la tabla.") # Debug

    def limpiar_busqueda(self):
        """Limpia los campos de búsqueda y muestra todos los resultados."""
        self.search_term_var.set("")
        self.search_type_var.set("UID")
        self.status_filter_var.set("Todos")
        self.date_filter_var.set("Todos")
        self.date_from_var.set("")
        self.date_to_var.set("")
        self.date_from_entry.config(state='disabled')
        self.date_to_entry.config(state='disabled')
        
        # Mostrar todos los resultados
        self.resultados_busqueda = self.historial_completo
        self.mostrar_resultados(self.historial_completo)
        
        print("BuscadorTab: Búsqueda limpiada, mostrando todos los resultados.") # Debug

    def enviar_por_correo(self):
        """Envía los resultados actuales por correo."""
        # Usar resultados de búsqueda si existen, sino usar historial completo
        datos_a_enviar = self.resultados_busqueda if self.resultados_busqueda else self.historial_completo
        
        if not datos_a_enviar:
            messagebox.showwarning("Advertencia", "No hay datos para enviar.")
            return
        
        # Crear CSV y enviar
        datos_csv = self.crear_csv_reporte(datos_a_enviar)
        self.email_sender.abrir_ventana_envio(datos_csv, "Reporte de Historial de Accesos")

    def crear_csv_reporte(self, datos):
        """Crea un archivo CSV con los datos especificados."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Escribir encabezados
        writer.writerow(['Fecha y Hora', 'UID', 'Nombre', 'Estado'])
        
        # Escribir datos
        for entrada in datos:
            writer.writerow([
                entrada.get('timestamp', 'N/A'),
                entrada.get('uid', 'N/A'),
                entrada.get('name', 'N/A'),
                entrada.get('status', 'N/A')
            ])
        
        return output.getvalue()
