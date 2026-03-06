import csv
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from dashboard.models import CodigoPostalCat

class Command(BaseCommand):
    help = 'Carga el catálogo de Códigos Postales desde el archivo CSV'

    def handle(self, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, 'dashboard', 'data', 'México.csv')
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'El archivo {file_path} no existe.'))
            return

        self.stdout.write(self.style.WARNING('Borrando datos anteriores...'))
        CodigoPostalCat.objects.all().delete()
        
        self.stdout.write(self.style.WARNING('Cargando nuevos datos desde CSV...'))
        
        objetos_a_crear = []
        contador = 0
        
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # ODS/CSV headers: d_codigo, d_asenta, d_tipo_asenta, D_mnpio, d_estado, d_ciudad
                codigo = row.get('d_codigo', '').strip()
                asentamiento = row.get('d_asenta', '').strip()
                tipo_asentamiento = row.get('d_tipo_asenta', '').strip()
                municipio = row.get('D_mnpio', '').strip()
                estado = row.get('d_estado', '').strip()
                ciudad = row.get('d_ciudad', '').strip()
                
                if not codigo or not asentamiento:
                    continue
                    
                objetos_a_crear.append(CodigoPostalCat(
                    codigo=codigo,
                    asentamiento=asentamiento,
                    tipo_asentamiento=tipo_asentamiento,
                    municipio=municipio,
                    estado=estado,
                    ciudad=ciudad
                ))
                
                contador += 1
                
                # Insertar en lotes de 2000 para no saturar la memoria
                if len(objetos_a_crear) >= 2000:
                    CodigoPostalCat.objects.bulk_create(objetos_a_crear)
                    objetos_a_crear = []
                    self.stdout.write(f'Procesados {contador} registros...')
        
        if objetos_a_crear:
            CodigoPostalCat.objects.bulk_create(objetos_a_crear)
            
        self.stdout.write(self.style.SUCCESS(f'Éxito: Se cargaron {contador} Códigos Postales en la base de datos.'))
