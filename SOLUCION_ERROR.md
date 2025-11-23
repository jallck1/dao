# ✅ Error Resuelto

## Problema
El error era un conflicto de versiones entre `sentence-transformers` (versión antigua 2.2.2) y `huggingface-hub` (versión nueva).

## Solución Aplicada
Se actualizó `sentence-transformers` a la versión 5.1.2 que es compatible con las versiones modernas de `huggingface-hub`.

## Para Ejecutar Ahora

1. **Asegúrate de tener las dependencias actualizadas:**
   ```bash
   pip install --upgrade sentence-transformers huggingface-hub
   ```

2. **Crea el archivo `.env`** (si no lo has hecho):
   ```powershell
   @"
   OPENROUTER_API_KEY=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
   OPENROUTER_API_URL=https://openrouter.ai/api/v1
   OPENROUTER_MODEL=x-ai/grok-4.1-fast:free
   OPENROUTER_HTTP_REFERER=http://localhost:5000
   OPENROUTER_APP_NAME=RAG Chatbot
   "@ | Out-File -FilePath .env -Encoding utf8
   ```

3. **Ejecuta la aplicación:**
   ```bash
   python app.py
   ```

4. **Espera a que cargue el modelo de embeddings** (puede tardar 30-60 segundos la primera vez):
   ```
   Cargando modelo de embeddings...
   Modelo de embeddings cargado!
   * Running on http://127.0.0.1:5000
   ```

5. **Abre en el navegador:**
   ```
   http://localhost:5000
   ```

## Nota Importante

La primera vez que ejecutes la aplicación, descargará el modelo de embeddings `all-MiniLM-L6-v2` (~80MB). Esto solo sucede una vez.

## Si Aún Hay Errores

Si ves algún otro error, ejecuta:
```bash
pip install -r requirements.txt --upgrade
```

Esto reinstalará todas las dependencias con las versiones correctas.

