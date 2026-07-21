import os
from flask import Flask, render_template, session, redirect, url_for

from config import Config
from models import init_db

def _as_bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}

# Obtener rutas base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_FOLDER = os.path.join(BASE_DIR, "templates")
STATIC_FOLDER = os.path.join(BASE_DIR, "static")

# Crear app Flask - SIN WhiteNoise
app = Flask(
    __name__,
    template_folder=TEMPLATE_FOLDER,
    static_folder=STATIC_FOLDER,
    static_url_path='/static'
)

app.config.from_object(Config)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

# Importar blueprints
from routes.auth import auth_bp
from routes.planillas import planillas_bp
from routes.boletin import boletin_bp
from routes.admin import admin_bp
from routes.docentes import docentes_bp
from routes.estudiantes import estudiantes_bp
from routes.grupos import grupos_bp
from routes.asignaturas import asignaturas_bp
from routes.plan_estudios import plan_estudios_bp
from routes.carga import carga_bp
from routes.backups import backups_bp
from routes.carga_masiva import carga_masiva_bp
from routes.configuracion import configuracion_bp

# Registrar blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(planillas_bp)
app.register_blueprint(boletin_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(docentes_bp)
app.register_blueprint(estudiantes_bp)
app.register_blueprint(grupos_bp)
app.register_blueprint(asignaturas_bp)
app.register_blueprint(plan_estudios_bp)
app.register_blueprint(carga_bp)
app.register_blueprint(backups_bp)
app.register_blueprint(carga_masiva_bp)
app.register_blueprint(configuracion_bp)

@app.context_processor
def inject_globals():
    return {
        "app_name": Config.APP_NAME,
        "app_version": Config.APP_VERSION
    }

# Inicializar base de datos
try:
    init_db()
except Exception as e:
    print(f"Error al conectar/inicializar la base de datos: {e}")

@app.route("/")
def splash():
    return render_template("splash.html")

@app.route("/index")
def index():
    if "user_id" in session:
        rol = session.get("rol")
        if rol == "docente":
            return redirect(url_for("auth_bp.panel_docente"))
        elif rol == "admin":
            return redirect(url_for("admin_bp.panel"))
    return redirect(url_for("auth_bp.login"))

@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "-1"
    return response

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template("500.html"), 500

if __name__ == "__main__":
    debug_mode = _as_bool(os.environ.get("FLASK_DEBUG"), bool(app.config.get("DEBUG", False)))

    print("=" * 60)
    print("🎓 Sistema de Gestión Académica SIEE")
    print("=" * 60)
    print(f"📡 Servidor disponible en http://0.0.0.0:5000")
    print(f"💻 Accede desde: http://localhost:5000")
    print(f"🔧 Modo DEBUG: {'Activado' if debug_mode else 'Desactivado'}")
    print("=" * 60)

    app.run(
        debug=debug_mode,
        host="0.0.0.0",
        port=5000,
        use_reloader=False
    )
