# RAG Chatbot con Flask y Grok

Aplicación web completa con chatbot inteligente que utiliza RAG (Retrieval-Augmented Generation) para analizar documentos PDF mediante Flask y Grok 4.1 Fast.

## Características

- 🤖 **Chatbot con Grok 4.1 Fast**: Integración con OpenRouter usando el modelo Grok 4.1 Fast (gratuito)
- 📄 **Carga y procesamiento de PDFs**: Sube múltiples PDFs y extrae texto e imágenes
- 🔍 **Sistema RAG**: Búsqueda semántica con embeddings para encontrar información relevante
- 🖼️ **Visualización de imágenes**: Muestra imágenes del PDF en el chat con visor ampliado
- 💾 **Historial persistente**: Almacena todas las conversaciones en SQLite
- 💡 **Preguntas recomendadas**: Sugiere preguntas basadas en el contexto
- 🎨 **UI Futurista**: Diseño moderno con efectos neón y modo oscuro

## Requisitos

- Python 3.8+
- pip

## Instalación

1. **Instala las dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Instala Poppler** (necesario para extraer imágenes de PDFs):
   - **Windows**: Descarga de https://github.com/oschwartz10612/poppler-windows/releases/
   - Extrae y agrega `bin` a tu PATH
   - O usa: `choco install poppler` (si tienes Chocolatey)

3. **Configura las variables de entorno:**
   Crea un archivo `.env`:
   ```env
   OPENROUTER_API_KEY=tu_api_key_aqui
   OPENROUTER_API_URL=https://openrouter.ai/api/v1
   OPENROUTER_MODEL=x-ai/grok-4.1-fast:free
   OPENROUTER_HTTP_REFERER=http://localhost:5000
   OPENROUTER_APP_NAME=RAG Chatbot
   ```

4. **Ejecuta la aplicación:**
   ```bash
   python app.py
   ```

5. **Abre en el navegador:**
   ```
   http://localhost:5000
   ```

## Uso

1. **Subir un PDF**: Haz clic en el botón flotante "+" en la esquina inferior derecha
2. **Seleccionar PDF**: Haz clic en un PDF en la barra lateral para seleccionarlo
3. **Hacer preguntas**: Escribe preguntas sobre el contenido del PDF
4. **Ver imágenes**: Las imágenes relevantes aparecerán automáticamente en las respuestas
5. **Revisar historial**: Todas las conversaciones se guardan automáticamente

## Estructura del Proyecto

```
├── app.py              # Aplicación Flask principal
├── requirements.txt    # Dependencias Python
├── templates/         # Plantillas HTML
│   └── index.html     # Interfaz principal
├── data/              # Datos almacenados (generado automáticamente)
│   ├── database.sqlite
│   ├── uploads/
│   └── images/
└── .env               # Variables de entorno (crear manualmente)
```

## API Endpoints

- `POST /api/upload-pdf`: Sube y procesa un PDF
- `POST /api/chat`: Envía un mensaje al chatbot
- `GET /api/list-pdfs`: Lista todos los PDFs cargados
- `GET /api/history`: Obtiene historial de conversaciones
- `GET /api/recommended-questions`: Genera preguntas sugeridas
- `GET /api/image`: Sirve imágenes de PDFs

## Tecnologías Utilizadas

- **Flask**: Framework web Python
- **SQLite**: Base de datos (nativo de Python, no requiere compilación)
- **PyPDF2**: Extracción de texto de PDFs
- **pdf2image**: Extracción de imágenes de PDFs
- **sentence-transformers**: Modelos de embeddings
- **OpenAI SDK**: Cliente compatible con OpenRouter API

## Notas

- Los PDFs se almacenan en `data/uploads/`
- Las imágenes se almacenan en `data/images/[pdfId]/`
- La base de datos se crea automáticamente en `data/database.sqlite`
- El modelo de embeddings se descarga automáticamente la primera vez

## Solución de Problemas

### Error: "poppler not found"
- Instala Poppler y agrega `bin` a tu PATH
- O usa: `choco install poppler` en Windows

### Error: "OPENROUTER_API_KEY is not defined"
- Verifica que el archivo `.env` exista y tenga la API key correcta

### Error al subir PDF
- Verifica que el archivo sea un PDF válido
- Asegúrate de que el directorio `data/` tenga permisos de escritura

## Licencia

MIT
