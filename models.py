import os
import pymysql
import pymysql.cursors
from werkzeug.security import generate_password_hash
from config import Config
import pymysql
import pymysql.cursors
from werkzeug.security import generate_password_hash
from config import Config


class DictCursor(pymysql.cursors.DictCursor):
    """Cursor que retorna resultados como diccionarios (compatible con sqlite3.Row)"""
    pass


def get_db_connection():
    """Establece y retorna una conexión a la base de datos MariaDB/MySQL"""
    try:
        conn = pymysql.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            charset='utf8mb4',
            cursorclass=DictCursor,
            autocommit=False
        )
        return conn
    except pymysql.Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        raise


def init_db():
    """Inicializa la base de datos con todas las tablas necesarias"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Crear tabla de usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            ID_Usuario INT AUTO_INCREMENT PRIMARY KEY,
            Usuario VARCHAR(255) UNIQUE NOT NULL,
            Contrasena TEXT NOT NULL,
            Rol VARCHAR(20) NOT NULL CHECK (Rol IN ('admin', 'docente', 'estudiante'))
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    ''')

    # Crear tabla de niveles
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS niveles (
            ID_Nivel INT AUTO_INCREMENT PRIMARY KEY,
            Nombre_Nivel VARCHAR(255) NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    ''')

    # Crear tabla de areas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS areas (
            ID_Area INT AUTO_INCREMENT PRIMARY KEY,
            Nombre_Area VARCHAR(255) NOT NULL UNIQUE,
            Orden INT DEFAULT 0
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    ''')

    # Crear tabla de grupos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS grupos (
            ID_Grupo INT AUTO_INCREMENT PRIMARY KEY,
            Nombre_Grupo VARCHAR(255) NOT NULL,
            ID_Nivel INT,
            FOREIGN KEY (ID_Nivel) REFERENCES niveles(ID_Nivel)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    ''')

    # Crear tabla de materias
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS materias (
            ID_Materia INT AUTO_INCREMENT PRIMARY KEY,
            Nombre_Materia VARCHAR(255) NOT NULL,
            ID_Area INT,
            Es_DIM INT DEFAULT 0,
            FOREIGN KEY (ID_Area) REFERENCES areas(ID_Area)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    ''')

    # Crear tabla de plan de estudios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS plan_estudios (
            ID_Plan INT AUTO_INCREMENT PRIMARY KEY,
            ID_Grupo INT NOT NULL,
            ID_Materia INT NOT NULL,
            FOREIGN KEY (ID_Grupo) REFERENCES grupos(ID_Grupo),
            FOREIGN KEY (ID_Materia) REFERENCES materias(ID_Materia),
            UNIQUE(ID_Grupo, ID_Materia)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    ''')

    # Crear tabla de estudiantes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS estudiantes (
            ID_Estudiante INT AUTO_INCREMENT PRIMARY KEY,
            Nombres VARCHAR(255) NOT NULL,
            Apellidos VARCHAR(255) NOT NULL,
            ID_Grupo INT,
            ID_Usuario INT,
            FOREIGN KEY (ID_Grupo) REFERENCES grupos(ID_Grupo),
            FOREIGN KEY (ID_Usuario) REFERENCES usuarios(ID_Usuario)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    ''')

    # Crear tabla de docentes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS docentes (
            ID_Docente INT AUTO_INCREMENT PRIMARY KEY,
            Nombres VARCHAR(255) NOT NULL,
            Apellidos VARCHAR(255) NOT NULL,
            ID_Usuario INT,
            Firma_URL VARCHAR(255),
            FOREIGN KEY (ID_Usuario) REFERENCES usuarios(ID_Usuario)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    ''')

    # Crear tabla de cargas académicas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cargas_academicas (
            ID_Carga INT AUTO_INCREMENT PRIMARY KEY,
            ID_Docente INT,
            ID_Materia INT,
            ID_Grupo INT,
            FOREIGN KEY (ID_Docente) REFERENCES docentes(ID_Docente),
            FOREIGN KEY (ID_Materia) REFERENCES materias(ID_Materia),
            FOREIGN KEY (ID_Grupo) REFERENCES grupos(ID_Grupo)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    ''')

    # Crear tabla de notas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notas (
            ID_Nota INT AUTO_INCREMENT PRIMARY KEY,
            ID_Estudiante INT,
            ID_Carga INT,
            Periodo INT DEFAULT 1,
            Tipo VARCHAR(20) CHECK (Tipo IN ('eval', 'tarea')),
            Numero INT CHECK (Numero BETWEEN 1 AND 10),
            Nota DOUBLE,
            FOREIGN KEY (ID_Estudiante) REFERENCES estudiantes(ID_Estudiante),
            FOREIGN KEY (ID_Carga) REFERENCES cargas_academicas(ID_Carga)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    ''')

    # Tabla de indicadores por estudiante
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS indicadores_logro (
            ID_Indicador INT AUTO_INCREMENT PRIMARY KEY,
            ID_Carga INT NOT NULL,
            ID_Estudiante INT NOT NULL,
            Periodo INT NOT NULL,
            Logros LONGTEXT,
            Dificultades LONGTEXT,
            Recomendaciones LONGTEXT,
            FOREIGN KEY (ID_Carga) REFERENCES cargas_academicas(ID_Carga),
            FOREIGN KEY (ID_Estudiante) REFERENCES estudiantes(ID_Estudiante),
            UNIQUE(ID_Carga, ID_Estudiante, Periodo)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    ''')

    # Indicadores unificados por planilla/grupo
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS indicadores_planilla (
            ID_Indicador_Planilla INT AUTO_INCREMENT PRIMARY KEY,
            ID_Carga INT NOT NULL,
            Periodo INT NOT NULL,
            Indicadores LONGTEXT,
            FOREIGN KEY (ID_Carga) REFERENCES cargas_academicas(ID_Carga),
            UNIQUE(ID_Carga, Periodo)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    ''')

    # Tabla de configuración
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS configuracion (
            Clave VARCHAR(255) PRIMARY KEY,
            Valor TEXT NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    ''')

    # Observaciones y fallas por estudiante y período
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS observador_estudiante (
            ID_Obs INT AUTO_INCREMENT PRIMARY KEY,
            ID_Estudiante INT NOT NULL,
            Periodo INT NOT NULL,
            Observacion LONGTEXT,
            Fallas INT DEFAULT 0,
            Fecha_Registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ID_Estudiante) REFERENCES estudiantes(ID_Estudiante),
            UNIQUE(ID_Estudiante, Periodo)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    ''')

    # Concepto final anual y promoción del estudiante
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS observador_anual (
            ID_Anual INT AUTO_INCREMENT PRIMARY KEY,
            ID_Estudiante INT NOT NULL UNIQUE,
            Observaciones_Generales LONGTEXT,
            Concepto_Final VARCHAR(255),
            Promovido_A VARCHAR(255),
            FOREIGN KEY (ID_Estudiante) REFERENCES estudiantes(ID_Estudiante)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    ''')

    # Titular de cada grupo (docente responsable del grupo)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS titulares_grupo (
            ID_Titular INT AUTO_INCREMENT PRIMARY KEY,
            ID_Grupo INT NOT NULL UNIQUE,
            ID_Docente INT NOT NULL,
            FOREIGN KEY (ID_Grupo) REFERENCES grupos(ID_Grupo),
            FOREIGN KEY (ID_Docente) REFERENCES docentes(ID_Docente)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    ''')

    # Índices
    cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_plan_estudios_grupo_materia ON plan_estudios (ID_Grupo, ID_Materia)')
    cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_cargas_grupo_materia ON cargas_academicas (ID_Grupo, ID_Materia)')

    # Migración: eliminar acceso individual de estudiantes al sistema
    cursor.execute('''
        UPDATE estudiantes
        SET ID_Usuario = NULL
        WHERE ID_Usuario IN (SELECT ID_Usuario FROM usuarios WHERE Rol = %s)
    ''', ('estudiante',))
    cursor.execute('DELETE FROM usuarios WHERE Rol = %s', ('estudiante',))

    # Migración: garantizar que todo usuario docente tenga ficha en docentes
    cursor.execute('''
        SELECT u.ID_Usuario, u.Usuario
        FROM usuarios u
        LEFT JOIN docentes d ON d.ID_Usuario = u.ID_Usuario
        WHERE u.Rol = %s AND d.ID_Docente IS NULL
    ''', ('docente',))
    docentes_huerfanos = cursor.fetchall()
    for docente in docentes_huerfanos:
        usuario = docente['Usuario']
        nombres = 'Docente'
        apellidos = usuario
        if usuario.startswith('doc_'):
            bruto = usuario[4:]
            partes = [p for p in bruto.replace('_', ' ').split() if p]
            if partes:
                nombres = ' '.join(p.capitalize() for p in partes[:2])
                apellidos = ' '.join(p.capitalize() for p in partes[2:]) or usuario
        elif usuario.startswith('docente'):
            nombres = 'Docente'
            apellidos = usuario.replace('docente', '').strip() or usuario
        cursor.execute(
            'INSERT INTO docentes (Nombres, Apellidos, ID_Usuario, Firma_URL) VALUES (%s, %s, %s, %s)',
            (nombres, apellidos, docente['ID_Usuario'], None),
        )

    # Migración: separar plan de estudios de la carga académica
    cursor.execute('''
        INSERT IGNORE INTO plan_estudios (ID_Grupo, ID_Materia)
        SELECT DISTINCT ID_Grupo, ID_Materia
        FROM cargas_academicas
        WHERE ID_Grupo IS NOT NULL AND ID_Materia IS NOT NULL
    ''')

    # Migración: unificar indicadores para toda la planilla/grupo
    cursor.execute('''
        INSERT IGNORE INTO indicadores_planilla (ID_Carga, Periodo, Indicadores)
        SELECT il.ID_Carga, il.Periodo, il.Logros
        FROM indicadores_logro il
        JOIN (
            SELECT ID_Carga, Periodo, MIN(ID_Indicador) AS min_id
            FROM indicadores_logro
            WHERE COALESCE(TRIM(Logros), '') <> ''
            GROUP BY ID_Carga, Periodo
        ) base ON base.min_id = il.ID_Indicador
    ''')

    conn.commit()

    # Si la BD es nueva, crear solo el usuario admin y configuración mínima
    cursor.execute("SELECT COUNT(*) as count FROM usuarios")
    if cursor.fetchone()['count'] == 0:
        cursor.execute(
            'INSERT INTO usuarios (Usuario, Contrasena, Rol) VALUES (%s, %s, %s)',
            ('admin', generate_password_hash('admin123'), 'admin')
        )
        cursor.execute("INSERT IGNORE INTO configuracion (Clave, Valor) VALUES (%s, %s)", ('periodo_activo', '1'))
        conn.commit()
        print("✓ Usuario admin creado (admin / admin123)")

    conn.close()
    print("✓ Base de datos inicializada correctamente")


def _insertar_datos_prueba(cursor):
    """Inserta datos de prueba en la base de datos"""

    # Insertar niveles
    niveles = ['Preescolar', 'Básica Primaria', 'Básica Secundaria', 'Media']
    for nivel in niveles:
        cursor.execute('INSERT INTO niveles (Nombre_Nivel) VALUES (%s)', (nivel,))

    # Insertar áreas académicas con su respectivo ORDEN
    areas = [
        ('HUMANIDADES', 0), ('MATEMATICAS', 0), ('CIENCIAS SOCIALES', 0), ('CIENCIAS NATURALES', 0),
        ('ETICA', 0), ('TECNOLOGIA E INFORMATICA', 0), ('RELIGION', 0), ('EDUCACION ARTISTICA', 0),
        ('EDUCACION FISICA', 0), ('COGNITIVA', 0), ('COMUNICATIVA', 0),
        ('ESTETICA', 0), ('CORPORAL', 0), ('SOCIOAFECTIVA', 0), ('ESPIRITUAL', 0),
        ('COMPORTAMIENTO', 98), ('CONVIVENCIA', 99),
    ]
    for area, orden in areas:
        cursor.execute('INSERT INTO areas (Nombre_Area, Orden) VALUES (%s, %s)', (area, orden))

    # Obtener IDs de áreas
    cursor.execute("SELECT ID_Area, Nombre_Area FROM areas")
    areas_dict = {area['Nombre_Area']: area['ID_Area'] for area in cursor.fetchall()}

    # Insertar materias
    materias = [
        ('ENGLISH', 'HUMANIDADES', False),
        ('ESPAÑOL Y LITERATURA', 'HUMANIDADES', False),
        ('MATEMATICAS', 'MATEMATICAS', False),
        ('CIENCIAS SOCIALES', 'CIENCIAS SOCIALES', False),
        ('CIENCIAS NATURALES', 'CIENCIAS NATURALES', False),
        ('ETICA', 'ETICA', False),
        ('TECNOLOGIA E INFORMATICA', 'TECNOLOGIA E INFORMATICA', False),
        ('RELIGION', 'RELIGION', False),
        ('EDUCACION ARTISTICA', 'EDUCACION ARTISTICA', False),
        ('EDUCACION FISICA', 'EDUCACION FISICA', False),
        ('DIM. COGNITIVA', 'COGNITIVA', True),
        ('DIM. COMUNICATIVA', 'COMUNICATIVA', True),
        ('DIM. ESTETICA', 'ESTETICA', True),
        ('DIM. CORPORAL', 'CORPORAL', True),
        ('DIM. SOCIOAFECTIVA', 'SOCIOAFECTIVA', True),
        ('DIM. ESPIRITUAL', 'ESPIRITUAL', True),
        ('DIM. ETICA Y VALORES', 'ETICA', True),
        ('COMPORTAMIENTO', 'COMPORTAMIENTO', True),
        ('CONVIVENCIA', 'CONVIVENCIA', False),
    ]
    for nombre, area_nombre, es_dim in materias:
        id_area = areas_dict.get(area_nombre)
        cursor.execute(
            'INSERT INTO materias (Nombre_Materia, ID_Area, Es_DIM) VALUES (%s, %s, %s)',
            (nombre, id_area, 1 if es_dim else 0),
        )

    # Insertar grupos
    grupos = [
        ('Prejardín A', 1), ('Jardín A', 1), ('Transición A', 1),
        ('Primero A', 2), ('Segundo A', 2), ('Tercero A', 2),
        ('Cuarto A', 2), ('Quinto A', 2),
        ('Prejardín B', 1), ('Jardín B', 1), ('Transición B', 1),
        ('Primero B', 2), ('Segundo B', 2), ('Tercero B', 2),
        ('Cuarto B', 2), ('Quinto B', 2),
    ]
    for grupo in grupos:
        cursor.execute('INSERT INTO grupos (Nombre_Grupo, ID_Nivel) VALUES (%s, %s)', grupo)

    # Insertar usuarios de prueba
    usuarios = [
        ('admin', generate_password_hash('admin123'), 'admin'),
        ('docente1', generate_password_hash('123456'), 'docente'),
        ('docente2', generate_password_hash('123456'), 'docente'),
    ]
    for usuario in usuarios:
        cursor.execute('INSERT INTO usuarios (Usuario, Contrasena, Rol) VALUES (%s, %s, %s)', usuario)

    # Configuración inicial
    cursor.execute("INSERT OR IGNORE INTO configuracion (Clave, Valor) VALUES (%s, %s)", ('periodo_activo', '1'))

    # Obtener IDs
    cursor.execute("SELECT ID_Usuario FROM usuarios WHERE Usuario = 'docente1'")
    id_docente1 = cursor.fetchone()['ID_Usuario']

    # Insertar docentes
    cursor.execute(
        'INSERT INTO docentes (Nombres, Apellidos, ID_Usuario, Firma_URL) VALUES (%s, %s, %s, %s)',
        ('María', 'González', id_docente1, 'docente_firma.png'),
    )

    # Insertar estudiantes
    estudiantes = [
        ('Juan', 'Pérez', 1, None),
        ('Ana', 'López', 1, None),
        ('Carlos', 'Ramírez', 2, None),
        ('Valentina', 'Rodríguez', 3, None),
        ('Samuel', 'Martínez', 4, None),
        ('Laura', 'Gómez', 9, None),
        ('Diego', 'Sánchez', 9, None),
        ('Sofía', 'Díaz', 10, None),
    ]
    for estudiante in estudiantes:
        cursor.execute(
            'INSERT INTO estudiantes (Nombres, Apellidos, ID_Grupo, ID_Usuario) VALUES (%s, %s, %s, %s)',
            estudiante,
        )

    # Obtener IDs necesarios
    cursor.execute("SELECT ID_Docente FROM docentes LIMIT 1")
    id_docente = cursor.fetchone()['ID_Docente']

    cursor.execute("SELECT ID_Grupo FROM grupos WHERE Nombre_Grupo = 'Prejardín A'")
    id_grupo_prejardin = cursor.fetchone()['ID_Grupo']

    cursor.execute("SELECT ID_Materia FROM materias WHERE Nombre_Materia = 'DIM. COGNITIVA'")
    id_materia_dim = cursor.fetchone()['ID_Materia']

    cursor.execute("SELECT ID_Materia FROM materias WHERE Nombre_Materia = 'MATEMATICAS'")
    id_materia_mate = cursor.fetchone()['ID_Materia']

    # Insertar plan de estudios de prueba
    planes = [
        (id_grupo_prejardin, id_materia_dim),
        (id_grupo_prejardin, id_materia_mate),
    ]
    for plan in planes:
        cursor.execute('INSERT IGNORE INTO plan_estudios (ID_Grupo, ID_Materia) VALUES (%s, %s)', plan)

    # Insertar cargas académicas de prueba
    cargas = [
        (id_docente, id_materia_dim, id_grupo_prejardin),
        (id_docente, id_materia_mate, id_grupo_prejardin),
    ]
    for carga in cargas:
        cursor.execute(
            'INSERT INTO cargas_academicas (ID_Docente, ID_Materia, ID_Grupo) VALUES (%s, %s, %s)',
            carga,
        )


def get_periodo_activo():
    """Obtiene el período activo actual"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT Valor FROM configuracion WHERE Clave = %s", ('periodo_activo',))
    row = cursor.fetchone()
    conn.close()
    return int(row['Valor']) if row else 1


def set_periodo_activo(periodo):
    """Establece el período activo"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO configuracion (Clave, Valor) VALUES (%s, %s) ON DUPLICATE KEY UPDATE Valor=%s",
        ('periodo_activo', str(periodo), str(periodo)),
    )
    conn.commit()
    conn.close()


if __name__ == '__main__':
    init_db()
    print("=" * 50)
    print("🎓 Base de datos inicializada")
    print("=" * 50)
    print("👥 Usuarios de prueba:")
    print("   Admin:   admin / admin123")
    print("=" * 50)