# File: core/access_logger.py
from datetime import datetime

class AccessLogger:
    def __init__(self, file_manager):
        self.file_manager = file_manager
        print("AccessLogger: Inicializado.")

    def log_access(self, uid, name, access_granted, message=""):
        """
        Registra un intento de acceso.
        
        Args:
            uid (str): UID de la tarjeta
            name (str): Nombre del usuario
            access_granted (bool): Si se concedió el acceso
            message (str): Mensaje adicional opcional
        """
        try:
            self.file_manager.log_access_attempt(uid, name, access_granted, message)
        except Exception as e:
            print(f"AccessLogger: Error al registrar acceso - {str(e)}")

    def log_attempt(self, uid, name, status_message):
        """
        Registra un intento de acceso basado en el mensaje de estado.
        
        Args:
            uid (str): UID de la tarjeta
            name (str): Nombre del usuario
            status_message (str): Mensaje de estado ("Permitido", "Denegado", etc.)
        """
        try:
            # Determinar si el acceso fue concedido basado en el mensaje
            access_granted = "permitido" in status_message.lower()
            
            # Registrar el intento
            self.file_manager.log_access_attempt(uid, name, access_granted, status_message)
            
            print(f"AccessLogger: Intento registrado - UID: {uid}, Nombre: {name}, Estado: {status_message}")
            
        except Exception as e:
            print(f"AccessLogger: Error al registrar intento - {str(e)}")

    def log_card_expired(self, uid, name, expiry_datetime):
        """
        Registra un intento de acceso con tarjeta caducada.
        
        Args:
            uid (str): UID de la tarjeta
            name (str): Nombre del usuario
            expiry_datetime (str): Fecha y hora de caducidad
        """
        try:
            message = f"Tarjeta caducada el {expiry_datetime}"
            self.file_manager.log_access_attempt(uid, name, False, message)
            print(f"AccessLogger: Tarjeta caducada registrada - UID: {uid}, Nombre: {name}")
        except Exception as e:
            print(f"AccessLogger: Error al registrar tarjeta caducada - {str(e)}")

    def log_registration(self, uid, name, card_type="Permanente", expiry_datetime=None):
        """
        Registra el registro de una nueva tarjeta.
        
        Args:
            uid (str): UID de la tarjeta
            name (str): Nombre del usuario
            card_type (str): Tipo de tarjeta ("Permanente" o "Temporal")
            expiry_datetime (str): Fecha de caducidad si es temporal
        """
        try:
            if card_type == "Temporal" and expiry_datetime:
                message = f"Tarjeta {card_type.lower()} registrada - Caduca: {expiry_datetime}"
            else:
                message = f"Tarjeta {card_type.lower()} registrada"
            
            # Usar un timestamp personalizado para registros
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] REGISTRO - UID: {uid} | Nombre: {name} | {message}\n"
            
            # Escribir directamente al archivo de log
            with open(self.file_manager.access_log_file, 'a', encoding='utf-8') as file:
                file.write(log_entry)
            
            print(f"AccessLogger: Registro de tarjeta documentado - UID: {uid}, Tipo: {card_type}")
            
        except Exception as e:
            print(f"AccessLogger: Error al registrar nueva tarjeta - {str(e)}")

    def log_card_deletion(self, uid, name):
        """
        Registra la eliminación de una tarjeta.
        
        Args:
            uid (str): UID de la tarjeta eliminada
            name (str): Nombre del usuario
        """
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] ELIMINACIÓN - UID: {uid} | Nombre: {name} | Tarjeta eliminada del sistema\n"
            
            with open(self.file_manager.access_log_file, 'a', encoding='utf-8') as file:
                file.write(log_entry)
            
            print(f"AccessLogger: Eliminación de tarjeta documentada - UID: {uid}")
            
        except Exception as e:
            print(f"AccessLogger: Error al registrar eliminación - {str(e)}")
