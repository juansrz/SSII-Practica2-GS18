from flask import Flask, render_template, request, make_response
import analisis
import analisis_Practica2 as analisis2
import vulnerabilidades
from xhtml2pdf import pisa
from io import BytesIO
from datetime import datetime

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/resultados")
def resultados():
    # Variables generales de analisis.py
    total_incid = analisis.total_incidencias
    media_satis_5 = analisis.media_satis_5
    std_satis_5 = analisis.std_satis_5
    media_incid = analisis.media_incid
    std_incid = analisis.std_incid
    media_horas = analisis.media_horas
    std_horas = analisis.std_horas
    min_horas = analisis.min_horas
    max_horas = analisis.max_horas
    min_duracion = analisis.min_duracion
    max_duracion = analisis.max_duracion
    min_incid_emp = analisis.min_incid_emp
    max_incid_emp = analisis.max_incid_emp

    # Diccionario con los resultados de las agrupaciones
    agrupaciones = {
        "Empleado": {
            "tabla": analisis.group_empleado.to_html(classes="table", index=False),
            "estadisticas": {
                "Mediana": analisis.mediana_empleado,
                "Media": analisis.media_empleado,
                "Varianza": analisis.varianza_empleado,
                "Máximo": analisis.max_empleado,
                "Mínimo": analisis.min_empleado
            }
        },
        "Nivel": {
            "tabla": analisis.group_nivel.to_html(classes="table", index=False),
            "estadisticas": {
                "Mediana": analisis.mediana_nivel,
                "Media": analisis.media_nivel,
                "Varianza": analisis.varianza_nivel,
                "Máximo": analisis.max_nivel,
                "Mínimo": analisis.min_nivel
            }
        },
        "Cliente": {
            "tabla": analisis.group_cliente.to_html(classes="table", index=False),
            "estadisticas": {
                "Mediana": analisis.mediana_cliente,
                "Media": analisis.media_cliente,
                "Varianza": analisis.varianza_cliente,
                "Máximo": analisis.max_cliente,
                "Mínimo": analisis.min_cliente
            }
        },
        "Tipo incidencia": {
            "tabla": analisis.group_incidencia.to_html(classes="table", index=False),
            "estadisticas": {
                "Mediana": analisis.mediana_incidencia,
                "Media": analisis.media_incidencia,
                "Varianza": analisis.varianza_incidencia,
                "Máximo": analisis.max_incidencia,
                "Mínimo": analisis.min_incidencia
            }
        },
        "Día de la semana": {
            "tabla": analisis.group_dia.to_html(classes="table", index=False),
            "estadisticas": {
                "Mediana": analisis.mediana_dia,
                "Media": analisis.media_dia,
                "Varianza": analisis.varianza_dia,
                "Máximo": analisis.max_dia,
                "Mínimo": analisis.min_dia
            }
        }
    }

    return render_template(
        "resultados.html",
        total=total_incid,
        media_satis_5=media_satis_5,
        std_satis_5=std_satis_5,
        media_incid=media_incid,
        std_incid=std_incid,
        media_horas=media_horas,
        std_horas=std_horas,
        min_horas=min_horas,
        max_horas=max_horas,
        min_duracion=min_duracion,
        max_duracion=max_duracion,
        min_incid_emp=min_incid_emp,
        max_incid_emp=max_incid_emp,
        agrupaciones=agrupaciones
    )

@app.route("/practica2")
def practica2():
    ver = request.args.get("ver", "todo")  # Por defecto, muestra todo

    top_clientes_html = None
    top_tipos_tiempo_html = None
    tiempo_empleado_html = None

    if ver in ["clientes", "todo"]:
        top_clientes_html = analisis2.obtener_top_clientes().to_html(classes="table", index=False)
    if ver in ["tipos", "todo"]:
        top_tipos_tiempo_html = analisis2.obtener_top_tipos_tiempo().to_html(classes="table", index=False)
    if ver in ["empleados", "todo"]:
        tiempo_empleado_html = analisis2.obtener_top_empleados_por_tiempo().to_html(classes="table", index=False)

    return render_template(
        "practica2.html",
        ver=ver,
        top_clientes=top_clientes_html,
        top_tipos_tiempo=top_tipos_tiempo_html,
        tiempo_empleado=tiempo_empleado_html
    )

@app.route("/vulnerabilidades")
def mostrar_vulnerabilidades():
    lista_cves = vulnerabilidades.obtener_ultimas_vulnerabilidades(10)
    return render_template("vulnerabilidades.html", cves=lista_cves)

@app.route("/generar_pdf")
def generar_pdf():
    fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")

    # Construcción dinámica de secciones del informe
    secciones = [
        {
            "id": "actuaciones",
            "titulo": "Actuaciones por empleado",
            "contenido": analisis.group_empleado.to_html(classes="table", index=False)
        },
        {
            "id": "tiempo_inc",
            "titulo": "Tiempo medio por tipo de incidencia",
            "contenido": analisis2.obtener_top_tipos_tiempo().to_html(classes="table", index=False)
        },
        {
            "id": "clientes_criticos",
            "titulo": "Clientes más críticos",
            "contenido": analisis2.obtener_top_clientes().to_html(classes="table", index=False)
        },
        {
            "id": "tiempo_mant",
            "titulo": "Tiempo medio de mantenimiento",
            "contenido": analisis2.obtener_top_empleados_por_tiempo().to_html(classes="table", index=False)
        }
    ]

    html = render_template(
        "informe.html",
        fecha=fecha_actual,
        secciones=secciones,
        urjc_logo="static/images/URJC.png",
        si_logo="static/images/SI.png"
    )

    pdf = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=pdf)

    if pisa_status.err:
        return "Error al generar PDF", 500

    response = make_response(pdf.getvalue())
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = "inline; filename=informe_CMI.pdf"

    return response


if __name__ == "__main__":
    app.run(debug=True)