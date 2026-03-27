# ==============================================================================
# 📔 LIBRO DE CONFIGURACIÓN MAESTRA: LOGÍSTICA CASA LUPITA (v2.3)
# ==============================================================================
# Edita este archivo con los valores REALES de tu negocio. 
# Una vez terminado, indícamelo para ejecutar la sincronización automática.

# ------------------------------------------------------------------------------
# ⚙️ A. CONFIGURACIÓN DE CARGA (CONTROL)
# ------------------------------------------------------------------------------
CONFIG_CARGA = {
    "limpiar_base_datos": True,      # ¡BORRA TODO lo anterior antes de cargar!
    "cargar_catalogos_csv": True,    # Carga México.csv y Clientes.csv
    "crear_superuser_por_defecto": True, # Crea usuario 'sergio' con pass 'password123'
}

# ------------------------------------------------------------------------------
# 🚛 B. UNIDADES DE LA FLOTILLA (Valores Reales)
# ------------------------------------------------------------------------------
# Agrega o modifica las unidades físicas que operan en el negocio.
UNIDADES = [
    {
        "nUnidad": "U-01", 
        "nombre_interno": "Camioneta Gris",
        "placas": "LF633212",
        "marca": "Ford",
        "submarca": "F-350",
        "modelo": 2019,
        "tipo": "CAMIONETA_3_5",         # Opciones: CAMION, CAMIONETA_3_5, CAMIONETA_1_5, AUTO, MOTO
        "capacidad_kg": 3500.0,
        "tanque_lts": 151,
        "serie": "1FDWF3G67KEE70144",
        "motor": "SIN-NUMERO",
        "descripcion": "FORD F-350 CHASIS CABINA KTP XL 6.2L",
        "tarjeta_circulacion": "CA-C-12581313",
        "combustible": "GASOLINA",
        "num_llantas": 6,
        "poliza_seguro": "SIN-NUMERO",
        "vigencia_poliza": "2026-12-31",
        "titular_poliza": "Guadalupe Baltazar Reyes",
        "cobertura_poliza": "AMPLIA"

    },
    {
        "nUnidad": "U-02", 
        "nombre_interno": "Camioneta Roja",
        "placas": "LE56337",
        "marca": "Nissan",
        "submarca": "NP300",
        "modelo": 2009,
        "tipo": "CAMIONETA_1_5",
        "capacidad_kg": 1000.0,
        "tanque_lts": 60,
        "serie": "3N6DD25T69K006408",
        "motor": "KA24396285A",
        "descripcion": "CS NISSAN CHASIS CABINA",
        "tarjeta_circulacion": "CA-C-15304151",
        "combustible": "GASOLINA",
        "num_llantas": 4,
        "poliza_seguro": "SIN-NUMERO",
        "vigencia_poliza": "2026-12-31",
        "titular_poliza": "Guadalupe Baltazar Reyes",
        "cobertura_poliza": "AMPLIA"
    },
    {
        "nUnidad": "U-03", 
        "nombre_interno": "Camioneta VERDE",
        "placas": "LE56336",
        "marca": "Ford",
        "submarca": "F-350",
        "modelo": 1994,
        "tipo": "CAMIONETA_3_5",
        "capacidad_kg": 3500.0,
        "tanque_lts": 110,
        "serie": "3FEKF27N5RMA07442",
        "motor": "L10155",
        "descripcion": "F-350 CHASIS CABINA CUSTOM K3S 4 X 2",
        "tarjeta_circulacion": "CA-C-15304148",
        "combustible": "GASOLINA",
        "num_llantas": 6,   
        "poliza_seguro": "SIN-NUMERO",
        "vigencia_poliza": "2026-12-31",
        "titular_poliza": "Guadalupe Baltazar Reyes",
        "cobertura_poliza": "AMPLIA"
    },
    {
        "nUnidad": "U-04", 
        "nombre_interno": "CAMION Blanca",
        "placas": "LG23795",
        "marca": "SINOTRUK",
        "submarca": "HOWO",
        "modelo": 2023,
        "tipo": "CAMION",
        "capacidad_kg": 6000.0,
        "tanque_lts": 160,
        "serie": "LEZAB1CC1PF115891",
        "motor": "77324796",
        "descripcion": "EQ SINOTRUK HOWO G3W 154 HP 6T 4X2 CH",
        "tarjeta_circulacion": "CA-C-14494935",
        "combustible": "DIESEL",
        "num_llantas": 6,
        "poliza_seguro": "SIN-NUMERO",
        "vigencia_poliza": "2026-12-31",
        "titular_poliza": "Guadalupe Baltazar Reyes",
        "cobertura_poliza": "AMPLIA"

    }
]

# ------------------------------------------------------------------------------
# 👥 C. EQUIPO OPERATIVO (Usuario y Perfil)
# ------------------------------------------------------------------------------
# Define quién usa el sistema y en qué área trabaja. 
# El sistema creará los usuarios automáticamente si no existen (pass: password123).
EQUIPO = [
    {"username": "sergio", "nombre": "Sergio", "apellidos": "Camarena Sagredo", "puesto": "ADMIN"},
    {"username": "michel", "nombre": "Michel Alejandra", "apellidos": "Contreras Baltazar", "puesto": "ADMIN"},
    {"username": "yoy", "nombre": "Yadira Yoathzi", "apellidos": "Fernandez Rodriguez", "puesto": "MOSTRADOR"},
    {"username": "nancy", "nombre": "Nancy", "apellidos": "Ramos", "puesto": "MOSTRADOR"},
    {"username": "fany", "nombre": "Estefania", "apellidos": "XX", "puesto": "ALMACEN"},
    {"username": "cris", "nombre": "Cristian", "apellidos": "Rodriguez", "puesto": "CHOFER"},
    {"username": "alfredo", "nombre": "Alfredo", "apellidos": "Rosas", "puesto": "CHOFER"},
]

# ------------------------------------------------------------------------------
# 💰 D. PARÁMETROS FINANCIEROS Y OPERATIVOS
# ------------------------------------------------------------------------------
CONFIG_NEGOCIO = {
    "sueldo_semanal_chofer": 3200.00,
    "sueldo_semanal_chalan": 1800.00,
    "tiempo_descarga_promedio_min": 40,
    "limite_mm_llanta_seguridad": 3.0,
    "vida_util_estimada_llanta_km": 120000,
}

