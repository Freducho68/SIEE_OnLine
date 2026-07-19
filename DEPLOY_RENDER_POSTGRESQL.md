# 🚀 Desplegar SIEE en Render (PostgreSQL)

## ✅ Cambios Realizados

Tu proyecto ha sido migrado de **MySQL** a **PostgreSQL**. Esto te permite usar Render completamente gratis (sin tarjeta de crédito).

### Archivos Modificados

- **models_postgresql.py** → Reemplaza el antiguo `models.py`
- **config_postgresql.py** → Reemplaza el antiguo `config.py`
- **requirements_postgresql.txt** → Reemplaza el antiguo `requirements.txt`

### Cambios Principales

| Aspecto | MySQL | PostgreSQL |
|---------|-------|-----------|
| Base de datos | MariaDB local | PostgreSQL en Render |
| Driver | `PyMySQL` | `psycopg2-binary` |
| Tipos de datos | `AUTO_INCREMENT` | `SERIAL` |
| Costo | Gratis pero necesita tarjeta | **Completamente gratis** |

---

## 📋 Pasos para Desplegar

### 1. **Actualizar archivos locales**

En tu carpeta del proyecto:

```bash
# Reemplaza estos 3 archivos
# Renombra los que descargas quitando el "_postgresql"
# models_postgresql.py → models.py
# config_postgresql.py → config.py  
# requirements_postgresql.txt → requirements.txt
```

### 2. **Subir cambios a GitHub**

```bash
git add .
git commit -m "Migrar a PostgreSQL para Render"
git push
```

### 3. **Crear base de datos en Render**

Ve a https://dashboard.render.com

1. Click **New +** → **PostgreSQL**
2. **Name:** `siee-db`
3. **Database:** `siee_db`
4. **Region:** Elige cercana a Colombia (us-east)
5. Click **Create Database**

Espera ~2 minutos a que se cree.

Cuando esté lista, copia estas credenciales:
- **Host**
- **Port**
- **Database**
- **User**
- **Password**

### 4. **Actualizar Web Service en Render**

Ve a tu servicio web `siee-app`:

1. Click en **Environment**
2. Agrega estas variables:
   ```
   DB_HOST = <copias del paso 3>
   DB_USER = <copias del paso 3>
   DB_PASSWORD = <copias del paso 3>
   DB_NAME = siee_db
   DB_PORT = 5432
   FLASK_DEBUG = 0
   ```
3. Click **Save**

Render va a redeployer automáticamente (~2 minutos).

### 5. **Verificar que funciona**

Espera a que termine el deploy (status debe decir "Live").

Abre: `https://siee-app.onrender.com`

Deberías ver el login. Intenta con `admin / admin123`.

---

## 🆘 Si Hay Errores

### Error: "relation does not exist"

La BD está vacía. Render debería crearla automáticamente, pero si no:

1. En Render, ve a tu **PostgreSQL database**
2. Click en **Connect**
3. Usa **psql** o la consola web para ejecutar:

```sql
CREATE DATABASE siee_db;
```

### Error: "password authentication failed"

Verifica que las variables de entorno en Render coinciden exactamente con las credenciales de PostgreSQL.

### La app no levanta

1. Ve a **siee-app** en Render
2. Click en **Logs**
3. Busca el error rojo
4. Reporta lo que dice

---

## 📊 Comparación: MySQL vs PostgreSQL

| Característica | MySQL | PostgreSQL |
|---|---|---|
| Gratis en Render | ❌ | ✅ |
| Tarjeta de crédito | ✅ Necesita | ❌ No necesita |
| Costo base | $39/mes | $0 |
| Rendimiento | Bueno | ⭐ Mejor |
| JSON support | Básico | ⭐ Excelente |
| Escalabilidad | Buena | ⭐ Mejor |

---

## ✅ Checklist de Verificación

- [ ] Copié y renombré los 3 archivos (sin el sufijo "_postgresql")
- [ ] Ejecuté `pip install -r requirements.txt`
- [ ] Subí cambios a GitHub (`git push`)
- [ ] Creé la BD PostgreSQL en Render
- [ ] Configuré las variables de entorno en el Web Service
- [ ] El deploy terminó sin errores (status "Live")
- [ ] Accedí a la URL y vi el login
- [ ] Logueé con `admin / admin123`
- [ ] Creé un docente de prueba
- [ ] Logueé con ese docente

¿Completaste todo? Avísame si algo falla.

---

## 🎯 Resultado Final

Tu aplicación estará:
- ✅ Online 24/7 (en la nube)
- ✅ Accesible desde internet (docentes desde sus casas)
- ✅ Con base de datos en PostgreSQL (gratis)
- ✅ Sin costo de servidor
- ✅ Auto-escalable con Render

**Próximo paso después de verificar:** Compartir el link con los docentes y empezar a cargar notas online. 🎓
