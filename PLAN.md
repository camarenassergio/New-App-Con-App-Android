# Plan de Proyecto: Logística Casa Lupita - Nueva App

## Hoja de Ruta Maestra
- [x] Fase 1: Inicialización del Proyecto y Configuración de Infraestructura
- [/] Fase 2: Diseño de Base de Datos e Implementación Backend
- [ ] Fase 3: Conexión App Android y Funcionalidades Básicas
- [x] Fase 4: Pruebas y Verificación (Tailscale, Docker)
- [x] Fase 5: Protocolos de Prevención y Plan de Contingencia

## Pendientes (Backlog)
- [ ] Modificar evidencias de entrega: permitir guardar más de una evidencia fotográfica y solicitar obligatoriamente la foto del ticket.
- [ ] **[HITO FUTURO]** Sistema Experto Predictivo de Tiempos de Maniobra: Aprenderá del historial empírico basado en familia de materiales, peso y unidad para cotizar dinámicamente.
- [ ] **[DEUDA TÉCNICA / UX]** Migración de flujos transaccionales (ej. Gastos, Checklist) a metodología SPA/AJAX (HTMX/JS Nativo) para eliminar *page reloads*, mejorar la percepción de velocidad (Immediate Feedback <100ms) y dar sensación de app nativa.

## Trayectoria Actual
- **Paso**: Refactorización de Arquitectura de Frontend (SPA/AJAX)
- **Objetivo**: Migrar todos los formularios existentes y transaccionales a HTMX/AJAX para eliminar reloads de página, y asegurar que todos los nuevos formularios sigan este estándar.
- **Estado**: En progreso - Implementando HTMX en formularios.

## Estado del Squad
| Agente | Tarea | Estado |
| :--- | :--- | :--- |
| Antigravity | Inicialización del Proyecto | Verificado [AUTO-HEALED] |
| Antigravity | Mapa Zonas de Entrega (Leaflet) | Verificado y Pulido |
| Antigravity | Command Center Híbrido, Flete Dinámico y Autocompletado | Verificado [AUTO-HEALED] |
| Antigravity | Auditoría de Seguridad y Hardening | Verificado [AUTO-HEALED] |
| Antigravity | Implementación Fase 2 (Auth/Dash) | Verificado [Environment Fixed] |
| Antigravity | Plan de Contingencia (SEDEMA Scraping) | Verificado y Pulido |
| Antigravity | UX/UI File Uploads (Perfil & Combustible) | Verificado y Pulido |
| Antigravity | BI: Gráfica de Gastos Mes Apilada (Dashboard) | Verificado y Pulido |
| Antigravity | Digitalización: Módulo "Orden de Servicio" (Mantenimiento) | Verificado y Pulido |
| Antigravity | Automatización: Carga de CPs en Railway (Release Phase) | Verificado [AUTO-HEALED] |
| Antigravity | Fix: Mostrar todas las colonias en tabla sin truncar | Verificado y Pulido |
| Antigravity | Nueva Vista: Configuraciones Generales (Sueldos) | Verificado y Pulido |
| Antigravity | KPI: Costo de cada llanta para unidades | Verificado [AUTO-HEALED] |
| Antigravity | Automatización: Cálculo Fecha de Vencimiento Llanta (DOT) | Verificado y Pulido |
| Antigravity | Monitoreo: Alertas de límite de seguridad y vida útil de llantas | Verificado y Pulido |
| Antigravity | Seguridad: Validación de Medición Neumática obligatoria en Checklist (15 días o 5M km) | Verificado y Pulido |
| Antigravity | Análisis Predictivo: Tasa de Desgaste (TE vs TA) y Causas Raíz (Irregular/Uniforme) | Verificado y Pulido |
| Antigravity | Diagnóstico Automático: Comparación por Eje y Gemelas con Esquema Visual de Desgaste | Verificado y Pulido |
| Antigravity | Refactor: Migración de Formularios a HTMX (SPA/AJAX) | Verificado y Pulido |
| Antigravity | UX: Implementación de "Empty States" Modernos | Verificado y Pulido |

## Reglas del Proyecto
- **Idioma**: Español (Obligatorio en Comentarios, Commits y Documentación).
- **Frontend / UX**: Todos los NUEVOS formularios y flujos transaccionales DEBEN implementarse usando HTMX o como una API (AJAX/JS Nativo) para asegurar un 'Immediate Feedback < 100ms' sin recargar la página completa, logrando una sensación de SPA (Single Page Application). No se permiten formularios SSR tradicionales (full page reload) para nuevas operaciones transaccionales.
- **Empty States / UI**: Todas las NUEVAS listas y tablas del sistema DEBEN incorporar "Empty States" vistosos y modernos en caso de no contener datos (etiqueta `{% empty %}`). En lugar de mensajes de texto genéricos (ej. "Sin registros"), se exige un diseño con un ícono semántico grande, mensaje de orientación descriptivo y un Botón de Llamado a la Acción (CTA) para invitar a crear el primer registro.
