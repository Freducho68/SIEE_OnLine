# routes/__init__.py
# Este archivo hace que la carpeta routes sea un paquete Python

from routes.auth import auth_bp
from routes.planillas import planillas_bp
from routes.boletin import boletin_bp
from routes.admin import admin_bp
from routes.docentes import docentes_bp
from routes.estudiantes import estudiantes_bp
from routes.plan_estudios import plan_estudios_bp
from routes.carga import carga_bp
from routes.backups import backups_bp
from routes.grupos import grupos_bp
from routes.asignaturas import asignaturas_bp
from routes.carga_masiva import carga_masiva_bp
from routes.configuracion import configuracion_bp

__all__ = [
    'auth_bp',
    'planillas_bp', 
    'boletin_bp',
    'admin_bp',
    'docentes_bp',
    'estudiantes_bp',
    'plan_estudios_bp',
    'carga_bp',
    'backups_bp',
    'grupos_bp',
    'asignaturas_bp',
    'carga_masiva_bp',
    'configuracion_bp'
]
