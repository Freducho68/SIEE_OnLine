from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
from functools import wraps
from models import get_db_connection

carga_bp = Blueprint('carga_bp', __name__)


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('rol') != 'admin':
            flash('Acceso no autorizado', 'danger')
            return redirect(url_for('auth_bp.login'))
        return f(*args, **kwargs)
    return decorated_function


@carga_bp.route('/carga')
@admin_required
def carga():
    """Lista de cargas académicas"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # INYECCIÓN DEV: Ordenamos la lista maestra por a.Orden ASC
    cursor.execute(
        """
        SELECT c.ID_Carga,
               d.ID_Docente, d.Nombres as Docente_Nombres, d.Apellidos as Docente_Apellidos,
               m.ID_Materia, m.Nombre_Materia,
               g.ID_Grupo, g.Nombre_Grupo,
               n.Nombre_Nivel
        FROM cargas_academicas c
        JOIN docentes d ON c.ID_Docente = d.ID_Docente
        JOIN materias m ON c.ID_Materia = m.ID_Materia
        LEFT JOIN areas a ON m.ID_Area = a.ID_Area
        JOIN grupos g ON c.ID_Grupo = g.ID_Grupo
        LEFT JOIN niveles n ON g.ID_Nivel = n.ID_Nivel
        ORDER BY n.Nombre_Nivel, g.Nombre_Grupo, a.Orden ASC, m.Nombre_Materia ASC
        """
    )
    cargas = cursor.fetchall()

    cursor.execute('SELECT ID_Docente, Nombres, Apellidos FROM docentes ORDER BY Apellidos, Nombres')
    docentes = cursor.fetchall()

    # INYECCIÓN DEV: El desplegable general también respeta el orden de las áreas
    cursor.execute(
        """
        SELECT m.ID_Materia, m.Nombre_Materia 
        FROM materias m
        LEFT JOIN areas a ON m.ID_Area = a.ID_Area
        ORDER BY a.Orden ASC, m.Nombre_Materia ASC
        """
    )
    materias_raw = cursor.fetchall()
    materias = [{'ID_Materia': m['ID_Materia'], 'Nombre_Materia': m['Nombre_Materia']} for m in materias_raw]

    cursor.execute(
        """
        SELECT g.ID_Grupo, g.Nombre_Grupo, n.Nombre_Nivel
        FROM grupos g
        LEFT JOIN niveles n ON g.ID_Nivel = n.ID_Nivel
        ORDER BY n.Nombre_Nivel, g.Nombre_Grupo
        """
    )
    grupos = cursor.fetchall()

    conn.close()
    return render_template('carga.html', cargas=cargas, docentes=docentes, materias=materias, grupos=grupos)


@carga_bp.route('/carga/crear', methods=['POST'])
@admin_required
def crear_carga():
    """Crear una nueva carga académica"""
    id_docente = request.form.get('id_docente')
    id_materia = request.form.get('id_materia')
    id_grupo = request.form.get('id_grupo')

    if not all([id_docente, id_materia, id_grupo]):
        flash('Todos los campos son requeridos', 'danger')
        return redirect(url_for('carga_bp.carga'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        'SELECT COUNT(*) as count FROM plan_estudios WHERE ID_Grupo = %s AND ID_Materia = %s',
        (id_grupo, id_materia),
    )
    if cursor.fetchone()['count'] == 0:
        flash('La materia seleccionada no hace parte del plan de estudios de ese grupo', 'danger')
        conn.close()
        return redirect(url_for('carga_bp.carga'))

    cursor.execute(
        'SELECT ID_Carga, ID_Docente FROM cargas_academicas WHERE ID_Materia = %s AND ID_Grupo = %s',
        (id_materia, id_grupo),
    )
    existente = cursor.fetchone()
    if existente:
        if str(existente['ID_Docente']) == str(id_docente):
            flash('Esa carga académica ya existe', 'warning')
        else:
            flash('Esa materia ya tiene un docente asignado en ese grupo. Use la opción de reasignación manual si desea cambiarlo.', 'warning')
        conn.close()
        return redirect(url_for('carga_bp.carga'))

    try:
        cursor.execute(
            'INSERT INTO cargas_academicas (ID_Docente, ID_Materia, ID_Grupo) VALUES (%s, %s, %s)',
            (id_docente, id_materia, id_grupo),
        )
        conn.commit()

        cursor.execute('SELECT Nombres, Apellidos FROM docentes WHERE ID_Docente = %s', (id_docente,))
        docente = cursor.fetchone()
        cursor.execute('SELECT Nombre_Materia FROM materias WHERE ID_Materia = %s', (id_materia,))
        materia = cursor.fetchone()
        cursor.execute('SELECT Nombre_Grupo FROM grupos WHERE ID_Grupo = %s', (id_grupo,))
        grupo = cursor.fetchone()

        flash(
            f'Carga creada: {docente["Nombres"]} {docente["Apellidos"]} - {materia["Nombre_Materia"]} - {grupo["Nombre_Grupo"]}',
            'success',
        )
    except Exception as e:
        flash(f'Error al crear la carga: {str(e)}', 'danger')
    finally:
        conn.close()

    return redirect(url_for('carga_bp.carga'))


@carga_bp.route('/carga/eliminar/<int:id_carga>', methods=['POST'])
@admin_required
def eliminar_carga(id_carga):
    """Eliminar una carga académica"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) as count FROM notas WHERE ID_Carga = %s', (id_carga,))
    notas_count = cursor.fetchone()['count']

    if notas_count > 0:
        flash(f'No se puede eliminar la carga porque tiene {notas_count} nota(s) registrada(s)', 'danger')
        conn.close()
        return redirect(url_for('carga_bp.carga'))

    try:
        cursor.execute('DELETE FROM cargas_academicas WHERE ID_Carga = %s', (id_carga,))
        conn.commit()
        flash('Carga académica eliminada exitosamente', 'success')
    except Exception as e:
        flash(f'Error al eliminar la carga: {str(e)}', 'danger')
    finally:
        conn.close()

    return redirect(url_for('carga_bp.carga'))


@carga_bp.route('/carga/ver_planilla/<int:id_carga>')
@admin_required
def ver_planilla(id_carga):
    return redirect(url_for('planillas_bp.planilla', id_carga=id_carga))


@carga_bp.route('/carga/obtener_materias_por_grupo/<int:id_grupo>')
@admin_required
def obtener_materias_por_grupo(id_grupo):
    """API para obtener materias del plan de estudios del grupo y el estado de asignación."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # INYECCIÓN DEV: El JSON de la petición AJAX ahora devolverá los datos ordenados correctamente
    cursor.execute(
        """
        SELECT pe.ID_Materia,
               m.Nombre_Materia,
               c.ID_Carga,
               d.Nombres AS Docente_Nombres,
               d.Apellidos AS Docente_Apellidos
        FROM plan_estudios pe
        JOIN materias m ON pe.ID_Materia = m.ID_Materia
        LEFT JOIN areas a ON m.ID_Area = a.ID_Area
        LEFT JOIN cargas_academicas c
               ON c.ID_Grupo = pe.ID_Grupo AND c.ID_Materia = pe.ID_Materia
        LEFT JOIN docentes d ON d.ID_Docente = c.ID_Docente
        WHERE pe.ID_Grupo = %s
        ORDER BY a.Orden ASC, m.Nombre_Materia ASC
        """,
        (id_grupo,),
    )
    rows = cursor.fetchall()
    conn.close()

    materias = []
    for m in rows:
        docente_nombre = None
        if m['Docente_Nombres'] and m['Docente_Apellidos']:
            docente_nombre = f"{m['Docente_Nombres']} {m['Docente_Apellidos']}"
        materias.append(
            {
                'ID_Materia': m['ID_Materia'],
                'Nombre_Materia': m['Nombre_Materia'],
                'asignada': bool(m['ID_Carga']),
                'docente': docente_nombre,
            }
        )

    return jsonify(materias)


@carga_bp.route('/carga/reasignar/<int:id_carga>', methods=['POST'])
@admin_required
def reasignar_carga(id_carga):
    """Reasigna manualmente el docente de una carga académica existente."""
    id_docente = request.form.get('id_docente')
    if not id_docente:
        flash('Debe seleccionar un docente para la reasignación', 'danger')
        return redirect(url_for('carga_bp.carga'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT c.ID_Carga, c.ID_Docente,
               m.Nombre_Materia, g.Nombre_Grupo
        FROM cargas_academicas c
        JOIN materias m ON m.ID_Materia = c.ID_Materia
        JOIN grupos g ON g.ID_Grupo = c.ID_Grupo
        WHERE c.ID_Carga = %s
        """,
        (id_carga,),
    )
    carga = cursor.fetchone()

    if not carga:
        conn.close()
        flash('La carga académica no existe', 'danger')
        return redirect(url_for('carga_bp.carga'))

    if str(carga['ID_Docente']) == str(id_docente):
        conn.close()
        flash('La carga ya está asignada a ese docente', 'info')
        return redirect(url_for('carga_bp.carga'))

    cursor.execute('SELECT Nombres, Apellidos FROM docentes WHERE ID_Docente = %s', (id_docente,))
    docente = cursor.fetchone()
    if not docente:
        conn.close()
        flash('El docente seleccionado no existe', 'danger')
        return redirect(url_for('carga_bp.carga'))

    try:
        cursor.execute('UPDATE cargas_academicas SET ID_Docente = %s WHERE ID_Carga = %s', (id_docente, id_carga))
        conn.commit()
        flash(
            f'Reasignación exitosa: {carga["Nombre_Materia"]} - {carga["Nombre_Grupo"]} ahora pertenece a {docente["Nombres"]} {docente["Apellidos"]}.',
            'success',
        )
    except Exception as e:
        flash(f'Error al reasignar la carga: {str(e)}', 'danger')
    finally:
        conn.close()

    return redirect(url_for('carga_bp.carga'))
