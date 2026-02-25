import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft, fftfreq
from scipy.ndimage import maximum_filter1d # <--- Para crear la envolvente

class AutoMaskMonitor:
    def __init__(self, fs=40000):
        self.fs = fs

    def _add_impact(self, t, t_start, freq, decay, amp):
        active = t >= t_start
        wave = amp * np.sin(2 * np.pi * freq * (t - t_start)) * np.exp(-decay * (t - t_start))
        return active * wave

    def generate_signal(self, condition="healthy"):
        N = int(self.fs * 0.1)
        t = np.linspace(0, 0.1, N)
        sig = np.zeros_like(t)

        # Ruido base (realista)
        sig += np.random.normal(0, 0.015, N)

        # --- COMPONENTES SANOS ---
        sig += self._add_impact(t, 0.005, freq=400, decay=200, amp=1.5)    # Fricción
        sig += self._add_impact(t, 0.025, freq=2500, decay=1000, amp=0.8)  # Varillaje
        sig += self._add_impact(t, 0.030, freq=3500, decay=2500, amp=1.2)  # Contactos
        sig += self._add_impact(t, 0.035, freq=8000, decay=3000, amp=0.4)  # Resortes

        if condition == "faulty":
            # FALLA 12 kHz (Pequeña pero aguda)
            sig += self._add_impact(t, 0.020, freq=12000, decay=4500, amp=0.6)

        # FFT
        yf = fft(sig)
        xf = fftfreq(N, 1 / self.fs)[:N//2]
        magnitude = 2.0/N * np.abs(yf[:N//2])

        return t, sig, xf, magnitude

    def generate_smart_mask(self, healthy_spectrum, tolerance_factor=2.0, floor=0.00):
        """
        Crea una máscara que SIGUE EL CONTORNO de la señal sana.
        1. Dilatación: Ensancha los picos (para tolerar ligeros cambios de freq).
        2. Multiplicación: Sube la amplitud por un factor de seguridad.
        3. Piso: Establece un mínimo para no detectar ruido térmico.
        """
        # 1. Dilatación (Ensanchar picos horizontalmente)
        # size=20 significa que buscamos el máximo en un vecindario de 20 bins
        envelope = maximum_filter1d(healthy_spectrum, size=20)

        # 2. Factor de Seguridad (Margen vertical)
        envelope = envelope * tolerance_factor

        # 3. Piso de Ruido (Safety Floor)
        envelope = np.maximum(envelope, floor)

        return envelope

# --- EJECUCIÓN ---
monitor = AutoMaskMonitor()

# 1. Obtenemos la FIRMA DE REFERENCIA (Golden Sample)
_, _, freq, mag_sana = monitor.generate_signal("healthy")

# 2. Generamos la MÁSCARA AUTOMÁTICA
# Le decimos: "Toma la señal sana, ensánchala y multiplícala x3"
mask = monitor.generate_smart_mask(mag_sana, tolerance_factor=2.0, floor=0.00)

# 3. Generamos la SEÑAL DE PRUEBA (Falla)
_, _, _, mag_falla = monitor.generate_signal("faulty")


# --- VISUALIZACIÓN ---
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# GRÁFICO 1: Calibración (Sano vs Máscara)
axes[0].set_title("1. Calibración: La máscara sigue el contorno", color='green', fontweight='bold')
axes[0].semilogy(freq, mag_sana, 'g', lw=1, alpha=0.8, label='Espectro Sano (Referencia)')
# La máscara ahora es una sombra roja que sigue la forma verde
axes[0].semilogy(freq, mask, 'r--', lw=2, label='Máscara Dinámica (x3)')
axes[0].fill_between(freq, mask, 10, color='red', alpha=0.05) # Zona Prohibida

axes[0].set_ylim(0.0001, 5)
axes[0].set_xlim(0, 20000)
axes[0].grid(True, which="both", alpha=0.2)
axes[0].legend()
axes[0].set_ylabel("Magnitud (dB)")
axes[0].text(2500, 0.5, "La máscara se\nadapta a los picos", ha='center', fontsize=9, bbox=dict(facecolor='white', alpha=0.8))

# GRÁFICO 2: Detección (Falla vs Máscara)
axes[1].set_title("2. Detección: El pico de 12kHz rompe el techo", color='red', fontweight='bold')
axes[1].semilogy(freq, mag_falla, 'k', lw=1, alpha=0.9, label='Espectro Falla')
axes[1].semilogy(freq, mask, 'r--', lw=2, label='Límite')

# Resaltar Violación
violation = mag_falla > mask
axes[1].scatter(freq[violation], mag_falla[violation], color='red', zorder=5, s=30)

# Flecha señalando la detección
axes[1].annotate('Posible falla', xy=(12000, 0.0020), xytext=(14000, 0.1),
             arrowprops=dict(facecolor='red', shrink=0.05), color='red', fontweight='bold')

axes[1].annotate('Ruido normal\n(Aceptado)', xy=(8000, 0.005), xytext=(8000, 0.009),
             arrowprops=dict(facecolor='green', shrink=0.05, alpha=0.5), color='green', ha='center')

axes[1].set_ylim(0.0001, 5)
axes[1].set_xlim(0, 20000)
axes[1].grid(True, which="both", alpha=0.2)
axes[1].legend()

plt.tight_layout()
plt.show()
