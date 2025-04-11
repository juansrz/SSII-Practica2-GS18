# -----------------------------------------------------------------------------
#                                  ANALISIS PRACTICA 2
# -----------------------------------------------------------------------------

from analisis import df_tickets, df_contactos

def obtener_top_clientes(top_n=10):
    conteo_clientes = df_tickets.groupby("cliente").size().reset_index(name="n_incidencias")
    return conteo_clientes.sort_values(by="n_incidencias", ascending=False).head(top_n)

def obtener_top_tipos_tiempo(top_n=10):
    df_tickets["duracion"] = (df_tickets["fecha_cierre"] - df_tickets["fecha_apertura"]).dt.total_seconds() / 3600
    top_tipos = df_tickets.groupby("tipo_incidencia")["duracion"].mean().reset_index()
    return top_tipos.sort_values(by="duracion", ascending=False).head(top_n)

def obtener_top_empleados_por_tiempo(top_n=10):
    tiempo_empleado = df_contactos.groupby("id_emp")["tiempo"].sum().reset_index()
    return tiempo_empleado.sort_values(by="tiempo", ascending=False).head(top_n)
