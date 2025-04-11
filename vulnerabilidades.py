import requests

def obtener_ultimas_vulnerabilidades(n=10):
    try:
        url = "https://cve.circl.lu/api/last"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            validos = []

            for cve in data:
                # Inicialización por defecto
                cve_id = cve.get("cveMetadata", {}).get("cveId", "N/A")
                publicado = cve.get("cveMetadata", {}).get("datePublished", "Fecha no disponible")

                descriptions = (
                    cve.get("containers", {})
                       .get("cna", {})
                       .get("descriptions", [])
                )
                if descriptions and isinstance(descriptions[0], dict):
                    resumen = descriptions[0].get("value", "Sin descripción")
                else:
                    resumen = "Sin descripción"

                cvss_score = "N/A"
                metrics = cve.get("containers", {}).get("cna", {}).get("metrics", [])
                if metrics:
                    if "cvssV3_1" in metrics[0]:
                        cvss_score = metrics[0]["cvssV3_1"].get("baseScore", "N/A")
                    elif "cvssV4_0" in metrics[0]:
                        cvss_score = metrics[0]["cvssV4_0"].get("baseScore", "N/A")

                # Validación
                if cve_id != "N/A" and resumen != "Sin descripción" and publicado != "Fecha no disponible":
                    print(f"CVE válida: {cve_id} | CVSS: {cvss_score} | Fecha: {publicado}")
                    validos.append({
                        "cve_id": cve_id,
                        "resumen": resumen,
                        "publicado": publicado[:10],
                        "cvss": cvss_score
                    })
                else:
                    # Clasificación por fuente
                    if "cveMetadata" in cve:
                        fuente = "NVD/MITRE"
                    elif cve.get("id", "").startswith("GHSA"):
                        fuente = "GitHub Advisory"
                    elif "schema_version" in cve and "summary" in cve:
                        fuente = "Otro feed estructurado (OSS Index, distro advisory...)"
                    else:
                        fuente = "Fuente desconocida"

                    print(f"Entrada omitida ({fuente})")
                    if cve_id == "N/A":
                        print("   - Falta de ID (cveMetadata → cveId)")
                    if resumen == "Sin descripción":
                        print("   - Falta de resumen (containers → cna → descriptions)")
                    if publicado == "Fecha no disponible":
                        print("   - Falta de fecha (cveMetadata → datePublished)")


                if len(validos) == n:
                    break

            return validos

        else:
            return [{
                "cve_id": "Error",
                "resumen": f"Error al obtener CVEs (status {response.status_code})",
                "publicado": "",
                "cvss": ""
            }]

    except Exception as e:
        return [{
            "cve_id": "Excepción",
            "resumen": str(e),
            "publicado": "",
            "cvss": ""
        }]
