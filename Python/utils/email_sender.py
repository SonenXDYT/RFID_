import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import sys
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import ssl

class EmailSender:
    def __init__(self, root):
        self.root = root
        
    def configurar_smtp(self):
        """Abre ventana para configurar SMTP."""
        config_window = tk.Toplevel(self.root)
        config_window.title("Configuración SMTP")
        config_window.geometry("450x400")
        config_window.transient(self.root)
        config_window.grab_set()

        main_frame = ttk.Frame(config_window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Configuración del Servidor SMTP", font=("Arial", 12, "bold")).pack(pady=(0, 20))

        # Cargar configuración existente
        config_existente = self.cargar_config_smtp()

        # Servidor SMTP
        ttk.Label(main_frame, text="Servidor SMTP:").pack(anchor=tk.W)
        smtp_server_var = tk.StringVar(value=config_existente.get('smtp_server', 'smtp.gmail.com') if config_existente else 'smtp.gmail.com')
        ttk.Entry(main_frame, textvariable=smtp_server_var, width=40).pack(fill=tk.X, pady=(0, 10))

        # Puerto
        ttk.Label(main_frame, text="Puerto:").pack(anchor=tk.W)
        puerto_var = tk.StringVar(value=str(config_existente.get('puerto', '587')) if config_existente else '587')
        ttk.Entry(main_frame, textvariable=puerto_var, width=40).pack(fill=tk.X, pady=(0, 10))

        # Email remitente
        ttk.Label(main_frame, text="Email remitente:").pack(anchor=tk.W)
        email_var = tk.StringVar(value=config_existente.get('email', '') if config_existente else '')
        ttk.Entry(main_frame, textvariable=email_var, width=40).pack(fill=tk.X, pady=(0, 10))

        # Contraseña
        ttk.Label(main_frame, text="Contraseña de aplicación:").pack(anchor=tk.W)
        password_var = tk.StringVar(value=config_existente.get('password', '') if config_existente else '')
        ttk.Entry(main_frame, textvariable=password_var, width=40, show="*").pack(fill=tk.X, pady=(0, 10))

        # Nota informativa
        info_text = """IMPORTANTE - Para Gmail:
1. Activa la verificación en 2 pasos
2. Ve a: Cuenta Google > Seguridad > Verificación en 2 pasos
3. Genera una "Contraseña de aplicación"
4. Usa esa contraseña aquí, NO tu contraseña normal"""
        
        info_label = ttk.Label(main_frame, text=info_text, wraplength=400, font=("Arial", 8))
        info_label.pack(pady=10)

        def guardar_config():
            config = {
                'smtp_server': smtp_server_var.get(),
                'puerto': puerto_var.get(),
                'email': email_var.get(),
                'password': password_var.get()
            }
            
            try:
                config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
                os.makedirs(config_dir, exist_ok=True)
                config_file = os.path.join(config_dir, 'email_settings.json')  # CAMBIADO AQUÍ
                
                with open(config_file, 'w') as f:
                    json.dump(config, f, indent=4)
                messagebox.showinfo("Éxito", f"Configuración guardada en:\n{config_file}")
                config_window.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar configuración: {str(e)}")

        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)

        ttk.Button(button_frame, text="Guardar", command=guardar_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=config_window.destroy).pack(side=tk.LEFT, padx=5)

    def cargar_config_smtp(self):
        """Carga la configuración SMTP desde archivo."""
        try:
            # Intentar cargar desde email_settings.json primero
            config_file = os.path.join(os.path.dirname(__file__), '..', 'config', 'email_settings.json')
            
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    
                # Si es el formato complejo de email_config.py, extraer la parte SMTP
                if 'smtp_settings' in data and 'sender_info' in data:
                    smtp_settings = data['smtp_settings']
                    sender_info = data['sender_info']
                    return {
                        'smtp_server': smtp_settings.get('server', ''),
                        'puerto': str(smtp_settings.get('port', 587)),
                        'email': sender_info.get('email', ''),
                        'password': sender_info.get('password', '')
                    }
                # Si es el formato simple, devolverlo directamente
                else:
                    return data
            
            # Si no existe email_settings.json, intentar con smtp_config.json (compatibilidad)
            config_file_old = os.path.join(os.path.dirname(__file__), '..', 'config', 'smtp_config.json')
            if os.path.exists(config_file_old):
                with open(config_file_old, 'r') as f:
                    return json.load(f)
            
            return None
            
        except Exception as e:
            print(f"Error al cargar configuración SMTP: {e}")
            return None

    def verificar_configuracion_completa(self):
        """Verifica si la configuración SMTP está completa."""
        config = self.cargar_config_smtp()
        if not config:
            return False, "No hay configuración guardada"
        
        campos_requeridos = ['smtp_server', 'puerto', 'email', 'password']
        campos_faltantes = []
        
        for campo in campos_requeridos:
            if not config.get(campo):
                campos_faltantes.append(campo)
        
        if campos_faltantes:
            return False, f"Campos faltantes: {', '.join(campos_faltantes)}"
        
        return True, "Configuración completa"

    def mostrar_debug_config(self):
        """Función de debug para mostrar la configuración actual."""
        config_file = os.path.join(os.path.dirname(__file__), '..', 'config', 'email_settings.json')
        
        debug_info = f"""=== DEBUG CONFIGURACIÓN ===

Archivo buscado: {config_file}
Archivo existe: {os.path.exists(config_file)}

"""
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    content = f.read()
                debug_info += f"Contenido del archivo:\n{content}\n\n"
                
                # Intentar parsear JSON
                data = json.loads(content)
                debug_info += f"JSON parseado correctamente:\n{data}\n\n"
                
                # Mostrar configuración procesada
                config = self.cargar_config_smtp()
                debug_info += f"Configuración procesada:\n{config}"
                
            except Exception as e:
                debug_info += f"Error al leer archivo: {e}"
        else:
            debug_info += "El archivo no existe."
        
        # Mostrar en ventana
        debug_window = tk.Toplevel(self.root)
        debug_window.title("Debug Configuración")
        debug_window.geometry("600x400")
        
        text_widget = tk.Text(debug_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert("1.0", debug_info)
        text_widget.config(state=tk.DISABLED)

    def abrir_ventana_envio(self, datos_csv, titulo="Reporte"):
        """Abre la ventana para enviar correos con configuración predeterminada."""
        
        # Verificar si hay configuración guardada
        config_completa, mensaje_config = self.verificar_configuracion_completa()
        
        if not config_completa:
            # Mostrar ventana con opciones
            respuesta_window = tk.Toplevel(self.root)
            respuesta_window.title("Configuración Requerida")
            respuesta_window.geometry("400x200")
            respuesta_window.transient(self.root)
            respuesta_window.grab_set()
            
            frame = ttk.Frame(respuesta_window, padding=20)
            frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(frame, text="⚠️ Configuración de Email", font=("Arial", 12, "bold")).pack(pady=(0, 10))
            ttk.Label(frame, text=mensaje_config, wraplength=350).pack(pady=(0, 20))
            
            button_frame = ttk.Frame(frame)
            button_frame.pack()
            
            def configurar():
                respuesta_window.destroy()
                self.configurar_smtp()
            
            def debug():
                respuesta_window.destroy()
                self.mostrar_debug_config()
            
            def cancelar():
                respuesta_window.destroy()
            
            ttk.Button(button_frame, text="⚙️ Configurar", command=configurar).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="🔍 Debug", command=debug).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="❌ Cancelar", command=cancelar).pack(side=tk.LEFT, padx=5)
            
            return

        # Cargar configuración predeterminada
        config_smtp = self.cargar_config_smtp()
        
        # Crear ventana de envío simplificada
        envio_window = tk.Toplevel(self.root)
        envio_window.title("Enviar Correo")
        envio_window.geometry("600x700")
        envio_window.transient(self.root)
        envio_window.grab_set()

        main_frame = ttk.Frame(envio_window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Título con información del remitente configurado
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(title_frame, text="Enviar Correo", font=("Arial", 16, "bold")).pack(side=tk.LEFT)
        ttk.Button(title_frame, text="⚙️ Configurar", command=self.configurar_smtp).pack(side=tk.RIGHT)

        # Mostrar configuración actual
        config_info_frame = ttk.LabelFrame(main_frame, text="Configuración Actual", padding=10)
        config_info_frame.pack(fill=tk.X, pady=(0, 15))

        info_text = f"""✅ Remitente configurado: {config_smtp['email']}
🌐 Servidor: {config_smtp['smtp_server']}:{config_smtp['puerto']}
🔒 Seguridad: TLS habilitado"""

        ttk.Label(config_info_frame, text=info_text, font=("Arial", 9)).pack(anchor=tk.W)

        # Destinatarios
        dest_frame = ttk.LabelFrame(main_frame, text="Destinatarios", padding=10)
        dest_frame.pack(fill=tk.X, pady=(0, 15))

        # Lista de correos predefinidos
        correos_predefinidos = [
            "admin@empresa.com",
            "supervisor@empresa.com", 
            "gerencia@empresa.com",
            "Alexandermenasabalete@gmail.com"
        ]

        correo_vars = {}
        for correo in correos_predefinidos:
            var = tk.BooleanVar()
            correo_vars[correo] = var
            ttk.Checkbutton(dest_frame, text=correo, variable=var).pack(anchor=tk.W, pady=2)

        # Correo personalizado
        ttk.Label(dest_frame, text="Destinatarios adicionales (separados por comas):").pack(anchor=tk.W, pady=(10, 5))
        correos_adicionales_var = tk.StringVar()
        ttk.Entry(dest_frame, textvariable=correos_adicionales_var, width=60).pack(fill=tk.X)

        # Asunto
        asunto_frame = ttk.LabelFrame(main_frame, text="Asunto", padding=10)
        asunto_frame.pack(fill=tk.X, pady=(0, 15))

        asunto_var = tk.StringVar(value=f"{titulo} - {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        ttk.Entry(asunto_frame, textvariable=asunto_var, width=60).pack(fill=tk.X)

        # Mensaje
        mensaje_frame = ttk.LabelFrame(main_frame, text="Mensaje", padding=10)
        mensaje_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        mensaje_text = tk.Text(mensaje_frame, height=10, wrap=tk.WORD)
        mensaje_text.pack(fill=tk.BOTH, expand=True)

        # Mensaje predeterminado
        mensaje_predeterminado = f"""Estimado/a,

Adjunto encontrará el {titulo.lower()} del sistema de control de acceso.

📊 Detalles del reporte:
• Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
• Tipo: {titulo}
• Formato: CSV (compatible con Excel)

El archivo contiene la información detallada solicitada.

Saludos cordiales,
Sistema de Control de Acceso"""

        mensaje_text.insert("1.0", mensaje_predeterminado)

        # Vista previa del archivo
        preview_frame = ttk.LabelFrame(main_frame, text="Vista Previa del Archivo", padding=10)
        preview_frame.pack(fill=tk.X, pady=(0, 15))

        # Información del archivo
        lineas_csv = len(datos_csv.split('\n'))
        tamaño_kb = len(datos_csv.encode('utf-8')) / 1024

        archivo_info = f"""📎 Archivo: reporte_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv
📏 Tamaño: {tamaño_kb:.1f} KB
📋 Líneas: {lineas_csv}"""

        ttk.Label(preview_frame, text=archivo_info, font=("Arial", 9)).pack(anchor=tk.W)

        # Mostrar primeras líneas del CSV
        primeras_lineas = '\n'.join(datos_csv.split('\n')[:3])
        ttk.Label(preview_frame, text="Primeras líneas:", font=("Arial", 8, "bold")).pack(anchor=tk.W, pady=(10, 0))
        
        csv_preview = tk.Text(preview_frame, height=3, wrap=tk.NONE, font=("Courier", 8))
        csv_preview.pack(fill=tk.X, pady=(5, 0))
        csv_preview.insert("1.0", primeras_lineas)
        csv_preview.config(state=tk.DISABLED)

        # Función para enviar correo
        def enviar_correo():
            # Obtener destinatarios
            destinatarios_seleccionados = [correo for correo, var in correo_vars.items() if var.get()]
            
            # Procesar correos adicionales
            correos_adicionales = correos_adicionales_var.get().strip()
            if correos_adicionales:
                emails_adicionales = [email.strip() for email in correos_adicionales.split(',') if email.strip()]
                destinatarios_seleccionados.extend(emails_adicionales)
            
            if not destinatarios_seleccionados:
                messagebox.showwarning("Sin Destinatarios", "Debe seleccionar al menos un destinatario.")
                return

            asunto = asunto_var.get().strip()
            if not asunto:
                messagebox.showerror("Asunto Vacío", "El asunto no puede estar vacío.")
                return

            mensaje = mensaje_text.get("1.0", tk.END).strip()

            # Confirmar envío
            confirmacion = messagebox.askyesno("Confirmar Envío", 
                f"""¿Confirma el envío del correo?

📧 Desde: {config_smtp['email']}
👥 Para: {len(destinatarios_seleccionados)} destinatario(s)
📋 Asunto: {asunto}
📎 Adjunto: {tamaño_kb:.1f} KB

¿Proceder con el envío?""")
            
            if not confirmacion:
                return

            # Ventana de progreso
            progress_window = tk.Toplevel(envio_window)
            progress_window.title("Enviando...")
            progress_window.geometry("350x120")
            progress_window.transient(envio_window)
            progress_window.grab_set()
            
            progress_frame = ttk.Frame(progress_window, padding=15)
            progress_frame.pack(fill=tk.BOTH, expand=True)
            
            progress_label = ttk.Label(progress_frame, text="Iniciando envío...", font=("Arial", 10))
            progress_label.pack(pady=5)
            
            progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
            progress_bar.pack(fill=tk.X, pady=5)
            progress_bar.start()
            
            status_label = ttk.Label(progress_frame, text="🔒 Conectando con TLS...", font=("Arial", 8))
            status_label.pack()
            
            progress_window.update()
            
            try:
                self.enviar_correo_smtp_simple(
                    destinatarios_seleccionados, 
                    asunto, 
                    mensaje, 
                    datos_csv, 
                    config_smtp, 
                    progress_label, 
                    status_label,
                    progress_window
                )
                
                progress_bar.stop()
                progress_window.destroy()
                
                messagebox.showinfo("Envío Exitoso", 
                    f"✅ Correo enviado correctamente\n\n📧 Desde: {config_smtp['email']}\n👥 A: {len(destinatarios_seleccionados)} destinatario(s)")
                envio_window.destroy()
                
            except Exception as e:
                progress_bar.stop()
                progress_window.destroy()
                messagebox.showerror("Error de Envío", f"❌ No se pudo enviar el correo:\n\n{str(e)}")

        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=15)

        ttk.Button(button_frame, text="📧 Enviar Correo", command=enviar_correo).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="❌ Cancelar", command=envio_window.destroy).pack(side=tk.LEFT)

    def enviar_correo_smtp_simple(self, destinatarios, asunto, mensaje, datos_csv, config_smtp, progress_label, status_label, progress_window):
        """Envía el correo usando la configuración predeterminada con starttls()."""
        try:
            # Crear contexto SSL seguro
            context = ssl.create_default_context()
            
            # Crear mensaje
            progress_label.config(text="Preparando mensaje...")
            status_label.config(text="📝 Configurando correo")
            progress_window.update()
            
            msg = MIMEMultipart()
            msg['From'] = f"Sistema de Control de Acceso <{config_smtp['email']}>"
            msg['To'] = ', '.join(destinatarios)
            msg['Subject'] = asunto

            # Adjuntar mensaje
            msg.attach(MIMEText(mensaje, 'plain', 'utf-8'))

            # Adjuntar CSV
            progress_label.config(text="Adjuntando archivo...")
            status_label.config(text="📎 Procesando CSV")
            progress_window.update()
            
            csv_attachment = MIMEBase('application', 'octet-stream')
            csv_attachment.set_payload(datos_csv.encode('utf-8'))
            encoders.encode_base64(csv_attachment)
            
            filename = f"reporte_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            csv_attachment.add_header('Content-Disposition', f'attachment; filename="{filename}"')
            msg.attach(csv_attachment)

            # Conectar al servidor
            progress_label.config(text="Conectando al servidor...")
            status_label.config(text=f"🌐 {config_smtp['smtp_server']}:{config_smtp['puerto']}")
            progress_window.update()
            
            server = smtplib.SMTP(config_smtp['smtp_server'], int(config_smtp['puerto']))
            
            # Habilitar TLS
            progress_label.config(text="Habilitando TLS...")
            status_label.config(text="🔒 Iniciando conexión segura")
            progress_window.update()
            
            server.starttls(context=context)
            
            # Autenticar
            progress_label.config(text="Autenticando...")
            status_label.config(text=f"🔑 {config_smtp['email']}")
            progress_window.update()
            
            server.login(config_smtp['email'], config_smtp['password'])

            # Enviar correo
            progress_label.config(text="Enviando correo...")
            status_label.config(text=f"📤 A {len(destinatarios)} destinatario(s)")
            progress_window.update()
            
            server.sendmail(config_smtp['email'], destinatarios, msg.as_string())
            server.quit()

            progress_label.config(text="¡Enviado exitosamente!")
            status_label.config(text="✅ Proceso completado")
            progress_window.update()

            print(f"Correo enviado desde {config_smtp['email']} a: {', '.join(destinatarios)}")

        except smtplib.SMTPAuthenticationError:
            raise Exception("Error de autenticación SMTP.\nVerifica tu email y contraseña de aplicación.")
        except smtplib.SMTPRecipientsRefused:
            raise Exception("Uno o más destinatarios fueron rechazados por el servidor.")
        except smtplib.SMTPServerDisconnected:
            raise Exception("Se perdió la conexión con el servidor SMTP.")
        except Exception as e:
            raise Exception(f"Error en envío SMTP: {str(e)}")
