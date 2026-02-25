#include <WiFi.h>
#include <HTTPClient.h>

// Configuración de muestreo
#define F_MUESTREO 24000
#define DURACION_SEG 4
#define TOTAL_MUESTRAS (F_MUESTREO * DURACION_SEG)

// Pines ADC para el ADXL354
const int pinX = 1; 
const int pinY = 2;
const int pinZ = 3;

// Usamos memoria PSRAM si tu S3 la tiene, o bajamos la duración
// 96k muestras * 2 bytes (int16) = ~192KB por eje. Total ~576KB.
int16_t* bufferX;
volatile int indice = 0;
volatile bool grabando = false;

hw_timer_t * timer = NULL;

// Función que se ejecuta cada 1/24000 segundos
void IRAM_ATTR onTimer() {
  if (grabando && indice < TOTAL_MUESTRAS) {
    bufferX[indice] = analogRead(pinX);
    // Podrías agregar Y y Z aquí si reduces la duración
    indice++;
  } else if (indice >= TOTAL_MUESTRAS) {
    grabando = false;
  }
}

void setup() {
  Serial.begin(115200);
  
  // Reservar memoria en el Heap
  bufferX = (int16_t*)malloc(TOTAL_MUESTRAS * sizeof(int16_t));

  // Configurar Timer a 24kHz
  timer = timerBegin(0, 80, true); // 80MHz / 80 = 1MHz tick
  timerAttachInterrupt(timer, &onTimer, true);
  timerAlarmWrite(timer, 1000000 / F_MUESTREO, true); 
  timerAlarmEnable(timer);

  WiFi.begin("SSID", "PASS");
}

void loop() {
  // Disparador manual o por umbral
  if (Serial.available() > 0 || checkUmbral()) {
    Serial.println("Iniciando captura de 4 seg a 24kHz...");
    indice = 0;
    grabando = true;
    
    while(grabando); // Esperar a que llene el buffer

    enviarDatosBinarios();
  }
}

bool checkUmbral() {
  return analogRead(pinX) > 2500; // Ajustar según sensibilidad
}

void enviarDatosBinarios() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin("http://tu-servidor.com/upload");
    http.addHeader("Content-Type", "application/octet-stream"); // Binario es mejor que JSON aquí

    // Enviamos el buffer directamente como bytes para ahorrar espacio
    int response = http.POST((uint8_t*)bufferX, TOTAL_MUESTRAS * sizeof(int16_t));
    
    Serial.printf("Enviado. Respuesta: %d\n", response);
    http.end();
  }
}
