import csv
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from dashboard.models import Cliente

class Command(BaseCommand):
    help = 'Carga el catálogo de Clientes desde el archivo CSV'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar la recarga de datos borrando los preexistentes.',
        )

    def handle(self, *args, **options):
        force = options['force']
        
        if Cliente.objects.exists() and not force:
            self.stdout.write(self.style.WARNING('Los clientes ya existen. Use --force para recargar.'))
            return

        file_path = os.path.join(settings.BASE_DIR, 'dashboard', 'data', 'Clientes.csv')
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'No se encontró el archivo: {file_path}'))
            return
            
        if force or not Cliente.objects.exists():
            self.stdout.write(self.style.WARNING('Borrando clientes existentes...'))
            Cliente.objects.all().delete()

        self.stdout.write(self.style.WARNING('Cargando clientes desde CSV...'))

        objetos_a_crear = []
        contador = 0

        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            # SOLUCIÓN 1: Limpiamos los espacios en blanco al inicio y final de cada encabezado
            # Esto convierte "Clave " en "Clave" y "Teléfono " en "Teléfono"
            if reader.fieldnames:
                reader.fieldnames = [field.strip() for field in reader.fieldnames if field]

            for row in reader:
                # SOLUCIÓN 2: Usamos 'Teléfono' con acento porque así viene en el CSV
                id_sae = row.get('Clave', '').strip()
                razon_social = row.get('Nombre', '').strip()
                telefono_principal = row.get('Teléfono', '').strip() 
                
                # Validación opcional: saltar filas que no tengan un ID válido
                if not id_sae:
                    continue
                    
                objetos_a_crear.append(Cliente(
                    id_sae=id_sae,
                    razon_social=razon_social,
                    telefono_principal=telefono_principal,
                ))
                
                contador += 1
                
                # Insertar en lotes de 2000 para no saturar la memoria
                if len(objetos_a_crear) >= 2000:
                    Cliente.objects.bulk_create(objetos_a_crear)
                    objetos_a_crear = []
                    self.stdout.write(f'Procesados {contador} registros...')
        
        if objetos_a_crear:
            Cliente.objects.bulk_create(objetos_a_crear)
            
        self.stdout.write(self.style.SUCCESS(f'Éxito: Se cargaron {contador} Clientes en la base de datos.'))