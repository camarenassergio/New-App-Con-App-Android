import os
import re

base_dir = "/home/sscamarenas/Proyectos/Logistica Casa Lupita/App_Stealth/templates/dashboard"

config = {
    "viaje_list.html": {
        "icon": "fas fa-truck-moving",
        "title": "Viajes",
        "url_name": "dashboard:viaje_create",
        "btn_text": "Programar Primer Viaje",
        "is_table": True
    },
    "inventario_llanta_list.html": {
        "icon": "fas fa-life-ring",
        "title": "Llantas en Inventario",
        "url_name": "dashboard:inventario_llanta_create",
        "btn_text": "Registrar Primera Llanta",
        "is_table": True
    },
    "gasto_list.html": {
        "icon": "fas fa-file-invoice-dollar",
        "title": "Gastos",
        "url_name": "dashboard:gastos_create",
        "btn_text": "Registrar Primer Gasto",
        "is_table": True
    },
    "checklist_unidad_list.html": {
        "icon": "fas fa-clipboard-check",
        "title": "Checklists Diarios",
        "url_name": "dashboard:checklist_unidad_create",
        "btn_text": "Crear Primer Checklist",
        "is_table": True
    },
    "orden_servicio_list.html": {
        "icon": "fas fa-tools",
        "title": "Órdenes de Servicio",
        "url_name": "dashboard:orden_servicio_create",
        "btn_text": "Crear Primera Orden",
        "is_table": True
    },
    "unidad_list.html": {
        "icon": "fas fa-truck",
        "title": "Unidades",
        "url_name": "dashboard:unidad_create",
        "btn_text": "Dar de Alta Unidad",
        "is_table": True
    },
    "zona_entrega_list.html": {
        "icon": "fas fa-map-marked-alt",
        "title": "Zonas de Entrega",
        "url_name": "dashboard:zona_entrega_create",
        "btn_text": "Crear Primera Zona",
        "is_table": True
    },
    "operador_list.html": {
        "icon": "fas fa-hard-hat",
        "title": "Operadores",
        "url_name": "dashboard:usuarios_list",
        "btn_text": "Crear Primer Operador",
        "is_table": False
    }
}

for filename, data in config.items():
    filepath = os.path.join(base_dir, filename)
    if not os.path.exists(filepath):
        print(f"File not found: {filename}")
        continue
        
    with open(filepath, "r") as f:
        content = f.read()

    # Skip if already applied
    if 'Aún no hay registros de' in content:
        print(f"Skipping {filename}, already applied.")
        continue

    # Identify empty block depending on if it's a table or div
    if data["is_table"]:
        # Find {% empty %} ... {% endfor %}
        pattern = re.compile(r'\{%\s*empty\s*%\}.*?\{%\s*endfor\s*%\}', re.DOTALL)
        
        replacement = f"""{{% empty %}}
<tr>
    <td colspan="100%" class="text-center" style="border: none; padding: 4rem 1rem;">
        <div class="empty-state d-flex flex-column align-items-center justify-content-center" style="opacity: 0.8; animation: fadeIn 0.6s ease-in-out;">
            <i class="{data['icon']} text-muted mb-3" style="font-size: 4.5rem; color: #cbd5e1 !important;"></i>
            <h4 class="text-muted fw-bold mb-2" style="color: #64748b !important;">Aún no hay registros de {data['title']}</h4>
            <p class="text-muted mb-4" style="max-width: 400px; font-size: 1.05rem;">Comienza creando el primer registro para visualizar y administrar la información aquí.</p>
            <a href="{{% url '{data['url_name']}' %}}" class="btn btn-primary btn-lg shadow-sm" style="border-radius: 50px; padding: 10px 30px;">
                <i class="fas fa-plus me-2"></i> {data['btn_text']}
            </a>
        </div>
    </td>
</tr>
{{% endfor %}}"""
        new_content = pattern.sub(replacement, content, count=1)
        
        if new_content != content:
            with open(filepath, "w") as f:
                f.write(new_content)
            print(f"Updated Empty State in {filename}")
        else:
            print(f"Could not find {{% empty %}} block in {filename}")
            
    else:
        # div based list (operador_list.html)
        pattern = re.compile(r'\{%\s*empty\s*%\}.*?\{%\s*endfor\s*%\}', re.DOTALL)
        
        replacement = f"""{{% empty %}}
<div style="grid-column: 1/-1; padding: 4rem 1rem;" class="text-center">
    <div class="empty-state d-flex flex-column align-items-center justify-content-center" style="opacity: 0.8; animation: fadeIn 0.6s ease-in-out;">
        <i class="{data['icon']} text-muted mb-3" style="font-size: 4.5rem; color: #cbd5e1 !important;"></i>
        <h4 class="text-muted fw-bold mb-2" style="color: #64748b !important;">Aún no hay registros de {data['title']}</h4>
        <p class="text-muted mb-4" style="max-width: 400px; font-size: 1.05rem;">Comienza creando el primer registro para visualizar y administrar la información aquí.</p>
    </div>
</div>
{{% endfor %}}"""
        new_content = pattern.sub(replacement, content, count=1)
        if new_content != content:
            with open(filepath, "w") as f:
                f.write(new_content)
            print(f"Updated div Empty State in {filename}")
