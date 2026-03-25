---
description: Design System & UI/UX Rulebook — Casa Lupita Logística
---

# 🎨 Design System Rulebook — Casa Lupita Logística

**Versión 2.1 | Aprobado: Marzo 2026**

> Este documento es la referencia obligatoria para TODA nueva vista, componente o template.
> 
> **ACTUALIZACIÓN 2.1:** Los patrones "Premium High-Fidelity" são ahora el estándar mandatorio.

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
--shadow-premium: 0 20px 40px rgba(0,0,0,0.1)

/* Gradientes Premium */
--grad-primary: linear-gradient(135deg, #003b70, #005aab)
--grad-info:    linear-gradient(135deg, #00d2ff, #3a7bd5)
--grad-success: linear-gradient(135deg, #10b981, #0a504a)
--grad-dark:    linear-gradient(135deg, #141e30, #243b55)
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

## 3. 📋 Componentes de Lista (Premium List v2.0)

### Regla de Oro
Toda vista de lista debe utilizar el contenedor `container-fluid py-4 px-md-5` y la clase `premium-table`.

### Estructura Mandatoria (Header + Table)

```html
<!-- HEADER PREMIUM -->
<div class="card border-0 shadow-lg mb-5 overflow-hidden" style="border-radius: 24px;">
    <div class="card-body p-0">
        <div class="bg-primary p-4 d-flex flex-column flex-md-row justify-content-between align-items-md-center text-white grad-primary">
            <div class="d-flex align-items-center mb-3 mb-md-0">
                <!-- ✅ USAR SIEMPRE .header-icon-box para garantizar contraste del icono -->
                <div class="header-icon-box me-3">
                    <i class="fas fa-[ICONO] fs-3"></i>
                </div>
                <div>
                    <h4 class="fw-bold mb-0">[Título del Módulo]</h4>
                    <p class="x-small mb-0 opacity-75 text-uppercase tracking-wider fw-bold">[Subtítulo Descriptivo]</p>
                </div>
            </div>
            <div class="d-flex gap-3 align-items-center">
                <a href="{% url 'dashboard:..._create' %}" class="btn btn-white rounded-pill px-4 fw-bold shadow-sm">
                    <i class="fas fa-plus-circle me-2"></i>[Acción Principal]
                </a>
            </div>
        </div>
    </div>
</div>

<!-- MAIN TABLE CARD -->
<div class="card border-0 shadow-lg overflow-hidden" style="border-radius: 28px;">
    <div class="card-body p-0">
        <div class="table-responsive">
            <table class="table table-hover align-middle mb-0 premium-table">
                <thead class="bg-light">
                    <tr>
                        <th class="ps-4">Folio / ID</th>
                        <th>Columna 1</th>
                        <th>Columna 2</th>
                        <th class="pe-4 text-center">Gestión</th>
                    </tr>
                </thead>
                <tbody>
                    {% for item in items %}
                    <tr class="animate__animated animate__fadeIn">
                        <td class="ps-4">...</td>
                        <td>...</td>
                        <td>...</td>
                        <td class="pe-4 text-center">
                            <!-- ACCIONES PREMIUM -->
                        </td>
                    </tr>
                    {% empty %}
                        <!-- Ver Sección 5 -->
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
### 3.1. Reglas de Oro del Hover y Contraste

Para garantizar la legibilidad en ambos temas (Light/Dark):

1. **Hover en Modo Dark**: El fondo de la fila al pasar el mouse **NUNCA** debe ser blanco o gris muy claro. Esto causa "ceguera" temporal al usuario y oculta el texto claro.
2. **Variable Mandatoria**: Usar exclusivamente `var(--premium-table-hover)` para fondos de hover.
3. **Contraste de Texto**: En modo Dark, se recomienda forzar `color: #fff !important;` en el estado `:hover` de la fila para asegurar que el texto destaque sobre el fondo resaltado.
4. **Badges en Hover**: Los badges internos (como `placa-badge`) deben tener estilos específicos para modo dark que mantengan su contraste incluso cuando la fila cambie de color.

```css
.premium-table tbody tr:hover td {
    background-color: var(--premium-table-hover) !important;
}
/* En styles.css ya existe el override para modo dark */
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

## 6. 📝 Formularios (Premium Form v2.0)

### Estructura Mandatoria (Standard Layout)

```html
<div class="container py-4">
    <div class="row justify-content-center">
        <div class="col-lg-10">
            <div class="card border-0 shadow-lg overflow-hidden" style="border-radius: 20px;">
                <!-- Header Premium -->
                <div class="card-header border-0 py-4 px-4 bg-primary position-relative overflow-hidden">
                    <!-- Icono decorativo de fondo -->
                    <div class="position-absolute top-0 end-0 opacity-10" style="font-size: 8rem; transform: translate(30%, -20%);">
                        <i class="fas fa-[ICONO-MODULO]"></i>
                    </div>
                    <div class="d-flex align-items-center position-relative">
                        <div class="bg-white rounded-circle p-3 me-3 d-flex align-items-center justify-content-center shadow-sm" style="width: 56px; height: 56px; background-color: rgba(255,255,255,0.2) !important;">
                            <i class="fas fa-[ICONO-ACCION] text-white fs-4"></i>
                        </div>
                        <div>
                            <h5 class="card-title mb-1 text-white fw-bold">
                                [Título de Acción: Ej. Alta de Vehículo]
                            </h5>
                            <p class="text-white-50 small mb-0">[Subtítulo Descriptivo]</p>
                        </div>
                    </div>
                </div>

                <div class="card-body p-4 p-md-5">
                    <form metod="POST" enctype="multipart/form-data" class="needs-validation">
                        {% csrf_token %}
                        
                        <div class="row">
                            <div class="col-12">
                                <div class="premium-form-grid">
                                    {{ form|crispy }}
                                </div>
                            </div>
                        </div>

                        <!-- Botones de Acción -->
                        <div class="d-flex justify-content-between align-items-center mt-5 pt-4 border-top">
                            <a href="..." class="btn btn-link text-muted text-decoration-none">
                                <i class="fas fa-arrow-left me-2"></i>Regresar a la lista
                            </a>
                            <button type="submit" class="btn btn-primary px-5 py-3 rounded-pill fw-bold shadow-sm" style="min-width: 220px;">
                                <i class="fas fa-save me-2"></i>GUARDAR REGISTRO
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>
```

### Clase `.premium-form-grid` (CSS Obligatorio)
Debe implementarse en el bloque `<style>` del template o globalmente:

```css
.premium-form-grid .form-group { margin-bottom: 1.5rem; }
.premium-form-grid label { 
    font-weight: 600; font-size: 0.85rem; color: var(--text-muted); 
    text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem; 
}
.premium-form-grid .form-control, .premium-form-grid .form-select { 
    border-radius: 12px; padding: 0.75rem 1rem; border-color: var(--border-color); 
}
.premium-form-grid .form-control:focus { 
    box-shadow: 0 4px 12px rgba(0, 59, 112, 0.1); transform: translateY(-1px); 
}
```

### 6.2. 🚫 Reglas de Oro del Layout (Evitar Deuda Técnica)

Para asegurar la consistencia, se prohíbe el uso de layouts antiguos o manuales:

1. **NUNCA** usar las clases `.form-container` o `.form-header` manuales. Estas son legado y deben ser reemplazadas por la estructura `card` + `card-header bg-primary` definida arriba.
2. **SIEMPRE** envolver el formulario en `container py-4` (para forms) o `container-fluid py-4` (para listas/dashboards).
3. **NUNCA** usar `style="max-width: ..."` en contenedores de primer nivel; usar las clases de grid de Bootstrap (`col-lg-10`, `col-xl-8`).

### 6.3. 🗂️ Secciones Especiales y Checklists

Si un formulario es extenso o requiere secciones funcionales (como el Checklist de Unidad):

1. **Secciones Internas**: Usar la clase `.premium-form-grid` para los campos estándar.
2. **Badge de Título**: Cada sección debe iniciar con un badge indicativo:

   ```html
   <div class="section-badge mb-4">
       <span class="badge rounded-pill bg-primary-subtle text-primary border-0 px-3 py-2 x-small fw-bold shadow-xs">
           <i class="fas fa-[ICONO] me-2"></i>TÍTULO SECCIÓN
       </span>
   </div>
   ```

3. **Componentes Custom**: Toggles y selectores de nivel (como gasolina) deben usar estados `:active` con colores corporativos y sombras `shadow-sm`.

### 6.4. 📁 Upload de Archivos / Evidencias (DnD v2.0)

**SIEMPRE usar el componente DnD global para campos de archivo:**

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

---

## 16. 🏗️ Reglas de Creación (Creation Rules)

Para garantizar la fluidez del usuario (User Flow), toda vista que gestione una colección de datos debe facilitar la creación de nuevos registros:

1. **CTA en Cabecera**: El `table-header` debe incluir siempre un botón link (`<a>`) con clase `btn-primary` y el icono `fa-plus`.
2. **CTA en Estado Vacío**: Si la lista está vacía (`{% empty %}`), el componente `empty-state` debe incluir obligatoriamente el mismo CTA en tamaño grande (`btn-lg`) como acción principal.
3. **Consistencia de URL**: Los botones de creación deben apuntar consistentemente a la vista `..._create` del módulo correspondiente.
4. **Visibilidad Staff**: Si el botón está restringido por permisos, asegurar que el estado vacío refleje un mensaje adecuado para el usuario sin permisos (p. ej., "Contacta al administrador" en lugar de un botón inútil).

> ✅ **Nota**: El objetivo es que el usuario NUNCA llegue a un "callejón sin salida" visual.
