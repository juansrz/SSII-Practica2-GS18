import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# 1) Conectamos y leemos los datos
conn = sqlite3.connect("incidencias.db")
df_tickets = pd.read_sql_query("SELECT * FROM tickets", conn)
df_contactos = pd.read_sql_query("SELECT * FROM contactos_empleados", conn)
df_empleados = pd.read_sql_query("SELECT * FROM empleados", conn)
df_clientes = pd.read_sql_query("SELECT * FROM clientes", conn)
conn.close()

# 2) Convertimos las columnas de fecha a tipo datetime
df_tickets["fecha_apertura"] = pd.to_datetime(df_tickets["fecha_apertura"])
df_tickets["fecha_cierre"]   = pd.to_datetime(df_tickets["fecha_cierre"])
df_contactos["fecha"]        = pd.to_datetime(df_contactos["fecha"])

# 3) Calculamos la fecha de último contacto de cada ticket
df_max_contact = (
    df_contactos.groupby("id_ticket")["fecha"]
    .max()                               # fecha máxima por ticket
    .reset_index(name="last_contact")
)

# 4) Hacemos un merge para añadir esa columna a df_tickets
df_tickets = df_tickets.merge(df_max_contact, on="id_ticket", how="left")

# 5) Sobrescribimos fecha_cierre con la última actuación (si es mayor)
#    Para ello, tomamos el máximo entre [fecha_cierre original, last_contact]
df_tickets["fecha_cierre"] = df_tickets[["fecha_cierre", "last_contact"]].max(axis=1)

# ----------------------------------------------------------------------------- #
#                                   Graficos                                    #
# ----------------------------------------------------------------------------- #


# 1) Grafico de la media de tiempo (apertura-cierre) de los incidentes aprupados por la variable mantenimiento

df_tickets["duracion_dias"] = (df_tickets["fecha_cierre"] - df_tickets["fecha_apertura"]).dt.days

group_tiempo = df_tickets.groupby("es_mantenimiento")["duracion_dias"].mean().reset_index()
group_tiempo["es_mantenimiento"] = group_tiempo["es_mantenimiento"].map({0: "No Mantenimiento", 1: "Mantenimiento"})

plt.figure(figsize=(12, 6))
plt.bar(group_tiempo["es_mantenimiento"], group_tiempo["duracion_dias"], color=["red", "blue"])
plt.xlabel("Tipo de incidencia")
plt.ylabel("Media de tiempo en dias")
plt.title("Tiempo medio de resolucion de incidencias")
plt.ylim(1)
plt.savefig(os.path.join("static", "images", "tiempo_mant.png"))
plt.close()


# 2) Gráfico boxplot con los tiempos de resolución por tipo de incidente

group_incidencias = df_tickets.groupby("tipo_incidencia")["duracion_dias"].apply(list)

fig, ax = plt.subplots(figsize=(12, 6))

# Boxplot estándar
ax.boxplot(
    [group_incidencias[tipo] for tipo in group_incidencias.index],
    vert=True,
    patch_artist=True,
    tick_labels=group_incidencias.index
)

# Calculamos p5 y p90 de duracion_dias por tipo_incidencia
percentil5 = df_tickets.groupby("tipo_incidencia")["duracion_dias"].quantile(0.05)
percentil90 = df_tickets.groupby("tipo_incidencia")["duracion_dias"].quantile(0.90)

# Dibujamos líneas horizontales en p5 y p90 para cada grupo
for i, tipo in enumerate(group_incidencias.index, start=1):
    p5 = percentil5.loc[tipo]
    p90 = percentil90.loc[tipo]
    ax.hlines(y=p5,  xmin=i - 0.2, xmax=i + 0.2, color='red', linestyle='--')
    ax.hlines(y=p90, xmin=i - 0.2, xmax=i + 0.2, color='red', linestyle='--')

ax.set_title("Tiempo de resolución por tipo de incidencia")
ax.set_xlabel("Tipo de incidencia")
ax.set_ylabel("Tiempo de resolución (días)")
plt.savefig(os.path.join("static", "images", "tipo_incidencia.png"))
plt.close()



# 3) Grafico de analisis de los 5 clientes mas criticos dependiendo de variables mantenimiento y tipo de incidencia

df_criticos = df_tickets[(df_tickets["es_mantenimiento"] == 1) & (df_tickets["tipo_incidencia"] != '1')]

group_criticos = df_criticos.groupby("cliente")["id_ticket"].count().reset_index(name="Incidencias")
group_criticos = group_criticos.merge(df_clientes[["id_cli", "nombre"]], left_on="cliente", right_on="id_cli", how="left")
group_criticos = group_criticos.nlargest(5, "Incidencias")

plt.figure(figsize=(12, 6))
plt.bar(group_criticos["nombre"], group_criticos["Incidencias"], color=["blue", "orange", "grey", "yellow", "red"])
plt.xlabel("Clientes")
plt.ylabel("Numero de incidencias")
plt.title("Top 5 clientes mas criticos")
plt.ylim(0, max(group_criticos["Incidencias"]) + 1)
plt.savefig(os.path.join("static", "images", "critical_clients.png"))
plt.close()


# 4) Grafico de analisis de las actuaciones de los empleados

df_actuaciones = df_contactos.groupby("id_emp")["id_contacto"].count().reset_index(name="Actuaciones")
group_actuaciones = df_actuaciones.merge(df_empleados[["id_emp", "nombre"]], on="id_emp", how="left")

# Se pone por id de empleado por espacio y para mejorar la comprensión
# Si se quisiera poner por nombre de empleado cambiar group_actuaciones["nombre"]
plt.figure(figsize=(12, 6))
plt.bar(group_actuaciones["id_emp"], group_actuaciones["Actuaciones"], color=["blue", "orange", "grey", "yellow", "red", "brown", "green"])
plt.xlabel("Empleados")
plt.ylabel("Numero de actuaciones")
plt.title("Actuaciones por empleado")
plt.ylim(10, max(group_actuaciones["Actuaciones"]) + 1)
plt.savefig(os.path.join("static", "images", "actuaciones_empleado.png"))
plt.close()


# 5) Grafico de actuaciones según el día de la semana

df_contactos["dia_semana"] = df_contactos["fecha"].dt.dayofweek
group_actuaciones = df_contactos.groupby("dia_semana").size().reset_index(name="Actuaciones")

group_actuaciones["Dia"] = group_actuaciones["dia_semana"].map({0: "Lunes", 1: "Martes", 2: "Miercoles", 3: "Jueves", 4: "Viernes", 5: "Sabado", 6: "Domingo"})

plt.figure(figsize=(12, 6))
plt.bar(group_actuaciones["Dia"], group_actuaciones["Actuaciones"], color=["blue", "orange", "grey", "yellow", "red", "brown", "green"])
plt.title("Actuaciones de los empleados por dia de la semana")
plt.xlabel("Dia de la semana")
plt.ylabel("Numero de actuaciones")
plt.ylim(25)
plt.savefig(os.path.join("static", "images", "actuaciones_semana.png"))
plt.close()

conn.close()