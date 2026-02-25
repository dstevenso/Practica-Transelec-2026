import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
import pywt

class BreakerSim:
    def __init__(self, fs=20000):
        self.fs = fs

    def get_impact(self, t, t0, freq, decay, amp):
        """Genera un impacto amortiguado"""
        active = t >= t0
        # Onda sinusoidal amortiguada
        wave = amp * np.sin(2 * np.pi * freq * (t - t0)) * np.exp(-decay * (t - t0))
        return active * wave

    def simulate(self, duration=0.1, mode="healthy"):
        t = np.linspace(0, duration, int(self.fs * duration))
        sig = np.zeros_like(t)

        # Tiempos base (en segundos)
        t1, t2, t3 = 0.015, 0.040, 0.070

        # --- LÓGICA DE FALLAS ---
        if mode == "healthy":
            # Operación nominal
            sig += self.get_impact(t, t1, 6000, 600, 1.0) # Latch
            sig += self.get_impact(t, t2, 3000, 300, 2.5) # Contactos
            sig += self.get_impact(t, t3, 800, 100, 4.0)  # Amortiguador

        elif mode == "friction":
            # FALLA 1: FRICCIÓN (Retraso + Pérdida de Energía)
            delay = 0.006 # 6ms de retraso general
            sig += self.get_impact(t, t1 + delay, 6000, 700, 0.8) # Más débil
            sig += self.get_impact(t, t2 + delay, 3000, 400, 2.0)
            sig += self.get_impact(t, t3 + delay, 800, 150, 3.0)

        elif mode == "loose_bolt":
            # FALLA 2: PERNO SUELTO (Ruido "Rattle" intermedio)
            # Los tiempos son normales, pero aparece vibración donde no debe
            sig += self.get_impact(t, t1, 6000, 600, 1.0)
            sig += self.get_impact(t, t2, 3000, 300, 2.5)

            # --> EL DEFECTO: Un traqueteo metálico entre contactos y amortiguador
            sig += self.get_impact(t, 0.055, 9000, 200, 0.8)

            sig += self.get_impact(t, t3, 800, 100, 4.0)

        # Añadir ruido base de sensor (realismo)
        noise = np.random.normal(0, 0.02, len(t))
        return t, sig + noise

# --- ANÁLISIS ---
sim = BreakerSim()

# 1. Generar Señales
t, sig_healthy = sim.simulate(mode="healthy")
_, sig_friction = sim.simulate(mode="friction")
_, sig_loose   = sim.simulate(mode="loose_bolt")

# 2. Calcular Envolventes (Hilbert) para comparar energía
env_healthy = np.abs(signal.hilbert(sig_healthy))
env_friction = np.abs(signal.hilbert(sig_friction))
env_loose = np.abs(signal.hilbert(sig_loose))

# 3. Calcular el "Residuo" (La señal de error)
# Esto es lo que un sistema automático monitorea: |Sano - Falla|
res_friction = np.abs(env_healthy - env_friction)
res_loose = np.abs(env_healthy - env_loose)

# --- GRAFICAR ---
fig, axes = plt.subplots(3, 2, figsize=(14, 10), sharex=True)

# COLUMNA 1: Comparación con Falla de Fricción
axes[0,0].set_title("CASO 1: Mecanismo Atascado (Fricción)")
axes[0,0].plot(t*1000, sig_healthy, 'g', alpha=0.5, label="Sano")
axes[0,0].plot(t*1000, sig_friction, 'r', alpha=0.7, label="Fricción")
axes[0,0].legend(loc="upper right")
axes[0,0].set_ylabel("Vibración (g)")

axes[1,0].set_title("Análisis de Envolvente (Energía)")
axes[1,0].plot(t*1000, env_healthy, 'g--')
axes[1,0].plot(t*1000, env_friction, 'r')
axes[1,0].fill_between(t*1000, env_healthy, env_friction, color='red', alpha=0.2)

axes[2,0].set_title("Residuo (Error Detectado)")
axes[2,0].plot(t*1000, res_friction, 'k')
axes[2,0].fill_between(t*1000, 0, res_friction, color='black', alpha=0.3)
axes[2,0].set_xlabel("Tiempo (ms)")
axes[2,0].text(10, 2, "ALERTA: Desplazamiento temporal", color='red', fontweight='bold')


# COLUMNA 2: Comparación con Falla de Perno Suelto
axes[0,1].set_title("CASO 2: Holgura Mecánica (Perno Suelto)")
axes[0,1].plot(t*1000, sig_healthy, 'g', alpha=0.5, label="Sano")
axes[0,1].plot(t*1000, sig_loose, 'purple', alpha=0.7, label="Perno Suelto")
axes[0,1].legend(loc="upper right")

axes[1,1].set_title("Análisis de Envolvente")
axes[1,1].plot(t*1000, env_healthy, 'g--')
axes[1,1].plot(t*1000, env_loose, 'purple')
axes[1,1].fill_between(t*1000, env_healthy, env_loose, color='purple', alpha=0.2)

axes[2,1].set_title("Residuo (Error Detectado)")
axes[2,1].plot(t*1000, res_loose, 'k')
axes[2,1].fill_between(t*1000, 0, res_loose, color='black', alpha=0.3)
axes[2,1].set_xlabel("Tiempo (ms)")
axes[2,1].text(45, 1.5, "ALERTA: Evento inesperado", color='purple', fontweight='bold')

plt.tight_layout()
plt.show()
