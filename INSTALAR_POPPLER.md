# Instalar Poppler (Opcional)

Poppler es necesario solo para **extraer imágenes** de los PDFs. La aplicación funciona perfectamente sin él, solo que no extraerá imágenes.

## Instalación Rápida

### Opción 1: Con Chocolatey (Recomendado)

Si tienes Chocolatey instalado:

```powershell
choco install poppler
```

### Opción 2: Descarga Manual

1. Descarga Poppler para Windows:
   - https://github.com/oschwartz10612/poppler-windows/releases/
   - Descarga la última versión (ej: `Release-XX.XX.X-X.zip`)

2. Extrae el ZIP en una carpeta (ej: `C:\poppler`)

3. Agrega `C:\poppler\Library\bin` a tu PATH:
   - Presiona `Win + X` → "Sistema"
   - "Configuración avanzada del sistema"
   - "Variables de entorno"
   - En "Variables del sistema", selecciona "Path" → "Editar"
   - "Nuevo" → Agrega `C:\poppler\Library\bin`
   - Acepta todo y reinicia la terminal

4. Verifica la instalación:
   ```bash
   pdftoppm -h
   ```

## Nota Importante

**La aplicación funciona sin Poppler**. Solo no podrá extraer imágenes de los PDFs, pero:
- ✅ Extraerá el texto correctamente
- ✅ Generará embeddings
- ✅ Permitirá hacer preguntas sobre el contenido
- ✅ Todo lo demás funcionará normalmente

Si no instalas Poppler, verás un mensaje de advertencia pero el PDF se cargará correctamente.

