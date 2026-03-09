import os
import re

templates = [
    "unidad_form.html",
    "viaje_form.html",
    "usuario_form.html",
    "combustible_form.html",
    "inventario_llanta_form.html",
    "evaluacion_entrega_form.html",
    "zona_entrega_form.html",
    "orden_servicio_form.html"
]

base_dir = "/home/sscamarenas/Proyectos/Logistica Casa Lupita/App_Stealth/templates/dashboard"

for t in templates:
    filepath = os.path.join(base_dir, t)
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        continue
        
    with open(filepath, "r") as f:
        content = f.read()

    # If attributes are hanging outside, fix them first
    content = content.replace('> hx-post="{{ request.path }}" hx-target="#formContainer" hx-select="#formContainer" hx-swap="outerHTML" hx-encoding="multipart/form-data"', ' hx-post="{{ request.path }}" hx-target="#formContainer" hx-select="#formContainer" hx-swap="outerHTML" hx-encoding="multipart/form-data">')
    content = content.replace('> hx-post="{{ request.path }}" hx-target="#formContainer" hx-select="#formContainer" hx-swap="outerHTML"', ' hx-post="{{ request.path }}" hx-target="#formContainer" hx-select="#formContainer" hx-swap="outerHTML">')
    
    with open(filepath, "w") as f:
        f.write(content)
    print(f"Fixed attributes in {t}")
