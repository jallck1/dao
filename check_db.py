import sqlite3
import os

def check_database():
    db_path = 'data/database.sqlite'
    
    if not os.path.exists(db_path):
        print(f"Error: No se encontró la base de datos en {os.path.abspath(db_path)}")
        return
    
    try:
        print(f"Conectando a la base de datos: {os.path.abspath(db_path)}")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Verificar tablas existentes
        print("\n=== Tablas en la base de datos ===")
        c.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = c.fetchall()
        
        if not tables:
            print("No se encontraron tablas en la base de datos.")
        else:
            for table in tables:
                print(f"- {table['name']}")
        
        # Verificar PDFs cargados
        print("\n=== PDFs cargados ===")
        c.execute("SELECT id, filename, total_pages FROM pdf_files;")
        pdfs = c.fetchall()
        
        if not pdfs:
            print("No se encontraron PDFs en la base de datos.")
        else:
            for pdf in pdfs:
                print(f"\nID: {pdf['id']}")
                print(f"Archivo: {pdf['filename']}")
                print(f"Páginas totales: {pdf['total_pages']}")
                
                # Contar páginas
                c.execute("SELECT COUNT(*) as count FROM pdf_pages WHERE pdf_id = ?", (pdf['id'],))
                page_count = c.fetchone()['count']
                print(f"Páginas en la base de datos: {page_count}")
                
                # Mostrar primeras páginas
                if page_count > 0:
                    c.execute("SELECT page_number, LENGTH(text_content) as text_length FROM pdf_pages WHERE pdf_id = ? ORDER BY page_number LIMIT 3", 
                             (pdf['id'],))
                    pages = c.fetchall()
                    print("\nPrimeras páginas:")
                    for page in pages:
                        print(f"  - Página {page['page_number']}: {page['text_length']} caracteres")
                
                # Contar embeddings
                c.execute("SELECT COUNT(*) as count FROM embeddings WHERE pdf_id = ?", (pdf['id'],))
                emb_count = c.fetchone()['count']
                print(f"Embeddings generados: {emb_count}")
                
                # Verificar imágenes
                c.execute("SELECT COUNT(*) as count FROM pdf_images WHERE pdf_id = ?", (pdf['id'],))
                img_count = c.fetchone()['count']
                print(f"Imágenes extraídas: {img_count}")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Error de SQLite: {str(e)}")
    except Exception as e:
        print(f"Error inesperado: {str(e)}")

if __name__ == '__main__':
    print("=== Verificación de la base de datos RAG Chatbot ===")
    check_database()
    input("\nPresiona Enter para salir...")
