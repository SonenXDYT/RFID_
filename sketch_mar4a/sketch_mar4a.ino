#include <SPI.h>
#include <MFRC522.h>
#include <Wire.h>
#include "RTClib.h"
#include <LiquidCrystal.h>

// Definición de pines
#define RST_PIN 9
#define SS_PIN 53
#define LED_VERDE 22
#define LED_ROJO 24
#define LED_AMBAR 23
#define BUZZER 3

// Inicialización de componentes
LiquidCrystal lcd(8, 7, 13, 12, 11, 10);
MFRC522 mfrc522(SS_PIN, RST_PIN);
RTC_DS1307 rtc;

// Variables de control
bool modoRegistro = false;
unsigned long tiempoInicioRegistro = 0;
unsigned long ultimaLectura = 0;
String ultimoUID = "";

void setup() {
  Serial.begin(9600);
  while (!Serial) {
    ; // Esperar a que se establezca la conexión serial
  }
  
  SPI.begin();
  mfrc522.PCD_Init();
  Wire.begin();
  rtc.begin();
  lcd.begin(16, 2);
  
  // Configurar pines
  pinMode(LED_VERDE, OUTPUT);
  pinMode(LED_ROJO, OUTPUT);
  pinMode(LED_AMBAR, OUTPUT);
  pinMode(BUZZER, OUTPUT);

  // Asegurar que todos los LEDs estén apagados al inicio
  digitalWrite(LED_VERDE, LOW);
  digitalWrite(LED_ROJO, LOW);
  digitalWrite(LED_AMBAR, LOW);

  // Sincronizar RTC si no está en marcha
  if (!rtc.isrunning()) {
    rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
  }

  mostrarMensajeInicial();
  
  // Esperar un poco antes de enviar confirmación
  delay(2000);
  Serial.println("ARDUINO_LISTO");
  Serial.flush();
}

void loop() {
  procesarComandosSerial();
  
  // Verificar timeout del modo registro (20 segundos)
  if (modoRegistro && (millis() - tiempoInicioRegistro > 20000)) {
    Serial.println("MODO_REGISTRO_TIMEOUT");
    Serial.flush();
    salirModoRegistro();
  }
  
  // Detección de tarjetas RFID
  if (mfrc522.PICC_IsNewCardPresent() && mfrc522.PICC_ReadCardSerial()) {
    String uid = obtenerUID();
    
    // Evitar lecturas duplicadas (debounce)
    if (uid != ultimoUID || (millis() - ultimaLectura > 2000)) {
      ultimoUID = uid;
      ultimaLectura = millis();
      
      if (modoRegistro) {
        // Modo registro: enviar UID detectado a Python
        Serial.print("UID_DETECTADO:");
        Serial.println(uid);
        Serial.flush();
        
        mostrarTarjetaDetectada(uid);
        tone(BUZZER, 1000, 500);
        
        // Salir del modo registro después de detectar una tarjeta
        delay(2000);
        salirModoRegistro();
        
      } else {
        // Modo normal: enviar a Python para verificación
        verificarAccesoConPython(uid);
      }
    }
    
    mfrc522.PICC_HaltA();
    delay(100);
  }
  
  delay(50);
}

// Función para obtener el UID de la tarjeta
String obtenerUID() {
  String uid = "";
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    if (mfrc522.uid.uidByte[i] < 0x10) {
      uid += "0";
    }
    uid += String(mfrc522.uid.uidByte[i], HEX);
  }
  uid.toLowerCase();
  return uid;
}

// Envía el UID a Python y espera la respuesta
void verificarAccesoConPython(String uid) {
  DateTime ahora = rtc.now();
  String fechaHora = formatearFechaHora(ahora);
  
  // Mostrar "Verificando..." mientras Python procesa
  lcd.clear();
  lcd.print("Verificando...");
  lcd.setCursor(0, 1);
  lcd.print("UID: " + uid.substring(0, 8));
  
  // Enviar a Python para verificación (Python determinará el acceso)
  Serial.print("REGISTRO:");
  Serial.print(uid);
  Serial.print("|");
  Serial.print(fechaHora);
  Serial.print("|");
  Serial.println("PENDIENTE"); // Python determinará si es PERMITIDO o DENEGADO
  Serial.flush();
  
  // Esperar respuesta de Python (con timeout)
  unsigned long startTime = millis();
  bool respuestaRecibida = false;
  String respuesta = "";
  
  while (millis() - startTime < 3000 && !respuestaRecibida) { // Esperar máximo 3 segundos
    if (Serial.available()) {
      String comando = Serial.readStringUntil('\n');
      comando.trim();
      
      if (comando.startsWith("ACCESO:")) {
        respuesta = comando.substring(7); // Remover "ACCESO:"
        respuestaRecibida = true;
      }
    }
    delay(10);
  }
  
  // Procesar respuesta
  if (respuestaRecibida) {
    if (respuesta.startsWith("PERMITIDO")) {
      // Extraer nombre si está presente
      String nombre = "";
      int separador = respuesta.indexOf("|");
      if (separador != -1) {
        nombre = respuesta.substring(separador + 1);
      }
      accesoConcedido(nombre);
    } else {
      accesoDenegado();
    }
  } else {
    // Timeout - sin respuesta de Python
    lcd.clear();
    lcd.print("Error de sistema");
    lcd.setCursor(0, 1);
    lcd.print("Intente de nuevo");
    tone(BUZZER, 500, 1000);
  }
  
  // Mantener mensaje por 2 segundos
  delay(2000);
  digitalWrite(LED_VERDE, LOW);
  digitalWrite(LED_ROJO, LOW);
  mostrarMensajeInicial();
}

// Procesa comandos recibidos desde Python
void procesarComandosSerial() {
  if (Serial.available() > 0) {
    String comando = Serial.readStringUntil('\n');
    comando.trim();
    
    if (comando == "MODO_REGISTRO") {
      activarModoRegistro();
    }
    // No procesar comandos ACCESO: aquí ya que se manejan en verificarAccesoConPython
  }
}

// Activa el modo registro
void activarModoRegistro() {
  modoRegistro = true;
  tiempoInicioRegistro = millis();
  digitalWrite(LED_AMBAR, HIGH);
  lcd.clear();
  lcd.print("MODO REGISTRO");
  lcd.setCursor(0, 1);
  lcd.print("Acerca tarjeta");
  tone(BUZZER, 800, 300);
  
  Serial.println("MODO_REGISTRO_ACTIVADO");
  Serial.flush();
}

// Sale del modo registro
void salirModoRegistro() {
  modoRegistro = false;
  digitalWrite(LED_AMBAR, LOW);
  mostrarMensajeInicial();
  
  Serial.println("MODO_REGISTRO_DESACTIVADO");
  Serial.flush();
}

// ---- Funciones auxiliares ----
void accesoConcedido(String nombre) {
  digitalWrite(LED_VERDE, HIGH);
  lcd.clear();
  lcd.print("Acceso Permitido");
  lcd.setCursor(0, 1);
  if (nombre.length() > 0 && nombre != "NA") {
    lcd.print(nombre);
  } else {
    lcd.print("Usuario");
  }
  tone(BUZZER, 1000, 200);
}

void accesoDenegado() {
  digitalWrite(LED_ROJO, HIGH);
  lcd.clear();
  lcd.print("Acceso Denegado");
  lcd.setCursor(0, 1);
  lcd.print("Tarjeta no valida");
  tone(BUZZER, 300, 1000);
}

void mostrarTarjetaDetectada(String uid) {
  lcd.clear();
  lcd.print("Tarjeta Detectada");
  lcd.setCursor(0, 1);
  String uidCorto = uid.substring(0, min(8, (int)uid.length()));
  lcd.print("UID: " + uidCorto);
}

String formatearFechaHora(DateTime dt) {
  char buffer[20];
  sprintf(buffer, "%02d-%02d-%04d %02d:%02d:%02d", 
    dt.day(), dt.month(), dt.year(), dt.hour(), dt.minute(), dt.second());
  return String(buffer);
}

void mostrarMensajeInicial() {
  lcd.clear();
  lcd.print("Acercar Tarjeta");
  lcd.setCursor(0, 1);
  DateTime now = rtc.now();
  lcd.print(now.day()); 
  lcd.print("/");
  lcd.print(now.month()); 
  lcd.print(" ");
  if (now.hour() < 10) lcd.print("0");
  lcd.print(now.hour()); 
  lcd.print(":");
  if (now.minute() < 10) lcd.print("0");
  lcd.print(now.minute());
}
