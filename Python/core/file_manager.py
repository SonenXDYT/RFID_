# File: core/file_manager.py
import json
import os
from datetime import datetime

class FileManager:
    def __init__(self, registered_uids_file="data/registered_uids.json", access_log_file="data/access_log.txt"):
        self.registered_uids_file = registered_uids_file
        self.access_log_file = access_log_file
        
        # Crear directorio data si no existe
        os.makedirs(os.path.dirname(self.registered_uids_file), exist_ok=True)
        os.makedirs(os.path.dirname(self.access_log_file), exist_ok=True)

    def load_registered_uids(self):
        """Carga los UIDs registrados desde el archivo."""
        try:
            if os.path.exists(self.registered_uids_file):
                with open(self.registered_uids_file, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    print(f"FileManager: {len(data)} UIDs cargados desde {self.registered_uids_file}")
                    return data
            else:
                print(f"FileManager: Archivo {self.registered_uids_file} no existe, creando nuevo diccionario.")
                return {}
        except Exception as e:
            print(f"FileManager: Error al cargar UIDs - {str(e)}")
            return {}

    def save_registered_uids(self, registered_uids):
        """Guarda los UIDs registrados en el archivo."""
        try:
            with open(self.registered_uids_file, 'w', encoding='utf-8') as file:
                json.dump(registered_uids, file, indent=4, ensure_ascii=False)
            print(f"FileManager: {len(registered_uids)} UIDs guardados en {self.registered_uids_file}")
            return True
        except Exception as e:
            print(f"FileManager: Error al guardar UIDs - {str(e)}")
            return False

    def log_access_attempt(self, uid, name, access_granted, message=""):
        """Registra un intento de acceso."""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status = "PERMITIDO" if access_granted else "DENEGADO"
            log_entry = f"[{timestamp}] UID: {uid} | Nombre: {name} | Estado: {status}"
            
            if message:
                log_entry += f" | Mensaje: {message}"
            
            log_entry += "\n"
            
            with open(self.access_log_file, 'a', encoding='utf-8') as file:
                file.write(log_entry)
                
            print(f"FileManager: Acceso registrado - {status} para {name} ({uid})")
            
        except Exception as e:
            print(f"FileManager: Error al registrar acceso - {str(e)}")

    def load_history(self, lines=100):
        """Carga el historial de accesos."""
        try:
            if not os.path.exists(self.access_log_file):
                print("FileManager: Archivo de historial no existe.")
                return []
                
            with open(self.access_log_file, 'r', encoding='utf-8') as file:
                all_lines = file.readlines()
                # Devolver las últimas 'lines' líneas, o todas si hay menos
                result = all_lines[-lines:] if len(all_lines) > lines else all_lines
                print(f"FileManager: {len(result)} líneas de historial cargadas.")
                return result
                
        except Exception as e:
            print(f"FileManager: Error al cargar historial - {str(e)}")
            return []

    def search_history(self, search_term, max_results=50):
        """Busca en el historial de accesos."""
        try:
            if not os.path.exists(self.access_log_file):
                return []
            
            search_term = search_term.lower()
            results = []
            
            with open(self.access_log_file, 'r', encoding='utf-8') as file:
                for line in file:
                    if search_term in line.lower():
                        results.append(line.strip())
                        if len(results) >= max_results:
                            break
            
            print(f"FileManager: {len(results)} resultados encontrados para '{search_term}'")
            return results
            
        except Exception as e:
            print(f"FileManager: Error al buscar en historial - {str(e)}")
            return []
