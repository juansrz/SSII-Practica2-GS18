import sqlite3
import pandas as pd
from datetime import datetime

# 1) Conectamos y leemos los datos
conn = sqlite3.connect("incidencias.db")
df_tickets = pd.read_sql_query("SELECT * FROM tickets", conn)
df_contactos = pd.read_sql_query("SELECT * FROM contactos_empleados", conn)
df_empleados = pd.read_sql_query("SELECT * FROM empleados", conn)
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

# -----------------------------------------------------------------------------
#                                   Análisis
# -----------------------------------------------------------------------------

# 1) Número de incidencias totales
total_incidencias = len(df_tickets)

# 2) Incidencias con satisfaccion_cliente >= 5
df_satis_5 = df_tickets[df_tickets["satisfaccion_cliente"] >= 5]
num_satis_5 = len(df_satis_5)

# Media y desviación std del total de incidencias (con sat >=5) por cliente
group_satis = df_satis_5.groupby("cliente").size()
media_satis_5 = group_satis.mean()
std_satis_5 = group_satis.std(ddof=1)

# 3) Media y std de número de incidentes por cliente
group_incidencias = df_tickets.groupby("cliente").size()
media_incid = group_incidencias.mean()
std_incid = group_incidencias.std(ddof=1)

# 4) Sumar horas de cada incidencia
horas_por_ticket = df_contactos.groupby("id_ticket")["tiempo"].sum().reset_index()
horas_por_ticket.columns = ["id_ticket", "horas_totales_incidente"]

media_horas = horas_por_ticket["horas_totales_incidente"].mean()
std_horas = horas_por_ticket["horas_totales_incidente"].std(ddof=1)

# 5) Mín y máx del total de horas realizadas por los empleados
horas_por_empleado = df_contactos.groupby("id_emp")["tiempo"].sum().reset_index()
min_horas = horas_por_empleado["tiempo"].min()
max_horas = horas_por_empleado["tiempo"].max()

# 6) Mín y máx del tiempo entre apertura y cierre en días
#    (Ya con fecha_cierre corregida)
df_tickets["duracion_dias"] = (df_tickets["fecha_cierre"] - df_tickets["fecha_apertura"]).dt.days
min_duracion = df_tickets["duracion_dias"].min()
max_duracion = df_tickets["duracion_dias"].max()

# 7) Mín y máx del número de incidentes atendidos por cada empleado
tickets_por_empleado = df_contactos.groupby("id_emp")["id_ticket"].nunique().reset_index()
min_incid_emp = tickets_por_empleado["id_ticket"].min()
max_incid_emp = tickets_por_empleado["id_ticket"].max()

# -----------------------------------------------------------------------------
# Mostramos los resultados
# -----------------------------------------------------------------------------
print(f"Total de incidencias: {total_incidencias}")
print(f"Media de incidencias (con sat >= 5) por cliente: {media_satis_5:.2f}, Desv: {std_satis_5:.2f}")
print(f"Media de incidencias por cliente: {media_incid:.2f}, Desv: {std_incid:.2f}")
print(f"Media de horas por incidencia: {media_horas:.2f}, Desv: {std_horas:.2f}")
print(f"Mín de horas totales por empleado: {min_horas:.2f}, Máx: {max_horas:.2f}")
print(f"Mín de duración (días) de un ticket: {min_duracion}, Máx: {max_duracion}")
print(f"Mín # incidencias atendidas por un empleado: {min_incid_emp}, Máx: {max_incid_emp}")



# -----------------------------------------------------------------------------
#                                   Agrupaciones
# -----------------------------------------------------------------------------

pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

df_fraude = df_tickets[df_tickets["tipo_incidencia"] == '5']
print(f"Numero de incidencias de fraude: {len(df_fraude)}\n")

# 1) Agrupaciones y calculos de incidencias y actuaciones en caso de fraude por empleado

group_fraude = df_contactos[df_contactos["id_ticket"].isin(df_fraude["id_ticket"])]

group_empleado = group_fraude.groupby("id_emp")["id_ticket"].nunique().reset_index(name="Incidencias")
group_empleado_actuaciones = group_fraude.groupby("id_emp")["id_ticket"].count().reset_index(name="Actuaciones")
group_empleado = group_empleado.merge(group_empleado_actuaciones, on="id_emp", how="left")

# Estadisticas basicas sobre el numero de incidencias de fraude por empleado
mediana_empleado = group_empleado["Incidencias"].median()
media_empleado = group_empleado["Incidencias"].mean()
varianza_empleado = group_empleado["Incidencias"].var()
max_empleado = group_empleado["Incidencias"].max()
min_empleado = group_empleado["Incidencias"].min()

print(f"Agrupacion por Empleado:\n{group_empleado}\n")
print(f"Estadisticas basicas por empleado:")
print(f"Mediana: {media_empleado}, Media: {mediana_empleado}, Varianza: {varianza_empleado}, Max: {max_empleado}, Min: {min_empleado}\n")


# 2) Agrupaciones y calculos de incidencias y actuaciones en caso de fraude por nivel de empleado

group_nivel = group_fraude.groupby("id_emp")["id_ticket"].nunique().reset_index(name="Incidencias")
group_nivel_actuaciones = group_fraude.groupby("id_emp")["id_ticket"].count().reset_index(name="Actuaciones")
group_nivel = group_nivel.merge(group_nivel_actuaciones, on="id_emp", how="left")
group_nivel = group_nivel.merge(df_empleados[["id_emp", "nivel"]], on="id_emp", how="left")
group_nivel = group_nivel.groupby("nivel", as_index=False)[["Incidencias", "Actuaciones"]].sum()

# Estadisticas basicas sobre el numero de incidencias de fraude por nivel de empleado
mediana_nivel = group_empleado["Incidencias"].median()
media_nivel = group_nivel["Incidencias"].mean()
varianza_nivel = group_nivel["Incidencias"].var()
max_nivel = group_nivel["Incidencias"].max()
min_nivel = group_nivel["Incidencias"].min()

print(f"Agrupacion por nivel de empleado:\n{group_nivel}\n")
print(f"Estadisticas basicas por nivel de empleado:")
print(f"Mediana: {mediana_nivel}, Media: {media_nivel}, Varianza: {varianza_nivel}, Max: {max_nivel}, Min: {min_nivel}\n")


# 3) Agrupaciones y calculos de incidencias y actuaciones en caso de fraude por cliente

group_cliente = df_fraude.groupby("cliente")["id_ticket"].nunique().reset_index(name="Incidencias")
group_cliente_actuaciones = group_fraude.merge(df_tickets[["id_ticket", "cliente"]], on="id_ticket", how="left")
group_cliente_actuaciones = group_cliente_actuaciones.groupby("cliente")["id_contacto"].count().reset_index(name="Actuaciones")
group_cliente = group_cliente.merge(group_cliente_actuaciones, on="cliente", how="left")


# Estadisticas basicas sobre el numero de incidencias de fraude por cliente
mediana_cliente = group_cliente["Incidencias"].median()
media_cliente = group_cliente["Incidencias"].mean()
varianza_cliente = group_cliente["Incidencias"].var()
max_cliente = group_cliente["Incidencias"].max()
min_cliente = group_cliente["Incidencias"].min()


print(f"Agrupacion por cliente:\n{group_cliente}\n")
print(f"Estadisticas basicas por cliente:")
print(f"Mediana: {mediana_cliente}, Media: {media_cliente}, Varianza: {varianza_cliente}, Max: {max_cliente}, Min: {min_cliente}\n")


# 4) Agrupaciones y calculos de incidencias y actuaciones en caso de fraude por tipo de incidencia

group_incidencia = df_fraude.groupby("tipo_incidencia")["id_ticket"].nunique().reset_index(name="Incidencias")
group_incidencia_actuaciones = group_fraude.merge(df_fraude[["id_ticket", "tipo_incidencia"]], on="id_ticket", how="inner")
group_incidencia_actuaciones = (group_incidencia_actuaciones.groupby("tipo_incidencia")["fecha"].count().reset_index(name="Actuaciones"))
group_incidencia = group_incidencia.merge(group_incidencia_actuaciones, on="tipo_incidencia", how="left")



# Estadisticas basicas sobre el numero de incidencias de fraude por tipo de incidencia
mediana_incidencia = group_incidencia["Incidencias"].median()
media_incidencia= group_incidencia["Incidencias"].mean()
varianza_incidencia = group_incidencia["Incidencias"].var()
max_incidencia = group_incidencia["Incidencias"].max()
min_incidencia = group_incidencia["Incidencias"].min()

print(f"Agrupacion por tipo de incidencia:\n{group_incidencia}\n")
print(f"Estadisticas basicas por tipo de incidencia:")
print(f"Mediana: {mediana_incidencia}, Media: {media_incidencia}, Varianza: {varianza_incidencia}, Max: {max_incidencia}, Min: {min_incidencia}\n")


# 5) Agrupaciones y calculos de incidencias y actuaciones en caso de fraude por dia de la semana

group_fraude = df_contactos[df_contactos["id_ticket"].isin(df_fraude["id_ticket"])].copy()
group_fraude_incidencias = group_fraude.groupby("id_ticket")["fecha"].min().reset_index()
group_fraude["dia_semana"] = group_fraude["fecha"].dt.dayofweek
group_fraude_incidencias["dia_semana"] = group_fraude_incidencias["fecha"].dt.dayofweek

group_dia = group_fraude_incidencias.groupby("dia_semana")["id_ticket"].nunique().reset_index(name="Incidencias")
group_dia_actuaciones = group_fraude.groupby("dia_semana")["id_ticket"].count().reset_index(name="Actuaciones")

dias = pd.DataFrame({"dia_semana": range(0, 7)})
group_dia = dias.merge(group_dia, on="dia_semana", how="left").fillna(0)
group_dia_actuaciones = dias.merge(group_dia_actuaciones, on="dia_semana", how="left")

group_dia = group_dia.merge(group_dia_actuaciones, on="dia_semana", how="left")


# Estadisticas basicas sobre el numero de incidencias de fraude por día de la semana
mediana_dia = group_dia["Incidencias"].median()
media_dia = group_dia["Incidencias"].mean()
varianza_dia = group_dia["Incidencias"].var()
max_dia = group_dia["Incidencias"].max()
min_dia = group_dia["Incidencias"].min()

print(f"Agrupacion por dia de la semana:\n{group_dia}\n")
print(f"Estadisticas basicas por dia de la semana:")
print(f"Mediana: {mediana_dia}, Media: {media_dia}, Varianza: {varianza_dia}, Max: {max_dia}, Min: {min_dia}\n")

# ----------------------------------------------------------------------
# Duración de incidencias de fraude
# ----------------------------------------------------------------------

df_fraude.loc[:, "duracion_dias"] = (df_fraude["fecha_cierre"] - df_fraude["fecha_apertura"]).dt.days

mediana_duracion_fraude = df_fraude["duracion_dias"].median()
media_duracion_fraude = df_fraude["duracion_dias"].mean()
varianza_duracion_fraude = df_fraude["duracion_dias"].var()
max_duracion_fraude = df_fraude["duracion_dias"].max()
min_duracion_fraude = df_fraude["duracion_dias"].min()

print(f"\n--- Estadísticas de duración (días) de incidentes de fraude ---")
print(f"Mediana: {mediana_duracion_fraude}")
print(f"Media: {media_duracion_fraude}")
print(f"Varianza: {varianza_duracion_fraude}")
print(f"Máximo: {max_duracion_fraude}")
print(f"Mínimo: {min_duracion_fraude}")


__all__ = ["df_tickets", "df_contactos", "df_empleados"]

conn.close()
