# 🚀 Cómo Ejecutar la Aplicación Flask

## Paso 1: Instalar Python

Si no tienes Python instalado:
1. Descarga de https://www.python.org/downloads/
2. Durante la instalación, marca "Add Python to PATH"

Verifica la instalación:
```bash
python --version
```

## Paso 2: Instalar Dependencias

```bash
pip install -r requirements.txt
```

**Nota**: La primera vez puede tardar porque descarga el modelo de embeddings (~80MB).

## Paso 3: Instalar Poppler (Para extraer imágenes de PDFs)

### Opción A: Con Chocolatey (Recomendado)
```powershell
choco install poppler
```

### Opción B: Manual
1. Descarga de: https://github.com/oschwartz10612/poppler-windows/releases/
2. Extrae el ZIP
3. Agrega la carpeta `bin` a tu PATH de Windows

**Nota**: Si no instalas Poppler, la extracción de imágenes no funcionará, pero el resto de la app sí.

## Paso 4: Configurar Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
OPENROUTER_API_KEY=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
OPENROUTER_API_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=x-ai/grok-4.1-fast:free
OPENROUTER_HTTP_REFERER=http://localhost:5000
OPENROUTER_APP_NAME=RAG Chatbot
```

**En PowerShell:**
```powershell
@"
OPENROUTER_API_KEY=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
OPENROUTER_API_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=x-ai/grok-4.1-fast:free
OPENROUTER_HTTP_REFERER=http://localhost:5000
OPENROUTER_APP_NAME=RAG Chatbot
"@ | Out-File -FilePath .env -Encoding utf8
```

## Paso 5: Ejecutar la Aplicación

```bash
python app.py
```

Deberías ver:
```
Cargando modelo de embeddings...
Modelo de embeddings cargado!
 * Running on http://127.0.0.1:5000
```

## Paso 6: Abrir en el Navegador

Ve a: **http://localhost:5000**

## ✅ ¡Listo!

Ya puedes:
1. Subir PDFs (botón "+" flotante)
2. Seleccionar un PDF en la barra lateral
3. Hacer preguntas sobre el contenido
4. Ver imágenes del PDF en las respuestas

## Comandos Útiles

### Detener el servidor
Presiona `Ctrl + C` en la terminal

### Ver errores
Los errores aparecerán en la terminal donde ejecutaste `python app.py`

## Solución de Problemas

### Error: "No module named 'flask'"
```bash
pip install -r requirements.txt
```

### Error: "poppler not found"
- Instala Poppler (ver Paso 3)
- O simplemente ignóralo si no necesitas extraer imágenes

### Error: "OPENROUTER_API_KEY is not defined"
- Verifica que el archivo `.env` exista
- Verifica que esté en la raíz del proyecto (mismo nivel que `app.py`)

### Error: "Port 5000 is already in use"
Cambia el puerto en `app.py`:
```python
app.run(debug=True, port=5001)  # Cambia 5000 a 5001
```

## Ventajas de Flask vs Next.js

✅ **No requiere compilación nativa** - Todo es Python puro
✅ **Más simple** - Menos dependencias
✅ **SQLite nativo** - No necesita better-sqlite3
✅ **Rápido de instalar** - Solo `pip install`

¡Disfruta tu aplicación! 🚀
