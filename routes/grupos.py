from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from functools import wraps
from models import get_db_connection

grupos_bp = Blueprint('grupos_bp', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('rol') != 'admin':
            flash('Acceso no autorizado', 'danger')
            return redirect(url_for('auth_bp.login'))
        return f(*args, **kwargs)
    return decorated_function

@grupos_bp.route('/grupos')
@admin_required
def grupos():
    """Lista de grupos"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT g.*, n.Nombre_Nivel 
        FROM grupos g
        LEFT JOIN niveles n ON g.ID_Nivel = n.ID_Nivel
        ORDER BY n.Nombre_Nivel, g.Nombre_Grupo
    """)
    
    grupos = cursor.fetchall()
    
    # Obtener niveles para el formulario
    cursor.execute("SELECT * FROM niveles ORDER BY ID_Nivel")
    niveles = cursor.fetchall()
    
    conn.close()
    
    return render_template('grupos.html', grupos=grupos, niveles=niveles)

@grupos_bp.route('/grupos/crear', methods=['POST'])
@admin_required
def crear_grupo():
    """Crear un nuevo grupo"""
    nombre_grupo = request.form.get('nombre_grupo')
    id_nivel = request.form.get('id_nivel')
    
    if not nombre_grupo:
        flash('El nombre del grupo es requerido', 'danger')
        return redirect(url_for('grupos_bp.grupos'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO grupos (Nombre_Grupo, ID_Nivel)
            VALUES (%s, %s)
        """, (nombre_grupo, id_nivel if id_nivel else None))
        
        conn.commit()
        flash(f'Grupo "{nombre_grupo}" creado exitosamente', 'success')
    except Exception as e:
        flash(f'Error al crear el grupo: {str(e)}', 'danger')
    finally:
        conn.close()
    
    return redirect(url_for('grupos_bp.grupos'))

@grupos_bp.route('/grupos/editar/<int:id_grupo>', methods=['POST'])
@admin_required
def editar_grupo(id_grupo):
    """Editar un grupo existente"""
    nombre_grupo = request.form.get('nombre_grupo')
    id_nivel = request.form.get('id_nivel')
    
    if not nombre_grupo:
        flash('El nombre del grupo es requerido', 'danger')
        return redirect(url_for('grupos_bp.grupos'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE grupos 
            SET Nombre_Grupo = %s, ID_Nivel = %s
            WHERE ID_Grupo = %s
        """, (nombre_grupo, id_nivel if id_nivel else None, id_grupo))
        
        conn.commit()
        flash(f'Grupo actualizado exitosamente', 'success')
    except Exception as e:
        flash(f'Error al actualizar el grupo: {str(e)}', 'danger')
    finally:
        conn.close()
    
    return redirect(url_for('grupos_bp.grupos'))

@grupos_bp.route('/grupos/eliminar/<int:id_grupo>', methods=['POST'])
@admin_required
def eliminar_grupo(id_grupo):
    """Eliminar un grupo"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar si el grupo tiene estudiantes
    cursor.execute("SELECT COUNT(*) as count FROM estudiantes WHERE ID_Grupo = %s", (id_grupo,))
    estudiantes_count = cursor.fetchone()['count']
    
    if estudiantes_count > 0:
        flash(f'No se puede eliminar el grupo porque tiene {estudiantes_count} estudiantes asignados', 'danger')
        conn.close()
        return redirect(url_for('grupos_bp.grupos'))
    
    try:
        cursor.execute("DELETE FROM grupos WHERE ID_Grupo = %s", (id_grupo,))
        conn.commit()
        flash('Grupo eliminado exitosamente', 'success')
    except Exception as e:
        flash(f'Error al eliminar el grupo: {str(e)}', 'danger')
    finally:
        conn.close()
    
    return redirect(url_for('grupos_bp.grupos'))
