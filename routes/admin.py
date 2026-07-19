from flask import Blueprint, render_template, session, flash, redirect, url_for, jsonify
from functools import wraps
from models import get_db_connection

admin_bp = Blueprint('admin_bp', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('rol') != 'admin':
            flash('Acceso no autorizado', 'danger')
            return redirect(url_for('auth_bp.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/admin/panel')
@admin_required
def panel():
    return render_template('panel_admin.html')

@admin_bp.route('/admin/estadisticas')
@admin_required
def estadisticas():
    """API para obtener estadísticas del sistema"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as count FROM docentes")
    docentes = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM estudiantes")
    estudiantes = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM grupos")
    grupos = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM materias")
    materias = cursor.fetchone()['count']
    
    conn.close()
    
    return jsonify({
        'docentes': docentes,
        'estudiantes': estudiantes,
        'grupos': grupos,
        'materias': materias
    })

@admin_bp.route('/admin/grupos')
@admin_required
def grupos_admin():
    flash('Módulo en construcción', 'info')
    return redirect(url_for('grupos_bp.grupos'))

@admin_bp.route('/admin/asignaturas')
@admin_required
def asignaturas_admin():
    flash('Módulo en construcción', 'info')
    return redirect(url_for('asignaturas_bp.asignaturas'))
