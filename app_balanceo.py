import numpy as np

def calcular_balanceo_1_plano(v0_amp, v0_fase, mp_masa, mp_fase, v1_amp, v1_fase):
    # Función interna para convertir Amplitud y Fase (grados) a Complejo
    to_comp = lambda a, f: a * np.exp(1j * np.radians(f))

    # 1. Vectores de vibración y masa de prueba
    V0 = to_comp(v0_amp, v0_fase)   # Vibración inicial
    Mp = to_comp(mp_masa, mp_fase) # Masa de prueba
    V1 = to_comp(v1_amp, v1_fase)   # Vibración con masa de prueba

    # 2. Calcular Coeficiente de Influencia (alpha)
    # alpha = (V_con_masa - V_inicial) / Masa_prueba
    alpha = (V1 - V0) / Mp

    # 3. Calcular Masa de Corrección (Mc)
    # Mc = -V_inicial / alpha
    Mc = -V0 / alpha

    return {
        "mc_masa": np.abs(Mc),
        "mc_fase_deg": np.degrees(np.angle(Mc)) % 360,
        "alpha_mag": np.abs(alpha)
    }

# --- EJEMPLO DE USO ---
# Vibración inicial: 5.0 mm/s a 30°
# Masa de prueba: 10 gramos a 0° 
# Vibración tras colocar masa: 8.0 mm/s a 120°
resultado = calcular_balanceo_1_plano(5.0, 30, 10, 0, 8.0, 120)

print(f"Masa de corrección: {resultado['mc_masa']:.2f} unidades")
print(f"Ángulo de colocación: {resultado['mc_fase_deg']:.2f}°")

