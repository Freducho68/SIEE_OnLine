#!/usr/bin/env python3
"""
Script para verificar que PyMySQL puede conectar a MariaDB
Ejecuta esto ANTES de intentar correr la app
"""

import sys

print("=" * 60)
print("🧪 TEST DE CONEXIÓN MYSQL")
print("=" * 60)

# Verificar que PyMySQL está instalado
print("\n1️⃣ Verificando PyMySQL...")
try:
    import pymysql
    print("   ✅ PyMySQL instalado correctamente")
except ImportError:
    print("   ❌ PyMySQL NO está instalado")
    print("   Ejecuta: pip install PyMySQL")
    sys.exit(1)

# Intentar conectar
print("\n2️⃣ Intentando conectar a MySQL...")
try:
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="root",
        database="siee_db",
        charset="utf8mb4"
    )
    print("   ✅ Conexión exitosa a MySQL")
    
    # Verificar que la BD tiene tablas
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    print(f"   ✅ Base de datos contiene {len(tables)} tablas")
    
    # Listar tablas
    if tables:
        print("\n   Tablas encontradas:")
        for table in tables:
            print(f"     - {table[0]}")
    
    conn.close()
    
except pymysql.Error as e:
    print(f"   ❌ Error de conexión: {e}")
    print("\n   Posibles soluciones:")
    print("   1. ¿MariaDB está corriendo? (mysql -u root -p)")
    print("   2. ¿Contraseña correcta? (debería ser 'root')")
    print("   3. ¿Base de datos creada? (CREATE DATABASE siee_db;)")
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ TODAS LAS VERIFICACIONES PASARON")
print("=" * 60)
print("\nYa puedes ejecutar: python app.py")
