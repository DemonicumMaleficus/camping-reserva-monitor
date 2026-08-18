import json
import os
import smtplib
import urllib.request
from email.message import EmailMessage

URL = "https://thelisresa.webcamp.fr/2017/services/Search/search?camping=bhplata94"

STATE_FILE = "availability_state.json"

payload = {
    "dates": {
        "begin": "2027-07-30",
        "end": "2027-08-16",
        "criteria": []
    },
    "type": "Bungalow",
    "nb_pers": "2duration=17",
    "promoCode": "",
    "duration": 17,
    "global_criteria": {
        "surface": None,
        "nb_bedrooms": None,
        "nb_bathrooms": None
    },
    "chosenSite": None
}

# Leer estado anterior
try:
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        state = json.load(f)
except FileNotFoundError:
    state = {"available": False}

previously_available = state.get("available", False)

# Hacer la búsqueda
data = json.dumps(payload).encode("utf-8")

request = urllib.request.Request(
    URL,
    data=data,
    method="POST",
    headers={
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": "https://thelisresa.webcamp.fr",
        "User-Agent": "Mozilla/5.0"
    }
)

with urllib.request.urlopen(request, timeout=30) as response:
    raw = response.read().decode("utf-8")

print("Respuesta:", raw)

result = json.loads(raw)
results = result.get("results", [])

available = bool(results)

print("Disponibilidad:", available)
print("Resultados:", len(results))

# Si NO hay disponibilidad
if not available:
    print("Sin disponibilidad todavía.")

    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"available": False}, f)

    exit(0)

# Hay disponibilidad
print("¡¡¡ DISPONIBILIDAD ENCONTRADA !!!")

# Si ya habíamos avisado, no mandar otro correo
if previously_available:
    print("Ya se había enviado un aviso anteriormente. No se envía otro.")
    exit(0)

# Primera detección de disponibilidad
smtp_host = os.environ["SMTP_HOST"]
smtp_port = int(os.environ.get("SMTP_PORT", "587"))
smtp_user = os.environ["SMTP_USER"]
smtp_password = os.environ["SMTP_PASSWORD"]
email_to = os.environ["EMAIL_TO"]

msg = EmailMessage()
msg["Subject"] = "🚨 ¡DISPONIBILIDAD! Camping La Plata 2027"
msg["From"] = smtp_user
msg["To"] = email_to

msg.set_content(
    "¡ATENCIÓN!\n\n"
    "El sistema de reservas del Camping La Plata "
    "ha detectado disponibilidad.\n\n"
    "Entrada: 30/07/2027\n"
    "Salida: 16/08/2027\n"
    "Duración: 17 noches\n"
    "Personas: 2\n"
    "Tipo: Bungalow\n\n"
    "Comprueba la reserva inmediatamente:\n"
    "https://thelisresa.webcamp.fr/list.php"
)

with smtplib.SMTP(smtp_host, smtp_port) as server:
    server.starttls()
    server.login(smtp_user, smtp_password)
    server.send_message(msg)

print("🚨 Correo de disponibilidad enviado.")

# Guardar que ya hemos avisado
with open(STATE_FILE, "w", encoding="utf-8") as f:
    json.dump({"available": True}, f)
