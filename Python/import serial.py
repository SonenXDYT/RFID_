import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from datetime import datetime
import csv
import io
import time

class BuscadorTab:
    def __init__(self, parent):
        self.parent = parent
        self.resultados_busqueda = []
        self.setup_ui()

    def setup_ui(self):
        # Frame principal
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Título
        title_label = ttk.Label(main_frame, text="Buscador de Registros", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))

        # Frame de búsqueda
        search_frame = ttk.LabelFrame(main_frame, text="Criterios de Búsqueda", padding=10)
        search_frame.pack(fill=tk.X, pady=(0, 10))

        # UID
        ttk.Label(search_frame, text="UID:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.uid_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.uid_var, width=30).grid(row=0, column=1, padx=(0, 20))

        # Nombre
        ttk.Label(search_frame, text="Nombre:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.nombre_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.nombre_var, width=30).grid(row=0, column=3)

        # Estado
        ttk.Label(search_frame, text="Estado:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(10, 0))
        self.estado_var = tk.StringVar()
        estado_combo = ttk.Combobox(search_frame, textvariable=self.estado_var, width=27)
        estado_combo['values'] = ('Todos', 'Activo', 'Inactivo', 'Pendiente')
        estado_combo.set('Todos')
        estado_combo.grid(row=1, column=1, pady=(10, 0), padx=(0, 20))

        # Fecha desde
        ttk.Label(search_frame, text="Fecha desde:").grid(row=1, column=2, sticky=tk.W, padx=(0, 5), pady=(10, 0))
        self.fecha_desde_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.fecha_desde_var, width=30).grid(row=1, column=3, pady=(10, 0))

        # Fecha hasta
        ttk.Label(search_frame, text="Fecha hasta:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5), pady=(10, 0))
        self.fecha_hasta_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.fecha_hasta_var, width=30).grid(row=2, column=1, pady=(10, 0), padx=(0, 20))

        # Botones de búsqueda
        button_frame = ttk.Frame(search_frame)
        button_frame.grid(row=3, column=0, columnspan=4, pady=(15, 0))

        ttk.Button(button_frame, text="Buscar", command=self.buscar_registros).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Limpiar", command=self.limpiar_campos).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Exportar", command=self.exportar_resultados).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Enviar por Correo", command=self.abrir_envio_correo).pack(side=tk.LEFT)

        # Frame de resultados
        results_frame = ttk.LabelFrame(main_frame, text="Resultados", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        # Treeview para mostrar resultados
        columns = ('Fecha y Hora', 'UID', 'Nombre', 'Estado')
        self.tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=15)

        # Configurar columnas
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(results_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Posicionar elementos
        self.tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')

        # Configurar expansión
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)

        # Label de información
        self.info_label = ttk.Label(results_frame, text="0 registros encontrados")
        self.info_label.grid(row=2, column=0, columnspan=2, pady=(10, 0))

    def buscar_registros(self):
        """Busca registros según los criterios especificados."""
        # Limpiar resultados anteriores
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.resultados_busqueda = []

        # Obtener criterios de búsqueda
        uid = self.uid_var.get().strip()
        nombre = self.nombre_var.get().strip()
        estado = self.estado_var.get()
        fecha_desde = self.fecha_desde_var.get().strip()
        fecha_hasta = self.fecha_hasta_var.get().strip()

        # Simular búsqueda (aquí iría la lógica real de búsqueda)
        # Por ahora generamos datos de ejemplo
        datos_ejemplo = [
            {'timestamp': '2024-01-15 10:30:00', 'uid': 'USR001', 'name': 'Juan Pérez', 'status': 'Activo'},
            {'timestamp': '2024-01-15 11:45:00', 'uid': 'USR002', 'name': 'María García', 'status': 'Inactivo'},
            {'timestamp': '2024-01-15 14:20:00', 'uid': 'USR003', 'name': 'Carlos López', 'status': 'Pendiente'},
            {'timestamp': '2024-01-16 09:15:00', 'uid': 'USR004', 'name': 'Ana Martínez', 'status': 'Activo'},
            {'timestamp': '2024-01-16 16:30:00', 'uid': 'USR005', 'name': 'Pedro Rodríguez', 'status': 'Activo'},
        ]

        # Filtrar datos según criterios
        for registro in datos_ejemplo:
            incluir = True
            
            if uid and uid.lower() not in registro['uid'].lower():
                incluir = False
            
            if nombre and nombre.lower() not in registro['name'].lower():
                incluir = False
            
            if estado != 'Todos' and estado != registro['status']:
                incluir = False
            
            if incluir:
                self.resultados_busqueda.append(registro)
                self.tree.insert('', tk.END, values=(
                    registro['timestamp'],
                    registro['uid'],
                    registro['name'],
                    registro['status']
                ))

        # Actualizar información
        self.info_label.config(text=f"{len(self.resultados_busqueda)} registros encontrados")

    def limpiar_campos(self):
        """Limpia todos los campos de búsqueda."""
        self.uid_var.set('')
        self.nombre_var.set('')
        self.estado_var.set('Todos')
        self.fecha_desde_var.set('')
        self.fecha_hasta_var.set('')
        
        # Limpiar resultados
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.resultados_busqueda = []
        self.info_label.config(text="0 registros encontrados")

    def exportar_resultados(self):
        """Exporta los resultados a un archivo CSV."""
        if not self.resultados_busqueda:
            messagebox.showwarning("Advertencia", "No hay resultados para exportar.")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Guardar resultados como..."
        )

        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['Fecha y Hora', 'UID', 'Nombre', 'Estado'])
                    
                    for registro in self.resultados_busqueda:
                        writer.writerow([
                            registro['timestamp'],
                            registro['uid'],
                            registro['name'],
                            registro['status']
                        ])
                
                messagebox.showinfo("Éxito", f"Resultados exportados exitosamente a {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Error al exportar: {str(e)}")

    def abrir_envio_correo(self):
        """Abre la ventana para enviar resultados por correo."""
        if not self.resultados_busqueda:
            messagebox.showwarning("Advertencia", "No hay resultados para enviar.")
            return

        # Crear ventana de envío
        envio_window = tk.Toplevel(self.parent)
        envio_window.title("Enviar por Correo")
        envio_window.geometry("500x600")
        envio_window.transient(self.parent)
        envio_window.grab_set()

        # Frame principal
        main_frame = ttk.Frame(envio_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Título
        ttk.Label(main_frame, text="Enviar Resultados por Correo", font=("Arial", 14, "bold")).pack(pady=(0, 20))

        # Destinatarios
        dest_frame = ttk.LabelFrame(main_frame, text="Destinatarios", padding=10)
        dest_frame.pack(fill=tk.X, pady=(0, 15))

        # Lista de correos predefinidos (esto podría venir de configuración)
        correos_predefinidos = [
            "abc@gmail.com",
        ]

        correo_vars = {}
        for correo in correos_predefinidos:
            var = tk.BooleanVar()
            correo_vars[correo] = var
            ttk.Checkbutton(dest_frame, text=correo, variable=var).pack(anchor=tk.W, pady=2)

        # Correo personalizado
        ttk.Label(dest_frame, text="Correo adicional:").pack(anchor=tk.W, pady=(10, 5))
        correo_adicional_var = tk.StringVar()
        ttk.Entry(dest_frame, textvariable=correo_adicional_var, width=50).pack(fill=tk.X)

        # Asunto
        asunto_frame = ttk.LabelFrame(main_frame, text="Asunto", padding=10)
        asunto_frame.pack(fill=tk.X, pady=(0, 15))

        asunto_var = tk.StringVar(value=f"Reporte de Búsqueda - {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        ttk.Entry(asunto_frame, textvariable=asunto_var, width=60).pack(fill=tk.X)

        # Mensaje
        mensaje_frame = ttk.LabelFrame(main_frame, text="Mensaje", padding=10)
        mensaje_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        mensaje_text = tk.Text(mensaje_frame, height=8, wrap=tk.WORD)
        mensaje_text.pack(fill=tk.BOTH, expand=True)

        # Mensaje predeterminado
        mensaje_predeterminado = f"""Estimado/a,

Adjunto encontrará el reporte de búsqueda solicitado con {len(self.resultados_busqueda)} registros encontrados.

Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

Saludos cordiales."""

        mensaje_text.insert("1.0", mensaje_predeterminado)

        # Función para enviar correo
        def enviar_correo():
            # Obtener destinatarios seleccionados
            destinatarios = [correo for correo, var in correo_vars.items() if var.get()]
            
            # Agregar correo adicional si existe
            correo_adicional = correo_adicional_var.get().strip()
            if correo_adicional:
                destinatarios.append(correo_adicional)
            
            if not destinatarios:
                messagebox.showwarning("Advertencia", "Seleccione al menos un destinatario.")
                return

            asunto = asunto_var.get().strip()
            mensaje = mensaje_text.get("1.0", tk.END).strip()

            if not asunto:
                messagebox.showerror("Error", "El asunto no puede estar vacío.")
                return

            # Crear archivo CSV con los resultados
            csv_data = self.crear_csv_reporte()
            
            # Configurar ventana de progreso
            progress_window = tk.Toplevel(envio_window)
            progress_window.title("Enviando...")
            progress_window.geometry("300x100")
            progress_window.transient(envio_window)
            progress_window.grab_set()
            
            ttk.Label(progress_window, text="Enviando correo...").pack(pady=20)
            progress_window.update()
            
            try:
                # Aquí iría la lógica real de envío de correo
                # Por ahora simularemos el envío
                time.sleep(2)  # Simular tiempo de envío
                
                progress_window.destroy()
                messagebox.showinfo("Éxito", f"Correo enviado exitosamente a {len(destinatarios)} destinatario(s).")
                envio_window.destroy()
                
            except Exception as e:
                progress_window.destroy()
                messagebox.showerror("Error", f"Error al enviar correo: {str(e)}")

        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Enviar", command=enviar_correo).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=envio_window.destroy).pack(side=tk.LEFT, padx=5)

    def crear_csv_reporte(self):
        """Crea un archivo CSV con los resultados de la búsqueda."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Escribir encabezados
        writer.writerow(['Fecha y Hora', 'UID', 'Nombre', 'Estado'])
        
        # Escribir datos
        for entrada in self.resultados_busqueda:
            writer.writerow([
                entrada.get('timestamp', 'N/A'),
                entrada.get('uid', 'N/A'),
                entrada.get('name', 'N/A'),
                entrada.get('status', 'N/A')
            ])
        
        return output.getvalue()
