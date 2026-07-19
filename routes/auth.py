from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from models import get_db_connection, get_periodo_activo
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth_bp', __name__)
ROLES_PERMITIDOS = {'admin', 'docente'}


def _redirect_by_role(rol: str):
    if rol == 'admin':
        return redirect(url_for('admin_bp.panel'))
    if rol == 'docente':
        return redirect(url_for('auth_bp.panel_docente'))
    session.clear()
    flash('Acceso no autorizado para este usuario.', 'danger')
    return redirect(url_for('auth_bp.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return _redirect_by_role(session.get('rol'))

    if request.method == 'POST':
        usuario = (request.form.get('usuario') or '').strip()
        contrasena = request.form.get('contrasena') or ''

        if not usuario or not contrasena:
            flash('Debe ingresar usuario y contraseña', 'danger')
            return render_template('login.html')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM usuarios WHERE Usuario = %s', (usuario,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['Contrasena'], contrasena):
            if user['Rol'] not in ROLES_PERMITIDOS:
                flash('Solo pueden acceder el administrador y los docentes registrados.', 'danger')
                return render_template('login.html')

            session.clear()
            session['user_id'] = user['ID_Usuario']
            session['rol'] = user['Rol']
            session['usuario'] = user['Usuario']
            session.permanent = False

            etiquetas = {
                'docente': 'docente',
                'admin': 'administrador',
            }
            flash(f"Bienvenido {etiquetas.get(user['Rol'], 'usuario')} {usuario}", 'success')
            return _redirect_by_role(user['Rol'])

        flash('Usuario o contraseña incorrectos', 'danger')

    return render_template('login.html')


@auth_bp.route('/panel_docente')
def panel_docente():
    if 'user_id' not in session or session.get('rol') != 'docente':
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('auth_bp.login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT ID_Docente, Nombres, Apellidos FROM docentes WHERE ID_Usuario = %s',
        (session['user_id'],)
    )
    docente = cursor.fetchone()

    if not docente:
        conn.close()
        flash('No se encontró información del docente', 'danger')
        session.clear()
        return redirect(url_for('auth_bp.login'))

    cursor.execute(
        '''
        SELECT c.ID_Carga, m.Nombre_Materia, g.Nombre_Grupo
        FROM cargas_academicas c
        JOIN materias m ON c.ID_Materia = m.ID_Materia
        JOIN grupos g ON c.ID_Grupo = g.ID_Grupo
        WHERE c.ID_Docente = %s
        ORDER BY g.Nombre_Grupo, m.Nombre_Materia
        ''',
        (docente['ID_Docente'],),
    )
    cargas = cursor.fetchall()
    conn.close()

    return render_template(
        'panel_docente.html',
        cargas=cargas,
        periodo_activo=get_periodo_activo(),
        docente=docente,
    )


@auth_bp.route('/cambiar_clave', methods=['GET', 'POST'])
def cambiar_clave():
    if 'user_id' not in session:
        flash('Debe iniciar sesión', 'warning')
        return redirect(url_for('auth_bp.login'))

    if request.method == 'POST':
        clave_actual = request.form.get('clave_actual') or ''
        clave_nueva = request.form.get('clave_nueva') or ''
        clave_confirmar = request.form.get('clave_confirmar') or ''

        if clave_nueva != clave_confirmar:
            flash('Las contraseñas nuevas no coinciden', 'danger')
            return redirect(url_for('auth_bp.cambiar_clave'))

        if len(clave_nueva) < 6:
            flash('La contraseña debe tener al menos 6 caracteres', 'danger')
            return redirect(url_for('auth_bp.cambiar_clave'))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT Contrasena FROM usuarios WHERE ID_Usuario = %s', (session['user_id'],))
        user = cursor.fetchone()

        if user and check_password_hash(user['Contrasena'], clave_actual):
            nueva_hash = generate_password_hash(clave_nueva)
            cursor.execute(
                'UPDATE usuarios SET Contrasena = %s WHERE ID_Usuario = %s',
                (nueva_hash, session['user_id'])
            )
            conn.commit()
            conn.close()
            flash('Contraseña cambiada exitosamente', 'success')
            return _redirect_by_role(session.get('rol'))

        conn.close()
        flash('Contraseña actual incorrecta', 'danger')

    return render_template('cambiar_clave.html')


@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    flash('Sesión cerrada correctamente', 'success')
    return redirect(url_for('auth_bp.login'))
