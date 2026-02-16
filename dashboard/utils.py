# Utilidades Dashboard

MESES_ES = {
    1: 'ENERO', 2: 'FEBRERO', 3: 'MARZO', 4: 'ABRIL',
    5: 'MAYO', 6: 'JUNIO', 7: 'JULIO', 8: 'AGOSTO',
    9: 'SEPTIEMBRE', 10: 'OCTUBRE', 11: 'NOVIEMBRE', 12: 'DICIEMBRE'
}

def get_month_name(month_number):
    """Devuelve el nombre del mes en español o 'DESCONOCIDO'."""
    return MESES_ES.get(month_number, 'DESCONOCIDO')
