from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from functools import wraps
from models import get_db_connection
from werkzeug.security import generate_password_hash

docentes_bp = Blueprint('docentes_bp', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('rol') != 'admin':
            flash('Acceso no autorizado', 'danger')
            return redirect(url_for('auth_bp.login'))
        return f(*args, **kwargs)
    return decorated_function


@docentes_bp.route('/docentes')
@admin_required
def docentes():
    """Lista de docentes"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT d.*, u.Usuario 
        FROM docentes d
        LEFT JOIN usuarios u ON d.ID_Usuario = u.ID_Usuario
    """)
    
    docentes = cursor.fetchall()
    conn.close()
    
    return render_template('docentes.html', docentes=docentes)


@docentes_bp.route('/docentes/crear', methods=['POST'])
@admin_required
def crear_docente():
    """Crear un nuevo docente"""
    nombres = request.form.get('nombres')
    apellidos = request.form.get('apellidos')
    email = request.form.get('email')
    
    if not nombres or not apellidos:
        flash('Los nombres y apellidos son requeridos', 'danger')
        return redirect(url_for('docentes_bp.docentes'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Crear usuario para el docente
        usuario = f"doc_{nombres.lower().replace(' ', '')}_{apellidos.lower().replace(' ', '')}"
        contador = 1
        usuario_original = usuario
        while True:
            cursor.execute("SELECT ID_Usuario FROM usuarios WHERE Usuario = %s", (usuario,))
            if not cursor.fetchone():
                break
            usuario = f"{usuario_original}{contador}"
            contador += 1
        
        contrasena_hash = generate_password_hash('123456')
        
        cursor.execute("""
            INSERT INTO usuarios (Usuario, Contrasena, Rol)
            VALUES (%s, %s, 'docente')
        """, (usuario, contrasena_hash))
        
        id_usuario = cursor.lastrowid
        
        # Insertar docente
        cursor.execute("""
            INSERT INTO docentes (Nombres, Apellidos, ID_Usuario)
            VALUES (%s, %s, %s)
        """, (nombres, apellidos, id_usuario))
        
        conn.commit()
        flash(f'Docente "{nombres} {apellidos}" creado exitosamente. Usuario: {usuario} / Contraseña: 123456', 'success')
        
    except Exception as e:
        flash(f'Error al crear el docente: {str(e)}', 'danger')
    finally:
        conn.close()
    
    return redirect(url_for('docentes_bp.docentes'))


@docentes_bp.route('/docentes/editar/<int:id_docente>', methods=['POST'])
@admin_required
def editar_docente(id_docente):
    """Editar un docente existente"""
    nombres = request.form.get('nombres')
    apellidos = request.form.get('apellidos')
    
    if not nombres or not apellidos:
        flash('Los nombres y apellidos son requeridos', 'danger')
        return redirect(url_for('docentes_bp.docentes'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE docentes 
            SET Nombres = %s, Apellidos = %s
            WHERE ID_Docente = %s
        """, (nombres, apellidos, id_docente))
        
        conn.commit()
        flash('Docente actualizado exitosamente', 'success')
        
    except Exception as e:
        flash(f'Error al actualizar el docente: {str(e)}', 'danger')
    finally:
        conn.close()
    
    return redirect(url_for('docentes_bp.docentes'))


@docentes_bp.route('/docentes/eliminar/<int:id_docente>', methods=['POST'])
@admin_required
def eliminar_docente(id_docente):
    """Eliminar un docente"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Obtener el ID de usuario del docente
    cursor.execute("SELECT ID_Usuario FROM docentes WHERE ID_Docente = %s", (id_docente,))
    docente = cursor.fetchone()
    
    if not docente:
        flash('Docente no encontrado', 'danger')
        conn.close()
        return redirect(url_for('docentes_bp.docentes'))
    
    id_usuario = docente['ID_Usuario']
    
    # Verificar si tiene cargas académicas
    cursor.execute("SELECT COUNT(*) as count FROM cargas_academicas WHERE ID_Docente = %s", (id_docente,))
    cargas_count = cursor.fetchone()['count']
    
    if cargas_count > 0:
        flash(f'No se puede eliminar el docente porque tiene {cargas_count} carga(s) académica(s) asignada(s)', 'danger')
        conn.close()
        return redirect(url_for('docentes_bp.docentes'))
    
    try:
        # Eliminar docente
        cursor.execute("DELETE FROM docentes WHERE ID_Docente = %s", (id_docente,))
        
        # Eliminar usuario si existe
        if id_usuario:
            cursor.execute("DELETE FROM usuarios WHERE ID_Usuario = %s", (id_usuario,))
        
        conn.commit()
        flash('Docente eliminado exitosamente', 'success')
        
    except Exception as e:
        flash(f'Error al eliminar el docente: {str(e)}', 'danger')
    finally:
        conn.close()
    
    return redirect(url_for('docentes_bp.docentes'))
