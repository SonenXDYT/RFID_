# File: core/serial_manager.py
import serial
import serial.tools.list_ports
import threading
import time
import queue

class SerialManager:
    def __init__(self, access_manager, access_logger, port=None, baudrate=9600):
        self.access_manager = access_manager
        self.access_logger = access_logger
        self.port = port
        self.baudrate = baudrate
        self.serial_connection = None
        self.is_connected = False
        
        # Cola para comunicación entre hilos
        self.data_queue = queue.Queue()
        
        # Control de lectura continua
        self.reading_active = False
        self.reading_thread = None
        self.pause_event = threading.Event()
        self.pause_event.set()  # Inicialmente no pausado
        
        print("SerialManager: Inicializando...")
        
        # Intentar autodetectar y conectar
        if not self.port:
            self.port = self.autodetect_arduino_port()
        
        if self.port:
            self.connect()
        else:
            print("SerialManager: No se pudo detectar un puerto Arduino.")

    def autodetect_arduino_port(self):
        """Intenta detectar automáticamente el puerto del Arduino."""
        print("SerialManager: Intentando autodetectar puerto serial de Arduino...")
        
        try:
            print("SerialManager: Buscando puertos seriales...")
            ports = serial.tools.list_ports.comports()
            available_ports = [port.device for port in ports]
            print(f"SerialManager: Puertos encontrados: {available_ports}")
            
            # Buscar puertos que contengan palabras clave relacionadas con Arduino
            arduino_keywords = ['arduino', 'ch340', 'ch341', 'ftdi', 'usb', 'serial']
            
            for port in ports:
                port_desc = port.description.lower()
                port_hwid = port.hwid.lower()
                
                print(f"SerialManager: Evaluando puerto {port.device} (Desc: {port.description}, HWID: {port.hwid})")
                
                # Verificar si contiene palabras clave de Arduino
                if any(keyword in port_desc or keyword in port_hwid for keyword in arduino_keywords):
                    print(f"SerialManager: Coincidencia encontrada para {port.device}")
                    print(f"SerialManager: Puerto serial de Arduino detectado: {port.device} ({port.description})")
                    return port.device
            
            # Si no se encuentra por palabras clave, intentar con el primer puerto disponible
            if available_ports:
                print(f"SerialManager: No se encontró Arduino específico, usando primer puerto disponible: {available_ports[0]}")
                return available_ports[0]
            else:
                print("SerialManager: No se encontraron puertos seriales.")
                return None
                
        except Exception as e:
            print(f"SerialManager: Error al autodetectar puerto: {str(e)}")
            return None

    def connect(self):
        """Establece la conexión serial."""
        try:
            # CORRECCIÓN: Mostrar puerto y baudrate en lugar de objetos
            print(f"SerialManager: Intentando conectar a {self.port}@{self.baudrate}...")
            
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()
            
            self.serial_connection = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)  # Esperar a que Arduino se reinicie
            
            self.is_connected = True
            print("SerialManager: Conexión serial establecida.")
            
        except Exception as e:
            self.is_connected = False
            print(f"SerialManager: Ocurrió un error inesperado al conectar: {str(e)}")

    def disconnect(self):
        """Cierra la conexión serial."""
        try:
            print("SerialManager: Cerrando conexión serial...")
            self.reading_active = False
            
            if self.reading_thread and self.reading_thread.is_alive():
                self.pause_event.set()  # Asegurar que el hilo no esté pausado
                self.reading_thread.join(timeout=2)
            
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()
            
            self.is_connected = False
            print("SerialManager: Conexión serial cerrada.")
            
        except Exception as e:
            print(f"SerialManager: Error al cerrar conexión: {str(e)}")

    def send_command(self, command):
        """Envía un comando al Arduino."""
        if self.is_connected and self.serial_connection:
            try:
                command_bytes = (command + '\n').encode('utf-8')
                self.serial_connection.write(command_bytes)
                self.serial_connection.flush()
                print(f"SerialManager: Comando enviado: '{command}'")
                return True
            except Exception as e:
                print(f"SerialManager: Error al enviar comando: {str(e)}")
                return False
        else:
            print("SerialManager: No hay conexión serial para enviar comando.")
            return False

    def read_continuous_data(self):
        """Lee datos continuamente del puerto serial."""
        if not self.is_connected or not self.serial_connection:
            return None
        
        try:
            if self.serial_connection.in_waiting > 0:
                data = self.serial_connection.readline().decode('utf-8').strip()
                if data:
                    return data
        except Exception as e:
            print(f"SerialManager: Error al leer datos continuos: {str(e)}")
        
        return None

    def read_single_uid_for_registration(self, timeout=15):
        """
        Lee un UID específicamente para registro, pausando la lectura continua.
        
        Args:
            timeout (int): Tiempo máximo de espera en segundos
        
        Returns:
            str: UID detectado o None si no se detecta
        """
        print("SerialManager: Iniciando lectura síncrona para registro...")
        
        # Pausar la lectura continua
        self.pause_event.clear()
        print("SerialManager: Lectura continua pausada.")
        
        try:
            # Enviar comando para activar modo registro
            if not self.send_command("MODO_REGISTRO"):
                return None
            
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                if self.is_connected and self.serial_connection and self.serial_connection.in_waiting > 0:
                    try:
                        data = self.serial_connection.readline().decode('utf-8').strip()
                        print(f"SerialManager: Dato leído durante registro: '{data}'")
                        
                        if data.startswith("UID_DETECTADO:"):
                            uid = data.split(":", 1)[1]
                            print(f"SerialManager: UID detectado para registro: '{uid}'")
                            return uid
                            
                    except Exception as e:
                        print(f"SerialManager: Error al leer durante registro: {str(e)}")
                
                time.sleep(0.1)  # Pequeña pausa para no saturar la CPU
            
            print("SerialManager: Timeout en lectura síncrona para registro.")
            return None
            
        finally:
            # Reanudar la lectura continua
            self.pause_event.set()
            print("SerialManager: Lectura continua reanudada.")
            print("SerialManager: Lectura síncrona para registro finalizada.")

    def __del__(self):
        """Destructor para asegurar que la conexión se cierre."""
        try:
            self.disconnect()
            print("SerialManager: Destructor llamado.")
        except:
            pass
