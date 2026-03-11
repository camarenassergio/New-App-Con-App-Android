---
description: Design System & UI/UX Rulebook — Casa Lupita Logística
---

# 🎨 Design System Rulebook — Casa Lupita Logística
**Versión 2.0 | Aprobado: Marzo 2026**

> Este documento es la referencia obligatoria para TODA nueva vista, componente o template.
> Cualquier violación a estas reglas = Auditoría < 9/10 automáticamente.

---

## 1. 🎨 Paleta de Colores Corporativa

### CSS Variables (SIEMPRE usar variables, NUNCA hexadecimales hardcodeados)

```css
/* Colores Primarios */
--primary-blue:   #003b70  (dark: #3b82f6)
--primary-orange: #f36f21  (dark: #ff7606)

/* Fondos */
--bg-body: #f8fafc        (dark: #0f172a)
--bg-card: #ffffff        (dark: #1e293b)

/* Texto */
--text-main:  #1e293b     (dark: #f8fafc)
--text-muted: #64748b     (dark: #94a3b8)

/* Bordes */
--border-color: #e2e8f0   (dark: #334155)

/* Estados */
--success: #10b981
--warning: #f59e0b
--danger:  #ef4444
--info:    #3b82f6

/* Sombras */
--shadow-sm: 0 2px 4px rgba(0,0,0,0.05)
--shadow-md: 0 4px 12px rgba(0,0,0,0.08)
```

### ❌ PROHIBIDO
```html
<!-- NUNCA hardcodear colores -->
style="background-color: #003366"
style="color: #e65100"
style="background: white"
style="border: 1px solid #ccc"
```

### ✅ CORRECTO
```html
style="background-color: var(--primary-blue)"
style="color: var(--text-main)"
```

---

## 2. 📐 Estructura de Templates

### Plantilla Mínima Obligatoria

```html
{% extends 'base.html' %}

{% block page_title %}[Nombre de la sección]{% endblock %}

{% block meta_description %}
<meta name="description" content="[Descripción de la página] — Casa Lupita Logística">
{% endblock %}

{% block content %}
<!-- Contenido aquí -->
{% endblock %}
```

### Jerarquía de Layout Obligatoria

```
page_title (h1 via base.html — ya está renderizado)
  └── table-container  ← Wrapper principal de listas
        ├── table-header  ← Título + botón CTA
        ├── table-responsive  ← Siempre en tablas
        │     └── data-table  ← Clase para tablas
        └── empty-state  ← Ver sección 5
```

---

## 3. 📋 Componentes de Lista (table-container)

### Estructura Completa Estándar

```html
<div class="table-container">
    <div class="table-header d-flex justify-content-between align-items-center">
        <h3>[Título de la sección]</h3>
        <a href="{% url 'dashboard:..._create' %}" class="btn btn-primary"
           aria-label="Crear nuevo [elemento]">
            <i class="fas fa-plus me-2"></i> Nuevo [Elemento]
        </a>
    </div>

    <div class="table-responsive">
        <table class="data-table">
            <thead>
                <tr>
                    <th>[Columna]</th>
                    ...
                    <th class="text-center">Acciones</th>
                </tr>
            </thead>
            <tbody>
                {% for item in items %}
                <tr>
                    <td>...</td>
                    <td class="text-center pe-4">
                        <div class="d-flex gap-2 justify-content-center">
                            <!-- BOTONES — ver sección 4 -->
                        </div>
                    </td>
                </tr>
                {% empty %}
                <!-- Empty State — ver sección 5 -->
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
```

---

## 4. 🔘 Botones de Acción en Listas

### Reglas OBLIGATORIAS

1. **SIEMPRE** incluir `aria-label` descriptivo con el contexto del ítem
2. **SIEMPRE** incluir `title` para tooltip
3. Usar SOLO clases Bootstrap — **NUNCA** inline styles en botones
4. Tamaño `btn-sm` en tablas, `btn` o `btn-lg` en cabeceras

### Patrones de Botones

```html
<!-- ✅ Editar -->
<a href="{% url 'dashboard:..._update' item.pk %}"
   class="btn btn-sm btn-outline-primary"
   title="Editar"
   aria-label="Editar [nombre] {{ item.nombre }}">
    <i class="fas fa-edit"></i>
</a>

<!-- ✅ Ver Detalle -->
<a href="{% url 'dashboard:..._detail' item.pk %}"
   class="btn btn-sm btn-outline-info"
   title="Ver detalle"
   aria-label="Ver detalle de [nombre] {{ item.nombre }}">
    <i class="fas fa-eye"></i>
</a>

<!-- ✅ Eliminar (siempre modal de confirmación) -->
<button type="button"
        class="btn btn-sm btn-outline-danger"
        data-bs-toggle="modal" data-bs-target="#deleteModal"
        data-bs-id="{{ item.pk }}"
        title="Eliminar"
        aria-label="Eliminar [nombre] {{ item.nombre }}">
    <i class="fas fa-trash"></i>
</button>
```

### Patrón Cabecera (CTA principal)

```html
<a href="{% url 'dashboard:..._create' %}"
   class="btn btn-primary"
   aria-label="Crear nuevo [elemento]">
    <i class="fas fa-plus me-2"></i> Nuevo [Elemento]
</a>
```

---

## 5. 📭 Empty States (Estado Vacío)

### Regla: TODA lista DEBE tener un `{% empty %}` con este formato

```html
{% empty %}
<tr>
    <td colspan="100%" class="text-center py-5">
        <div class="empty-state d-flex flex-column align-items-center justify-content-center">
            <i class="fas fa-[icono-semantico] mb-3" style="font-size: 5rem;"></i>
            <h4 class="fw-bold mb-2">Aún no hay registros de [Módulo]</h4>
            <p class="text-muted mb-4" style="max-width: 400px; font-size: 1.1rem;">
                [Descripción orientativa de qué hace este módulo y por qué crear el primero]
            </p>
            <a href="{% url 'dashboard:..._create' %}"
               class="btn btn-primary btn-lg shadow-sm px-5"
               style="border-radius: 50px;">
                <i class="fas fa-plus me-2"></i> Crear Primer [Elemento]
            </a>
        </div>
    </td>
</tr>
```

### Íconos Semánticos por Módulo

| Módulo | Ícono |
|---|---|
| Unidades/Flotilla | `fa-truck` |
| Combustible | `fa-gas-pump` |
| Gastos | `fa-file-invoice-dollar` |
| Órdenes de Servicio | `fa-tools` |
| Llantas | `fa-life-ring` |
| Checklist | `fa-clipboard-check` |
| Viajes | `fa-truck-moving` |
| Operadores | `fa-id-card` |
| Zonas | `fa-map-marked-alt` |

---

## 6. 📝 Formularios (form-container)

### Estructura Obligatoria

```html
<div class="form-container">
    <div class="form-section">
        <h5 class="form-section-title">
            <i class="fas fa-[icono] me-2"></i>[Título de Sección]
        </h5>
        <div class="form-row">
            <div class="form-group">
                <label class="form-label">Campo</label>
                {{ form.campo }}
            </div>
        </div>
    </div>

    <!-- Botones SIEMPRE al final -->
    <div class="d-flex gap-3 mt-4 justify-content-end">
        <a href="{% url 'dashboard:..._list' %}"
           class="btn btn-outline-secondary"
           aria-label="Cancelar y volver al listado">
            <i class="fas fa-times me-2"></i> Cancelar
        </a>
        <button type="submit" class="btn btn-primary"
                aria-label="Guardar [nombre del formulario]">
            <i class="fas fa-save me-2"></i> Guardar
        </button>
    </div>
</div>
```

### Upload de Archivos / Evidencias

**SIEMPRE usar el componente DnD global:**

```html
<!-- Zona DnD -->
<div class="dnd-upload-zone" id="dndZone-[nombre-unico]"
     role="button" tabindex="0"
     aria-label="[Descripción de lo que se sube]">
    <input type="file" accept="image/*,application/pdf"
           class="dnd-input"
           aria-label="Seleccionar archivo">
    <div class="dnd-content">
        <i class="fas fa-cloud-upload-alt dnd-icon"></i>
        <p class="dnd-title">Arrastra aquí tu archivo</p>
        <p class="dnd-subtitle">o toca para abrir la cámara</p>
        <span class="dnd-badge">JPG / PNG / PDF · Máx. 10MB</span>
    </div>
</div>
<div class="dnd-preview" id="dndPreview-[nombre-unico]"></div>
```

**❌ PROHIBIDO:** `<input type="file" class="form-control">` sin envolver en DnD zone.

---

## 7. 🪟 Modales

### Estructura Corporativa Obligatoria

```html
<div class="modal fade" id="[nombre]Modal" tabindex="-1"
     aria-labelledby="[nombre]ModalTitle" aria-hidden="true">
  <div class="modal-dialog modal-dialog-centered">
    <div class="modal-content">

      <!-- Header: NUNCA bg-white. Usar bg-primary/bg-danger/bg-warning o sin clase -->
      <div class="modal-header bg-primary text-white">
        <h5 class="modal-title" id="[nombre]ModalTitle">
            <i class="fas fa-[icono] me-2"></i>[Título]
        </h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"
                aria-label="Cerrar"></button>
      </div>

      <div class="modal-body">
        <!-- Contenido -->
      </div>

      <div class="modal-footer">
        <button type="button" class="btn btn-outline-secondary"
                data-bs-dismiss="modal"
                aria-label="Cancelar y cerrar">Cancelar</button>
        <button type="submit" class="btn btn-primary"
                aria-label="[Acción principal]">Confirmar</button>
      </div>

    </div>
  </div>
</div>
```

### Tipos de Header por Contexto

| Situación | Clase del header |
|---|---|
| Acción neutral / info | `modal-header` (sin clase de color) |
| Acción de creación / confirmación positiva | `modal-header bg-primary text-white` |
| Advertencia / alerta | `modal-header bg-warning` |
| Eliminación / acción destructiva | `modal-header bg-danger text-white` |
| Éxito | `modal-header bg-success text-white` |

> ✅ El dark mode aplica automáticamente — no necesitas inline styles en modales.

---

## 8. 🌙 Dark Mode — Checklist de Compatibilidad

Antes de publicar cualquier template, verifica:

| Elemento | ✅ Correcto | ❌ Incorrecto |
|---|---|---|
| Fondos | `var(--bg-card)` | `white`, `#fff`, `#f9f9f9` |
| Texto | `var(--text-main)` | `#333`, `black`, `#1a1a1a` |
| Bordes | `var(--border-color)` | `#ccc`, `#ddd`, `#eee` |
| Colores primarios | `var(--primary-blue)` | `#003366`, `#003b70` hardcoded |
| Colores naranja | `var(--primary-orange)` | `#f36f21`, `#e65100` hardcoded |
| Tablas — header | `var(--table-header-bg)` | `#003366` hardcoded |
| Tablas — totales | clase CSS | `style="background: #f0f0f0"` |
| Modales | Sin inline styles en `.modal-content` | `style="background: white"` |

---

## 9. ♿ Accesibilidad (WCAG AA — Obligatorio)

### Checklist

- [ ] Todos los `<button>` de solo ícono tienen `aria-label`
- [ ] Todos los `<a>` de solo ícono tienen `aria-label`
- [ ] Imágenes tienen `alt` descriptivo
- [ ] Formularios: cada `<input>` tiene `<label>` asociado o `aria-label`
- [ ] Modales tienen `aria-labelledby` apuntando al `id` del título
- [ ] Modales tienen `aria-hidden="true"` cuando están cerrados
- [ ] Tablas de datos: `<thead>` con `<th>` para todas las columnas
- [ ] Inputs file envueltos en DnD zone con `role="button"` y `tabindex="0"`

---

## 10. 📱 Responsive — Checklist

- [ ] Grids: usar `grid-template-columns` con `@media (max-width: 768px) { 1fr }`
- [ ] Tablas anchas: envolver en `<div class="table-responsive">`
- [ ] Imágenes: usar clases Bootstrap (`img-fluid`) o CSS variables
- [ ] Botones en móvil: no menor a 44×44px de área táctil
- [ ] Formularios: columnas colapsadas en mobile (`col-md-6` → `col-12`)

---

## 11. 🔔 Feedback al Usuario

### Sistema de Mensajes Django → Toasts

Los toasts se muestran automáticamente desde `base.html`. Solo agrega en la vista:

```python
# views.py
from django.contrib import messages

messages.success(request, "Registro guardado exitosamente.")
messages.error(request, "Error: revisa los campos del formulario.")
messages.warning(request, "Atención: este registro ya existe.")
```

### Estados Obligatorios en Formularios

| Estado | Implementación |
|---|---|
| **Cargando** | `disabled` en botón submit + spinner icon |
| **Éxito** | `messages.success` → Toast verde |
| **Error** | `messages.error` → Toast rojo |
| **Vacío** | Empty State con CTA |

---

## 12. 🔒 Seguridad — Checklist por Vista

- [ ] Formularios POST incluyen `{% csrf_token %}`
- [ ] Vistas de eliminación requieren password de admin (patrón `admin_password`)
- [ ] Vistas protegidas usan `@login_required` o `LoginRequiredMixin`
- [ ] Inputs de solo staff/admin protegidos por `{% if request.user.is_superuser %}`

---

## 13. 📊 Puntuación de Auditoría (Objetivo ≥ 9/10)

| Categoría | Peso | Criterios |
|---|---|---|
| **Identidad Corporativa** | 20% | Colores navy/naranja, logo, sin colores hardcoded |
| **Dark Mode** | 20% | 100% compatible con CSS variables |
| **Accesibilidad WCAG** | 15% | aria-labels, focus ring, skip-link, contraste |
| **Responsive** | 15% | table-responsive, grids colapsables, touch targets |
| **Feedback UX** | 15% | Toasts, empty states, loading states |
| **Código limpio** | 10% | Sin inline styles, clases semánticas |
| **SEO/Meta** | 5% | page_title, meta_description por vista |

---

## 14. ✅ Checklist Pre-PR (Todo nuevo template debe pasar esto)

```
[ ] Extiende base.html con {% block page_title %}
[ ] Tiene {% block meta_description %}
[ ] Sin hexadecimales hardcodeados (usa var(--))
[ ] Sin inline style="background: white/black"
[ ] Tablas con class="data-table" + table-responsive
[ ] Botones de acción: aria-label + title en todos
[ ] Empty state completo con {% empty %}
[ ] Upload de archivos usa DnD zone global
[ ] Modales con aria-labelledby y header corporativo
[ ] Probado en light mode ✓
[ ] Probado en dark mode ✓
[ ] Probado en móvil (≤768px) ✓
[ ] messages.success/error en views.py correspondiente
```

---

## 15. 🟠 Texto Generado por JavaScript — Dark Mode

### El Problema
Cuando JavaScript inyecta HTML con colores hardcodeados (típico en `innerHTML`, template literals), **el dark mode no puede hacer override** porque el color está en `style=""` inline con alta especificidad.

### Solución Obligatoria

**Nunca hardcodear colores en JS-injected HTML:**
```javascript
// ❌ PROHIBIDO — invisible en dark mode
`<strong style="color: #003366;">COSTO BASE TOTAL: $${val.toFixed(2)}</strong>`

// ✅ CORRECTO — usa clase CSS que respeta el tema
`<strong class="costo-base-total">COSTO BASE TOTAL: $${val.toFixed(2)}</strong>`
```

### Clases Disponibles para Resultados Calculados

| Clase CSS | Uso | Light | Dark |
|---|---|---|---|
| `.costo-base-total` | Totales de cotización y costos principales | Navy `--primary-blue` | Naranja `--primary-orange` |
| `.resultado-calculo` | Cualquier resultado numérico destacado | Navy | Naranja |
| `.total-destacado` | Subtotales y sumatorias | Navy | Naranja |
| `.valor-calculado` | Valores auto-calculados por JS | Navy | Naranja |

### Animaciones de Highlight en Inputs — Theme Aware

```javascript
// ❌ PROHIBIDO — azul invisible en dark mode
input.style.backgroundColor = '#e3f2fd';

// ✅ CORRECTO — detecta el tema en tiempo de ejecución
const isDark = document.body.classList.contains('dark-theme');
input.style.backgroundColor = isDark ? 'rgba(255,118,6,0.15)' : '#e3f2fd';
setTimeout(() => { input.style.backgroundColor = ''; }, 1000);
```

### Color de Links en Dark Mode

Los links `<a href="">` en dark mode son manejados automáticamente:
- Color normal: `#60a5fa` (blue-400 — visible en fondos oscuros)
- Color hover: `var(--primary-orange)` — refuerza identidad corporativa

> ✅ **Regla de oro:** Si el color está en `innerHTML` o un template literal de JS, **SIEMPRE** usar una clase CSS en lugar de `style=""`.
