# Análisis de Seguridad — Publicación en Streamlit

Información que debe **ocultarse o eliminarse** antes de publicar el repo en GitHub y desplegar en Streamlit Community Cloud.

---

## 🔴 CRÍTICO — Eliminar antes de publicar

### 1. Datos de negocio (HUs reales)

| Archivo/Carpeta | Riesgo | Acción |
|-----------------|--------|--------|
| `Raw Data/` | Contiene HUs reales de Actinver (TDC, Cuenta Remunerada, Onboarding, Crédito Simple) | **Eliminar del repo** o mover a .gitignore |
| `Output/*.xlsx` | Resultados de análisis con datos internos | **Eliminar del repo** (ya en .gitignore pero ya fueron commiteados) |
| `HUs_Compilado_analizado.xlsx` (raíz) | Excel analizado con datos de negocio | **Eliminar del repo** |
| `mi_proyecto.zip` | Contenido desconocido; puede incluir datos sensibles | **Eliminar del repo** o verificar contenido |

**Comando para remover del historial (sin borrar localmente):**
```bash
git rm -r --cached "Raw Data/" Output/*.xlsx HUs_Compilado_analizado.xlsx mi_proyecto.zip 2>/dev/null
git commit -m "Remove sensitive business data before public deploy"
```

---

### 2. API Keys y secrets

| Elemento | Estado | Acción |
|----------|--------|--------|
| `secrets.toml` | En .gitignore ✓ | **Verificar** que NUNCA se haya commiteado |
| `ANTHROPIC_API_KEY` | Solo en Secrets de Streamlit | Configurar en **Advanced settings** al desplegar, no en código |

**La API key NUNCA debe estar en el código ni en el repo.**

---

## 🟠 MEDIO — Considerar ocultar o generalizar

### 3. Información corporativa explícita

| Ubicación | Contenido actual | Opción |
|-----------|------------------|--------|
| README, app.py, hu_analyzer.py | "Actinver", "Productos Digitales Actinver" | **Mantener** si la app es oficial de Actinver; **generalizar** si quieres reutilizarla como plantilla |
| Prompts (hu_analyzer.py) | "Onboarding N4, Cuenta Remunerada, Crédito Simple, TDC Actinver" | Productos específicos — OK si es uso interno; considerar **parametrizar** si se comparte fuera |
| SECURITY.md | "[contacto interno Actinver]" | Reemplazar por email genérico o eliminar sección si no aplica |

### 4. Historial de Git (commits)

Los commits pueden exponer:
- **Emails:** `gagaviv@gmail.com` (en autor de commits)
- **Usuarios:** `5p1kes`

**Opciones:**
- Dejar como está (común en repos públicos)
- Reescribir historial con `git filter-branch` o `git filter-repo` (avanzado)

---

## 🟢 BAJO — Ya cubierto

| Elemento | Estado |
|----------|--------|
| `.streamlit/secrets.toml` | En .gitignore ✓ |
| `secrets.toml.example` | Solo plantilla, sin clave real ✓ |
| `.hu_analyzer_speed.json` | En .gitignore ✓ |
| Paths locales (OneDrive) | Solo en DEV.md como nota de troubleshooting ✓ |

---

## Checklist pre-publicación

- [ ] Eliminar `Raw Data/` del repo
- [ ] Eliminar `Output/*.xlsx` del repo
- [ ] Eliminar `HUs_Compilado_analizado.xlsx` y `mi_proyecto.zip`
- [ ] Verificar que `secrets.toml` no esté en el repo (`git status`)
- [ ] Configurar `ANTHROPIC_API_KEY` solo en Streamlit Secrets (no en código)
- [ ] Revisar SECURITY.md: contacto interno
- [ ] (Opcional) Decidir si mantener referencias a Actinver o generalizar

---

## Resumen ejecutivo

**Debe ocultarse/eliminarse:**
1. **Datos de negocio:** Raw Data, Output, Excels analizados, mi_proyecto.zip
2. **API Key:** Solo en Streamlit Secrets, nunca en el repo

**Puede mantenerse (según política):**
- Referencias a Actinver si la app es de uso interno/corporativo
- Historial de commits (emails visibles)
