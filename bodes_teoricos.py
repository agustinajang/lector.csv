import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
import os

# ==============================================================================
# OBTENER RUTA EXACTA DE ESTE ARCHIVO
# ==============================================================================
DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))

# ==============================================================================
# 1. PARÁMETROS DEL CIRCUITO (Modificar con sus valores)
# ==============================================================================
R_SF = 0.0       # Resistencia del generador (Ohms)
R_F = 50.0       # Resistencia del filtro (Ohms)
L_F = 1e-3      # Inductancia (Henries) - Ej: 1.5mH
C_F = 15e-9       # Capacitancia (Faradios) - Ej: 10nF

# Parámetros derivados
R_tot = R_SF + R_F
w0_cuadrado = 1 / (L_F * C_F)
termino_medio = R_tot / L_F

# ==============================================================================
# 2. DEFINICIÓN DE LAS FUNCIONES DE TRANSFERENCIA
# ==============================================================================
denominador = [1, termino_medio, w0_cuadrado]

num_LP = [w0_cuadrado]
num_HP = [1, 0, 0]
num_BP = [R_F / L_F, 0]
num_Notch = [1, 0, w0_cuadrado]

filtro_LP = signal.TransferFunction(num_LP, denominador)
filtro_HP = signal.TransferFunction(num_HP, denominador)
filtro_BP = signal.TransferFunction(num_BP, denominador)
filtro_Notch = signal.TransferFunction(num_Notch, denominador)

# ==============================================================================
# 3. FUNCIÓN PARA GRAFICAR Y GUARDAR
# ==============================================================================
def graficar_bode(sistema, titulo, nombre_archivo):
    f = np.logspace(3, 6, 1000) 
    w = 2 * np.pi * f
    
    w, mag, phase = signal.bode(sistema, w)
    
    fig, (ax_mag, ax_phase) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    
    # Magnitud
    ax_mag.semilogx(f, mag, color='blue', linewidth=2)
    ax_mag.set_title(titulo, fontsize=14, fontweight='bold')
    ax_mag.set_ylabel('Magnitud [dB]', fontsize=12)
    ax_mag.grid(True, which="both", ls="-", alpha=0.5)
    ax_mag.axhline(0, color='black', linewidth=0.8, linestyle='--')
    
    # Fase
    ax_phase.semilogx(f, phase, color='red', linewidth=2)
    ax_phase.set_xlabel('Frecuencia [Hz]', fontsize=12)
    ax_phase.set_ylabel('Fase [°]', fontsize=12)
    ax_phase.grid(True, which="both", ls="-", alpha=0.5)
    
    plt.tight_layout()
    
    # RUTA ABSOLUTA PARA GUARDAR
    ruta_completa = os.path.join(DIRECTORIO_ACTUAL, nombre_archivo)
    plt.savefig(ruta_completa, dpi=300)
    print(f"Gráfico guardado con éxito en:\n{ruta_completa}\n")
    plt.close()

# ==============================================================================
# 4. GENERAR LOS GRÁFICOS
# ==============================================================================
print("Calculando funciones de transferencia y generando gráficos...")
graficar_bode(filtro_LP, 'Bode Teórico: Filtro Pasa Bajo', 'bode_teorico_LP.png')
graficar_bode(filtro_HP, 'Bode Teórico: Filtro Pasa Alto', 'bode_teorico_HP.png')
graficar_bode(filtro_BP, 'Bode Teórico: Filtro Pasa Banda', 'bode_teorico_BP.png')
graficar_bode(filtro_Notch, 'Bode Teórico: Filtro Rechaza Banda', 'bode_teorico_Notch.png')

print("¡Proceso terminado exitosamente!")