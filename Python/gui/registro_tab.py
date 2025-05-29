# File: gui/registro_tab.py
import tkinter as tk
from tkinter import ttk, messagebox
import time
import datetime
import re # Importar re para parsear
# Importar managers necesarios
from core.serial_manager import SerialManager
from core.access_manager import AccessManager
from core.file_manager import FileManager

class RegistroTab(ttk.Frame):
    def __init__(self, parent, root, serial_manager, access_manager, file_manager):
        super().__init__(parent, padding="10")
        self.root = root # Referencia a la ventana principal
        self.serial_manager = serial_manager
        self.access_manager = access_manager
        self.file_manager = file_manager

        self._uid_to_register = None # Para almacenar el UID leído para registro

        self.configurar_gui()

    def configurar_gui(self):
        # Configurar el layout para que se expanda
        self.columnconfigure(1, weight=1) # La columna de entrada se expandirá

        # Sección para leer UID
        ttk.Label(self, text="Leer UID para Registrar:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.read_uid_button = ttk.Button(self, text="Leer UID", command=self.read_uid_for_registration)
        self.read_uid_button.grid(row=0, column=1, sticky=tk.W, padx=5)

        ttk.Label(self, text="UID Leído:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.uid_label = ttk.Label(self, text="Presione 'Leer UID' para comenzar...")
        self.uid_label.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)

        # Sección para Nombre
        ttk.Label(self, text="Nombre:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.name_entry = ttk.Entry(self, width=40)
        self.name_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5)

        # Sección para Tarjeta Temporal
        self.temporal_var = tk.BooleanVar()
        self.temporal_check = ttk.Checkbutton(self, text="Tarjeta Temporal", variable=self.temporal_var, command=self.toggle_temporal_options)
        self.temporal_check.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=10)

        # Frame para opciones temporales (inicialmente oculto)
        self.temporal_options_frame = ttk.Frame(self)

        ttk.Label(self.temporal_options_frame, text="Fecha de Caducidad (YYYY-MM-DD):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.expiry_date_entry = ttk.Entry(self.temporal_options_frame, width=20)
        self.expiry_date_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)

        ttk.Label(self.temporal_options_frame, text="Hora de Caducidad (HH:MM:SS):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.expiry_time_entry = ttk.Entry(self.temporal_options_frame, width=20)
        self.expiry_time_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)

        # Botón para establecer fecha/hora actual + tiempo adicional
        ttk.Button(self.temporal_options_frame, text="Ahora + 1 hora", command=self.set_current_plus_hour).grid(row=2, column=0, padx=5, pady=5)
        ttk.Button(self.temporal_options_frame, text="Ahora + 1 día", command=self.set_current_plus_day).grid(row=2, column=1, padx=5, pady=5)

        # Botón para Registrar
        ttk.Button(self, text="Registrar Tarjeta", command=self.register_card).grid(row=5, column=0, columnspan=2, pady=20)

        # Inicialmente ocultar opciones temporales
        self.toggle_temporal_options()

    def set_current_plus_hour(self):
        """Establece la fecha y hora actual + 1 hora."""
        future_time = datetime.datetime.now() + datetime.timedelta(hours=1)
        self.expiry_date_entry.delete(0, tk.END)
        self.expiry_date_entry.insert(0, future_time.strftime('%Y-%m-%d'))
        self.expiry_time_entry.delete(0, tk.END)
        self.expiry_time_entry.insert(0, future_time.strftime('%H:%M:%S'))

    def set_current_plus_day(self):
        """Establece la fecha y hora actual + 1 día."""
        future_time = datetime.datetime.now() + datetime.timedelta(days=1)
        self.expiry_date_entry.delete(0, tk.END)
        self.expiry_date_entry.insert(0, future_time.strftime('%Y-%m-%d'))
        self.expiry_time_entry.delete(0, tk.END)
        self.expiry_time_entry.insert(0, future_time.strftime('%H:%M:%S'))

    def toggle_temporal_options(self):
        """Muestra u oculta las opciones de tarjeta temporal."""
        if self.temporal_var.get():
            self.temporal_options_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=10)
        else:
            self.temporal_options_frame.grid_forget()

    def read_uid_for_registration(self):
        """
        Activa el modo registro en Arduino, lee un UID síncronamente
        y lo muestra en la GUI de registro.
        """
        print("RegistroTab: Intentando leer UID para registro...") # Debug
        self._uid_to_register = None # Limpiar UID anterior
        
        # Deshabilitar el botón mientras se lee
        self.read_uid_button.config(state=tk.DISABLED, text="Leyendo...")
        self.uid_label.config(text="Modo registro activado - Acerca la tarjeta...")
        
        # Actualizar la GUI antes de la operación bloqueante
        self.root.update()

        if self.serial_manager and self.serial_manager.is_connected:
            # Usar el nuevo método síncrono para leer un UID específico para registro
            # Este método pausa/reanuda el hilo de monitoreo y envía comandos al Arduino
            uid_detectado = self.serial_manager.read_single_uid_for_registration(timeout=15) # Esperar hasta 15 segundos

            if uid_detectado:
                 print(f"RegistroTab: UID detectado para registro: '{uid_detectado}'") # Debug
                 self._uid_to_register = uid_detectado
                 self.uid_label.config(text=uid_detectado)
                 print(f"RegistroTab: UID '{uid_detectado}' listo para registro.") # Debug
            else:
                self._uid_to_register = None
                self.uid_label.config(text="Timeout - No se leyó UID")
                print("RegistroTab: Timeout o no se recibió UID_DETECTADO para registro.") # Debug
                messagebox.showinfo("Info", "No se leyó ningún UID dentro del tiempo de espera (15 segundos).\nIntente nuevamente.")
        else:
            self._uid_to_register = None
            self.uid_label.config(text="SerialManager no disponible")
            print("RegistroTab: SerialManager no disponible o no conectado.") # Debug
            messagebox.showerror("Error", "El SerialManager no está disponible o no conectado. No se puede leer del sensor.")

        # Rehabilitar el botón
        self.read_uid_button.config(state=tk.NORMAL, text="Leer UID")

    def register_card(self):
        """Registra la tarjeta con el UID y nombre ingresados."""
        print("RegistroTab: Intentando registrar tarjeta...") # Debug
        uid = self._uid_to_register
        name = self.name_entry.get().strip()
        is_temporal = self.temporal_var.get()
        expiry_date = self.expiry_date_entry.get().strip() if is_temporal else ""
        expiry_time = self.expiry_time_entry.get().strip() if is_temporal else ""

        # Validar que se haya leído un UID válido
        if not uid or uid in ["Presione 'Leer UID' para comenzar...", "Modo registro activado - Acerca la tarjeta...", "Timeout - No se leyó UID", "SerialManager no disponible"] or "Error" in uid:
            messagebox.showwarning("Advertencia", "Por favor, lea un UID válido primero usando el botón 'Leer UID'.")
            print("RegistroTab: Registro fallido - UID no válido o no leído.") # Debug
            return

        if not name:
            # Asignar "NA" si el nombre está vacío
            name = "NA"

        expiry_datetime_str = ""
        if is_temporal:
            if not expiry_date or not expiry_time:
                messagebox.showwarning("Advertencia", "Por favor, ingrese la fecha y hora de caducidad para la tarjeta temporal.")
                print("RegistroTab: Registro fallido - Datos de caducidad incompletos.") # Debug
                return
            # Validar formato de fecha y hora (básico)
            try:
                # Intentar parsear para validar
                datetime_str = f"{expiry_date} {expiry_time}"
                # Usar strptime para validar el formato
                time.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
                expiry_datetime_str = datetime_str # Usar el formato validado
                
                # Validar que la fecha de caducidad sea futura
                expiry_dt = datetime.datetime.strptime(expiry_datetime_str, '%Y-%m-%d %H:%M:%S')
                current_dt = datetime.datetime.now()
                
                if expiry_dt <= current_dt:
                    messagebox.showwarning("Advertencia", "La fecha y hora de caducidad debe ser futura.")
                    print("RegistroTab: Registro fallido - Fecha de caducidad no es futura.") # Debug
                    return
                    
            except ValueError:
                messagebox.showwarning("Advertencia", "Formato de fecha u hora incorrecto.\nUse YYYY-MM-DD para la fecha y HH:MM:SS para la hora.")
                print("RegistroTab: Registro fallido - Formato de fecha/hora incorrecto.") # Debug
                return

        print(f"RegistroTab: Datos para registrar - UID: {uid}, Nombre: {name}, Temporal: {is_temporal}, Caducidad: {expiry_datetime_str}") # Debug

        # Llamar al AccessManager para registrar la tarjeta con datos de caducidad
        if is_temporal and expiry_datetime_str:
            # Registrar tarjeta temporal con fecha de caducidad
            success = self.access_manager.register_temporal_uid(uid, name, expiry_datetime_str)
        else:
            # Registrar tarjeta permanente
            success = self.access_manager.register_new_uid(uid, name)

        if success:
            card_type = "temporal" if is_temporal else "permanente"
            expiry_info = f" (caduca: {expiry_datetime_str})" if is_temporal else ""
            messagebox.showinfo("Éxito", f"Tarjeta {card_type} con UID '{uid}' registrada exitosamente con nombre '{name}'{expiry_info}.")
            print(f"RegistroTab: Tarjeta '{uid}' registrada con éxito como {card_type}.") # Debug
            # Limpiar campos después del registro exitoso
            self.uid_label.config(text="Presione 'Leer UID' para comenzar...")
            self.name_entry.delete(0, tk.END)
            self.temporal_var.set(False)
            self.expiry_date_entry.delete(0, tk.END)
            self.expiry_time_entry.delete(0, tk.END)
            self.toggle_temporal_options() # Ocultar opciones temporales
            self._uid_to_register = None
        else:
            # El AccessManager ya mostrará un mensaje si el UID ya existe
            print(f"RegistroTab: Registro de tarjeta '{uid}' fallido (ya existe o error interno).") # Debug
