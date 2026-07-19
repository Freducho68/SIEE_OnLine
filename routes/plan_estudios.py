from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
from functools import wraps
from models import get_db_connection

plan_estudios_bp = Blueprint('plan_estudios_bp', __name__)


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('rol') != 'admin':
            flash('Acceso no autorizado', 'danger')
            return redirect(url_for('auth_bp.login'))
        return f(*args, **kwargs)
    return decorated_function


@plan_estudios_bp.route('/plan_estudios')
@admin_required
def plan_estudios():
    """Plan de estudios - Materias por grupo"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT g.ID_Grupo, g.Nombre_Grupo, n.Nombre_Nivel
        FROM grupos g
        LEFT JOIN niveles n ON g.ID_Nivel = n.ID_Nivel
        ORDER BY n.ID_Nivel, g.Nombre_Grupo
        """
    )
    grupos = cursor.fetchall()

    cursor.execute(
        """
        SELECT m.ID_Materia, m.Nombre_Materia, m.Es_DIM, a.Nombre_Area
        FROM materias m
        LEFT JOIN areas a ON m.ID_Area = a.ID_Area
        ORDER BY a.Nombre_Area, m.Nombre_Materia
        """
    )
    materias_raw = cursor.fetchall()
    materias = [
        {
            'ID_Materia': m['ID_Materia'],
            'Nombre_Materia': m['Nombre_Materia'],
            'Es_DIM': m['Es_DIM'],
            'Nombre_Area': m['Nombre_Area'],
        }
        for m in materias_raw
    ]

    conn.close()
    return render_template('plan_estudios.html', grupos=grupos, materias=materias)


@plan_estudios_bp.route('/plan_estudios/materias_por_grupo/<int:id_grupo>')
@admin_required
def materias_por_grupo(id_grupo):
    """API para obtener materias del plan de estudios de un grupo."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT pe.ID_Plan,
               pe.ID_Grupo,
               pe.ID_Materia,
               m.Nombre_Materia,
               m.Es_DIM,
               a.Nombre_Area,
               c.ID_Carga,
               d.Nombres AS Docente_Nombres,
               d.Apellidos AS Docente_Apellidos
        FROM plan_estudios pe
        JOIN materias m ON pe.ID_Materia = m.ID_Materia
        LEFT JOIN areas a ON m.ID_Area = a.ID_Area
        LEFT JOIN cargas_academicas c
               ON c.ID_Grupo = pe.ID_Grupo AND c.ID_Materia = pe.ID_Materia
        LEFT JOIN docentes d ON c.ID_Docente = d.ID_Docente
        WHERE pe.ID_Grupo = %s
        ORDER BY a.Nombre_Area, m.Nombre_Materia
        """,
        (id_grupo,),
    )
    materias_raw = cursor.fetchall()
    conn.close()

    materias = []
    for m in materias_raw:
        docente_nombre = None
        if m['Docente_Nombres'] and m['Docente_Apellidos']:
            docente_nombre = f"{m['Docente_Nombres']} {m['Docente_Apellidos']}"
        materias.append(
            {
                'ID_Plan': m['ID_Plan'],
                'ID_Materia': m['ID_Materia'],
                'Nombre_Materia': m['Nombre_Materia'],
                'Es_DIM': m['Es_DIM'],
                'Nombre_Area': m['Nombre_Area'],
                'ID_Carga': m['ID_Carga'],
                'Docente_Nombre': docente_nombre,
            }
        )
    return jsonify(materias)


@plan_estudios_bp.route('/plan_estudios/materias_disponibles/<int:id_grupo>')
@admin_required
def materias_disponibles(id_grupo):
    """API para obtener materias no asignadas a un grupo"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT ID_Materia FROM plan_estudios WHERE ID_Grupo = %s", (id_grupo,))
    materias_asignadas = [row['ID_Materia'] for row in cursor.fetchall()]

    if materias_asignadas:
        placeholders = ','.join('%s' * len(materias_asignadas))
        cursor.execute(
            f"""
            SELECT m.ID_Materia, m.Nombre_Materia, m.Es_DIM, a.Nombre_Area
            FROM materias m
            LEFT JOIN areas a ON m.ID_Area = a.ID_Area
            WHERE m.ID_Materia NOT IN ({placeholders})
            ORDER BY a.Nombre_Area, m.Nombre_Materia
            """,
            materias_asignadas,
        )
    else:
        cursor.execute(
            """
            SELECT m.ID_Materia, m.Nombre_Materia, m.Es_DIM, a.Nombre_Area
            FROM materias m
            LEFT JOIN areas a ON m.ID_Area = a.ID_Area
            ORDER BY a.Nombre_Area, m.Nombre_Materia
            """
        )

    materias_raw = cursor.fetchall()
    conn.close()

    materias = [
        {
            'ID_Materia': m['ID_Materia'],
            'Nombre_Materia': m['Nombre_Materia'],
            'Es_DIM': m['Es_DIM'],
            'Nombre_Area': m['Nombre_Area'],
        }
        for m in materias_raw
    ]
    return jsonify(materias)


@plan_estudios_bp.route('/plan_estudios/asignar', methods=['POST'])
@admin_required
def asignar_materia():
    """Asignar una materia a un grupo dentro del plan de estudios."""
    id_grupo = request.form.get('id_grupo')
    id_materia = request.form.get('id_materia')

    if not id_grupo or not id_materia:
        flash('Debe seleccionar un grupo y una materia', 'danger')
        return redirect(url_for('plan_estudios_bp.plan_estudios'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) as count FROM plan_estudios WHERE ID_Grupo = %s AND ID_Materia = %s",
        (id_grupo, id_materia),
    )
    if cursor.fetchone()['count'] > 0:
        flash('Esta materia ya está incluida en el plan de estudios del grupo', 'warning')
        conn.close()
        return redirect(url_for('plan_estudios_bp.plan_estudios'))

    try:
        cursor.execute(
            "INSERT INTO plan_estudios (ID_Grupo, ID_Materia) VALUES (%s, %s)",
            (id_grupo, id_materia),
        )
        conn.commit()
        flash('Materia agregada al plan de estudios exitosamente', 'success')
    except Exception as e:
        flash(f'Error al asignar: {str(e)}', 'danger')
    finally:
        conn.close()

    return redirect(url_for('plan_estudios_bp.plan_estudios'))


@plan_estudios_bp.route('/plan_estudios/desasignar/<int:id_plan>', methods=['POST'])
@admin_required
def desasignar_materia(id_plan):
    """Eliminar una materia del plan de estudios de un grupo."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT ID_Grupo, ID_Materia FROM plan_estudios WHERE ID_Plan = %s', (id_plan,))
    plan = cursor.fetchone()
    if not plan:
        conn.close()
        flash('No se encontró la asignación del plan de estudios', 'warning')
        return redirect(url_for('plan_estudios_bp.plan_estudios'))

    cursor.execute(
        'SELECT ID_Carga FROM cargas_academicas WHERE ID_Grupo = %s AND ID_Materia = %s',
        (plan['ID_Grupo'], plan['ID_Materia']),
    )
    carga = cursor.fetchone()
    if carga:
        cursor.execute('SELECT COUNT(*) as count FROM notas WHERE ID_Carga = %s', (carga['ID_Carga'],))
        notas_count = cursor.fetchone()['count']
        conn.close()
        if notas_count > 0:
            flash('No se puede quitar del plan de estudios porque ya hay notas registradas para esa materia en el grupo', 'danger')
        else:
            flash('No se puede quitar del plan de estudios mientras exista una carga académica asociada. Elimine o reasigne primero la carga académica.', 'warning')
        return redirect(url_for('plan_estudios_bp.plan_estudios'))

    try:
        cursor.execute('DELETE FROM plan_estudios WHERE ID_Plan = %s', (id_plan,))
        conn.commit()
        flash('Materia retirada del plan de estudios exitosamente', 'success')
    except Exception as e:
        flash(f'Error al desasignar: {str(e)}', 'danger')
    finally:
        conn.close()

    return redirect(url_for('plan_estudios_bp.plan_estudios'))
