# File: core/access_manager.py
import tkinter as tk
from tkinter import messagebox
import datetime

class AccessManager:
    def __init__(self, file_manager):
        self.file_manager = file_manager
        self.registered_uids = {}
        self.load_registered_uids()

    def load_registered_uids(self):
        """Carga los UIDs registrados desde el archivo."""
        try:
            self.registered_uids = self.file_manager.load_registered_uids()
            print(f"AccessManager: {len(self.registered_uids)} UIDs cargados desde archivo.")
        except Exception as e:
            print(f"AccessManager: Error al cargar UIDs - {str(e)}")
            self.registered_uids = {}

    def get_registered_name(self, uid):
        """
        Obtiene el nombre registrado para un UID.
        
        Args:
            uid (str): UID de la tarjeta
        
        Returns:
            str: Nombre del usuario o "No registrado" si no existe
        """
        if uid not in self.registered_uids:
            return "No registrado"
        
        card_data = self.registered_uids[uid]
        
        # Manejar formato antiguo (string) y nuevo formato (dict)
        if isinstance(card_data, str):
            return card_data
        elif isinstance(card_data, dict):
            return card_data.get("name", "Usuario")
        else:
            return "Error en datos"

    def register_temporal_uid(self, uid, name, expiry_datetime):
        """
        Registra una tarjeta temporal con fecha de caducidad.
        
        Args:
            uid (str): UID de la tarjeta
            name (str): Nombre del usuario
            expiry_datetime (str): Fecha y hora de caducidad en formato 'YYYY-MM-DD HH:MM:SS'
        
        Returns:
            bool: True si el registro fue exitoso, False en caso contrario
        """
        # Verificar si el UID ya existe
        if uid in self.registered_uids:
            print(f"AccessManager: UID {uid} ya está registrado.")
            messagebox.showerror("Error", f"El UID {uid} ya está registrado en el sistema.")
            return False

        try:
            # Crear entrada para la tarjeta temporal
            card_data = {
                "name": name,
                "temporal": True,
                "expiry_datetime": expiry_datetime
            }

            # Guardar en el diccionario de UIDs registrados
            self.registered_uids[uid] = card_data

            # Guardar en el archivo
            self.file_manager.save_registered_uids(self.registered_uids)

            print(f"AccessManager: Tarjeta temporal registrada - UID: {uid}, Nombre: {name}, Caducidad: {expiry_datetime}")
            return True

        except Exception as e:
            print(f"AccessManager: Error al registrar tarjeta temporal - {str(e)}")
            messagebox.showerror("Error", f"Error al registrar la tarjeta: {str(e)}")
            return False

    def check_access(self, uid):
        """
        Verifica si un UID tiene acceso, considerando la caducidad para tarjetas temporales.
        
        Args:
            uid (str): UID a verificar
        
        Returns:
            tuple: (bool, str) - (tiene_acceso, mensaje)
        """
        print(f"AccessManager: Verificando acceso para UID: {uid}") # Debug
        
        if uid not in self.registered_uids:
            print(f"AccessManager: UID {uid} no registrado. Acceso denegado.") # Debug
            return False, "UID no registrado"

        card_data = self.registered_uids[uid]
        
        # Manejar formato antiguo (string) y nuevo formato (dict)
        if isinstance(card_data, str):
            # Formato antiguo: solo nombre. Considerar como permanente.
            print(f"AccessManager: UID {uid} encontrado (formato antiguo). Acceso permitido.") # Debug
            return True, card_data
        
        elif isinstance(card_data, dict):
            # Formato nuevo: diccionario con información completa
            name = card_data.get("name", "Usuario")
            
            # Verificar si es una tarjeta temporal
            if card_data.get("temporal", False):
                print(f"AccessManager: UID {uid} es temporal.") # Debug
                try:
                    expiry_str = card_data.get("expiry_datetime")
                    if not expiry_str:
                         print(f"AccessManager: UID {uid} temporal sin fecha de caducidad. Acceso denegado.") # Debug
                         return False, "Tarjeta temporal sin fecha de caducidad"

                    expiry = datetime.datetime.strptime(expiry_str, '%Y-%m-%d %H:%M:%S')
                    now = datetime.datetime.now()
                    
                    if now > expiry:
                        print(f"AccessManager: UID {uid} caducado ({expiry_str}). Acceso denegado.") # Debug
                        return False, f"Tarjeta temporal caducada el {expiry_str}"
                    else:
                        print(f"AccessManager: UID {uid} temporal vlido. Acceso permitido.") # Debug
                        return True, name
                        
                except (ValueError, KeyError) as e:
                    print(f"AccessManager: Error al verificar caducidad de {uid} - {str(e)}. Acceso denegado.") # Debug
                    return False, f"Error al verificar caducidad: {str(e)}"
            else:
                # Tarjeta permanente (formato nuevo)
                print(f"AccessManager: UID {uid} es permanente (formato nuevo). Acceso permitido.") # Debug
                return True, name
        else:
            # Formato de datos inesperado
            print(f"AccessManager: UID {uid} con formato de datos invlido. Acceso denegado.") # Debug
            return False, "Formato de datos inválido"

    def register_new_uid(self, uid, name):
        """
        Registra una tarjeta permanente (sin caducidad).
        
        Args:
            uid (str): UID de la tarjeta
            name (str): Nombre del usuario
        
        Returns:
            bool: True si el registro fue exitoso, False en caso contrario
        """
        if uid in self.registered_uids:
            print(f"AccessManager: UID {uid} ya está registrado.")
            messagebox.showerror("Error", f"El UID {uid} ya está registrado en el sistema.")
            return False

        try:
            # Crear entrada para la tarjeta permanente
            card_data = {
                "name": name,
                "temporal": False
            }

            # Guardar en el diccionario de UIDs registrados
            self.registered_uids[uid] = card_data

            # Guardar en el archivo
            self.file_manager.save_registered_uids(self.registered_uids)

            print(f"AccessManager: Tarjeta permanente registrada - UID: {uid}, Nombre: {name}")
            return True

        except Exception as e:
            print(f"AccessManager: Error al registrar tarjeta permanente - {str(e)}")
            messagebox.showerror("Error", f"Error al registrar la tarjeta: {str(e)}")
            return False

    def remove_uid(self, uid):
        """
        Elimina un UID del sistema.
        
        Args:
            uid (str): UID a eliminar
        
        Returns:
            bool: True si se eliminó exitosamente, False en caso contrario
        """
        if uid not in self.registered_uids:
            print(f"AccessManager: UID {uid} no está registrado.")
            messagebox.showwarning("Advertencia", f"El UID {uid} no está registrado en el sistema.")
            return False

        try:
            card_data = self.registered_uids[uid]
            del self.registered_uids[uid]
            
            # Guardar cambios en el archivo
            self.file_manager.save_registered_uids(self.registered_uids)
            
            # Obtener nombre para el log
            if isinstance(card_data, str):
                name = card_data
            elif isinstance(card_data, dict):
                name = card_data.get("name", "Usuario")
            else:
                name = "Desconocido"
            
            print(f"AccessManager: UID {uid} eliminado - era de {name}")
            return True

        except Exception as e:
            print(f"AccessManager: Error al eliminar UID {uid} - {str(e)}")
            messagebox.showerror("Error", f"Error al eliminar la tarjeta: {str(e)}")
            return False

    def get_all_registered_uids(self):
        """
        Retorna todos los UIDs registrados con su información.
        
        Returns:
            dict: Diccionario con todos los UIDs registrados
        """
        return self.registered_uids.copy()

    def get_card_info(self, uid):
        """
        Obtiene información completa de una tarjeta.
        
        Args:
            uid (str): UID de la tarjeta
        
        Returns:
            dict: Información de la tarjeta o None si no existe
        """
        if uid not in self.registered_uids:
            return None
        
        card_data = self.registered_uids[uid]
        
        if isinstance(card_data, str):
            # Formato antiguo: convertir a formato nuevo
            return {
                "name": card_data,
                "temporal": False,
                "expiry_datetime": None
            }
        elif isinstance(card_data, dict):
            return card_data.copy()
        else:
            return None

    def is_card_expired(self, uid):
        """
        Verifica si una tarjeta temporal ha caducado.
        
        Args:
            uid (str): UID de la tarjeta
        
        Returns:
            bool: True si ha caducado, False si no ha caducado o es permanente
        """
        card_info = self.get_card_info(uid)
        if not card_info or not card_info.get("temporal", False):
            return False
        
        try:
            expiry_str = card_info.get("expiry_datetime")
            if not expiry_str:
                return False # Considerar no caducada si no hay fecha
                
            expiry = datetime.datetime.strptime(expiry_str, '%Y-%m-%d %H:%M:%S')
            now = datetime.datetime.now()
            return now > expiry
        except (ValueError, KeyError):
            return False

    def cleanup_expired_cards(self):
        """
        Elimina automáticamente las tarjetas temporales que han caducado.
        
        Returns:
            int: Número de tarjetas eliminadas
        """
        expired_uids = []
        current_time = datetime.datetime.now()
        
        for uid, card_data in self.registered_uids.items():
            if isinstance(card_data, dict) and card_data.get("temporal", False):
                try:
                    expiry_str = card_data.get("expiry_datetime")
                    if expiry_str: # Solo verificar si hay fecha de caducidad
                        expiry = datetime.datetime.strptime(expiry_str, '%Y-%m-%d %H:%M:%S')
                        if current_time > expiry:
                            expired_uids.append(uid)
                except (ValueError, KeyError) as e:
                    print(f"AccessManager: Error al verificar caducidad de {uid} para limpieza - {str(e)}")
        
        # Eliminar tarjetas caducadas
        for uid in expired_uids:
            try:
                card_data = self.registered_uids[uid]
                card_name = card_data.get("name", "Usuario") if isinstance(card_data, dict) else str(card_data)
                del self.registered_uids[uid]
                print(f"AccessManager: Tarjeta temporal caducada eliminada - UID: {uid}, Nombre: {card_name}")
            except KeyError:
                pass
        
        if expired_uids:
            # Guardar cambios si se eliminaron tarjetas
            self.file_manager.save_registered_uids(self.registered_uids)
            print(f"AccessManager: {len(expired_uids)} tarjetas caducadas eliminadas automáticamente.")
        
        return len(expired_uids)
