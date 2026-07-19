from flask import Blueprint, render_template, flash, redirect, url_for, session, send_file
from functools import wraps
from models import get_db_connection
import csv
import io
import os
import sys
import shutil
import tempfile
from datetime import datetime
import zipfile

backups_bp = Blueprint('backups_bp', __name__)


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('rol') != 'admin':
            flash('Acceso no autorizado', 'danger')
            return redirect(url_for('auth_bp.login'))
        return f(*args, **kwargs)
    return decorated_function


def _get_base_dir():
    """Ruta base correcta en desarrollo y en exe PyInstaller (one-file)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _get_backup_dir():
    d = os.path.join(_get_base_dir(), 'backups')
    os.makedirs(d, exist_ok=True)
    return d


def _get_db_path():
    return os.path.join(_get_base_dir(), 'database.db')


def _safe_backup_path(nombre: str):
    if not nombre:
        return None
    nombre_seguro = os.path.basename(nombre)
    file_path = os.path.abspath(os.path.join(_get_backup_dir(), nombre_seguro))
    backup_root = os.path.abspath(_get_backup_dir())
    if not file_path.startswith(backup_root + os.sep):
        return None
    return file_path


@backups_bp.route('/backups')
@admin_required
def backups():
    backups_list = []
    for file in os.listdir(_get_backup_dir()):
        if file.endswith(('.db', '.zip')):
            file_path = os.path.join(_get_backup_dir(), file)
            stat = os.stat(file_path)
            backups_list.append({
                'nombre': file,
                'tamaño': stat.st_size,
                'fecha': datetime.fromtimestamp(stat.st_mtime),
                'ruta': file_path,
            })

    backups_list.sort(key=lambda x: x['fecha'], reverse=True)
    for item in backups_list:
        item['fecha'] = item['fecha'].strftime('%Y-%m-%d %H:%M:%S')
    return render_template('backups.html', backups=backups_list)


@backups_bp.route('/backups/crear')
@admin_required
def crear_backup():
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'backup_{timestamp}.db'
        backup_path = os.path.join(_get_backup_dir(), backup_filename)
        shutil.copy2(_get_db_path(), backup_path)

        zip_filename = f'backup_{timestamp}.zip'
        zip_path = os.path.join(_get_backup_dir(), zip_filename)
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(backup_path, os.path.basename(backup_path))

        limpiar_backups_antiguos()
        flash(f'Backup creado exitosamente: {zip_filename}', 'success')
    except Exception as e:
        flash(f'Error al crear backup: {str(e)}', 'danger')
    return redirect(url_for('backups_bp.backups'))


@backups_bp.route('/backups/descargar/<nombre>')
@admin_required
def descargar_backup(nombre):
    file_path = _safe_backup_path(nombre)
    if not file_path or not os.path.exists(file_path):
        flash('El archivo de backup no existe', 'danger')
        return redirect(url_for('backups_bp.backups'))
    return send_file(file_path, as_attachment=True, download_name=os.path.basename(file_path))


@backups_bp.route('/backups/restaurar/<nombre>')
@admin_required
def restaurar_backup(nombre):
    backup_path = _safe_backup_path(nombre)
    if not backup_path or not os.path.exists(backup_path):
        flash('El archivo de backup no existe', 'danger')
        return redirect(url_for('backups_bp.backups'))

    if not nombre.endswith(('.db', '.zip')):
        flash('Solo se pueden restaurar archivos .db o .zip', 'danger')
        return redirect(url_for('backups_bp.backups'))

    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safety_backup = os.path.join(_get_backup_dir(), f'safety_backup_{timestamp}.db')
        shutil.copy2(_get_db_path(), safety_backup)

        if nombre.endswith('.db'):
            shutil.copy2(backup_path, _get_db_path())
        else:
            with tempfile.TemporaryDirectory() as tmpdir:
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    nombres_db = [n for n in zipf.namelist() if n.lower().endswith('.db')]
                    if not nombres_db:
                        raise ValueError('El ZIP no contiene ningún archivo .db válido')
                    miembro = nombres_db[0]
                    zipf.extract(miembro, tmpdir)
                    shutil.copy2(os.path.join(tmpdir, miembro), _get_db_path())

        flash(f'Base de datos restaurada exitosamente desde {nombre}', 'success')
    except Exception as e:
        flash(f'Error al restaurar backup: {str(e)}', 'danger')
    return redirect(url_for('backups_bp.backups'))


@backups_bp.route('/backups/eliminar/<nombre>', methods=['POST'])
@admin_required
def eliminar_backup(nombre):
    file_path = _safe_backup_path(nombre)
    if not file_path or not os.path.exists(file_path):
        flash('El archivo de backup no existe', 'danger')
        return redirect(url_for('backups_bp.backups'))
    try:
        os.remove(file_path)
        flash(f'Backup {os.path.basename(file_path)} eliminado exitosamente', 'success')
    except Exception as e:
        flash(f'Error al eliminar backup: {str(e)}', 'danger')
    return redirect(url_for('backups_bp.backups'))


def limpiar_backups_antiguos():
    backups = []
    for file in os.listdir(_get_backup_dir()):
        if file.endswith('.zip'):
            file_path = os.path.join(_get_backup_dir(), file)
            stat = os.stat(file_path)
            backups.append((file_path, stat.st_mtime))
    backups.sort(key=lambda x: x[1], reverse=True)
    for file_path, _ in backups[10:]:
        try:
            os.remove(file_path)
        except OSError:
            pass


@backups_bp.route('/backups/exportar_datos')
@admin_required
def exportar_datos():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        estudiantes_data = cursor.execute(
            '''
            SELECT e.ID_Estudiante, e.Nombres, e.Apellidos, g.Nombre_Grupo
            FROM estudiantes e
            LEFT JOIN grupos g ON e.ID_Grupo = g.ID_Grupo
            '''
        ).fetchall()
        docentes_data = cursor.execute(
            '''
            SELECT d.ID_Docente, d.Nombres, d.Apellidos, u.Usuario
            FROM docentes d
            LEFT JOIN usuarios u ON d.ID_Usuario = u.ID_Usuario
            '''
        ).fetchall()
        cargas_data = cursor.execute(
            '''
            SELECT c.ID_Carga,
                   d.Nombres || ' ' || d.Apellidos as Docente,
                   m.Nombre_Materia,
                   g.Nombre_Grupo
            FROM cargas_academicas c
            JOIN docentes d ON c.ID_Docente = d.ID_Docente
            JOIN materias m ON c.ID_Materia = m.ID_Materia
            JOIN grupos g ON c.ID_Grupo = g.ID_Grupo
            '''
        ).fetchall()
        conn.close()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['=== DATOS DEL SISTEMA ACADÉMICO ==='])
        writer.writerow([])
        writer.writerow(['=== ESTUDIANTES ==='])
        writer.writerow(['ID', 'Nombres', 'Apellidos', 'Grupo'])
        for e in estudiantes_data:
            writer.writerow([e['ID_Estudiante'], e['Nombres'], e['Apellidos'], e['Nombre_Grupo'] or 'Sin grupo'])
        writer.writerow([])
        writer.writerow(['=== DOCENTES ==='])
        writer.writerow(['ID', 'Nombres', 'Apellidos', 'Usuario'])
        for d in docentes_data:
            writer.writerow([d['ID_Docente'], d['Nombres'], d['Apellidos'], d['Usuario'] or 'Sin usuario'])
        writer.writerow([])
        writer.writerow(['=== CARGAS ACADÉMICAS ==='])
        writer.writerow(['ID', 'Docente', 'Materia', 'Grupo'])
        for c in cargas_data:
            writer.writerow([c['ID_Carga'], c['Docente'], c['Nombre_Materia'], c['Nombre_Grupo']])

        csv_bytes = io.BytesIO(output.getvalue().encode('utf-8-sig'))
        csv_bytes.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return send_file(csv_bytes, as_attachment=True, download_name=f'exportacion_{timestamp}.csv', mimetype='text/csv')
    except Exception as e:
        flash(f'Error al exportar datos: {str(e)}', 'danger')
        return redirect(url_for('backups_bp.backups'))
