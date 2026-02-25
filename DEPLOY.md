# Despliegue en Streamlit Community Cloud

Guía paso a paso para publicar HU Analyzer en [share.streamlit.io](https://share.streamlit.io).

---

## Requisitos previos

- [ ] Cuenta en [GitHub](https://github.com)
- [ ] API Key de Anthropic (para Claude)
- [ ] Git instalado en tu máquina

---

## Paso 1: Inicializar repositorio Git (si aún no lo tienes)

En la terminal, desde la carpeta del proyecto:

```bash
cd hu-analyzer
git init
git add .
git status   # Verifica que NO aparezca .streamlit/secrets.toml
git commit -m "Initial commit - HU Analyzer"
```

**⚠️ Acción tuya:** Confirma que `secrets.toml` NO está en la lista de archivos a commitear (está en .gitignore).

---

## Paso 2: Crear repositorio en GitHub

1. Ve a [github.com/new](https://github.com/new)
2. Nombre sugerido: `hu-analyzer` (o el que prefieras)
3. Visibilidad: **Privado** (recomendado) o Público
4. **No** marques "Add a README" (ya tienes uno)
5. Clic en **Create repository**

**⚠️ Acción tuya:** Copia la URL del repo (ej: `https://github.com/tu-usuario/hu-analyzer.git`).

---

## Paso 3: Conectar y subir el código

En la terminal (desde `hu-analyzer`):

```bash
git remote add origin https://github.com/TU-USUARIO/hu-analyzer.git
git branch -M main
git push -u origin main
```

Reemplaza `TU-USUARIO` por tu usuario de GitHub.

**⚠️ Acción tuya:** Si GitHub te pide autenticación, usa un Personal Access Token o SSH.

---

## Paso 4: Crear cuenta en Streamlit Community Cloud

1. Ve a [share.streamlit.io](https://share.streamlit.io)
2. Clic en **Sign up** o **Get started**
3. Inicia sesión con **GitHub** (recomendado para conectar repos)

**⚠️ Acción tuya:** Autoriza a Streamlit para acceder a tus repositorios.

---

## Paso 5: Desplegar la app

1. En [share.streamlit.io](https://share.streamlit.io), clic en **Create app** (esquina superior derecha)
2. Selecciona **"Yup, I have an app"**
3. Completa:
   - **Repository:** `tu-usuario/hu-analyzer`
   - **Branch:** `main`
   - **Main file path:** `app.py`
4. (Opcional) **App URL:** Ej. `hu-analyzer-actinver` → `https://hu-analyzer-actinver.streamlit.app`
5. Clic en **Advanced settings**

---

## Paso 6: Configurar Secrets (OBLIGATORIO)

En **Advanced settings** → campo **Secrets**, pega exactamente:

```toml
ANTHROPIC_API_KEY = "sk-ant-api03-TU-API-KEY-AQUI"
```

Reemplaza `TU-API-KEY-AQUI` por tu clave real de Anthropic.

6. Clic en **Save**
7. Clic en **Deploy**

**⚠️ Acción tuya:** Obtén tu API Key en [console.anthropic.com](https://console.anthropic.com) si no la tienes.

---

## Paso 7: Esperar el despliegue

- La app suele estar lista en 2–5 minutos
- Puedes ver los logs en tiempo real
- Si hay errores, revisa que `requirements.txt` esté en la raíz y que los Secrets estén bien configurados

---

## Verificación post-despliegue

| Verificación | Cómo |
|--------------|------|
| App carga | Abre la URL (ej. `https://tu-app.streamlit.app`) |
| API Key funciona | Sube un Excel de prueba y ejecuta un análisis |
| Descarga funciona | Descarga el Excel analizado |

---

## Actualizar la app después de cambios

```bash
git add .
git commit -m "Descripción del cambio"
git push origin main
```

Streamlit detecta el push y redespliega automáticamente en unos minutos.

---

## Privacidad y compartir

- **App privada:** Por defecto, cualquiera con el link puede acceder
- Para restringir: considera [Streamlit Teams](https://streamlit.io/cloud) (de pago) o exponer la app detrás de un túnel (Cloudflare Tunnel + Access)

---

## Solución de problemas

| Problema | Solución |
|----------|----------|
| "ANTHROPIC_API_KEY no configurada" | Revisa Secrets en App settings → Secrets |
| Error al instalar dependencias | Verifica que `requirements.txt` esté en la raíz |
| App no actualiza | Espera 2–3 min tras el push; revisa que el branch sea el correcto |
| Timeout o error 502 | Reduce `MAX_HUS_PER_RUN` en `config.py` si analizas muchas HUs |
