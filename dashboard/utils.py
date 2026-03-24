# Utilidades Dashboard

MESES_ES = {
    1: 'ENERO', 2: 'FEBRERO', 3: 'MARZO', 4: 'ABRIL',
    5: 'MAYO', 6: 'JUNIO', 7: 'JULIO', 8: 'AGOSTO',
    9: 'SEPTIEMBRE', 10: 'OCTUBRE', 11: 'NOVIEMBRE', 12: 'DICIEMBRE'
}

def get_month_name(month_number):
    """Devuelve el nombre del mes en español o 'DESCONOCIDO'."""
    return MESES_ES.get(month_number, 'DESCONOCIDO')

from PIL import Image
from io import BytesIO
import sys
from django.core.files.uploadedfile import InMemoryUploadedFile

def compress_image(image_field, quality=70, max_width=1280):
    """
    Comprime una imagen subida mediante un ImageField.
    
    Args:
        image_field: El campo de imagen (ej. self.evidencia_antes)
        quality: Calidad de compresión (1-100, default 70)
        max_width: Ancho máximo en pixeles (default 1280)
    
    Returns:
        InMemoryUploadedFile: El archivo comprimido listo para guardarse.
        O None si no hay imagen o hubo error.
    """
    if not image_field:
        return None
    
    try:
        # Abrir imagen con Pillow
        img = Image.open(image_field)
        
        # Convertir a RGB si es necesario (para PNGs transparentes que pasan a JPEG)
        if img.mode != 'RGB':
            img = img.convert('RGB')
            
        # Redimensionar si es muy grande
        if img.width > max_width:
            ratio = max_width / float(img.width)
            height = int((float(img.height) * float(ratio)))
            img = img.resize((max_width, height), Image.Resampling.LANCZOS)
            
        # Guardar en buffer
        output = BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        output.seek(0)
        
        # Crear nuevo InMemoryUploadedFile
        new_image = InMemoryUploadedFile(
            output,
            'ImageField',
            f"{image_field.name.split('.')[0]}.jpg",
            'image/jpeg',
            sys.getsizeof(output),
            None
        )
        return new_image
        
    except Exception as e:
        print(f"Error comprimiendo imagen: {e}")
        return image_field # Retornar original si falla

import requests
from dashboard.models import ConfiguracionLogistica

from bs4 import BeautifulSoup

def obtener_paridad_del_texto(texto_comunicado):
    texto = texto_comunicado.lower()
    if "último dígito numérico sea par" in texto:
        return "PAR"
    elif "último dígito numérico sea impar" in texto or "nones" in texto:
        return "NON"
    return "NA"

import urllib3
import ssl
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class LegacySSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        # Bypass 'dh key too small' lowering the OPenSSL SECLEVEL to 0
        context.set_ciphers('DEFAULT@SECLEVEL=0')
        kwargs['ssl_context'] = context
        return super(LegacySSLAdapter, self).init_poolmanager(*args, **kwargs)

def verificar_contingencia_oficial():
    # URL oficial de reportes de ultima hora en CDMX
    url = "https://www.aire.cdmx.gob.mx/ultima-hora-reporte.php"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        session = requests.Session()
        session.mount('https://', LegacySSLAdapter())
        response = session.get(url, headers=headers, timeout=10, verify=False)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        texto_pagina = soup.get_text().upper()

        fase_oficial = "NORMAL"
        # Lógica de prioridades basada en el comunicado oficial de SEDEMA/CAMe
        if "SE MANTIENE LA FASE I" in texto_pagina or "ACTIVA FASE I" in texto_pagina or "ACTIVA LA FASE 1" in texto_pagina or "MANTIENE LA FASE 1" in texto_pagina:
            fase_oficial = "FASE_1"
        elif "FASE II" in texto_pagina or "FASE 2" in texto_pagina:
            fase_oficial = "FASE_2"
        elif "SE SUSPENDE LA CONTINGENCIA" in texto_pagina or "OPERA DE MANERA NORMAL" in texto_pagina:
            fase_oficial = "NORMAL"
            
        # Intentar extraer la paridad del comunicado oficial si aplica
        paridad = obtener_paridad_del_texto(texto_pagina)
            
        return fase_oficial, paridad
            
    except Exception as e:
        print(f"Error en validación oficial SEDEMA: {e}")
        return None, "NA"

def sincronizar_contingencia_automatica():
    config = ConfiguracionLogistica.objects.first()
    if not config:
        config = ConfiguracionLogistica.objects.create()

    # 1. Obtener AQI (Solo como referencia visual, no acciona reglas por falso positivo)
    TOKEN = "b1effacd62cc5c032068412df66692ecf12791be"
    CIUDAD = "mexico-city"
    url_aqi = f"https://api.waqi.info/feed/{CIUDAD}/?token={TOKEN}"
    aqi_actual = "Desconocido"
    try:
        response_aqi = requests.get(url_aqi, timeout=10).json()
        if response_aqi.get('status') == 'ok':
            aqi_actual = response_aqi['data']['aqi']
    except Exception as e:
        print(f"Error al consultar API AQI: {e}")

    # 2. Intentar Scraping Oficial de la CAMe/SEDEMA
    fase_oficial, paridad = verificar_contingencia_oficial()
    
    if fase_oficial:
        config.estado_contingencia = fase_oficial
        
        # Generar alerta combinada asegurando que el estado Oficial prevalece
        if fase_oficial == "FASE_1":
            config.restringir_h1 = paridad
            config.mensaje_alerta = f"OFICIAL: Fase 1 Activa (AQI: {aqi_actual}) | Restricción H1: {paridad}"
        elif fase_oficial == "FASE_2":
            config.restringir_h1 = "NA"
            config.mensaje_alerta = f"OFICIAL: Fase 2 Activa (AQI: {aqi_actual})"
        else:
            config.restringir_h1 = "NA"
            # Si es normal, pero AQI marca mala calidad, notificar informativamente
            if aqi_actual != "Desconocido" and int(aqi_actual) > 150:
                config.mensaje_alerta = f"Operación Normal Oficial | Calidad aire mala (AQI: {aqi_actual}) monitoreando comunicados."
            else:
                config.mensaje_alerta = f"Operación Normal Oficial (AQI: {aqi_actual})"

        config.save()
        return True
        
    return False

def crear_notificacion(usuario, titulo, descripcion, tipo='SISTEMA', link=None):
    """
    Utilidad para crear una notificación para un usuario.
    """
    from dashboard.models import Notificacion
    return Notificacion.objects.create(
        usuario=usuario,
        titulo=titulo,
        descripcion=descripcion,
        tipo=tipo,
        link=link
    )
