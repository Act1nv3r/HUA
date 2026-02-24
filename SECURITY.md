# Análisis de Riesgos y Mitigaciones — HU Analyzer Platform

## Alcance

Plataforma para análisis de Historias de Usuario con IA, desplegada de forma **privada** vía Streamlit (Community Cloud o self-hosted).

---

## 1. Matriz de Riesgos

| ID | Riesgo | Prob. | Impacto | Severidad | Mitigación |
|----|--------|-------|---------|-----------|------------|
| R1 | Exposición de API Key en código/repositorio | Media | Crítico | **Alto** | Secrets management (st.secrets / env) |
| R2 | Archivos maliciosos subidos (macro, oversize) | Media | Alto | **Alto** | Validación tipo, tamaño, sanitización |
| R3 | Datos sensibles (HUs) expuestos a usuarios no autorizados | Media | Alto | **Alto** | Autenticación, acceso privado |
| R4 | Costo descontrolado por abuso de API Anthropic | Media | Medio | **Medio** | Límite de HUs, rate limiting |
| R5 | Información sensible en mensajes de error | Baja | Medio | **Medio** | Sanitización de errores |
| R6 | Archivos temporales no eliminados | Baja | Medio | **Medio** | Limpieza garantizada (try/finally) |
| R7 | Path traversal en nombres de archivo | Baja | Alto | **Medio** | Validación de nombres |
| R8 | Datos enviados a terceros (Anthropic) | Baja | Medio | **Medio** | Política de privacidad, consentimiento |
| R9 | Sesión compartida entre usuarios (Streamlit) | Baja | Medio | **Medio** | Output por sesión, no compartir archivos |
| R10 | Logs con datos sensibles | Baja | Medio | **Medio** | No loguear contenido de HUs |

---

## 2. Mitigaciones Implementadas

### R1 — API Key
- **Implementado:** Uso de `st.secrets` (Streamlit Cloud) o `ANTHROPIC_API_KEY` en variables de entorno.
- **No hardcodear** la clave en el código.
- **`.gitignore`** debe incluir `secrets.toml` y `.streamlit/secrets.toml`.

### R2 — Validación de archivos
- **Tamaño máximo:** 25 MB (configurable).
- **Tipos permitidos:** Solo `.xlsx` (openpyxl no ejecuta macros).
- **Validación de extensión** antes de procesar.
- **Nombre sanitizado** para evitar path traversal.

### R3 — Acceso privado
- **Streamlit Community Cloud:** App privada (solo invitados con link).
- **Alternativa:** Cloudflare Tunnel + Cloudflare Access para SSO corporativo.
- **Recomendación:** Repo privado en GitHub para el despliegue.

### R4 — Control de costos
- **Límite de HUs por análisis:** Configurable (default 0 = todas, máx 200).
- **Límite global:** 200 HUs por ejecución para evitar costos excesivos.
- **Modo prueba:** Límite de 5 HUs sugerido en UI.

### R5 — Errores sanitizados
- **No exponer** stack traces completos al usuario en producción.
- **Mensajes genéricos** para errores inesperados.
- **Logs detallados** solo en servidor (no en UI).

### R6 — Archivos temporales
- **Eliminación garantizada** con `try/finally`.
- **Output en carpeta dedicada** con limpieza opcional de archivos antiguos.

### R7 — Path traversal
- **Sanitización de nombres** de archivo subido.
- **Output path** generado internamente, no por usuario.

### R8 — Datos a terceros
- **Documentar** que las HUs se envían a Anthropic para análisis.
- **Política de privacidad** de Anthropic aplicable.
- **Uso interno** — datos de negocio, no PII de clientes finales.

### R9 — Aislamiento de sesión
- **Output por sesión:** Archivos generados asociados a la sesión actual.
- **Streamlit:** Cada sesión tiene su propio estado.
- **Evitar** almacenar outputs en rutas predecibles compartidas.

### R10 — Logs
- **No loguear** contenido de HUs ni datos sensibles.
- **Solo** IDs, conteos, errores técnicos (sin payload).

---

## 3. Configuración para Despliegue Privado

### Streamlit Community Cloud (privado)

1. Repo **privado** en GitHub.
2. En **Secrets** de la app:
   ```
   ANTHROPIC_API_KEY = "sk-ant-..."
   ```
3. **Sharing:** "Private" — solo usuarios con acceso al repo o link de invitación.
4. **Branch:** `main` o la rama que uses.

### Self-hosted (más control)

- **Docker** + **nginx** con HTTPS.
- **Cloudflare Tunnel** + **Cloudflare Access** para autenticación.
- Variables de entorno inyectadas en el contenedor.

---

## 4. Checklist Pre-Despliegue

- [ ] API Key en secrets, no en código
- [ ] `.gitignore` incluye `secrets.toml`
- [ ] Límite de HUs configurado
- [ ] Tamaño máximo de archivo configurado
- [ ] App configurada como privada
- [ ] Repositorio privado (si aplica)
- [ ] Revisión de mensajes de error expuestos al usuario

---

## 5. Contacto

Para reportar vulnerabilidades de seguridad: [contacto interno Actinver].
