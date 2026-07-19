# 🚀 Migración SIEE: SQLite → MySQL + Flask Remoto

## 📋 Cambios Realizados

Tu proyecto ha sido migrado de **SQLite (aplicación de escritorio)** a **MySQL (servidor web remoto)**. Aquí está lo que cambió:

### ✅ Archivos Modificados

1. **config.py** — Nuevas credenciales MySQL
2. **models.py** — Conexión a MySQL en lugar de SQLite
3. **app.py** — Escucha en `0.0.0.0:5000` (accesible remotamente)
4. **requirements.txt** — Nuevas dependencias (PyMySQL)

### ❌ Eliminado/Removido

- `launcher_siee.pyw` — Ya no se necesita (no es ejecutable compilado)
- `SIEE_App.spec` y `SIEE_Launcher.spec` — No más PyInstaller
- Toda la lógica de rutas locales en `config.py`

---

## 🔧 Pasos de Instalación

### 1. **Reemplazar los 4 archivos en tu proyecto**

Descargá los 4 archivos desde aquí:
- `config.py` → **Copia a la carpeta raíz del proyecto**
- `models.py` → **Copia a la carpeta raíz del proyecto**
- `app.py` → **Copia a la carpeta raíz del proyecto**
- `requirements.txt` → **Copia a la carpeta raíz del proyecto**

### 2. **Instalar dependencias**

Abrí CMD en la carpeta del proyecto y ejecutá:

```bash
pip install -r requirements.txt
```

Esto instala:
- Flask (servidor web)
- PyMySQL (conexión a MySQL/MariaDB)
- pandas y openpyxl (para Excel)
- python-dotenv (para variables de entorno)

### 3. **Verificar conexión a MySQL**

En CMD, verifica que MariaDB está corriendo:

```bash
cd "C:\Program Files\MariaDB 11.4\bin"
mysql -u root -p
```

Ingresa contraseña: `root`

Si ves `MariaDB [(none)]>` — ¡funciona!

Escribe `quit` para salir.

### 4. **Inicializar la Base de Datos**

En la carpeta de tu proyecto, en CMD:

```bash
python models.py
```

Esto crea todas las tablas en `siee_db`. Deberías ver:

```
✓ Base de datos inicializada correctamente
✓ Usuario admin creado (admin / admin123)
```

---

## 🚀 Ejecutar la Aplicación

En la carpeta del proyecto:

```bash
python app.py
```

Deberías ver algo como:

```
============================================================
🎓 Sistema de Gestión Académica SIEE
============================================================
📡 Servidor disponible en http://0.0.0.0:5000
💻 Accede desde: http://localhost:5000
🔧 Modo DEBUG: Desactivado
============================================================
```

Abre tu navegador en: **http://localhost:5000**

---

## 🔑 Credenciales de Acceso

| Usuario | Contraseña | Rol |
|---------|-----------|-----|
| admin | admin123 | Administrador |

Los docentes y estudiantes se crean desde el panel admin como antes.

---

## 📍 Estructura de Carpetas

```
tu-proyecto/
├── app.py                    ← MODIFICADO
├── config.py                 ← MODIFICADO
├── models.py                 ← MODIFICADO
├── requirements.txt          ← MODIFICADO
├── routes/                   ← Sin cambios
│   ├── admin.py
│   ├── auth.py
│   ├── docentes.py          ← NOTA: cambiará ligeramente
│   └── ... (otras rutas)
├── templates/                ← Sin cambios
├── static/                   ← Sin cambios
└── database.db              ← ELIMINADO (ahora está en MySQL)
```

---

## 🆘 Si no funciona

### Error: "pymysql" no está instalado
```bash
pip install PyMySQL
```

### Error: "Cannot connect to MySQL server"
- Verifica que MariaDB está corriendo: `mysql -u root -p`
- Verifica que usaste contraseña `root`
- Verifica que la base de datos `siee_db` existe (revisá en MySQL)

### Error: "Table already exists"
La base de datos ya tenía tablas. Si querés empezar limpio:

```bash
# En MySQL:
mysql -u root -p
DROP DATABASE siee_db;
```

Luego corre `python models.py` de nuevo.

### Error: "Connection refused"
MariaDB no está corriendo. Abrí Services de Windows y busca "MariaDB" → iniciá el servicio.

---

## 📝 Próximos Pasos (Importante)

Una vez que funcione localmente:

1. **Los docentes TODAVÍA no pueden ingresar online** — El servidor está en localhost
2. Cuando esté 100% estable, desplazaremos esto a un servidor en la nube ($5-10/mes)
3. En ese momento, los docentes accederán desde internet con un dominio real

Por ahora: **testea con usuarios locales, asegúrate que todo funciona, reporta bugs**.

---

## 🎯 Cambios Pequeños que Notarás

### En `routes/docentes.py`

El código sigue igual, PERO ahora todas las queries usan `%s` en lugar de `?`. Ejemplo:

**Antes (SQLite):**
```python
cursor.execute("SELECT * FROM usuarios WHERE Usuario = ?", (usuario,))
```

**Ahora (MySQL):**
```python
cursor.execute("SELECT * FROM usuarios WHERE Usuario = %s", (usuario,))
```

Si editas rutas manualmente, recuerda: **usa `%s` en MySQL, NO `?`**

---

## ✅ Checklist de Verificación

- [ ] Instalé MariaDB en Windows
- [ ] Creé la base de datos `siee_db`
- [ ] Copié los 4 archivos modificados
- [ ] Ejecuté `pip install -r requirements.txt`
- [ ] Ejecuté `python models.py` sin errores
- [ ] Ejecuté `python app.py` sin errores
- [ ] Accedí a `http://localhost:5000` en el navegador
- [ ] Inicié sesión con `admin / admin123`
- [ ] Probé crear un docente

¿Completaste todo? → Avísame qué funciona y qué no.

---

**Soporte:** Si hay errores, captura la pantalla de la terminal y reporta.
