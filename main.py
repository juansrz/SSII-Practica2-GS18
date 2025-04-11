import json          # Para trabajar con el contenido del archivo JSON
import sqlite3       # Para conectarnos y gestionar la base de datos SQLite
import pandas as pd  # Para analizar y manejar los datos de forma más cómoda

# Establecemos conexión con la base de datos (se crea si no existe)
conn = sqlite3.connect("incidencias.db")
cursor = conn.cursor()

# Borramos las tablas si ya existían para comenzar con una base limpia
cursor.execute("DROP TABLE IF EXISTS contactos_empleados;")
cursor.execute("DROP TABLE IF EXISTS tickets;")
cursor.execute("DROP TABLE IF EXISTS clientes;")
cursor.execute("DROP TABLE IF EXISTS empleados;")
cursor.execute("DROP TABLE IF EXISTS tipos_incidentes;")

# Creamos la tabla que guarda la información de los clientes
cursor.execute("""
CREATE TABLE clientes(
    id_cli TEXT PRIMARY KEY,
    nombre TEXT,
    telefono TEXT,
    provincia TEXT
);
""")

# Creamos la tabla que guarda los datos de cada empleado
cursor.execute("""
CREATE TABLE empleados(
    id_emp TEXT PRIMARY KEY,
    nombre TEXT,
    nivel INTEGER,
    fecha_contrato TEXT
);
""")

# Creamos la tabla que define los tipos de incidentes
cursor.execute("""
CREATE TABLE tipos_incidentes(
    id_inci TEXT PRIMARY KEY,
    nombre TEXT
);
""")

# Creamos la tabla principal de tickets (o incidencias)
cursor.execute("""
CREATE TABLE tickets(
    id_ticket INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente TEXT,
    fecha_apertura TEXT,
    fecha_cierre TEXT,
    es_mantenimiento INTEGER,
    satisfaccion_cliente INTEGER,
    tipo_incidencia TEXT,
    FOREIGN KEY (cliente) REFERENCES clientes(id_cli),
    FOREIGN KEY (tipo_incidencia) REFERENCES tipos_incidentes(id_inci)
);
""")

# Creamos la tabla que relaciona cada ticket con los empleados que lo atendieron
cursor.execute("""
CREATE TABLE contactos_empleados(
    id_contacto INTEGER PRIMARY KEY AUTOINCREMENT,
    id_ticket INTEGER,
    id_emp TEXT,
    fecha TEXT,
    tiempo REAL,
    FOREIGN KEY (id_ticket) REFERENCES tickets(id_ticket),
    FOREIGN KEY (id_emp) REFERENCES empleados(id_emp)
);
""")

# Abrimos el archivo JSON para leer la información de clientes, empleados, etc.
with open("datos.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Insertamos la información de los clientes en la tabla 'clientes'
for cli in data["clientes"]:
    cursor.execute("""
        INSERT INTO clientes(id_cli, nombre, telefono, provincia)
        VALUES (?, ?, ?, ?)
    """, (
        cli["id_cli"],
        cli["nombre"],
        cli["telefono"],
        cli["provincia"]
    ))

# Insertamos la información de los empleados en la tabla 'empleados'
for emp in data["empleados"]:
    cursor.execute("""
        INSERT INTO empleados(id_emp, nombre, nivel, fecha_contrato)
        VALUES (?, ?, ?, ?)
    """, (
        emp["id_emp"],
        emp["nombre"],
        emp["nivel"],
        emp["fecha_contrato"]
    ))

# Insertamos los distintos tipos de incidentes
for t_in in data["tipos_incidentes"]:
    cursor.execute("""
        INSERT INTO tipos_incidentes(id_inci, nombre)
        VALUES (?, ?)
    """, (
        t_in["id_inci"],
        t_in["nombre"]
    ))

# Insertamos cada ticket en la tabla 'tickets'
for ticket in data["tickets_emitidos"]:
    cursor.execute("""
        INSERT INTO tickets(cliente, fecha_apertura, fecha_cierre,
                            es_mantenimiento, satisfaccion_cliente, tipo_incidencia)
        VALUES(?, ?, ?, ?, ?, ?)
    """, (
        ticket["cliente"],
        ticket["fecha_apertura"],
        ticket["fecha_cierre"],
        1 if ticket["es_mantenimiento"] else 0,
        ticket["satisfaccion_cliente"],
        ticket["tipo_incidencia"]
    ))
    # Obtenemos el ID que se generó automáticamente para este ticket
    id_ticket = cursor.lastrowid

    # Insertamos la relación de cada empleado con el ticket correspondiente
    for contacto in ticket["contactos_con_empleados"]:
        cursor.execute("""
            INSERT INTO contactos_empleados(id_ticket, id_emp, fecha, tiempo)
            VALUES (?, ?, ?, ?)
        """, (
            id_ticket,
            contacto["id_emp"],
            contacto["fecha"],
            contacto["tiempo"]
        ))

# Obtenemos el query necesario para obtener la ultima fecha de actuacion para actualizarla despues
query_ultima_actuacion = """
    SELECT id_ticket, MAX(fecha) AS ultima_fecha
    FROM contactos_empleados
    GROUP BY id_ticket
    """

df_ultima_actuacion = pd.read_sql_query(query_ultima_actuacion, conn)

# Actualizamos la fecha_cierre en la tabla tickets con la ultima actuacion para cada ticket
for index, row in df_ultima_actuacion.iterrows():
    cursor.execute("""
        UPDATE tickets
        SET fecha_cierre = ?
        WHERE id_ticket = ?
    """, (
        row["ultima_fecha"],
        row["id_ticket"]
    ))


# Guardamos todos los cambios en la base de datos
conn.commit()
print("Datos insertados correctamente.")

# Leemos los datos de las tablas con Pandas para realizar alguna verificación
df_tickets = pd.read_sql_query("SELECT * FROM tickets;", conn)
df_contactos = pd.read_sql_query("SELECT * FROM contactos_empleados;", conn)

# Mostramos un conteo básico de tickets como ejemplo
print("\n=== Conteo de Tickets ===")
print(f"Número total de tickets: {len(df_tickets)}")

# Cerramos la conexión para liberar recursos
conn.close()
