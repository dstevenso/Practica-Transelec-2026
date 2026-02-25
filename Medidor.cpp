#include <Arduino.h>
#include <driver/i2s.h>
#include <WiFi.h>
#include <HTTPClient.h>

// --- Configuración de Muestreo ---
#define SAMPLE_RATE     30000   // 30kHz (Suficiente para armónicos de 12kHz)
#define CAPTURE_TIME_S  4       // 4 segundos de ráfaga
#define NUM_SAMPLES     (SAMPLE_RATE * CAPTURE_TIME_S)
#define ADC_CHANNEL     ADC1_CHANNEL_0 // GPIO 1 en ESP32-S3

// --- Credenciales ---
const char* ssid = "ssid";
const char* password = "contrasena";
const char* webhookUrl = "urlwebhook";

uint16_t* sampleBuffer;

void setupI2S() {
    i2s_config_t i2s_config = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX | I2S_MODE_ADC_BUILT_IN),
        .sample_rate = SAMPLE_RATE,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
        .channel_format = I2S_CHANNEL_FMT_ONLY_RIGHT,
        .communication_format = I2S_COMM_FORMAT_STAND_I2S,
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count = 4,
        .dma_buf_len = 1024,
        .use_apll = false
    };
    
    i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL);
    i2s_set_adc_mode(ADC_UNIT_1, ADC_CHANNEL);
    i2s_adc_enable(I2S_NUM_0);
}

void setup() {
    Serial.begin(115200);
    sampleBuffer = (uint16_t*)malloc(NUM_SAMPLES * sizeof(uint16_t));
    
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) delay(500);
    
    setupI2S();
    Serial.println("Sistema Listo. Esperando disparo...");
}

void loop() {
    int valorActual = analogRead(1); 
    if (valorActual > 2500 || valorActual < 1500) { //Revisa si se escapa del umbral para luego capturar los siguentes 4 segundos de vibración
        Serial.println("¡Umbral detectado! Capturando 4 seg...");
        
        size_t bytesRead;
        // La función i2s_read llena el buffer a la velocidad exacta del reloj hardware
        i2s_read(I2S_NUM_0, (void*)sampleBuffer, NUM_SAMPLES * sizeof(uint16_t), &bytesRead, portMAX_DELAY);
        
        enviarDatos();
        delay(5000); // Pausa para no saturar
    }
}

void enviarDatos() {
    if (WiFi.status() == WL_CONNECTED) {
        HTTPClient http;
        http.begin(webhookUrl);
        http.addHeader("Content-Type", "application/octet-stream");

        Serial.println("Subiendo ráfaga binaria...");
        int httpCode = http.POST((uint8_t*)sampleBuffer, NUM_SAMPLES * sizeof(uint16_t));
        
        if (httpCode > 0) Serial.printf("Enviado con éxito: %d\n", httpCode);
        else Serial.printf("Error en envío: %s\n", http.errorString(httpCode).c_str());
        
        http.end();
    }
}
