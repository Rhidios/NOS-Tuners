import datetime

reasons_and_sanctions = {
    1: {"color": "Sancion Blanca", "amount": "$30,000", "reason": "No reabastecer las cajas en las grúas."},
    2: {"color": "Sancion Blanca", "amount": "$30,000", "reason": "No repostar gasolina en las grúas."},
    3: {"color": "Sancion Blanca", "amount": "$30,000", "reason": "Abandonar grúas en áreas no autorizadas."},
    4: {"color": "Sancion Blanca", "amount": "$50,000", "reason": "Utilizar el teléfono de manera irresponsable."},
    5: {"color": "Sancion Amarilla", "amount": "$50,000", "reason": "Utilizar la radio de manera irresponsable (OOC / IC)."},
    6: {"color": "Sancion Amarilla", "amount": "$60,000", "reason": "No informar sobre las facturas de actividad."},
    7: {"color": "Sancion Blanca", "amount": "$30,000", "reason": "Participación insuficiente en tareas de campo."},
}

def is_within_30_days(timestamp, current_timestamp):
    timestamp_datetime = datetime.datetime.fromisoformat(timestamp)
    current_datetime = datetime.datetime.fromisoformat(current_timestamp)
    return (current_datetime - timestamp_datetime).days <= 30

def get_expiration_date(timestamp):
    timestamp_datetime = datetime.datetime.fromisoformat(timestamp)
    expiration_datetime = timestamp_datetime + datetime.timedelta(days=30)
    return expiration_datetime.strftime('%d/%m/%Y')
