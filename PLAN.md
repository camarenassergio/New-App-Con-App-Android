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

- **Paso**: Desarrollo Fase 2 y 3 (Mostrador, Logística, App Chofer y Mensajería)
- **Objetivo**: Implementar el flujo híbrido de pedidos (CEMEX), Kanban logístico con cálculos de peso, bifurcación a proveedores externos y App Móvil de Chofer (Módulo HTMX asíncrono y Motor de Mensajes).
- **Estado**: En progreso - Validación del Plan V3 de implementación.

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
| Antigravity | UX: Pulido de Dark Mode en Historial de Gastos y Listas | Verificado y Pulido |
| Antigravity | UI/UX: Auditoría Full — Modales dark mode, skip-link, aria-labels, focus ring, toasts, DnD perfil | Verificado [AUTO-HEALED] |
| Antigravity | UX: Eliminación de páginas intermedias de éxito — solo Toast feedback (AjaxSuccessMixin refactor) | Verificado y Pulido |
| Antigravity | Design System Rulebook v2.0 (15 secciones) registrado en .agent/workflows | Verificado y Pulido |
| Antigravity | HTMX Audit: convertidos configuracion_general, usuario_cambiar_password, unidad_list toggle | Verificado y Pulido |
| Antigravity | UX: Redirección de ConfiguracionGeneral a Dashboard Home post-guardado | Verificado y Pulido |
| Antigravity | Paso 1 (Fase 2): Mostrador — Registro, Cotizador, SAE Sync y Bloqueo de Edición | Verificado y Pulido |
| Antigravity | Notificaciones: Campana, Badge HTMX y Autorización de Zonas | Verificado y Pulido |
| Antigravity | UX Mapas: Previsualización de Ruta OSRM, Pin Centroide y Geo-Dissolve | Verificado [AUTO-HEALED] |
| Antigravity | Fix: Búsqueda de Colonia Estricta (Municipio) — Evita zonas incorrectas en CPs ajenos | Verificado [AUTO-HEALED] |
| Antigravity | Paso 2 (Fase 2): Logística — Command Center (Kanban Board) con HTMX Drag/Drop state | Verificado y Pulido |
| Antigravity | Mantenimiento: Respaldo y Restauración de Base de Datos (mysqldump) | Verificado [AUTO-HEALED] |
| Antigravity | UX: Sincronización SAE Modal, Cliente Propietario Dinámico y Captura de Teléfono | Verificado [AUTO-HEALED] |
| Antigravity | Dashboard: Métricas Personales de Mostrador (Pedidos Hoy) | Verificado y Pulido |
| Antigravity | Gestión de Despachos: Edición, Cancelación y División de Saldos | Verificado y Pulido |
| Antigravity | Kanban Logístico: Transición a Flujo Granular (Despacho > Ruta) | Verificado [AUTO-HEALED] |
| Antigravity | Almacén: Panel de Surtido Personalizado (Filtro por Surtidor) | Verificado y Pulido |
| Antigravity | UX Modales: Centralización de lupita-modal-container y Stándar Global | Verificado [AUTO-HEALED] |

## Reglas del Proyecto

- **Idioma**: Español (Obligatorio en Comentarios, Commits y Documentación).
- **Frontend — HTMX (REGLA ABSOLUTA)**: TODO formulario transaccional DEBE usar HTMX (`hx-post`, `hx-put`, etc.). PROHIBIDO usar `<form method="post">` sin atributos HTMX en vistas del dashboard. La única excepción permitida es `login.html` y `usuario_perfil.html` (upload binario multipart con cropper). Spinner obligatorio con `hx-indicator`.
- **Frontend / UX**: Todos los NUEVOS formularios y flujos transaccionales DEBEN implementarse usando HTMX para asegurar 'Immediate Feedback < 100ms' sin recargar página completa.
- **Empty States / UI**: Todas las NUEVAS listas y tablas DEBEN incorporar "Empty States" vistosos con ícono semántico, mensaje orientativo y CTA.
- **Feedback de Acciones**: PROHIBIDO mostrar páginas intermedias de "éxito" o "confirmación". El único feedback permitido son Toasts vía `messages.success/error/warning` → `base.html`.
- **Dark Mode**: TODA nueva vista debe ser 100% compatible con dark mode usando CSS variables. Ver Design System `/ui_ux_design_system`.
