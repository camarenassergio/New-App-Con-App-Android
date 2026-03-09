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
        
    # Check if already modified
    if 'id="formContainer"' in content or 'hx-post' in content:
        print(f"Ya modificado: {t}")
        continue

    # Regex to find <form method="post" ... >
    # Usually it's <form method="post"> or <form method="post" enctype="multipart/form-data"> or <form ... method="post">
    def replacer(match):
        original_form = match.group(0)
        # Check if multipart is needed
        extra_attrs = ' hx-encoding="multipart/form-data"' if 'multipart' in original_form else ''
        return f'<div id="formContainer">\n{original_form} hx-post="{{{{ request.path }}}}" hx-target="#formContainer" hx-select="#formContainer" hx-swap="outerHTML"{extra_attrs}'

    content = re.sub(r'<form\b[^>]*method=["\']post["\'][^>]*>', replacer, content, count=1, flags=re.IGNORECASE)
    
    # Check for original </form>
    if '</form>' in content:
        # replace the last </form>
        parts = content.rsplit('</form>', 1)
        content = parts[0] + '</form>\n</div>' + parts[1]
        with open(filepath, "w") as f:
            f.write(content)
        print(f"Updated {t}")
    else:
        print(f"Could not find </form> in {t}")
