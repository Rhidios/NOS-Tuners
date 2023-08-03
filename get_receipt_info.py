import json

def get_next_activity_number():
    with open('data.json', 'r') as file:
        data = json.load(file)
        activity_number = int(data['actividad_numero'])
        receipts = data.get('recibos', [])
    return activity_number, receipts

def update_activity_number(activity_number, receipts):
    with open('data.json', 'w') as file:
        data = {
            "actividad_numero": activity_number,
            "recibos": receipts
        }
        json.dump(data, file)

def get_receipts_for_user(user_id):
    activity_number, receipts = get_next_activity_number()
    receipts_for_user = [receipt for receipt in receipts if receipt["UserID"] == user_id]
    return receipts_for_user

def is_allowed_role(ctx):
    allowed_roles = [1133497390247182396, 1133495683270332498, 1091845677455245352, 1091822086848266270, 1136467799900962836] #Last Id is for testing only
    return any(role.id in allowed_roles for role in ctx.author.roles)