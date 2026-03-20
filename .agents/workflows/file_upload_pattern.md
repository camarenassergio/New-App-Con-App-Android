---
description: Patrón obligatorio para subida de archivos (DnD Upload Zone) — Casa Lupita
---

# 📎 Patrón DnD Upload Zone — Regla Obligatoria

> **REGLA:** En este proyecto SIEMPRE se usa el componente `dnd-upload-zone` para cualquier campo de subida de archivos (imágenes, PDFs, documentos). **Nunca** se debe usar el `<input type="file">` desnudo ni el widget por defecto de Django (`{{ form.campo }}`).

---

## ¿Por qué?

- El handler global en `base.html` (líneas ~452–532) ya lo gestiona automáticamente.
- Ofrece UX mejorada: drag-and-drop, vista previa de imagen, icono PDF, botón de quitar.
- Consistente con combustible_form.html, gasto_form.html y usuario_perfil.html.

---

## Estructura del Componente

```html
<!-- Zona clickeable / drag-and-drop -->
<div class="dnd-upload-zone" id="dndZone-{nombre_campo}">
    <input type="file" name="{nombre_campo}" id="id_{nombre_campo}" accept="image/*,application/pdf">
    <i class="fas fa-{icono} dnd-icon"></i>
    <span class="dnd-label">{Texto principal}</span>
    <span class="dnd-sublabel">{Restricciones o descripción corta}</span>
</div>
<!-- Contenedor de vista previa — el ID DEBE seguir la convención dndPreview-{nombre_campo} -->
<div class="dnd-preview-container" id="dndPreview-{nombre_campo}"></div>
```

### Convención de IDs (CRÍTICA)
El handler en base.html deriva el ID del preview a partir del ID de la zona:
```
dndZone-evidencia_antes  →  dndPreview-evidencia_antes
dndZone-evidencia_ticket →  dndPreview-evidencia_ticket
```
**Si no sigues esta convención, las vistas previas no funcionarán.**

---

## Íconos sugeridos por tipo de campo

| Tipo de archivo      | Clase FontAwesome              |
|----------------------|-------------------------------|
| Foto de cámara       | `fa-camera-retro`             |
| Evidencia/resultados | `fa-images`                   |
| Ticket / factura     | `fa-file-invoice`             |
| PDF genérico         | `fa-file-pdf`                 |
| Foto de perfil       | `fa-user-circle`              |
| Documento general    | `fa-file-alt`                 |

---

## Atributos del `<input>`

| Atributo   | Valor habitual                      | Notas                              |
|-----------|-------------------------------------|------------------------------------|
| `accept`  | `image/*` / `image/*,application/pdf` | Limitar al tipo necesario        |
| `capture` | `environment`                       | Solo si se quiere forzar cámara   |
| `required`| (omitir si es opcional)             | Agregar solo si el campo es \*     |
| `name`    | Nombre del campo Django             | Debe coincidir con el form field  |

---

## Ejemplos Existentes en el Proyecto

| Template                  | Campo               | ID de zona                    |
|--------------------------|---------------------|-------------------------------|
| `combustible_form.html`  | evidencia_antes     | `dndZone-evidencia_antes`     |
| `combustible_form.html`  | evidencia_despues   | `dndZone-evidencia_despues`   |
| `gasto_form.html`        | evidencia           | `dndZone-evidencia`           |
| `usuario_perfil.html`    | foto (perfil)       | `dndZone-perfil`              |
| `pedido_form.html`       | evidencia_ticket    | `dndZone-evidencia_ticket`    |

---

## Checklist antes de hacer PR

- [ ] ¿Usas `dnd-upload-zone` en vez del widget Django?
- [ ] ¿El `id` de la zona empieza con `dndZone-`?
- [ ] ¿El `id` del preview empieza con `dndPreview-` y coincide exactamente?
- [ ] ¿El `name` del input coincide con el campo del `ModelForm`?
- [ ] ¿El `enctype="multipart/form-data"` está en el `<form>`?
