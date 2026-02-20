from django.core.management.base import BaseCommand
from dashboard.utils import sincronizar_contingencia_automatica

class Command(BaseCommand):
    help = 'Sincroniza el estado de la contingencia ambiental consultando la API de WAQI'

    def handle(self, *args, **kwargs):
        self.stdout.write("Iniciando sincronización con API de calidad del aire...")
        try:
            exito = sincronizar_contingencia_automatica()
            if exito:
                self.stdout.write(self.style.SUCCESS('Sincronización exitosa. El estado ha sido actualizado.'))
            else:
                self.stdout.write(self.style.WARNING('La sincronización finalizó sin actualizar (estado sin cambios o error de API).'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error grave durante la sincronización: {e}'))
