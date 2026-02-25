import numpy as np
import matplotlib.pyplot as plt
import pywt

# Configuración
fs = 40000  # Frecuencia de muestreo alta (40kHz) para capturar bien los agudos
duration = 0.1
t = np.linspace(0, duration, int(fs * duration))
sig = np.zeros_like(t)

def add_impact(t, t0, freq):
    """Genera un impacto corto"""
    # Usamos una ventana muy corta para que sea un 'golpe'
    decay = freq / 4  # El decaimiento es proporcional a la frecuencia para que suenen 'secos'
    active = t >= t0
    wave = np.sin(2 * np.pi * freq * (t - t0)) * np.exp(-decay * (t - t0))
    # Normalizamos amplitud para que visualmente tengan la misma 'fuerza' pico
    return active * wave

# --- GENERAMOS 3 IMPACTOS ---
# 1. BAJA (500 Hz) en t=0.02s
sig += add_impact(t, 0.02, 500)

# 2. MEDIA (4000 Hz) en t=0.05s
sig += add_impact(t, 0.05, 4000)

# 3. ALTA (12000 Hz) en t=0.08s
sig += add_impact(t, 0.08, 12000)

# Ruido de fondo suave
sig += np.random.normal(0, 0.05, len(t))

# --- ANÁLISIS WAVELET ---
# Definimos escalas logarítmicas para cubrir desde 100Hz hasta 15000Hz
# Es importante elegir bien las escalas para ver todo el rango
scales = np.geomspace(1, 100, num=150)

# Usamos Wavelet Compleja (cmor)
coefs, freqs = pywt.cwt(sig, scales, 'cmor1.5-1.0', sampling_period=1/fs)
power = np.abs(coefs)

# --- GRAFICAR ---
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

# 1. Señal en el Tiempo
ax1.set_title("Señal en el Tiempo: 3 Impactos de distinta frecuencia")
ax1.plot(t*1000, sig, 'k', linewidth=1)
ax1.text(20, 1.2, "500 Hz\n(Grave)", color='blue', ha='center')
ax1.text(50, 1.2, "4000 Hz\n(Medio)", color='green', ha='center')
ax1.text(80, 1.2, "12000 Hz\n(Agudo)", color='red', ha='center')
ax1.set_ylabel("Amplitud")
ax1.grid(True, alpha=0.3)

# 2. Escalograma Wavelet
ax2.set_title("Escalograma Wavelet: ¿Cómo se ven las distintas frecuencias?")
# Usamos pcolormesh para tener ejes reales de Frecuencia vs Tiempo
# Usamos escala Log en Y porque las frecuencias varían mucho
im = ax2.pcolormesh(t*1000, freqs, power, cmap='jet', shading='gouraud')
ax2.set_yscale('log')
ax2.set_ylabel("Frecuencia (Hz) [Escala Log]")
ax2.set_xlabel("Tiempo (ms)")

# Marcar las zonas
ax2.axhline(500, color='white', linestyle='--', alpha=0.5)
ax2.axhline(4000, color='white', linestyle='--', alpha=0.5)
ax2.axhline(12000, color='white', linestyle='--', alpha=0.5)

# Barra de color
plt.colorbar(im, ax=ax2, label="Energía")

plt.tight_layout()
plt.show()
