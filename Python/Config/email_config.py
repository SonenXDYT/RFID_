import json
import os
from typing import Dict, List, Optional

class EmailConfig:
    """Clase para manejar la configuración de correo electrónico."""
    
    def __init__(self):
        self.config_dir = os.path.join(os.path.dirname(__file__))
        self.config_file = os.path.join(self.config_dir, 'email_settings.json')
        self.default_config = self._get_default_config()
        self.config = self.load_config()
    
    def _get_default_config(self) -> Dict:
        """Retorna la configuración por defecto."""
        return {
            "smtp_settings": {
                "server": "smtp.gmail.com",
                "port": 587,
                "use_tls": True,
                "use_ssl": False,
                "timeout": 30
            },
            "sender_info": {
                "email": "Alexandermenasabalete@gmail.com",
                "password": "wqnniujxdetegcoc",
                "display_name": "Sistema de Control de Acceso"
            },
            "default_recipients": [
                {
                    "name": "Reportes",
                    "email": "alexandermenasabalete@gmail.com",
                    "enabled": False
                }
            ],
            "email_templates": {
                "subject_template": "{report_type} - {date}",
                "body_template": """Estimado/a,

Adjunto encontrará el {report_type} solicitado con {record_count} registros.

Fecha de generación: {generation_date}
Período del reporte: {report_period}

Resumen:
- Total de registros: {record_count}
- Accesos permitidos: {allowed_count}
- Accesos denegados: {denied_count}

Saludos cordiales,
{sender_name}""",
                "attachment_name_template": "reporte_accesos_{date}.csv"
            },
            "report_settings": {
                "auto_send_daily": False,
                "auto_send_weekly": False,
                "auto_send_monthly": False,
                "daily_time": "08:00",
                "weekly_day": "monday",
                "monthly_day": 1,
                "include_summary": True,
                "max_records_per_email": 10000
            },
            "security": {
                "encrypt_password": True,
                "require_confirmation": True,
                "log_email_activity": True
            }
        }
    
    def load_config(self) -> Dict:
        """Carga la configuración desde el archivo."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # Fusionar con configuración por defecto para agregar nuevas claves
                return self._merge_config(self.default_config, config)
            else:
                return self.default_config.copy()
        except Exception as e:
            print(f"Error al cargar configuración de email: {e}")
            return self.default_config.copy()
    
    def save_config(self) -> bool:
        """Guarda la configuración actual al archivo."""
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error al guardar configuración de email: {e}")
            return False
    
    def _merge_config(self, default: Dict, loaded: Dict) -> Dict:
        """Fusiona la configuración cargada con la por defecto."""
        result = default.copy()
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
        return result
    
    # Métodos para acceder a configuraciones específicas
    def get_smtp_settings(self) -> Dict:
        """Retorna la configuración SMTP."""
        return self.config.get("smtp_settings", {})
    
    def get_sender_info(self) -> Dict:
        """Retorna la información del remitente."""
        return self.config.get("sender_info", {})
    
    def get_default_recipients(self) -> List[Dict]:
        """Retorna la lista de destinatarios por defecto."""
        return self.config.get("default_recipients", [])
    
    def get_enabled_recipients(self) -> List[Dict]:
        """Retorna solo los destinatarios habilitados."""
        return [r for r in self.get_default_recipients() if r.get("enabled", False)]
    
    def get_email_templates(self) -> Dict:
        """Retorna las plantillas de email."""
        return self.config.get("email_templates", {})
    
    def get_report_settings(self) -> Dict:
        """Retorna la configuración de reportes."""
        return self.config.get("report_settings", {})
    
    def get_security_settings(self) -> Dict:
        """Retorna la configuración de seguridad."""
        return self.config.get("security", {})
    
    # Métodos para actualizar configuraciones
    def update_smtp_settings(self, server: str, port: int, email: str, password: str, use_tls: bool = True):
        """Actualiza la configuración SMTP."""
        self.config["smtp_settings"].update({
            "server": server,
            "port": port,
            "use_tls": use_tls
        })
        self.config["sender_info"].update({
            "email": email,
            "password": password
        })
        return self.save_config()
    
    def add_recipient(self, name: str, email: str, enabled: bool = True):
        """Agrega un nuevo destinatario."""
        new_recipient = {
            "name": name,
            "email": email,
            "enabled": enabled
        }
        self.config["default_recipients"].append(new_recipient)
        return self.save_config()
    
    def remove_recipient(self, email: str):
        """Elimina un destinatario por email."""
        self.config["default_recipients"] = [
            r for r in self.config["default_recipients"] 
            if r.get("email") != email
        ]
        return self.save_config()
    
    def update_recipient_status(self, email: str, enabled: bool):
        """Actualiza el estado de un destinatario."""
        for recipient in self.config["default_recipients"]:
            if recipient.get("email") == email:
                recipient["enabled"] = enabled
                break
        return self.save_config()
    
    def update_email_template(self, template_type: str, template_content: str):
        """Actualiza una plantilla de email."""
        if template_type in self.config["email_templates"]:
            self.config["email_templates"][template_type] = template_content
            return self.save_config()
        return False
    
    def reset_to_defaults(self):
        """Resetea la configuración a los valores por defecto."""
        self.config = self.default_config.copy()
        return self.save_config()
    
    def validate_config(self) -> List[str]:
        """Valida la configuración actual y retorna una lista de errores."""
        errors = []
        
        # Validar configuración SMTP
        smtp = self.get_smtp_settings()
        if not smtp.get("server"):
            errors.append("Servidor SMTP no configurado")
        if not isinstance(smtp.get("port"), int) or smtp.get("port") <= 0:
            errors.append("Puerto SMTP inválido")
        
        # Validar información del remitente
        sender = self.get_sender_info()
        if not sender.get("email"):
            errors.append("Email del remitente no configurado")
        if not sender.get("password"):
            errors.append("Contraseña del remitente no configurada")
        
        # Validar que hay al menos un destinatario habilitado
        if not self.get_enabled_recipients():
            errors.append("No hay destinatarios habilitados")
        
        return errors
    
    def is_configured(self) -> bool:
        """Verifica si la configuración básica está completa."""
        return len(self.validate_config()) == 0

# Instancia global de configuración
email_config = EmailConfig()
