import json
import os
import smtplib
import urllib.request
from email.message import EmailMessage


# ============================================================
# CONFIGURACIÓN
# ============================================================

URL = (
    "https://thelisresa.webcamp.fr/"
    "2017/services/Search/search?camping=bhplata94"
)

# ------------------------------------------------------------
# BÚSQUEDA PRINCIPAL
# ------------------------------------------------------------

MAIN_SEARCH = {
    "begin": "2027-07-30",
    "end": "2027-08-16",
    "duration": 17
}


# ------------------------------------------------------------
# BÚSQUEDAS ALTERNATIVAS
# ------------------------------------------------------------
#
# Solo se realizan si la búsqueda principal está vacía.
#
# Son estancias cortas de 2 noches para aumentar la
# posibilidad de detectar que la temporada está abierta.
#
# Máximo: 8 peticiones adicionales.
#

ALTERNATIVE_SEARCHES = [
    # JULIO
    {
        "begin": "2027-07-01",
        "end": "2027-07-03",
        "duration": 2
    },
    {
        "begin": "2027-07-09",
        "end": "2027-07-11",
        "duration": 2
    },
    {
        "begin": "2027-07-17",
        "end": "2027-07-19",
        "duration": 2
    },
    {
        "begin": "2027-07-25",
        "end": "2027-07-27",
        "duration": 2
    },

    # AGOSTO
    {
        "begin": "2027-08-02",
        "end": "2027-08-04",
        "duration": 2
    },
    {
        "begin": "2027-08-10",
        "end": "2027-08-12",
        "duration": 2
    },
    {
        "begin": "2027-08-18",
        "end": "2027-08-20",
        "duration": 2
    },
    {
        "begin": "2027-08-26",
        "end": "2027-08-28",
        "duration": 2
    }
]


# Archivo donde guardamos el estado anterior
STATE_FILE = "availability_state.json"


# ============================================================
# HACER UNA BÚSQUEDA
# ============================================================

def buscar(begin, end, duration):

    payload = {
        "dates": {
            "begin": begin,
            "end": end,
            "criteria": []
        },
        "type": "Bungalow",
        "nb_pers": "2",
        "promoCode": "",
        "duration": duration,
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
            "Referer": (
                "https://thelisresa.webcamp.fr/"
                "list.php?camping=bhplata94"
            ),
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/150.0.0.0 Safari/537.36"
            )
        }
    )

    with urllib.request.urlopen(
        request,
        timeout=30
    ) as response:

        raw = response.read().decode("utf-8")

    return json.loads(raw)


# ============================================================
# EXTRAER ALOJAMIENTOS
# ============================================================

def extraer_alojamientos(response):

    alojamientos = []

    for campsite_result in response.get(
        "results",
        []
    ):

        campsite = campsite_result.get(
            "campsite",
            {}
        )

        campsite_name = campsite.get(
            "name",
            "Camping Bahía de la Plata"
        )

        for result_group in campsite_result.get(
            "results",
            []
        ):

            for item in result_group.get(
                "products",
                []
            ):

                product = item.get(
                    "product",
                    {}
                )

                nombre = product.get(
                    "name",
                    "Alojamiento"
                )

                stock = item.get(
                    "stock",
                    "N/D"
                )

                capacidad = product.get(
                    "capacity",
                    "N/D"
                )

                habitaciones = product.get(
                    "room",
                    "N/D"
                )

                banos = product.get(
                    "bathroom",
                    "N/D"
                )

                superficie = product.get(
                    "surface",
                    "N/D"
                )

                stays = item.get(
                    "stays",
                    []
                )

                for stay in stays:

                    alojamientos.append({
                        "camping": campsite_name,

                        "nombre": nombre,

                        "stock": stock,

                        "capacidad": capacidad,

                        "habitaciones": habitaciones,

                        "banos": banos,

                        "superficie": superficie,

                        "begin": stay.get(
                            "begin",
                            "N/D"
                        ),

                        "end": stay.get(
                            "end",
                            "N/D"
                        ),

                        "duration": stay.get(
                            "duration",
                            "N/D"
                        ),

                        "price": stay.get(
                            "price",
                            "N/D"
                        ),

                        "idproduct": product.get(
                            "idProduct",
                            {}
                        )
                    })

    return alojamientos


# ============================================================
# LEER ESTADO ANTERIOR
# ============================================================

try:

    with open(
        STATE_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        state = json.load(f)

except FileNotFoundError:

    state = {
        "main_available": False,
        "alternative_available": False
    }


previous_main = state.get(
    "main_available",
    False
)

previous_alternative = state.get(
    "alternative_available",
    False
)


# ============================================================
# ENVIAR EMAIL
# ============================================================

def enviar_email(
    subject,
    message
):

    smtp_host = os.environ["SMTP_HOST"]

    smtp_port = int(
        os.environ.get(
            "SMTP_PORT",
            "587"
        )
    )

    smtp_user = os.environ["SMTP_USER"]

    smtp_password = os.environ["SMTP_PASSWORD"]

    email_to = os.environ["EMAIL_TO"]

    msg = EmailMessage()

    msg["Subject"] = subject

    msg["From"] = smtp_user

    msg["To"] = email_to

    msg.set_content(message)

    with smtplib.SMTP(
        smtp_host,
        smtp_port
    ) as server:

        server.starttls()

        server.login(
            smtp_user,
            smtp_password
        )

        server.send_message(msg)


# ============================================================
# 1. BÚSQUEDA PRINCIPAL
# ============================================================

print("=" * 70)

print("BÚSQUEDA PRINCIPAL")

print("=" * 70)

print(
    f"Entrada: {MAIN_SEARCH['begin']}"
)

print(
    f"Salida:  {MAIN_SEARCH['end']}"
)

print(
    f"Duración: {MAIN_SEARCH['duration']} noches"
)

print(
    "Personas: 2"
)

print(
    "Tipo: Bungalow"
)

try:

    main_response = buscar(
        MAIN_SEARCH["begin"],
        MAIN_SEARCH["end"],
        MAIN_SEARCH["duration"]
    )

except Exception as e:

    print(
        f"❌ Error en la búsqueda principal: {e}"
    )

    exit(1)


main_accommodations = extraer_alojamientos(
    main_response
)


print(
    f"Resultados principales: "
    f"{len(main_accommodations)}"
)


# ============================================================
# 2. DISPONIBILIDAD EN NUESTRAS FECHAS
# ============================================================

if main_accommodations:

    print(
        "🚨 DISPONIBILIDAD EN TUS FECHAS"
    )

    # Evitar repetir el correo mientras siga disponible
    if previous_main:

        print(
            "Ya se había enviado un aviso "
            "de disponibilidad principal."
        )

        exit(0)


    lines = []


    for alojamiento in main_accommodations:

        lines.append(
            f"🏠 {alojamiento['nombre']}"
        )

        lines.append(
            f"   📦 Stock: "
            f"{alojamiento['stock']}"
        )

        lines.append(
            f"   👥 Capacidad: "
            f"{alojamiento['capacidad']} personas"
        )

        lines.append(
            f"   🛏️ Habitaciones: "
            f"{alojamiento['habitaciones']}"
        )

        lines.append(
            f"   🚿 Baños: "
            f"{alojamiento['banos']}"
        )

        lines.append(
            f"   📐 Superficie: "
            f"{alojamiento['superficie']} m²"
        )

        lines.append(
            f"   📅 "
            f"{alojamiento['begin']} → "
            f"{alojamiento['end']}"
        )

        lines.append(
            f"   🌙 Duración: "
            f"{alojamiento['duration']} noches"
        )

        lines.append(
            f"   💶 Precio: "
            f"{alojamiento['price']} €"
        )

        lines.append("")


    details = "\n".join(lines)


    message = (
        "🚨 ¡DISPONIBILIDAD EN TUS FECHAS!\n\n"

        "El Camping Bahía de la Plata "
        "ha encontrado disponibilidad "
        "para tu búsqueda.\n\n"

        "TU BÚSQUEDA\n"
        "================================\n"

        "Entrada: 30/07/2027\n"
        "Salida: 16/08/2027\n"
        "Duración: 17 noches\n"
        "Personas: 2\n"
        "Tipo: Bungalow\n\n"

        "ALOJAMIENTOS DISPONIBLES\n"
        "================================\n"

        + details +

        "\n"
        "🔗 RESERVAR:\n"
        "https://thelisresa.webcamp.fr/list.php\n"
    )


    enviar_email(
        "🚨 ¡DISPONIBILIDAD! "
        "Camping Bahía de la Plata",
        message
    )


    print(
        "📧 Correo de disponibilidad enviado."
    )


    with open(
        STATE_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            {
                "main_available": True,
                "alternative_available": False
            },
            f,
            indent=2
        )


    exit(0)


# ============================================================
# 3. NO HAY DISPONIBILIDAD PRINCIPAL
# ============================================================

print(
    "❌ No hay disponibilidad "
    "para tus fechas."
)

print(
    ""
)

print(
    "Comenzando búsquedas alternativas "
    "de 2 noches..."
)


# ============================================================
# 4. BÚSQUEDAS ALTERNATIVAS
# ============================================================

alternative_results = []

found_alternative = None


for alternative in ALTERNATIVE_SEARCHES:

    print(
        ""
    )

    print(
        "Comprobando:"
    )

    print(
        f"  {alternative['begin']} "
        f"→ "
        f"{alternative['end']}"
    )

    try:

        response = buscar(
            alternative["begin"],
            alternative["end"],
            alternative["duration"]
        )

        accommodations = extraer_alojamientos(
            response
        )

    except Exception as e:

        print(
            f"  ⚠️ Error: {e}"
        )

        continue


    if accommodations:

        print(
            "  ✅ ¡DISPONIBILIDAD ENCONTRADA!"
        )

        found_alternative = alternative

        for accommodation in accommodations:

            alternative_results.append(
                {
                    **accommodation,

                    "search_begin":
                        alternative["begin"],

                    "search_end":
                        alternative["end"]
                }
            )

        # Paramos inmediatamente.
        break

    else:

        print(
            "  ❌ Sin disponibilidad."
        )


# ============================================================
# 5. DISPONIBILIDAD EN OTRAS FECHAS
# ============================================================

if alternative_results:

    print(
        ""
    )

    print(
        "⚠️ SE HA DETECTADO "
        "DISPONIBILIDAD ALTERNATIVA."
    )


    # Evitar repetir el aviso
    if previous_alternative:

        print(
            "Ya se había enviado un aviso "
            "de disponibilidad alternativa."
        )

        exit(0)


    lines = []


    for alojamiento in alternative_results:

        lines.append(
            f"🏠 {alojamiento['nombre']}"
        )

        lines.append(
            f"   📅 Búsqueda: "
            f"{alojamiento['search_begin']} "
            f"→ "
            f"{alojamiento['search_end']}"
        )

        lines.append(
            f"   📅 Estancia devuelta: "
            f"{alojamiento['begin']} "
            f"→ "
            f"{alojamiento['end']}"
        )

        lines.append(
            f"   📦 Stock: "
            f"{alojamiento['stock']}"
        )

        lines.append(
            f"   👥 Capacidad: "
            f"{alojamiento['capacidad']} personas"
        )

        lines.append(
            f"   🛏️ Habitaciones: "
            f"{alojamiento['habitaciones']}"
        )

        lines.append(
            f"   🚿 Baños: "
            f"{alojamiento['banos']}"
        )

        lines.append(
            f"   📐 Superficie: "
            f"{alojamiento['superficie']} m²"
        )

        lines.append(
            f"   💶 Precio: "
            f"{alojamiento['price']} €"
        )

        lines.append("")


    details = "\n".join(lines)


    message = (
        "⚠️ ¡LA TEMPORADA 2027 "
        "PARECE ESTAR ABIERTA!\n\n"

        "No se ha encontrado disponibilidad "
        "para tus fechas principales:\n\n"

        "❌ 30/07/2027 → 16/08/2027\n"
        "❌ 17 noches\n"
        "❌ 2 personas\n"
        "❌ Bungalow\n\n"

        "PERO EL SISTEMA HA DEVUELTO "
        "DISPONIBILIDAD PARA UNA ESTANCIA "
        "CORTA:\n\n"

        "================================\n"

        + details +

        "\n"

        "Esto indica que el sistema de "
        "reservas está ofreciendo "
        "alojamientos durante el periodo "
        "de verano de 2027.\n\n"

        "👉 Entra rápidamente y prueba "
        "otras fechas.\n\n"

        "🔗 RESERVAS:\n"
        "https://thelisresa.webcamp.fr/list.php\n"
    )


    enviar_email(
        "⚠️ Temporada 2027 abierta - "
        "Prueba otras fechas",
        message
    )


    print(
        "📧 Correo de disponibilidad "
        "alternativa enviado."
    )


    with open(
        STATE_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            {
                "main_available": False,
                "alternative_available": True
            },
            f,
            indent=2
        )


    exit(0)


# ============================================================
# 6. NO HAY DISPONIBILIDAD EN NINGUNA BÚSQUEDA
# ============================================================

print(
    ""
)

print(
    "❌ No hay disponibilidad "
    "ni para tus fechas ni "
    "en las búsquedas alternativas."
)

print(
    "El monitor continuará vigilando."
)


# ============================================================
# RESTABLECER EL ESTADO
# ============================================================

with open(
    STATE_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        {
            "main_available": False,
            "alternative_available": False
        },
        f,
        indent=2
    )
