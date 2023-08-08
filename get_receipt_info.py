import json

def get_next_activity_number():
    with open('reciept.json', 'r') as file:
        data = json.load(file)
        activity_number = int(data['actividad_numero'])
    return activity_number

def update_activity_number(activity_number):
    with open('reciept.json', 'w') as file:
        data = {
            "actividad_numero": activity_number,
        }
        json.dump(data, file)

def get_industrial_activity():
    with open('industrial.json', 'r') as file:
        data = json.load(file)
        activity_number = int(data['actividad_numero'])
    return activity_number

def update_industrial_activity(activity_number):
    with open('industrial.json', 'w') as file:
        data = {
            "actividad_numero": activity_number
        }
        json.dump(data, file)

def get_roadfix_activity():
    with open('roadfix.json', 'r') as file:
        data = json.load(file)
        activity_number = int(data['actividad_numero'])
    return activity_number

def update_roadfix_activity(activity_number):
    with open('roadfix.json', 'w') as file:
        data = {
            "actividad_numero": activity_number
        }
        json.dump(data, file)

def get_receipts_for_user(user_id):
    activity_number, receipts = get_next_activity_number()
    receipts_for_user = [receipt for receipt in receipts if receipt["UserID"] == user_id]
    return receipts_for_user

def is_allowed_role(ctx):
    allowed_roles = [1133497390247182396, 1133495683270332498, 1091845677455245352, 1091822086848266270, 1136467799900962836] #Last Id is for testing only
    return any(role.id in allowed_roles for role in ctx.author.roles)

def get_sanctions_for_user(user_id):
    data = get_sanctions_data()
    user_id_str = str(user_id)
    if "sanctions" not in data:
        return []  # Return an empty list if no sanctions data is found
    sanctions = data["sanctions"].get(user_id_str, [])
    return sanctions


def get_sanctions_data():
    try:
        with open('sanctions.json', 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {"sanciones": {}}  # Initialize an empty dictionary for sanctions
    return data

def save_sanctions_data(data):
    with open('sanctions.json', 'w') as file:
        json.dump(data, file, indent=4)

def add_sanction(sanction):
    data = get_sanctions_data()
    user_id = str(sanction['UserID'])
    if "sanciones" not in data:
        data["sanciones"] = {}
    if user_id not in data["sanciones"]:
        data["sanciones"][user_id] = []
    data["sanciones"][user_id].append(sanction)
    save_sanctions_data(data)

def load_invoice_data():
    try:
        with open('invoices.json', 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {"users": {}}
    return data

def save_invoice_data(data):
    with open('invoices.json', 'w') as file:
        json.dump(data, file, indent=4)

def get_user_invoices(user_id):
    data = load_invoice_data()
    user_invoices = data["users"].get(str(user_id), 0)
    return user_invoices

def increment_user_invoices(user_id):
    data = load_invoice_data()
    user_invoices = data["users"].get(str(user_id), 0)
    data["users"][str(user_id)] = user_invoices + 1
    save_invoice_data(data)