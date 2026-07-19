from flask import Blueprint, render_template, session, flash, redirect, url_for, request
from models import get_db_connection, get_periodo_activo
from functools import wraps
from datetime import datetime

boletin_bp = Blueprint('boletin_bp', __name__)

# Constantes Institucionales
DIRECTORA_NOMBRE = 'MÉRIDA ROSA MÁRQUEZ SANJUÁN'
DIRECTORA_FIRMA = 'firmas/dir_meridarosa_marquez.png'

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debe iniciar sesión para acceder a esta página', 'warning')
            return redirect(url_for('auth_bp.login'))
        return f(*args, **kwargs)
    return decorated_function

# ==========================================
# FUNCIONES DE APOYO (LÓGICA KISS)
# ==========================================

def es_materia_dim(nombre_materia):
    if nombre_materia:
        nombre_upper = nombre_materia.upper()
        return nombre_upper.startswith('DIM') or nombre_upper.startswith('DIM.')
    return False

def es_grupo_preescolar(nombre_grupo):
    if not nombre_grupo: return False
    nombre = nombre_grupo.upper()
    return any(x in nombre for x in ['PREJARDIN', 'PREJARDÍN', 'JARDIN', 'JARDÍN', 'TRANSICION', 'TRANSICIÓN'])

def es_grupo_primaria(nombre_grupo):
    """Grados 1° a 5° (primaria básica)."""
    if not nombre_grupo: return False
    import re
    nombre = nombre_grupo.upper()
    # Detecta: PRIMERO, SEGUNDO, TERCERO, CUARTO, QUINTO, 1°, 2°, 3°, 4°, 5°, 1º, etc.
    palabras = ['PRIMERO', 'SEGUNDO', 'TERCERO', 'CUARTO', 'QUINTO']
    if any(p in nombre for p in palabras):
        return True
    # Detecta patrones numéricos: 1°, 2°, 3°, 4°, 5° (con o sin espacio)
    if re.search(r'\b[1-5]\s*[°º]', nombre):
        return True
    return False

def calcular_promedio(notas):
    notas_validas = [n for n in notas if n is not None]
    if not notas_validas: return None
    return round(sum(notas_validas) / len(notas_validas), 1)

# ==========================================
# FUNCIONES DE PRIMARIA (promedios y puestos)
# ==========================================

def _calcular_datos_primaria(cursor, id_grupo, estudiante_id, periodo_actual, materias):
    """Calcula promedio general, puestos por periodo y escala de valoración.
    
    Usa una sola consulta agregada para obtener los promedios de todos los
    estudiantes del grupo en los 4 periodos, evitando N²×4 queries individuales.
    """
    # Promedio general del estudiante (promedio de los promedios anuales por materia)
    promedios_anuales = [m['promedio_anual'] for m in materias if m['promedio_anual'] is not None]
    promedio_general = round(sum(promedios_anuales) / len(promedios_anuales), 1) if promedios_anuales else None

    # Promedios por periodo del estudiante actual
    promedios_por_periodo = {}
    for p in range(1, 5):
        notas_p = [m[f'nota_p{p}'] for m in materias if m[f'nota_p{p}'] is not None]
        promedios_por_periodo[p] = round(sum(notas_p) / len(notas_p), 1) if notas_p else None

    # Una sola consulta: promedio por estudiante y periodo para todo el grupo
    cursor.execute("""
        SELECT n.ID_Estudiante, n.Periodo, AVG(n.Nota) AS Prom
        FROM notas n
        JOIN cargas_academicas c ON n.ID_Carga = c.ID_Carga
        WHERE c.ID_Grupo = %s
        GROUP BY n.ID_Estudiante, n.Periodo
    """, (id_grupo,))
    
    # Organizar resultados: {id_est: {periodo: promedio}}
    promedios_raw = {}
    for row in cursor.fetchall():
        est_id = row['ID_Estudiante']
        periodo = row['Periodo']
        prom = round(row['Prom'], 1) if row['Prom'] is not None else None
        if est_id not in promedios_raw:
            promedios_raw[est_id] = {}
        promedios_raw[est_id][periodo] = prom

    # Calcular puestos por periodo
    puestos_por_periodo = {}
    for p in range(1, 5):
        promedios_p = {
            est_id: datos[p]
            for est_id, datos in promedios_raw.items()
            if p in datos and datos[p] is not None
        }
        if promedios_p and estudiante_id in promedios_p:
            # Ordenar de mayor a menor; el puesto se calcula contando cuántos
            # estudiantes tienen un promedio estrictamente mayor
            prom_est = promedios_p[estudiante_id]
            puesto = sum(1 for v in promedios_p.values() if v > prom_est) + 1
            puestos_por_periodo[p] = puesto
        else:
            puestos_por_periodo[p] = None

    # Puesto general (promedio de los 4 periodos)
    promedios_generales = {}
    for est_id, datos in promedios_raw.items():
        vals = [v for v in datos.values() if v is not None]
        if vals:
            promedios_generales[est_id] = round(sum(vals) / len(vals), 1)

    puesto_general = None
    if promedios_generales and promedio_general is not None and estudiante_id in promedios_generales:
        prom_est_g = promedios_generales[estudiante_id]
        puesto_general = sum(1 for v in promedios_generales.values() if v > prom_est_g) + 1

    # Asignar puesto del periodo actual a cada materia
    puesto_periodo = puestos_por_periodo.get(periodo_actual)
    for m in materias:
        m['puesto_periodo'] = puesto_periodo

    # Escala de valoración: contar cuántas notas del periodo actual caen en cada rango
    notas_periodo = [m[f'nota_p{periodo_actual}'] for m in materias if m[f'nota_p{periodo_actual}'] is not None]
    notas_escala = {
        'superior': sum(1 for n in notas_periodo if n >= 4.5),
        'alto':     sum(1 for n in notas_periodo if 4.0 <= n < 4.5),
        'basico':   sum(1 for n in notas_periodo if 3.0 <= n < 4.0),
        'bajo':     sum(1 for n in notas_periodo if n < 3.0),
    }

    return {
        'promedio_general': promedio_general,
        'puesto_general': puesto_general,
        'promedios_por_periodo': promedios_por_periodo,
        'puestos_por_periodo': puestos_por_periodo,
        'notas_escala': notas_escala,
    }

def _obtener_titular_grupo(cursor, id_grupo):
    cursor.execute("""
        SELECT d.Nombres, d.Apellidos, d.Firma_URL
        FROM titulares_grupo t
        JOIN docentes d ON t.ID_Docente = d.ID_Docente
        WHERE t.ID_Grupo = %s
    """, (id_grupo,))
    fila = cursor.fetchone()
    if not fila: 
        return {'nombre': 'DOCENTE TITULAR', 'firma': None}
    return {
        'nombre': f"{fila['Nombres']} {fila['Apellidos']}".strip().upper(),
        'firma': fila['Firma_URL']
    }

def _obtener_indicadores_carga(cursor, id_carga, periodo):
    cursor.execute("SELECT Indicadores FROM indicadores_planilla WHERE ID_Carga = %s AND Periodo = %s", (id_carga, periodo))
    fila = cursor.fetchone()
    if fila and fila['Indicadores']:
        return [item.strip() for item in str(fila['Indicadores']).split('\n') if item and item.strip()]
    return []

# ==========================================
# CONSTRUCTORES DE CONTEXTO (BLINDADOS)
# ==========================================

def _construir_contexto_boletin(cursor, estudiante):
    periodo_actual = get_periodo_activo()
    titular = _obtener_titular_grupo(cursor, estudiante['ID_Grupo'])
    
    cursor.execute("SELECT Observacion, Fallas FROM observador_estudiante WHERE ID_Estudiante = %s AND Periodo = %s", 
                   (estudiante['ID_Estudiante'], periodo_actual))
    obs_periodo = cursor.fetchone()

    cursor.execute("""
        SELECT c.ID_Carga, m.Nombre_Materia, a.Nombre_Area, m.Es_DIM
        FROM cargas_academicas c 
        JOIN materias m ON c.ID_Materia = m.ID_Materia
        LEFT JOIN areas a ON m.ID_Area = a.ID_Area
        WHERE c.ID_Grupo = %s 
        ORDER BY a.Orden ASC, a.Nombre_Area ASC, m.Nombre_Materia ASC
    """, (estudiante['ID_Grupo'],))
    cargas = cursor.fetchall()

    materias = []
    for carga in cargas:
        es_dim = (carga['Es_DIM'] == 1 or 
                  es_materia_dim(carga['Nombre_Materia']) or 
                  es_grupo_preescolar(estudiante['Nombre_Grupo']))
        
        notas_p = {}
        for p in range(1, 5):
            cursor.execute("SELECT Tipo, Nota FROM notas WHERE ID_Estudiante = %s AND ID_Carga = %s AND Periodo = %s", 
                           (estudiante['ID_Estudiante'], carga['ID_Carga'], p))
            notas_db = cursor.fetchall()
            p_eval = calcular_promedio([n['Nota'] for n in notas_db if n['Tipo'] == 'eval'])
            p_tarea = calcular_promedio([n['Nota'] for n in notas_db if n['Tipo'] != 'eval'])
            
            nota_final = None
            if p_eval is not None and p_tarea is not None:
                nota_final = round((p_eval * 0.95) + (p_tarea * 0.05), 1)
            elif p_eval is not None: nota_final = round(p_eval, 1)
            elif p_tarea is not None: nota_final = round(p_tarea, 1)

            if es_dim and nota_final is not None:
                nr = round(nota_final)
                nota_final = 3.0 if nr < 3 else (5.0 if nr > 5 else float(nr))
            notas_p[p] = nota_final

        materias.append({
            'Nombre_Materia': carga['Nombre_Materia'].upper(),
            'Nombre_Area': carga['Nombre_Area'].upper() if carga['Nombre_Area'] else 'OTRAS ÁREAS',
            'nota_p1': notas_p[1], 'nota_p2': notas_p[2], 'nota_p3': notas_p[3], 'nota_p4': notas_p[4],
            'indicadores': _obtener_indicadores_carga(cursor, carga['ID_Carga'], periodo_actual),
            'promedio_anual': calcular_promedio([notas_p[p] for p in range(1, 5)]),
            'puesto_periodo': None,  # se rellena si es primaria
        })

    contexto_base = {
        'estudiante': estudiante, 'materias': materias, 'periodo_actual': periodo_actual,
        'observacion_periodo': obs_periodo['Observacion'] if obs_periodo else '',
        'fallas_periodo': obs_periodo['Fallas'] if obs_periodo else 0,
        'titular_nombre': titular['nombre'], 'firma_titular': titular['firma'],
        'directora_nombre': DIRECTORA_NOMBRE, 'firma_directora': DIRECTORA_FIRMA,
        'fecha_actual': datetime.now().strftime('%d/%m/%Y'),
        # valores por defecto (se sobreescriben si es primaria)
        'promedio_general': None, 'puesto_general': None,
        'promedios_por_periodo': {1: None, 2: None, 3: None, 4: None},
        'puestos_por_periodo': {1: None, 2: None, 3: None, 4: None},
        'notas_escala': {'superior': 0, 'alto': 0, 'basico': 0, 'bajo': 0},
    }

    if es_grupo_primaria(estudiante['Nombre_Grupo']):
        datos_prim = _calcular_datos_primaria(
            cursor, estudiante['ID_Grupo'], estudiante['ID_Estudiante'], periodo_actual, materias
        )
        contexto_base.update(datos_prim)

    return contexto_base

def _construir_contexto_informe_final(cursor, estudiante):
    titular = _obtener_titular_grupo(cursor, estudiante['ID_Grupo'])
    cursor.execute("""
        SELECT c.ID_Carga, m.Nombre_Materia, a.Nombre_Area, m.Es_DIM
        FROM cargas_academicas c 
        JOIN materias m ON c.ID_Materia = m.ID_Materia
        LEFT JOIN areas a ON m.ID_Area = a.ID_Area
        WHERE c.ID_Grupo = %s 
        ORDER BY a.Orden ASC, a.Nombre_Area ASC, m.Nombre_Materia ASC
    """, (estudiante['ID_Grupo'],))
    cargas = cursor.fetchall()

    materias_f = []
    for c in cargas:
        es_dim = (c['Es_DIM'] == 1 or
                  es_materia_dim(c['Nombre_Materia']) or
                  es_grupo_preescolar(estudiante['Nombre_Grupo']))

        notas_anio = []
        for p in range(1, 5):
            cursor.execute("SELECT Tipo, Nota FROM notas WHERE ID_Estudiante = %s AND ID_Carga = %s AND Periodo = %s",
                           (estudiante['ID_Estudiante'], c['ID_Carga'], p))
            notas_db = cursor.fetchall()
            p_eval  = calcular_promedio([n['Nota'] for n in notas_db if n['Tipo'] == 'eval'])
            p_tarea = calcular_promedio([n['Nota'] for n in notas_db if n['Tipo'] != 'eval'])

            nota_final = None
            if p_eval is not None and p_tarea is not None:
                nota_final = round((p_eval * 0.95) + (p_tarea * 0.05), 1)
            elif p_eval is not None:
                nota_final = round(p_eval, 1)
            elif p_tarea is not None:
                nota_final = round(p_tarea, 1)

            if es_dim and nota_final is not None:
                nr = round(nota_final)
                nota_final = 3.0 if nr < 3 else (5.0 if nr > 5 else float(nr))

            notas_anio.append(nota_final)

        validas = [v for v in notas_anio if v is not None]
        nota_def = round(sum(validas) / len(validas), 1) if validas else None

        materias_f.append({
            'Materia': c['Nombre_Materia'].upper(),
            'Nombre_Area': c['Nombre_Area'].upper() if c['Nombre_Area'] else 'OTRAS ÁREAS',
            'p1': notas_anio[0], 'p2': notas_anio[1], 'p3': notas_anio[2], 'p4': notas_anio[3],
            'def': nota_def
        })

    cursor.execute("SELECT * FROM observador_anual WHERE ID_Estudiante = %s", (estudiante['ID_Estudiante'],))
    anual = cursor.fetchone()

    defs = [m['def'] for m in materias_f if m['def'] is not None]
    promedio_general_final = round(sum(defs) / len(defs), 1) if defs else None

    return {
        'estudiante': estudiante, 'materias': materias_f, 'anual': anual,
        'titular_nombre': titular['nombre'], 'firma_titular': titular['firma'],
        'directora_nombre': DIRECTORA_NOMBRE, 'firma_directora': DIRECTORA_FIRMA,
        'promedio_general_final': promedio_general_final,
        'fecha_actual': datetime.now().strftime('%d/%m/%Y')
    }

# ==========================================
# RUTAS (ENDPOINTS)
# ==========================================

@boletin_bp.route('/boletines/carga/<int:id_carga>')
@login_required
def boletines_carga(id_carga):
    conn = get_db_connection()
    conn.row_factory = lambda cursor, row: dict(zip([col[0] for col in cursor.description], row))
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT c.*, g.Nombre_Grupo, m.Nombre_Materia 
        FROM cargas_academicas c 
        JOIN grupos g ON c.ID_Grupo = g.ID_Grupo 
        JOIN materias m ON c.ID_Materia = m.ID_Materia 
        WHERE c.ID_Carga = %s
    """, (id_carga,))
    carga = cursor.fetchone()
    
    cursor.execute("SELECT * FROM estudiantes WHERE ID_Grupo = %s ORDER BY Apellidos, Nombres", (carga['ID_Grupo'],))
    estudiantes = cursor.fetchall()
    conn.close()
    return render_template('seleccionar_estudiante_boletin.html', carga=carga, estudiantes=estudiantes)

@boletin_bp.route('/boletin')
@login_required
def boletin():
    id_est = request.args.get('id_estudiante', type=int)
    conn = get_db_connection()
    conn.row_factory = lambda cursor, row: dict(zip([col[0] for col in cursor.description], row))
    cursor = conn.cursor()
    
    cursor.execute("SELECT e.*, g.Nombre_Grupo FROM estudiantes e JOIN grupos g ON e.ID_Grupo = g.ID_Grupo WHERE e.ID_Estudiante = %s", (id_est,))
    estudiante = cursor.fetchone()
    
    contexto = _construir_contexto_boletin(cursor, estudiante)
    conn.close()
    template = 'boletin_primaria.html' if es_grupo_primaria(estudiante['Nombre_Grupo']) else 'boletin.html'
    return render_template(template, **contexto)

@boletin_bp.route('/boletines/lote/<int:id_carga>')
@login_required
def boletines_lote(id_carga):
    conn = get_db_connection()
    conn.row_factory = lambda cursor, row: dict(zip([col[0] for col in cursor.description], row))
    cursor = conn.cursor()
    
    cursor.execute("SELECT g.Nombre_Grupo, c.ID_Carga, c.ID_Grupo FROM cargas_academicas c JOIN grupos g ON c.ID_Grupo = g.ID_Grupo WHERE c.ID_Carga = %s", (id_carga,))
    carga = cursor.fetchone()
    
    cursor.execute("SELECT e.*, g.Nombre_Grupo FROM estudiantes e JOIN grupos g ON e.ID_Grupo = g.ID_Grupo WHERE e.ID_Grupo = %s ORDER BY e.Apellidos", (carga['ID_Grupo'],))
    estudiantes = cursor.fetchall()
    
    boletines = [_construir_contexto_boletin(cursor, e) for e in estudiantes]
    conn.close()
    nombre_grupo = carga['Nombre_Grupo'] if carga else ''
    template = 'boletines_lote_primaria.html' if es_grupo_primaria(nombre_grupo) else 'boletines_lote.html'
    return render_template(template, carga=carga, boletines=boletines)

@boletin_bp.route('/informe_final/<int:id_estudiante>')
@login_required
def informe_final(id_estudiante):
    conn = get_db_connection()
    conn.row_factory = lambda cursor, row: dict(zip([col[0] for col in cursor.description], row))
    cursor = conn.cursor()
    
    cursor.execute("SELECT e.*, g.Nombre_Grupo FROM estudiantes e JOIN grupos g ON e.ID_Grupo = g.ID_Grupo WHERE e.ID_Estudiante = %s", (id_estudiante,))
    estudiante = cursor.fetchone()
    
    contexto = _construir_contexto_informe_final(cursor, estudiante)
    conn.close()
    return render_template('informe_final.html', **contexto)

@boletin_bp.route('/informe_final/lote/<int:id_carga>')
@login_required
def informe_final_lote(id_carga):
    conn = get_db_connection()
    conn.row_factory = lambda cursor, row: dict(zip([col[0] for col in cursor.description], row))
    cursor = conn.cursor()
    
    cursor.execute("SELECT ID_Grupo, ID_Carga FROM cargas_academicas WHERE ID_Carga = %s", (id_carga,))
    carga = cursor.fetchone()
    
    cursor.execute("SELECT e.*, g.Nombre_Grupo FROM estudiantes e JOIN grupos g ON e.ID_Grupo = g.ID_Grupo WHERE e.ID_Grupo = %s ORDER BY e.Apellidos", (carga['ID_Grupo'],))
    estudiantes = cursor.fetchall()
    
    informes = [_construir_contexto_informe_final(cursor, e) for e in estudiantes]
    conn.close()
    return render_template('informe_final_lote.html', informes=informes, carga={'Nombre_Grupo': informes[0]['estudiante']['Nombre_Grupo']} if informes else {})


@boletin_bp.route('/boletines/lote/grupo/<int:id_grupo>')
@login_required
def boletines_lote_grupo(id_grupo):
    """Genera boletines en lote a partir del ID de grupo (usado desde admin/estudiantes)."""
    conn = get_db_connection()
    conn.row_factory = lambda cursor, row: dict(zip([col[0] for col in cursor.description], row))
    cursor = conn.cursor()

    cursor.execute("SELECT ID_Grupo, Nombre_Grupo FROM grupos WHERE ID_Grupo = %s", (id_grupo,))
    grupo = cursor.fetchone()

    cursor.execute(
        "SELECT e.*, g.Nombre_Grupo FROM estudiantes e JOIN grupos g ON e.ID_Grupo = g.ID_Grupo WHERE e.ID_Grupo = %s ORDER BY e.Apellidos",
        (id_grupo,)
    )
    estudiantes = cursor.fetchall()

    boletines = [_construir_contexto_boletin(cursor, e) for e in estudiantes]
    conn.close()

    nombre_grupo = grupo['Nombre_Grupo'] if grupo else ''
    template = 'boletines_lote_primaria.html' if es_grupo_primaria(nombre_grupo) else 'boletines_lote.html'
    return render_template(template, carga=grupo, boletines=boletines)


@boletin_bp.route('/informe_final/lote/grupo/<int:id_grupo>')
@login_required
def informe_final_lote_grupo(id_grupo):
    """Genera informes finales en lote a partir del ID de grupo (usado desde admin/estudiantes)."""
    conn = get_db_connection()
    conn.row_factory = lambda cursor, row: dict(zip([col[0] for col in cursor.description], row))
    cursor = conn.cursor()

    cursor.execute("SELECT ID_Grupo, Nombre_Grupo FROM grupos WHERE ID_Grupo = %s", (id_grupo,))
    grupo = cursor.fetchone()

    cursor.execute(
        "SELECT e.*, g.Nombre_Grupo FROM estudiantes e JOIN grupos g ON e.ID_Grupo = g.ID_Grupo WHERE e.ID_Grupo = %s ORDER BY e.Apellidos",
        (id_grupo,)
    )
    estudiantes = cursor.fetchall()

    informes = [_construir_contexto_informe_final(cursor, e) for e in estudiantes]
    conn.close()

    return render_template(
        'informe_final_lote.html',
        informes=informes,
        carga={'Nombre_Grupo': grupo['Nombre_Grupo'] if grupo else ''}
    )

@boletin_bp.route('/observador/<int:id_estudiante>')
@login_required
def observador(id_estudiante):
    conn = get_db_connection()
    conn.row_factory = lambda cursor, row: dict(zip([col[0] for col in cursor.description], row))
    cursor = conn.cursor()
    
    cursor.execute("SELECT e.*, g.Nombre_Grupo FROM estudiantes e JOIN grupos g ON e.ID_Grupo = g.ID_Grupo WHERE e.ID_Estudiante = %s", (id_estudiante,))
    estudiante = cursor.fetchone()
    
    cursor.execute("SELECT Periodo, Observacion, Fallas FROM observador_estudiante WHERE ID_Estudiante = %s ORDER BY Periodo", (id_estudiante,))
    periodos = cursor.fetchall()
    
    cursor.execute("SELECT * FROM observador_anual WHERE ID_Estudiante = %s", (id_estudiante,))
    anual = cursor.fetchone()
    
    titular = _obtener_titular_grupo(cursor, estudiante['ID_Grupo'])
    conn.close()
    
    return render_template('observador.html', estudiante=estudiante, periodos=periodos, anual=anual, 
                           titular_nombre=titular['nombre'], firma_titular=titular['firma'],
                           directora_nombre=DIRECTORA_NOMBRE, firma_directora=DIRECTORA_FIRMA,
                           current_year=datetime.now().year)

@boletin_bp.route('/observador/editar/<int:id_estudiante>', methods=['GET', 'POST'])
@login_required
def editar_observador(id_estudiante):
    conn = get_db_connection()
    conn.row_factory = lambda cursor, row: dict(zip([col[0] for col in cursor.description], row))
    cursor = conn.cursor()
    
    if request.method == 'POST':
        obs = request.form.get('observaciones_generales')
        concepto = request.form.get('concepto_final')
        prom = request.form.get('promovido_a')
        
        cursor.execute("""
            INSERT INTO observador_anual (ID_Estudiante, Observaciones_Generales, Concepto_Final, Promovido_A)
            VALUES (%s, %s, %s, %s) ON CONFLICT(ID_Estudiante) DO UPDATE SET 
            Observaciones_Generales=excluded.Observaciones_Generales, Concepto_Final=excluded.Concepto_Final, Promovido_A=excluded.Promovido_A
        """, (id_estudiante, obs, concepto, prom))
        conn.commit()
        conn.close()
        flash('Observador actualizado', 'success')
        return redirect(url_for('boletin_bp.observador', id_estudiante=id_estudiante))
    
    cursor.execute("SELECT * FROM estudiantes WHERE ID_Estudiante = %s", (id_estudiante,))
    estudiante = cursor.fetchone()
    cursor.execute("SELECT * FROM observador_anual WHERE ID_Estudiante = %s", (id_estudiante,))
    anual = cursor.fetchone()
    conn.close()
    return render_template('editar_observador.html', estudiante=estudiante, anual=anual)
