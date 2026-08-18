import json
import os
import smtplib
import urllib.request
from email.message import EmailMessage

URL = "https://thelisresa.webcamp.fr/2017/services/Search/search?camping=bhplata94"

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

try:
    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read().decode("utf-8")

    print("Respuesta:", raw)

    result = json.loads(raw)
    results = result.get("results", [])

    if results:
        print("¡¡¡ DISPONIBILIDAD ENCONTRADA !!!")
        
        smtp_host = os.environ["SMTP_HOST"]
        smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        smtp_user = os.environ["SMTP_USER"]
        smtp_password = os.environ["SMTP_PASSWORD"]
        email_to = os.environ["EMAIL_TO"]

        msg = EmailMessage()
        msg["Subject"] = "🚨 ¡Reserva 2027 disponible!"
        msg["From"] = smtp_user
        msg["To"] = email_to

        msg.set_content(
            "¡Hay disponibilidad para el Camping La Plata!\n\n"
            "Entrada: 30/07/2027\n"
            "Salida: 16/08/2027\n"
            "Personas: 2\n\n"
            "Revisa la reserva inmediatamente."
        )

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

        print("Email enviado.")

    else:
        print("Sin disponibilidad todavía.")

except Exception as e:
    print("ERROR:", e)
    raise
