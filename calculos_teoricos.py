import math

# ==============================================================================
# 1. INGRESÁ LOS VALORES DE TUS COMPONENTES ACÁ
# ==============================================================================
R_SF = 0.0       # Resistencia del generador (Ohms) - Ej: 50
R_F = 50.0       # Resistencia del filtro (Ohms)
L_F = 1e-3      # Inductancia (Henries) - Ej: 1.5mH se escribe 1.5e-3
C_F = 15e-9       # Capacitancia (Faradios) - Ej: 10nF se escribe 10e-9

# ==============================================================================
# 2. CÁLCULOS INTRÍNSECOS (Compartidos por todos los filtros)
# ==============================================================================
R_tot = R_SF + R_F
w0 = 1 / math.sqrt(L_F * C_F)
f0 = w0 / (2 * math.pi)
Q = (1 / R_tot) * math.sqrt(L_F / C_F)
BW = f0 / Q  # Ancho de banda intrínseco (Delta f)

print("--- RESULTADOS TEÓRICOS ---")
print(f"Frecuencia de Resonancia (f0): {f0 / 1000:.2f} kHz")
print(f"Factor de Calidad (Q): {Q:.2f}")
print(f"Ancho de banda intrinseco (Pasa/Rechaza Banda): {BW / 1000:.2f} kHz")

# ==============================================================================
# 3. CÁLCULOS EXTRÍNSECOS (Específicos por filtro)
# ==============================================================================

# PASA BANDA Y RECHAZA BANDA (Frecuencias de corte a -3dB)
fc_inferior = f0 * (math.sqrt(1 + 1/(4 * Q**2)) - 1/(2*Q))
fc_superior = f0 * (math.sqrt(1 + 1/(4 * Q**2)) + 1/(2*Q))

print("\n--- PASA BANDA / RECHAZA BANDA ---")
print(f"Frecuencia de corte inferior (fc-1): {fc_inferior / 1000:.2f} kHz")
print(f"Frecuencia de corte superior (fc1): {fc_superior / 1000:.2f} kHz")

# PASA BAJO Y PASA ALTO (Frecuencias de corte a -3dB)
# La fórmula teórica exacta para fc en orden 2 es compleja, Python la calcula en un segundo:
factor = 1 - (1 / (2 * Q**2))
termino_raiz = math.sqrt(factor**2 + 1)

# Solo aplica si Q > 0.707 (que en tu caso sabemos que da 2.58)
fc_pasa_bajo = f0 * math.sqrt(factor + termino_raiz)
fc_pasa_alto = f0 / math.sqrt(factor + termino_raiz)

print("\n--- PASA BAJO ---")
print(f"Frecuencia de corte (fc): {fc_pasa_bajo / 1000:.2f} kHz")

print("\n--- PASA ALTO ---")
print(f"Frecuencia de corte (fc): {fc_pasa_alto / 1000:.2f} kHz")