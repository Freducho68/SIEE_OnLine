from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from functools import wraps
from models import get_db_connection

estudiantes_bp = Blueprint('estudiantes_bp', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('rol') != 'admin':
            flash('Acceso no autorizado', 'danger')
            return redirect(url_for('auth_bp.login'))
        return f(*args, **kwargs)
    return decorated_function

@estudiantes_bp.route('/estudiantes')
@admin_required
def estudiantes():
    """Lista de estudiantes"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT e.ID_Estudiante, e.Nombres, e.Apellidos, e.ID_Grupo,
               g.Nombre_Grupo
        FROM estudiantes e
        LEFT JOIN grupos g ON e.ID_Grupo = g.ID_Grupo
        ORDER BY e.Apellidos, e.Nombres
        """
    )
    estudiantes = cursor.fetchall()

    cursor.execute("SELECT ID_Grupo, Nombre_Grupo FROM grupos ORDER BY Nombre_Grupo")
    grupos = cursor.fetchall()

    conn.close()
    return render_template('estudiantes.html', estudiantes=estudiantes, grupos=grupos)

@estudiantes_bp.route('/estudiantes/crear', methods=['POST'])
@admin_required
def crear_estudiante():
    """Crear un nuevo estudiante sin credenciales de acceso."""
    nombres = request.form.get('nombres')
    apellidos = request.form.get('apellidos')
    id_grupo = request.form.get('id_grupo')

    if not nombres or not apellidos:
        flash('Los nombres y apellidos son requeridos', 'danger')
        return redirect(url_for('estudiantes_bp.estudiantes'))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO estudiantes (Nombres, Apellidos, ID_Grupo, ID_Usuario)
            VALUES (%s, %s, %s, NULL)
            """,
            (nombres, apellidos, id_grupo if id_grupo else None),
        )
        conn.commit()
        flash(f'Estudiante "{nombres} {apellidos}" creado exitosamente.', 'success')
    except Exception as e:
        flash(f'Error al crear el estudiante: {str(e)}', 'danger')
    finally:
        conn.close()

    return redirect(url_for('estudiantes_bp.estudiantes'))

@estudiantes_bp.route('/estudiantes/editar/<int:id_estudiante>', methods=['POST'])
@admin_required
def editar_estudiante(id_estudiante):
    """Editar un estudiante existente"""
    nombres = request.form.get('nombres')
    apellidos = request.form.get('apellidos')
    id_grupo = request.form.get('id_grupo')

    if not nombres or not apellidos:
        flash('Los nombres y apellidos son requeridos', 'danger')
        return redirect(url_for('estudiantes_bp.estudiantes'))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            UPDATE estudiantes
            SET Nombres = %s, Apellidos = %s, ID_Grupo = %s
            WHERE ID_Estudiante = %s
            """,
            (nombres, apellidos, id_grupo if id_grupo else None, id_estudiante),
        )

        conn.commit()
        flash('Estudiante actualizado exitosamente', 'success')

    except Exception as e:
        flash(f'Error al actualizar el estudiante: {str(e)}', 'danger')
    finally:
        conn.close()

    return redirect(url_for('estudiantes_bp.estudiantes'))

@estudiantes_bp.route('/estudiantes/eliminar/<int:id_estudiante>', methods=['POST'])
@admin_required
def eliminar_estudiante(id_estudiante):
    """Eliminar un estudiante"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM estudiantes WHERE ID_Estudiante = %s", (id_estudiante,))
    estudiante = cursor.fetchone()

    if not estudiante:
        flash('Estudiante no encontrado', 'danger')
        conn.close()
        return redirect(url_for('estudiantes_bp.estudiantes'))

    try:
        cursor.execute("DELETE FROM notas WHERE ID_Estudiante = %s", (id_estudiante,))
        cursor.execute("DELETE FROM indicadores_logro WHERE ID_Estudiante = %s", (id_estudiante,))
        cursor.execute("DELETE FROM observador_estudiante WHERE ID_Estudiante = %s", (id_estudiante,))
        cursor.execute("DELETE FROM observador_anual WHERE ID_Estudiante = %s", (id_estudiante,))
        cursor.execute("DELETE FROM estudiantes WHERE ID_Estudiante = %s", (id_estudiante,))
        conn.commit()
        flash('Estudiante eliminado exitosamente', 'success')

    except Exception as e:
        flash(f'Error al eliminar el estudiante: {str(e)}', 'danger')
    finally:
        conn.close()

    return redirect(url_for('estudiantes_bp.estudiantes'))

@estudiantes_bp.route('/estudiantes/ver_boletin/<int:id_estudiante>')
@admin_required
def ver_boletin(id_estudiante):
    """Redirigir al boletín del estudiante"""
    return redirect(url_for('boletin_bp.boletin', id_estudiante=id_estudiante))
