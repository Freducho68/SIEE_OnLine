from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from functools import wraps
from models import get_db_connection

asignaturas_bp = Blueprint('asignaturas_bp', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('rol') != 'admin':
            flash('Acceso no autorizado', 'danger')
            return redirect(url_for('auth_bp.login'))
        return f(*args, **kwargs)
    return decorated_function


@asignaturas_bp.route('/asignaturas')
@admin_required
def asignaturas():
    """Lista de asignaturas agrupadas por área"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT m.ID_Materia, m.Nombre_Materia, m.Es_DIM, a.Nombre_Area
        FROM materias m
        LEFT JOIN areas a ON m.ID_Area = a.ID_Area
        ORDER BY a.Nombre_Area, m.Nombre_Materia
    """)
    
    materias = cursor.fetchall()
    conn.close()
    
    asignaturas_por_area = {}
    asignaturas_basica = []
    asignaturas_dim = []
    
    for materia in materias:
        area = materia['Nombre_Area'] or 'Sin área'
        if area not in asignaturas_por_area:
            asignaturas_por_area[area] = []
        asignaturas_por_area[area].append(materia)
        
        if materia['Es_DIM']:
            asignaturas_dim.append(materia)
        else:
            asignaturas_basica.append(materia)
    
    return render_template('asignaturas.html', 
                         asignaturas_por_area=asignaturas_por_area,
                         asignaturas_basica=asignaturas_basica,
                         asignaturas_dim=asignaturas_dim)


@asignaturas_bp.route('/asignaturas/crear', methods=['POST'])
@admin_required
def crear_asignatura():
    """Crear una nueva asignatura"""
    nombre_materia = request.form.get('nombre_materia')
    nombre_area = request.form.get('nombre_area')
    
    if not nombre_materia:
        flash('El nombre de la asignatura es requerido', 'danger')
        return redirect(url_for('asignaturas_bp.asignaturas'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Obtener ID del área
        id_area = None
        if nombre_area:
            cursor.execute("SELECT ID_Area FROM areas WHERE Nombre_Area = %s", (nombre_area,))
            area = cursor.fetchone()
            if area:
                id_area = area['ID_Area']
        
        # Detectar si es DIM
        es_dim = 1 if nombre_materia.upper().startswith('DIM') else 0
        
        cursor.execute("""
            INSERT INTO materias (Nombre_Materia, ID_Area, Es_DIM)
            VALUES (%s, %s, %s)
        """, (nombre_materia, id_area, es_dim))
        
        conn.commit()
        flash(f'Asignatura "{nombre_materia}" creada exitosamente', 'success')
        
    except Exception as e:
        flash(f'Error al crear la asignatura: {str(e)}', 'danger')
    finally:
        conn.close()
    
    return redirect(url_for('asignaturas_bp.asignaturas'))


@asignaturas_bp.route('/asignaturas/editar/<int:id_materia>', methods=['POST'])
@admin_required
def editar_asignatura(id_materia):
    """Editar una asignatura existente"""
    nombre_materia = request.form.get('nombre_materia')
    
    if not nombre_materia:
        flash('El nombre de la asignatura es requerido', 'danger')
        return redirect(url_for('asignaturas_bp.asignaturas'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("UPDATE materias SET Nombre_Materia = %s WHERE ID_Materia = %s", 
                      (nombre_materia, id_materia))
        conn.commit()
        flash(f'Asignatura actualizada exitosamente', 'success')
        
    except Exception as e:
        flash(f'Error al actualizar la asignatura: {str(e)}', 'danger')
    finally:
        conn.close()
    
    return redirect(url_for('asignaturas_bp.asignaturas'))


@asignaturas_bp.route('/asignaturas/eliminar/<int:id_materia>', methods=['POST'])
@admin_required
def eliminar_asignatura(id_materia):
    """Eliminar una asignatura"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar si la materia está en uso
    cursor.execute("SELECT COUNT(*) as count FROM cargas_academicas WHERE ID_Materia = %s", (id_materia,))
    cargas_count = cursor.fetchone()['count']
    
    if cargas_count > 0:
        flash(f'No se puede eliminar la asignatura porque está asignada a {cargas_count} carga(s) académica(s)', 'danger')
        conn.close()
        return redirect(url_for('asignaturas_bp.asignaturas'))
    
    try:
        cursor.execute("DELETE FROM materias WHERE ID_Materia = %s", (id_materia,))
        conn.commit()
        flash('Asignatura eliminada exitosamente', 'success')
        
    except Exception as e:
        flash(f'Error al eliminar la asignatura: {str(e)}', 'danger')
    finally:
        conn.close()
    
    return redirect(url_for('asignaturas_bp.asignaturas'))
