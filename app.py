from flask import Flask, render_template, request, jsonify, send_file
import os
import sqlite3
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
import json
from dotenv import load_dotenv
import requests
from sentence_transformers import SentenceTransformer
import PyPDF2
import fitz  # PyMuPDF
from PIL import Image
import io

load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'data/uploads'
app.config['IMAGES_FOLDER'] = 'data/images'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

# Crear directorios necesarios
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['IMAGES_FOLDER'], exist_ok=True)
os.makedirs('data', exist_ok=True)

# Inicializar modelos
print("Cargando modelo de embeddings...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
print("Modelo de embeddings cargado!")

# Configuración de OpenRouter
# IMPORTANTE: la API key ya no se guarda en el código. Se debe definir como variable de entorno OPENROUTER_API_KEY.
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
MODEL_NAME = "openai/gpt-3.5-turbo"  # Modelo válido de OpenRouter
API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_URL = os.getenv('OPENROUTER_API_URL', API_URL)

# Base de datos
def init_db():
    conn = sqlite3.connect('data/database.sqlite')
    c = conn.cursor()
    
    # Tabla de PDFs
    c.execute('''
        CREATE TABLE IF NOT EXISTS pdf_files (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER,
            uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP,
            total_pages INTEGER DEFAULT 0
        )
    ''')
    
    # Tabla de páginas
    c.execute('''
        CREATE TABLE IF NOT EXISTS pdf_pages (
            id TEXT PRIMARY KEY,
            pdf_id TEXT NOT NULL,
            page_number INTEGER NOT NULL,
            text_content TEXT,
            FOREIGN KEY (pdf_id) REFERENCES pdf_files(id) ON DELETE CASCADE
        )
    ''')
    
    # Tabla de imágenes
    c.execute('''
        CREATE TABLE IF NOT EXISTS pdf_images (
            id TEXT PRIMARY KEY,
            pdf_id TEXT NOT NULL,
            page_number INTEGER NOT NULL,
            image_path TEXT,
            image_index INTEGER,
            FOREIGN KEY (pdf_id) REFERENCES pdf_files(id) ON DELETE CASCADE
        )
    ''')
    
    # Tabla de embeddings
    c.execute('''
        CREATE TABLE IF NOT EXISTS embeddings (
            id TEXT PRIMARY KEY,
            pdf_id TEXT NOT NULL,
            page_id TEXT,
            chunk_text TEXT NOT NULL,
            embedding TEXT NOT NULL,
            chunk_index INTEGER,
            FOREIGN KEY (pdf_id) REFERENCES pdf_files(id) ON DELETE CASCADE,
            FOREIGN KEY (page_id) REFERENCES pdf_pages(id) ON DELETE CASCADE
        )
    ''')
    
    # Tabla de sesiones
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id TEXT PRIMARY KEY,
            title TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de mensajes
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            image_ids TEXT,
            pdf_references TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
        )
    ''')
    
    # Índices
    c.execute('CREATE INDEX IF NOT EXISTS idx_embeddings_pdf ON embeddings(pdf_id)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_images_pdf ON pdf_images(pdf_id)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_pages_pdf ON pdf_pages(pdf_id)')
    
    conn.commit()
    conn.close()

init_db()

def get_db():
    conn = sqlite3.connect('data/database.sqlite')
    conn.row_factory = sqlite3.Row
    return conn

def cosine_similarity(vec1, vec2):
    import numpy as np
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(dot_product / (norm1 * norm2))

def chunk_text(text, chunk_size=500, overlap=50):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload-pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.pdf'):
        return jsonify({'error': 'File must be a PDF'}), 400
    
    pdf_id = str(uuid.uuid4())
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{pdf_id}_{filename}')
    file.save(file_path)
    
    try:
        # Extraer texto
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            num_pages = len(pdf_reader.pages)
            
            conn = get_db()
            c = conn.cursor()
            
            # Guardar PDF
            c.execute('''
                INSERT INTO pdf_files (id, filename, file_path, file_size, total_pages)
                VALUES (?, ?, ?, ?, ?)
            ''', (pdf_id, filename, file_path, os.path.getsize(file_path), num_pages))
            
            # Extraer texto de cada página
            for page_num in range(num_pages):
                try:
                    page = pdf_reader.pages[page_num]
                    
                    # Intentar extraer texto de diferentes maneras
                    text = ''
                    
                    # Método 1: Extracción estándar
                    text = page.extract_text() or ''
                    
                    # Si no se extrajo suficiente texto, intentar con parámetros alternativos
                    if len(text.strip()) < 10:  # Si el texto es muy corto
                        # Intentar con extracción más agresiva
                        text = page.extract_text(x_tolerance=3, y_tolerance=3) or ''
                    
                    # Si aún no hay suficiente texto, intentar extraer por palabras
                    if len(text.strip()) < 10:
                        words = page.extract_words()
                        if words:
                            text = ' '.join(word['text'] for word in words)
                    
                    # Si aún no hay texto, registrar una advertencia
                    if not text.strip():
                        print(f"Advertencia: No se pudo extraer texto de la página {page_num + 1}")
                        text = f"[Contenido no extraíble de la página {page_num + 1}]"
                    
                    # Insertar en la base de datos
                    page_id = str(uuid.uuid4())
                    c.execute('''
                        INSERT INTO pdf_pages (id, pdf_id, page_number, text_content)
                        VALUES (?, ?, ?, ?)
                    ''', (page_id, pdf_id, page_num + 1, text))
                    
                    # Crear embeddings solo si hay suficiente texto
                    if len(text.strip()) > 10:
                        chunks = chunk_text(text)
                        for i, chunk in enumerate(chunks):
                            try:
                                embedding = embedding_model.encode(chunk)
                                embedding_json = json.dumps(embedding.tolist())
                                embedding_id = str(uuid.uuid4())
                                c.execute('''
                                    INSERT INTO embeddings (id, pdf_id, page_id, chunk_text, embedding, chunk_index)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                ''', (embedding_id, pdf_id, page_id, chunk, embedding_json, i))
                            except Exception as e:
                                print(f"Error al crear embedding para el chunk {i} de la página {page_num + 1}: {str(e)}")
                    
                    # Mostrar progreso cada 10 páginas
                    if (page_num + 1) % 10 == 0:
                        print(f"Procesadas {page_num + 1}/{num_pages} páginas...")
                        
                except Exception as e:
                    print(f"Error al procesar la página {page_num + 1}: {str(e)}")
                    continue
                
                # Crear embeddings
                chunks = chunk_text(text)
                for i, chunk in enumerate(chunks):
                    embedding = embedding_model.encode(chunk)
                    embedding_json = json.dumps(embedding.tolist())
                    
                    embedding_id = str(uuid.uuid4())
                    c.execute('''
                        INSERT INTO embeddings (id, pdf_id, page_id, chunk_text, embedding, chunk_index)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (embedding_id, pdf_id, page_id, chunk, embedding_json, i))
            
            # Extraer imágenes usando PyMuPDF
            image_count = 0
            try:
                # Abrir el PDF con PyMuPDF
                pdf_document = fitz.open(file_path)
                
                for page_num in range(len(pdf_document)):
                    page = pdf_document.load_page(page_num)
                    image_list = page.get_images(full=True)
                    
                    if image_list:
                        for img_index, img in enumerate(image_list):
                            xref = img[0]
                            base_image = pdf_document.extract_image(xref)
                            image_data = base_image["image"]
                            
                            # Crear directorio si no existe
                            image_dir = os.path.join(app.config['IMAGES_FOLDER'], pdf_id)
                            os.makedirs(image_dir, exist_ok=True)
                            
                            # Guardar la imagen
                            image_path = os.path.join(image_dir, f'page_{page_num + 1}_img_{img_index + 1}.png')
                            with open(image_path, "wb") as img_file:
                                img_file.write(image_data)
                            
                            # Guardar en la base de datos
                            image_id = str(uuid.uuid4())
                            c.execute('''
                                INSERT INTO pdf_images (id, pdf_id, page_number, image_path, image_index)
                                VALUES (?, ?, ?, ?, ?)
                            ''', (image_id, pdf_id, page_num + 1, image_path, image_count))
                            image_count += 1
                            
                            print(f"Imagen {img_index + 1} extraída de la página {page_num + 1}")
                    
                    # Si no hay imágenes en la página, intentar renderizar la página como imagen
                    elif page.get_text().strip() == '':  # Si la página está vacía de texto
                        pix = page.get_pixmap()
                        image_dir = os.path.join(app.config['IMAGES_FOLDER'], pdf_id)
                        os.makedirs(image_dir, exist_ok=True)
                        image_path = os.path.join(image_dir, f'page_{page_num + 1}_render.png')
                        pix.save(image_path)
                        
                        # Guardar en la base de datos
                        image_id = str(uuid.uuid4())
                        c.execute('''
                            INSERT INTO pdf_images (id, pdf_id, page_number, image_path, image_index)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (image_id, pdf_id, page_num + 1, image_path, image_count))
                        image_count += 1
                        
                        print(f"Página {page_num + 1} guardada como imagen")
                
                pdf_document.close()
                print(f"Total de imágenes extraídas: {image_count}")
                
            except Exception as e:
                print(f"Advertencia: Error al extraer imágenes: {str(e)}")
                print("La aplicación continuará funcionando, pero sin extracción de imágenes.")
                # Continuar sin imágenes - no es crítico
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'pdfId': pdf_id,
                'pages': num_pages,
                'images': image_count
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/list-pdfs', methods=['GET'])
def list_pdfs():
    conn = get_db()
    c = conn.cursor()
    
    c.execute('''
        SELECT 
            id, filename, file_size, uploaded_at, total_pages,
            (SELECT COUNT(*) FROM pdf_images WHERE pdf_id = pdf_files.id) as image_count
        FROM pdf_files
        ORDER BY uploaded_at DESC
    ''')
    
    pdfs = []
    for row in c.fetchall():
        pdfs.append({
            'id': row['id'],
            'filename': row['filename'],
            'file_size': row['file_size'],
            'uploaded_at': row['uploaded_at'],
            'total_pages': row['total_pages'],
            'image_count': row['image_count']
        })
    
    conn.close()
    return jsonify({'pdfs': pdfs})

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message')
    session_id = data.get('sessionId')
    pdf_id = data.get('pdfId')
    
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    
    conn = get_db()
    c = conn.cursor()
    
    # Crear sesión si no existe
    if not session_id:
        session_id = str(uuid.uuid4())
        c.execute('''
            INSERT INTO chat_sessions (id, title, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        ''', (session_id, message[:50], datetime.now().isoformat(), datetime.now().isoformat()))
    
    # Guardar mensaje del usuario
    user_message_id = str(uuid.uuid4())
    c.execute('''
        INSERT INTO messages (id, session_id, role, content, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_message_id, session_id, 'user', message, datetime.now().isoformat()))
    
    # Buscar contexto relevante
    context = None
    if pdf_id:
        # Generar embedding de la pregunta
        query_embedding = embedding_model.encode(message)
        
        # Buscar chunks similares
        c.execute('''
            SELECT e.id, e.chunk_text, e.embedding, p.page_number, e.pdf_id
            FROM embeddings e
            JOIN pdf_pages p ON e.page_id = p.id
            WHERE e.pdf_id = ?
        ''', (pdf_id,))
        
        chunks = []
        for row in c.fetchall():
            try:
                chunk_embedding = json.loads(row['embedding'])
                similarity = cosine_similarity(query_embedding, chunk_embedding)
                chunks.append({
                    'text': row['chunk_text'],
                    'similarity': similarity,
                    'page_number': row['page_number']
                })
            except Exception as e:
                print(f"Error procesando chunk: {e}")
                continue
        
        chunks.sort(key=lambda x: x['similarity'], reverse=True)
        top_chunks = chunks[:3]
        
        if top_chunks:
            relevant_text = '\n\n'.join([c['text'] for c in top_chunks])
            page_numbers = list(set([c['page_number'] for c in top_chunks]))
            
            # Obtener imágenes
            if page_numbers:
                placeholders = ','.join('?' * len(page_numbers))
                c.execute(f'''
                    SELECT id, page_number, image_path
                    FROM pdf_images
                    WHERE pdf_id = ? AND page_number IN ({placeholders})
                ''', [pdf_id] + page_numbers)
            else:
                c.execute('''
                    SELECT id, page_number, image_path
                    FROM pdf_images
                    WHERE pdf_id = ?
                ''', (pdf_id,))
            
            images = []
            for row in c.fetchall():
                # Normalizar ruta para que sea relativa a IMAGES_FOLDER
                raw_path = row['image_path'] or ''
                # Usar separadores tipo Unix para simplificar
                rel_path = raw_path.replace('\\', '/')
                # Quitar prefijo data/images/ si viene incluido
                if rel_path.startswith('data/images/'):
                    rel_path = rel_path[len('data/images/'):]
                images.append({
                    'pageNumber': row['page_number'],
                    'imagePath': rel_path
                })
            
            context = {
                'relevantText': relevant_text,
                'images': images,
                'pdfReferences': [{'pdfId': pdf_id, 'pageNumber': pn} for pn in page_numbers]
            }
    
    # Obtener historial
    c.execute('''
        SELECT role, content
        FROM messages
        WHERE session_id = ?
        ORDER BY created_at ASC
    ''', (session_id,))
    
    history = []
    for row in c.fetchall():
        history.append({
            'role': row['role'],
            'content': row['content']
        })
    
    # Preparar mensaje para OpenRouter
    system_message = {
        'role': 'system',
        'content': '''Eres un asistente inteligente especializado en analizar documentos PDF. 
Cuando respondas preguntas sobre documentos:
- Si hay contexto relevante proporcionado, úsalo para responder.
- Si hay imágenes asociadas, menciona que están disponibles y en qué página del PDF.
- Sé preciso y cita las páginas cuando sea relevante.
- Si no tienes información suficiente en el contexto, indícalo claramente.'''
    }
    
    user_content = message
    if context and context.get('relevantText'):
        user_content = f"Contexto del documento:\n{context['relevantText']}\n\nPregunta del usuario: {message}"
        if context.get('pdfReferences'):
            refs = ', '.join([f"Página {r['pageNumber']}" for r in context['pdfReferences']])
            user_content += f"\n\nReferencias: {refs}"
        if context.get('images'):
            img_refs = ', '.join([f"Imagen en página {img['pageNumber']}" for img in context['images']])
            user_content += f"\n\nImágenes disponibles: {img_refs}"
    
    messages = [system_message] + [
        {'role': msg['role'], 'content': msg['content']} 
        for msg in history[:-1]
    ] + [{'role': 'user', 'content': user_content}]
    
    # Llamar a OpenRouter usando requests
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": os.getenv('OPENROUTER_HTTP_REFERER', 'http://localhost:5000'),
            "X-Title": os.getenv('OPENROUTER_APP_NAME', 'RAG Chatbot'),
        }
        
        data = {
            "model": MODEL_NAME,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        response = requests.post(API_URL, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        try:
            response_data = response.json()
            if 'choices' in response_data and len(response_data['choices']) > 0:
                assistant_response = response_data['choices'][0]['message']['content']
            else:
                assistant_response = "No se pudo obtener una respuesta del modelo."
        except ValueError as e:
            error_msg = f"Error al procesar la respuesta de la API: {str(e)}\nRespuesta: {response.text[:200]}"
            assistant_response = error_msg
        
        # Guardar respuesta
        assistant_message_id = str(uuid.uuid4())
        # Guardar solo la ruta relativa de las imágenes, compatible con /api/image
        image_ids = ','.join([img['imagePath'] for img in context['images']]) if context and context.get('images') else None
        pdf_refs = ','.join([f"{r['pdfId']}:{r['pageNumber']}" for r in context['pdfReferences']]) if context and context.get('pdfReferences') else None
        
        c.execute('''
            INSERT INTO messages (id, session_id, role, content, image_ids, pdf_references, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (assistant_message_id, session_id, 'assistant', assistant_response, image_ids, pdf_refs, datetime.now().isoformat()))
        
        c.execute('''
            UPDATE chat_sessions
            SET updated_at = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), session_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'response': assistant_response,
            'sessionId': session_id,
            'context': {
                'images': context['images'] if context else [],
                'pdfReferences': context['pdfReferences'] if context else []
            } if context else None
        })
    except requests.exceptions.RequestException as e:
        if 'conn' in locals():
            conn.close()
        import traceback
        error_details = traceback.format_exc()
        print(f"Error en la API de OpenRouter: {error_details}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                print(f"Respuesta de error de la API: {error_data}")
            except:
                print(f"Respuesta de error (texto): {e.response.text}")
        return jsonify({'error': f'Error al comunicarse con la API: {str(e)}'}), 500
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        import traceback
        error_details = traceback.format_exc()
        print(f"Error en /api/chat: {error_details}")
        return jsonify({'error': f'Error al procesar el chat: {str(e)}'}), 500

@app.route('/api/history', methods=['GET'])
def history():
    session_id = request.args.get('sessionId')
    conn = get_db()
    c = conn.cursor()
    
    if session_id:
        c.execute('''
            SELECT id, role, content, image_ids, pdf_references, created_at
            FROM messages
            WHERE session_id = ?
            ORDER BY created_at ASC
        ''', (session_id,))
        
        messages = []
        for row in c.fetchall():
            messages.append({
                'id': row['id'],
                'role': row['role'],
                'content': row['content'],
                'imageIds': row['image_ids'],
                'pdfReferences': row['pdf_references'],
                'createdAt': row['created_at']
            })
        
        c.execute('SELECT id, title, created_at, updated_at FROM chat_sessions WHERE id = ?', (session_id,))
        session_row = c.fetchone()
        session = {
            'id': session_row['id'],
            'title': session_row['title'],
            'created_at': session_row['created_at'],
            'updated_at': session_row['updated_at']
        } if session_row else None
        
        conn.close()
        return jsonify({'session': session, 'messages': messages})
    else:
        c.execute('SELECT id, title, created_at, updated_at FROM chat_sessions ORDER BY updated_at DESC')
        sessions = []
        for row in c.fetchall():
            sessions.append({
                'id': row['id'],
                'title': row['title'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            })
        conn.close()
        return jsonify({'sessions': sessions})

@app.route('/api/recommended-questions', methods=['GET'])
def recommended_questions():
    session_id = request.args.get('sessionId')
    pdf_id = request.args.get('pdfId')
    limit = int(request.args.get('limit', 5))
    
    questions = []
    
    if pdf_id:
        questions = [
            '¿Cuál es el tema principal de este documento?',
            '¿Puedes resumir las ideas clave?',
            '¿Qué información importante contiene?',
            '¿Hay gráficos o imágenes que deba revisar?',
            '¿Puedes explicar el contenido de la primera página?'
        ]
    else:
        questions = [
            '¿Qué documentos has cargado?',
            '¿Cómo funciona este sistema?',
            '¿Puedes ayudarme a analizar un documento?'
        ]
    
    return jsonify({'questions': questions[:limit]})

@app.route('/api/image', methods=['GET'])
def get_image():
    # Obtener la ruta de la imagen de manera segura
    image_path = request.args.get('path')
    if not image_path:
        return jsonify({'error': 'Se requiere la ruta de la imagen'}), 400
    
    # Asegurarse de que la ruta esté dentro del directorio permitido
    upload_dir = os.path.abspath(app.config['IMAGES_FOLDER'])
    try:
        image_path = os.path.abspath(os.path.join(upload_dir, image_path))
        if not image_path.startswith(upload_dir):
            return jsonify({'error': 'Ruta de imagen no permitida'}), 403
    except Exception as e:
        return jsonify({'error': 'Ruta de imagen inválida'}), 400
    
    # Verificar que el archivo exista
    if not os.path.isfile(image_path):
        return jsonify({'error': 'Imagen no encontrada'}), 404
    
    # Determinar el tipo MIME basado en la extensión del archivo
    mimetype = 'application/octet-stream'
    if image_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
        mimetype = f'image/{image_path.split(".")[-1].lower()}'
    
    try:
        # Enviar el archivo con el tipo MIME correcto
        return send_file(
            image_path,
            mimetype=mimetype,
            as_attachment=False,
            download_name=os.path.basename(image_path)
        )
    except Exception as e:
        return jsonify({'error': f'Error al cargar la imagen: {str(e)}'}), 500

    return send_file(image_path, mimetype='image/png')

@app.route('/api/ai-chat', methods=['POST'])
def ai_chat():
    """Chat IA con acceso a la base de datos"""
    data = request.json
    message = data.get('message')
    
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    
    conn = get_db()
    c = conn.cursor()
    
    # Obtener información de la base de datos
    db_info = []
    
    # Información de PDFs
    c.execute('SELECT COUNT(*) as count FROM pdf_files')
    pdf_count = c.fetchone()['count']
    
    # Información de sesiones
    c.execute('SELECT COUNT(*) as count FROM chat_sessions')
    session_count = c.fetchone()['count']
    
    # Información de mensajes
    c.execute('SELECT COUNT(*) as count FROM messages')
    message_count = c.fetchone()['count']
    
    # Últimos PDFs cargados
    c.execute('SELECT filename, uploaded_at, total_pages FROM pdf_files ORDER BY uploaded_at DESC LIMIT 5')
    recent_pdfs = [dict(row) for row in c.fetchall()]
    
    # Últimas sesiones
    c.execute('SELECT id, title, updated_at FROM chat_sessions ORDER BY updated_at DESC LIMIT 5')
    recent_sessions = [dict(row) for row in c.fetchall()]
    
    # Estadísticas de embeddings
    c.execute('SELECT COUNT(*) as count FROM embeddings')
    embedding_count = c.fetchone()['count']
    
    db_info_text = f"""
Información de la Base de Datos:
- Total de PDFs: {pdf_count}
- Total de sesiones de chat: {session_count}
- Total de mensajes: {message_count}
- Total de embeddings: {embedding_count}

Últimos PDFs cargados:
{chr(10).join([f"- {pdf['filename']} ({pdf['total_pages']} páginas, cargado: {pdf['uploaded_at']})" for pdf in recent_pdfs])}

Últimas sesiones:
{chr(10).join([f"- {session['title'] or 'Sin título'} (ID: {session['id'][:8]}..., actualizada: {session['updated_at']})" for session in recent_sessions])}
"""
    
    conn.close()
    
    # Preparar mensaje para Grok
    system_message = {
        'role': 'system',
        'content': '''Eres un asistente IA especializado en analizar y responder preguntas sobre la base de datos del sistema RAG Chatbot.
Puedes responder preguntas sobre:
- Los PDFs cargados
- Las sesiones de chat
- Los mensajes almacenados
- Estadísticas del sistema
- Cualquier información relacionada con la base de datos

Sé preciso, útil y amigable en tus respuestas.'''
    }
    
    user_message = f"{db_info_text}\n\nPregunta del usuario: {message}"
    
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": os.getenv('OPENROUTER_HTTP_REFERER', 'http://localhost:5000'),
            "X-Title": os.getenv('OPENROUTER_APP_NAME', 'RAG Chatbot'),
        }
        
        data = {
            "model": MODEL_NAME,
            "messages": [
                system_message,
                {'role': 'user', 'content': user_message}
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        api_response = requests.post(API_URL, headers=headers, json=data)
        api_response.raise_for_status()
        response_data = api_response.json()
        
        if 'choices' in response_data and len(response_data['choices']) > 0:
            ai_response = response_data['choices'][0]['message']['content']
        else:
            ai_response = "No se pudo obtener una respuesta del modelo."
        
        return jsonify({
            'response': ai_response,
            'dbInfo': {
                'pdfCount': pdf_count,
                'sessionCount': session_count,
                'messageCount': message_count,
                'embeddingCount': embedding_count
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Para despliegue en Cloud Run / contenedores: usar el puerto de la variable de entorno PORT (por defecto 8080)
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)

