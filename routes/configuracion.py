from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from functools import wraps
from models import get_db_connection, get_periodo_activo, set_periodo_activo

configuracion_bp = Blueprint('configuracion_bp', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('rol') != 'admin':
            flash('Acceso no autorizado', 'danger')
            return redirect(url_for('auth_bp.login'))
        return f(*args, **kwargs)
    return decorated_function


@configuracion_bp.route('/configuracion')
@admin_required
def configuracion():
    """Panel de configuración del sistema"""
    periodo_activo = get_periodo_activo()
    return render_template('configuracion.html', periodo_activo=periodo_activo)


@configuracion_bp.route('/configuracion/set_periodo', methods=['POST'])
@admin_required
def set_periodo():
    """Cambiar el período activo"""
    periodo = request.form.get('periodo', type=int)
    
    if periodo not in [1, 2, 3, 4]:
        flash('Período inválido', 'danger')
        return redirect(url_for('configuracion_bp.configuracion'))
    
    set_periodo_activo(periodo)
    flash(f'Período activo cambiado a {periodo}', 'success')
    
    return redirect(url_for('configuracion_bp.configuracion'))
