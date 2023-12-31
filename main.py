import discord
import json
import asyncio
import datetime
import os

from discord.ext import commands
import fetchinfo
import sanctioncheck


intents = discord.Intents.all()

TOKEN = "MTEzNg.m--WnaQfwGAMxcw"

intents = discord.Intents().all()
client = discord.Client(intents = intents)
bot = commands.Bot(command_prefix='/', intents=intents)


messages_by_time = {
    "00:00": {"activity": "Reparacion Industrial", "channel_id": 1138166569210491032},
    "01:00": {"activity": "Reparacion en carretera", "channel_id": 1138166549459517512},
    "02:00": {"activity": "Entrega de Herramientas", "channel_id": 1091815853978292229},
    "03:00": {"activity": "Reparacion Industrial", "channel_id": 1138166569210491032},
    "05:00": {"activity": "Entrega de Herramientas", "channel_id": 1091815853978292229},
    "08:00": {"activity": "Reparacion en Carretera", "channel_id": 1138166549459517512},
    "11:00": {"activity": "Reparacion Industrial", "channel_id": 1138166569210491032},
    "13:00": {"activity": "Reparacion en Carretera", "channel_id": 1138166549459517512},
    "15:00": {"activity": "Entrega de Herramientas", "channel_id": 1091815853978292229},
    "17:00": {"activity": "Reparacion en Carretera", "channel_id": 1138166549459517512},
    "18:00": {"activity": "Entrega de Herramientas", "channel_id": 1091815853978292229},
    "20:00": {"activity": "Reparacion Industrial", "channel_id": 1138166569210491032},
    "21:00": {"activity": "Entrega de Herramientas", "channel_id": 1091815853978292229},
    "22:00": {"activity": "Reparacion en Carretera", "channel_id": 1138166549459517512},
}

scheduled_messages_running = False
scheduled_messages_lock = asyncio.Lock()

def clear_invoice_data():
    data = {"users": {}}
    with open('invoices.json', 'w') as file:
        json.dump(data, file, indent=4)

def clear_activity_data():
    data = {"users": {}}
    with open('user_activity.json', 'w') as file:
        json.dump(data, file, indent=4)

async def send_weekly_top_performers():
    # Load the data from user_activity.json and invoices.json JSON file
    user_weekly_data = fetchinfo.load_weekly_data()
    user_all_data = fetchinfo.load_invoice_data()  # Replace with the actual function to load the other JSON file

    specific_channel_id = 1091815853978292227  # Replace with the actual channel ID
    specific_channel = bot.get_channel(specific_channel_id)

    # Sort user_weekly_data based on activity count
    sorted_users = sorted(user_weekly_data["users"].items(), key=lambda x: x[1], reverse=True)
    # Create the top performers message
    top_performers_message = "Este es el top 3 de los mejores trabajadores de esta semana:\n"
    for i, (user_id, activity_count) in enumerate(sorted_users[:3]):
        user = bot.get_user(int(user_id))
        if user:
            top_performers_message += f"{i+1}. {user.mention} - {activity_count} actividades\n"

    sorted_users = sorted(user_all_data["users"].items(), key=lambda x: x[1], reverse=True)
    # Create the top activity users message using user_all_data
    top_activity_users_message = "Este es el top 3 de las personas que más actividades hicieron:\n"
    for i, (user_id, activity_count) in enumerate(sorted_users[:3]):
        user = bot.get_user(int(user_id))
        if user:
            top_activity_users_message += f"{i+1}. {user.mention} - {activity_count} actividades\n"

    # Send the complete top performers message
    await specific_channel.send(top_performers_message)

    # Send the complete top activity users message
    await specific_channel.send(top_activity_users_message)
    print("Trying to send top")

async def scheduled_announce_messages():
    global scheduled_messages_running
    while True:
        current_time = datetime.datetime.utcnow().strftime("%H:%M")
        if not scheduled_messages_running:
            if current_time == "23:59" and datetime.datetime.utcnow().weekday() == 4:  # 4 represents Friday
                print("Sending top")
                await send_weekly_top_performers()

        next_time = (datetime.datetime.utcnow() + datetime.timedelta(minutes=1)).replace(second=0, microsecond=0)
        time_difference = (next_time - datetime.datetime.utcnow()).total_seconds()
        await asyncio.sleep(time_difference)
        scheduled_messages_running = False


async def publish_scheduled_messages():
    global scheduled_messages_running
    while True:
        current_time = datetime.datetime.utcnow().strftime("%H:%M")
        if not scheduled_messages_running:
            async with scheduled_messages_lock:
                if not scheduled_messages_running:  # Double check the flag to avoid race condition
                    scheduled_messages_running = True

                    # Check if it's Saturday at 00:01
                    if current_time == "00:01" and datetime.datetime.utcnow().weekday() == 5:  # 5 represents Saturday
                        # Clear the contents of invoices.json
                        clear_invoice_data()
                        clear_activity_data()
                        print("Data cleared")

                    if current_time in messages_by_time:
                        activity_info = messages_by_time[current_time]
                        activity_type = activity_info["activity"]
                        channel_id = activity_info["channel_id"]

                        specific_channel = bot.get_channel(channel_id)
                        if specific_channel:
                            message_content = f":wrench: Actividad de **{activity_type}** disponible ahora! @everyone"
                            await specific_channel.send(message_content)
                        else:
                            print(f"Couldn't find the specific channel (ID: {channel_id}) to publish the message.")

                    # Calculate the time until the next scheduled message (1 minute interval in this example)
                    next_time = (datetime.datetime.utcnow() + datetime.timedelta(minutes=1)).replace(second=0, microsecond=0)

                    # Calculate the time difference between the current time and the next scheduled time
                    time_difference = (next_time - datetime.datetime.utcnow()).total_seconds()

                    # Sleep for the required time until the next scheduled message
                    await asyncio.sleep(time_difference)
                    scheduled_messages_running = False

        # If scheduled_messages_running is True or the lock is not acquired, wait for a short duration before checking again
        await asyncio.sleep(5)

async def reset_weekly_data():
        while True:
            now = datetime.datetime.now()
            if now.weekday() == 5 and now.hour == 0 and now.minute == 5:  # Saturday at 00:10
                data = {"users": {}}
                fetchinfo.save_weekly_data(data)
                print("Weekly data reset successfully.")

            # Sleep for a day (86400 seconds)
            await asyncio.sleep(86400)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    # Start the scheduled messages publishing task
    bot.loop.create_task(publish_scheduled_messages())

    bot.loop.create_task(scheduled_announce_messages())

    # Schedule the weekly data reset task
    bot.loop.create_task(reset_weekly_data())


@bot.event
async def on_member_join(member):
    channel = bot.get_channel(1091815853776978070) ## Change to NOS Tuners channel id
    greeting_message = (f"**¡Bienvenido a NOS Tuners!** {member.mention}.\n"
    f"Por favor solicita tu rol de civil en el canal <#1091815853776978071> y utiliza tu nombre IC para acceder al servidor.")

    await channel.send(greeting_message)


@bot.command(name='sancionar')
@commands.check(fetchinfo.is_allowed_role)
async def sancionar(ctx):
    allowed_roles = [1133497390247182396, 1133495683270332498, 1091845677455245352, 1091822086848266270, 1136467799900962836]
    if not any(role.id in allowed_roles for role in ctx.author.roles):
        return await ctx.author.send("No tienes permiso para usar este comando.")

    await ctx.send("¿A quién deseas sancionar? Menciona al usuario con @.")

    try:
        user_to_sanction_message = await bot.wait_for('message', timeout=60.0, check=lambda message: message.author == ctx.author)
        user_to_sanction = user_to_sanction_message.mentions[0] if user_to_sanction_message.mentions else None
    except asyncio.TimeoutError:
        return await ctx.send("Tiempo de espera agotado. Vuelve a intentarlo.")

    if not user_to_sanction:
        return await ctx.send("No se mencionó a ningún usuario. Vuelve a intentarlo.")

    # Display the list of reasons and sanctions to the user
    reason_list = "\n".join(f"{num}: {reason}" for num, reason in sanctioncheck.reasons_and_sanctions.items())
    reason_prompt = await ctx.send(f"Elige una razón para la sanción:\n{reason_list}")

    try:
        # Get the chosen reason number
        chosen_reason_message = await bot.wait_for('message', timeout=60.0, check=lambda message: message.author == ctx.author and message.channel == ctx.channel)
        chosen_reason = int(chosen_reason_message.content)

        # Validate if the chosen_reason is in the list
        if chosen_reason not in sanctioncheck.reasons_and_sanctions:
            raise ValueError("Razón inválida.")
    except (asyncio.TimeoutError, ValueError):
        await reason_prompt.delete()  # Delete the prompt for the reason
        return await ctx.send("Razón inválida o tiempo de espera agotado. Vuelve a intentarlo.")

    # Check if the user being sanctioned has received a sanction in the last 30 days
    sanctions_data = fetchinfo.get_sanctions_data()
    user_sanctions = sanctions_data.get(str(user_to_sanction.id), [])
    current_timestamp = datetime.datetime.utcnow().isoformat()

    for sanction in user_sanctions:
        timestamp = datetime.datetime.fromisoformat(sanction['Fecha'])
        if (timestamp + datetime.timedelta(days=30)) > datetime.datetime.utcnow():
            return await ctx.send(f"{user_to_sanction.mention} ya ha recibido una sanción en los últimos 30 días.")


    # Update the user_sanctions list with the new sanction data
    user_sanctions.append({
        "Fecha": current_timestamp,
        "Razon": sanctioncheck.reasons_and_sanctions[chosen_reason]["reason"],
        "Color": sanctioncheck.reasons_and_sanctions[chosen_reason]["color"],
        "Monto": sanctioncheck.reasons_and_sanctions[chosen_reason]["amount"]
    })
    sanctions_data[str(user_to_sanction.id)] = user_sanctions

    # Save the updated sanctions data to the JSON file
    with open('sanctions.json', 'r+') as file:
        data = json.load(file)
        data["sanctions"] = sanctions_data
        file.seek(0)
        json.dump(data, file, indent=4)

    # Display the sanction message in the specific channel
    sanction_message = (
        f":pushpin: **SANCION** {user_to_sanction.mention} ha recibido una: "
        f"{sanctioncheck.reasons_and_sanctions[chosen_reason]['color']}.\n"
        f"Deberá abonar a la organización (#Y00JZN) el monto de {sanctioncheck.reasons_and_sanctions[chosen_reason]['amount']} "
        f"antes de cumplirse las 48 hs.\n\n"
        f"Motivos:\n- {sanctioncheck.reasons_and_sanctions[chosen_reason]['reason']}\n\n"
        f"<@&1091815852959072301> Esta misma vence el {sanctioncheck.get_expiration_date(current_timestamp)} "
        f"(30 días desde el momento de la sanción).\n"
        f"Acumula ({len(user_sanctions)}/2) Sanciones Blancas -> "
        f"En caso de recibir 1 más, será penalizado con una sanción Amarilla.\n\n"
        f":x: SIN PAGAR"
    )
    specific_channel_id = 1116814092053774488  # Reemplazar por NOS Tuners
    specific_channel = bot.get_channel(specific_channel_id)
    if specific_channel:
        await specific_channel.send(sanction_message)
    else:
        await ctx.send("No se pudo encontrar el canal específico para publicar la sanción.")


@bot.command(name='ver_sanciones')
async def ver_sanciones(ctx, user: discord.Member = None):
    if not user:
        user = ctx.author

    user_id = user_id = str(user.id)
    sanctions_for_user = fetchinfo.get_sanctions_for_user(user_id)

    if not sanctions_for_user:
        return await ctx.author.send(f"No se encontraron sanciones para el usuario {user.mention}.")

    await ctx.author.send(f"Sanciones para el usuario {user.mention}:")
    for sanction in sanctions_for_user:
        await ctx.author.send(f"Fecha: {sanction['Fecha']}")
        await ctx.author.send(f"Razón: {sanction['Razon']}")
        await ctx.author.send(f"Monto: {sanction['Monto']}")
        await ctx.author.send("**━━━━━━━━━━━━━━━━━━━━━━━━━━━━━**")


@bot.command(name='mod_actividad')
@commands.check(fetchinfo.is_allowed_role)
async def update_activity(ctx):
    allowed_roles = [1133497390247182396, 1133495683270332498, 1091845677455245352, 1091822086848266270, 1136467799900962836]
    if not any(role.id in allowed_roles for role in ctx.author.roles):
        return await ctx.author.send("No tienes permiso para usar este comando.")

    await ctx.author.send("¿Cuál es el nombre del archivo JSON para actualizar la actividad? (Por ejemplo, 'file1.json'):")
    try:
        json_file_message = await bot.wait_for('message', timeout=60.0, check=lambda message: message.author == ctx.author)
        json_file_name = json_file_message.content
    except asyncio.TimeoutError:
        return await ctx.author.send("Tiempo de espera agotado. Vuelve a intentarlo.")

    # Check if the JSON file exists
    if not os.path.exists(json_file_name):
        return await ctx.author.send(f"El archivo JSON '{json_file_name}' no existe.")

    if json_file_name == 'reciept.json':
        current_activity = fetchinfo.get_next_activity_number()
    elif json_file_name == 'industrial.json':
        current_activity = fetchinfo.get_industrial_activity()
    elif json_file_name == 'roadfix.json':
        current_activity = fetchinfo.get_roadfix_activity()
    else:
        return await ctx.author.send(f"El archivo JSON '{json_file_name}' no es compatible para actualizar la actividad.")

    await ctx.author.send(f"Cual es el numero de actividad correcto en el archivo '{json_file_name}'?: ")
    try:
        new_activity_number_message = await bot.wait_for('message', timeout=60.0, check=lambda message: message.author == ctx.author)
        new_activity_number = new_activity_number_message.content
    except asyncio.TimeoutError:
        return await ctx.author.send("Tiempo de espera agotado. Vuelve a intentarlo.")

    if json_file_name == 'reciept.json':
        fetchinfo.update_activity_number(new_activity_number)
    elif json_file_name == 'industrial.json':
        fetchinfo.update_industrial_activity(new_activity_number)
    elif json_file_name == 'roadfix.json':
        fetchinfo.update_roadfix_activity(new_activity_number)

    await ctx.send(f"Se ha cambiado el numero de actividad de {current_activity} a {new_activity_number}.")

    # Find the last message in the channel that matches the pattern and edit it with the updated activity number
    async for message in ctx.channel.history(limit=None, oldest_first=False):
        if f"Reparacion en Carretera N°: {current_activity}" in message.content:
            # Edit the message with the updated activity number
            new_message_content = message.content.replace(f"Reparacion en Carretera N°: {current_activity}", f"Reparacion en Carretera N°: {new_activity_number}")
            await message.edit(content=new_message_content)
            break  # Stop looping once we find and edit the message
        if f"Reparacion Industrial N°: {current_activity}" in message.content:
            # Edit the message with the updated activity number
            new_message_content = message.content.replace(f"Reparacion Industrial N°: {current_activity}", f"Reparacion Industrial N°: {new_activity_number}")
            await message.edit(content=new_message_content)
            break  # Stop looping once we find and edit the message
        if f"Entrega de Herramientas N°: {current_activity}" in message.content:
            # Edit the message with the updated activity number
            new_message_content = message.content.replace(f"Entrega de Herramientas N°: {current_activity}", f"Entrega de Herramientas N°: {new_activity_number}")
            await message.edit(content=new_message_content)
            break  # Stop looping once we find and edit the message

    await ctx.message.delete()


@bot.command(name='ver_recibos')
@commands.check(fetchinfo.is_allowed_role)
async def ver_recibos(ctx, *, user_name=None):
    allowed_roles = [1133497390247182396, 1133495683270332498, 1091845677455245352, 1091822086848266270, 1136467799900962836]
    if not any(role.id in allowed_roles for role in ctx.author.roles):
        return await ctx.author.send("No tienes permiso para usar este comando.")

    if not user_name:
        # If no user_name is provided, assume the author wants to check their own receipts
        user = ctx.author
    else:
        # Try to find the user by name (case-insensitive)
        user = discord.utils.find(lambda m: m.display_name.lower() == user_name.lower(), ctx.guild.members)
        if user is None:
            return await ctx.send("Usuario no encontrado.")

    user_id = user.id
    user_invoices = fetchinfo.get_user_invoices(user_id)
    await ctx.send(f"Número de recibos para {user.display_name}: {user_invoices}")


@bot.command(name='factura')
async def upload_factura(ctx):
    user = ctx.author
    prompt_responses = []
    await ctx.author.send("Sube la imagen del auto antes de la reparacion (adjunta una imagen):")
    try:
        after_image = await bot.wait_for('message', timeout=300.0, check=lambda message: message.author == ctx.author and message.attachments)
        after_image = after_image.attachments[0].url
    except asyncio.TimeoutError:
        return await ctx.author.send("Tiempo de espera agotado. Vuelve a intentarlo.")

    await ctx.author.send("Sube la imagen del auto luego de la reparacion (adjunta una imagen):")
    try:
        after_image = await bot.wait_for('message', timeout=300.0, check=lambda message: message.author == ctx.author and message.attachments)
        after_image = after_image.attachments[0].url
    except asyncio.TimeoutError:
        return await ctx.author.send("Tiempo de espera agotado. Vuelve a intentarlo.")

    await ctx.author.send("Ingresa la matricula del auto:")
    try:
        car_plate = await bot.wait_for('message', timeout=60.0, check=lambda message: message.author == ctx.author)
        car_plate = car_plate.content
    except asyncio.TimeoutError:
        return await ctx.author.send("Tiempo de espera agotado. Vuelve a intentarlo.")

    specific_channel_id = 1139003062984376390
    specific_channel = bot.get_channel(specific_channel_id)
    if specific_channel:
        await specific_channel.send(f"**Numero de factura de {user.mention}: {fetchinfo.get_user_invoices(user.id)}**\n"
                    "**━━━━━━━━━━━━━━━━━━━━━━━━━━━━━**\n"
                    f"**Matricula del auto: **{car_plate}\n")
        await specific_channel.send("**Imagen despues de la reparacion:**")
        await specific_channel.send(after_image)

    # Delete the command message and prompt messages after the command is done
    # prompt_responses.append(before_image)
    prompt_responses.append(after_image)
    prompt_responses.append(car_plate)

    fetchinfo.increment_user_invoices(user.id)

    try:
        await ctx.message.delete()
    except discord.NotFound:
        pass


@bot.command(name='ranking')
async def display_ranking(ctx):
    # List of role IDs to filter the users
    role_ids = [1091815852959072301, 1091822638810271885, 1133497390247182396, 1133495683270332498, 1091845677455245352, 1091822086848266270]

    # Filter users to include only those with the specified roles
    users_with_roles = [user for user in ctx.guild.members if any(role.id in role_ids for role in user.roles)]

    # Create a list to store tuples (user_id, invoice_count)
    user_invoices_list = [(user.id, fetchinfo.get_user_invoices(user.id)) for user in users_with_roles]

    # Sort the list in descending order based on invoice count
    sorted_user_invoices = sorted(user_invoices_list, key=lambda x: x[1], reverse=True)

    # Prepare the ranking message
    ranking_message = "**Ranking de usuarios por cantidad de facturas:**\n"
    for idx, (user_id, invoice_count) in enumerate(sorted_user_invoices, start=1):
        user = ctx.guild.get_member(user_id)
        if user:
            # Use user.display_name to get the nickname (server name) of the user
            ranking_message += f"{idx}. {user.display_name}: {invoice_count} facturas\n"

    # Send the ranking message to the channel
    await ctx.send(ranking_message)


@bot.command(name='semanal')
async def get_user_activity(ctx):
    # List of role IDs to filter the users
    role_ids = [1091815852959072301, 1091822638810271885, 1133497390247182396, 1133495683270332498, 1091845677455245352, 1091822086848266270]

    # Filter users to include only those with the specified roles
    users_with_roles = [user for user in ctx.guild.members if any(role.id in role_ids for role in user.roles)]

    # Create a list to store tuples (user_id, weekly_count)
    user_weekly_activity = [(user.id, fetchinfo.get_user_weekly(user.id)) for user in users_with_roles]

    # Sort the list in descending order based on invoice count
    sorted_user_weekly = sorted(user_weekly_activity, key=lambda x: x[1], reverse=True)

    # Prepare the ranking message
    weekly_activity_msg = "**Lista de usuarios por actividad semanal:**\n"
    for idx, (user_id, weekly_count) in enumerate(sorted_user_weekly, start=1):
        user = ctx.guild.get_member(user_id)
        if user:
            # Use user.display_name to get the nickname (server name) of the user
            weekly_activity_msg += f"{idx}. {user.display_name}: {weekly_count} semanales\n"

    # Send the ranking message to the channel
    await ctx.send(weekly_activity_msg)


@bot.command(name='entrega')
async def subir_recibo_entrega(ctx):
    activity_number = fetchinfo.get_next_activity_number()
    user = ctx.author
    messages_to_delete = [ctx.message]  # List to keep track of messages to delete

    # Function to delete the messages stored in messages_to_delete list
    async def delete_messages():
        try:
            for message in messages_to_delete:
                if isinstance(message, discord.Message):
                    await message.delete()
        except discord.HTTPException:
            pass

    car_plate_prompt = await ctx.send("**Matricula de la grua: **")
    messages_to_delete.append(car_plate_prompt)
    try:
        car_plate_message = await bot.wait_for('message', timeout=60.0, check=lambda message: message.author == ctx.author)
        car_plate = car_plate_message.content
        messages_to_delete.append(car_plate_message)
    except asyncio.TimeoutError:
        return await ctx.send("Tiempo de espera agotado. Vuelve a intentarlo.")

    remaining_boxes_prompt = await ctx.send("**Cajas restantes (de 0 a 6): **")
    messages_to_delete.append(remaining_boxes_prompt)
    try:
        remaining_boxes_message = await bot.wait_for('message', timeout=60.0, check=lambda message: message.author == ctx.author)
        if not remaining_boxes_message.content.isdigit():
            correction = await ctx.send("Por favor introduce un número válido.")
            messages_to_delete.append(remaining_boxes_message)
            messages_to_delete.append(correction)
            await asyncio.sleep(3)
            await delete_messages()  # Delete all collected messages
            return
        remaining_boxes = int(remaining_boxes_message.content)
        messages_to_delete.append(remaining_boxes_message)
    except asyncio.TimeoutError:
        timeout = await ctx.send("Tiempo de espera agotado. Vuelve a intentarlo.")
        messages_to_delete.append(timeout)
        await asyncio.sleep(3)
        await delete_messages()  # Delete all collected messages
        return

    remaining_fuel_prompt = await ctx.send("**Combustible restante (de 0 a 64): **")
    messages_to_delete.append(remaining_fuel_prompt)
    try:
        remaining_fuel_message = await bot.wait_for('message', timeout=60.0, check=lambda message: message.author == ctx.author)
        if not remaining_fuel_message.content.isdigit():
            correction = await ctx.send("Por favor introduce un número válido.")
            messages_to_delete.append(remaining_fuel_message)
            messages_to_delete.append(correction)
            await asyncio.sleep(3)
            await delete_messages()  # Delete the invalid message
            return
        remaining_fuel = int(remaining_fuel_message.content)
        messages_to_delete.append(remaining_fuel_message)
    except asyncio.TimeoutError:
        timeout = await ctx.send("Tiempo de espera agotado. Vuelve a intentarlo.")
        messages_to_delete.append(timeout)
        await asyncio.sleep(3)
        await delete_messages()  # Delete all collected messages
        return

    delivery_time_prompt = await ctx.send("**Hora de entrega (formato HH:mm): **")
    messages_to_delete.append(delivery_time_prompt)
    try:
        delivery_time_message = await bot.wait_for('message', timeout=60.0, check=lambda message: message.author == ctx.author)
        delivery_time = delivery_time_message.content
        messages_to_delete.append(delivery_time_message)
    except asyncio.TimeoutError:
        return await ctx.send("Tiempo de espera agotado. Vuelve a intentarlo.")

    receipt_image_prompt = await ctx.send("**Comprobante (por favor adjuntar una imagen): **")
    messages_to_delete.append(receipt_image_prompt)
    try:
        receipt_image_message = await bot.wait_for('message', timeout=60.0, check=lambda message: message.author == ctx.author and message.attachments)
        receipt_image = receipt_image_message.attachments[0].url
        messages_to_delete.append(receipt_image_message)
    except asyncio.TimeoutError:
        return await ctx.send("Tiempo de espera agotado. Vuelve a intentarlo.")

    employee_name_prompt = await ctx.send("**Nombre del empleado (por favor mencionar con @): **")
    messages_to_delete.append(employee_name_prompt)
    try:
        employee_name_message = await bot.wait_for('message', timeout=60.0, check=lambda message: message.author == ctx.author)
        employee_name = employee_name_message.content
        messages_to_delete.append(employee_name_message)

        # Extract mentioned users
        mentioned_users = employee_name_message.mentions

        # Increment invoices for mentioned users
        for mentioned_user in mentioned_users:
                fetchinfo.increment_user_invoices(mentioned_user.id)
                fetchinfo.increment_user_weekly(mentioned_user.id)
    except asyncio.TimeoutError:
        fetchinfo.decrease_user_invoices(mentioned_user.id)
        fetchinfo.decrease_user_weekly(mentioned_user.id)
        await asyncio.sleep(3)
        return await ctx.send("Tiempo de espera agotado. Vuelve a intentarlo.")

    # Displaying all the information
    specific_channel_id = 1091815853978292229
    specific_channel = bot.get_channel(specific_channel_id)
    if specific_channel:
        activity_number += 1
        await specific_channel.send(f"**/ Entrega de Herramientas N°: {activity_number}**\n"
                                    "**━━━━━━━━━━━━━━━━━━━━━━━━━━━━━**\n"
                                    f"**/ Nombre del empleado: **{employee_name}\n"
                                    f"**/ Hora de entrega: **{delivery_time}\n"
                                    f"**/ Patente grua: **{car_plate}\n"
                                    f"**/ Gasolina restante: **{remaining_fuel}\n"
                                    f"**/ Cajas restantes: **{remaining_boxes}\n"
                                    "**/ Comprobante:**")
        await specific_channel.send(receipt_image)
    else:
        await ctx.send("No se pudo encontrar el canal específico para publicar el recibo.")


    fetchinfo.update_activity_number(activity_number)

    # Call the delete_messages function at the end of the command
    await delete_messages()

    try:
        await ctx.message.delete()
    except discord.NotFound:
        pass

@bot.command(name='industrial')
async def subir_recibo_industrial(ctx):
    activity_number = fetchinfo.get_industrial_activity()
    user = ctx.author
    messages_to_delete = [ctx.message]  # List to keep track of messages to delete

    # Function to delete the messages stored in messages_to_delete list
    async def delete_messages():
        try:
            for message in messages_to_delete:
                if isinstance(message, discord.Message):
                    await message.delete()
        except discord.HTTPException:
            pass

    car_plate_prompt = await ctx.send("**Matricula del vehiculo: **")
    messages_to_delete.append(car_plate_prompt)
    try:
        car_plate_message = await bot.wait_for('message', timeout=60.0, check=lambda message: message.author == ctx.author)
        car_plate = car_plate_message.content
        messages_to_delete.append(car_plate_message)
    except asyncio.TimeoutError:
        return await ctx.send("Tiempo de espera agotado. Vuelve a intentarlo.")

    remaining_boxes_prompt = await ctx.send("**Cajas de herramientas restantes: **")
    messages_to_delete.append(remaining_boxes_prompt)
    try:
        remaining_boxes_message = await bot.wait_for('message', timeout=60.0, check=lambda message: message.author == ctx.author)
        if not remaining_boxes_message.content.isdigit():
            correction = await ctx.send("Por favor introduce un número válido.")
            messages_to_delete.append(remaining_boxes_message)
            messages_to_delete.append(correction)
            await asyncio.sleep(3)
            await delete_messages()  # Delete all collected messages
            return
        remaining_boxes = int(remaining_boxes_message.content)
        messages_to_delete.append(remaining_boxes_message)
    except asyncio.TimeoutError:
        timeout = await ctx.send("Tiempo de espera agotado. Vuelve a intentarlo.")
        messages_to_delete.append(timeout)
        await asyncio.sleep(3)
        await delete_messages()  # Delete all collected messages
        return

    remaining_fuel_prompt = await ctx.send("**Combustible restante (de 0 a 64): **")
    messages_to_delete.append(remaining_fuel_prompt)
    try:
        remaining_fuel_message = await bot.wait_for('message', timeout=60.0, check=lambda message: message.author == ctx.author)
        if not remaining_fuel_message.content.isdigit():
            correction = await ctx.send("Por favor introduce un número válido.")
            messages_to_delete.append(remaining_fuel_message)
            messages_to_delete.append(correction)
            await asyncio.sleep(3)
            await delete_messages()  # Delete the invalid message
            return
        remaining_fuel = int(remaining_fuel_message.content)
        messages_to_delete.append(remaining_fuel_message)
    except asyncio.TimeoutError:
        timeout = await ctx.send("Tiempo de espera agotado. Vuelve a intentarlo.")
        messages_to_delete.append(timeout)
        await asyncio.sleep(3)
        await delete_messages()  # Delete all collected messages
        return

    delivery_time_prompt = await ctx.send("**Hora de entrega (formato HH:mm): **")
    messages_to_delete.append(delivery_time_prompt)
    try:
        delivery_time_message = await bot.wait_for('message', timeout=60.0, check=lambda message: message.author == ctx.author)
        delivery_time = delivery_time_message.content
        messages_to_delete.append(delivery_time_message)
    except asyncio.TimeoutError:
        return await ctx.send("Tiempo de espera agotado. Vuelve a intentarlo.")

    receipt_image_prompt = await ctx.send("**Comprobante (por favor adjuntar una imagen): **")
    messages_to_delete.append(receipt_image_prompt)
    try:
        receipt_image_message = await bot.wait_for('message', timeout=60.0, check=lambda message: message.author == ctx.author and message.attachments)
        receipt_image = receipt_image_message.attachments[0].url
        messages_to_delete.append(receipt_image_message)
    except asyncio.TimeoutError:
        return await ctx.send("Tiempo de espera agotado. Vuelve a intentarlo.")

    employee_name_prompt = await ctx.send("**Nombre del empleado (por favor mencionar con @): **")
    messages_to_delete.append(employee_name_prompt)
    try:
        employee_name_message = await bot.wait_for('message', timeout=60.0, check=lambda message: message.author == ctx.author)
        employee_name = employee_name_message.content
        messages_to_delete.append(employee_name_message)

        # Extract mentioned users
        mentioned_users = employee_name_message.mentions

        # Increment invoices for mentioned users
        for mentioned_user in mentioned_users:
                fetchinfo.increment_user_invoices(mentioned_user.id)
                fetchinfo.increment_user_weekly(mentioned_user.id)
    except asyncio.TimeoutError:
        fetchinfo.decrease_user_invoices(mentioned_user.id)
        fetchinfo.decrease_user_weekly(mentioned_user.id)
        await asyncio.sleep(3)
        return await ctx.send("Tiempo de espera agotado. Vuelve a intentarlo.")


    # Displaying all the information
    specific_channel_id = 1138166569210491032
    specific_channel = bot.get_channel(specific_channel_id)
    activity_number += 1
    if specific_channel:
        await specific_channel.send(f"**/ Reparacion Industrial N°: {activity_number}**\n"
                                    "**━━━━━━━━━━━━━━━━━━━━━━━━━━━━━**\n"
                                    f"**/ Nombre del empleado: **{employee_name}\n"
                                    f"**/ Hora de entrega: **{delivery_time}\n"
                                    f"**/ Patente vehiculo: **{car_plate}\n"
                                    f"**/ Gasolina restante: **{remaining_fuel}\n"
                                    f"**/ Cajas de herramientas restantes: **{remaining_boxes}\n"
                                    "**/ Comprobante:**")
        await specific_channel.send(receipt_image)
    else:
        await ctx.send("No se pudo encontrar el canal específico para publicar el recibo.")


    fetchinfo.update_industrial_activity(activity_number)

    # Call the delete_messages function at the end of the command
    await delete_messages()

    try:
        await ctx.message.delete()
    except discord.NotFound:
        pass

@bot.command(name='carretera')
async def subir_recibo_carretera(ctx):
    activity_number = fetchinfo.get_roadfix_activity()
    user = ctx.author
    messages_to_delete = [ctx.message]  # List to keep track of messages to delete

    # Function to delete the messages stored in messages_to_delete list
    async def delete_messages():
        try:
            for message in messages_to_delete:
                if isinstance(message, discord.Message):
                    await message.delete()
        except discord.HTTPException:
            pass

    car_plate_prompt = await ctx.send("**Matricula del vehiculo: **")
    messages_to_delete.append(car_plate_prompt)
    try:
        car_plate_message = await bot.wait_for('message', timeout=60.0, check=lambda message: message.author == ctx.author)
        car_plate = car_plate_message.content
        messages_to_delete.append(car_plate_message)
    except asyncio.TimeoutError:
        return await ctx.send("Tiempo de espera agotado. Vuelve a intentarlo.")

    remaining_boxes_prompt = await ctx.send("**Cajas de herramientas restantes: **")
    messages_to_delete.append(remaining_boxes_prompt)
    try:
        remaining_boxes_message = await bot.wait_for('message', timeout=60.0, check=lambda message: message.author == ctx.author)
        if not remaining_boxes_message.content.isdigit():
            correction = await ctx.send("Por favor introduce un número válido.")
            messages_to_delete.append(remaining_boxes_message)
            messages_to_delete.append(correction)
            await asyncio.sleep(3)
            await delete_messages()  # Delete all collected messages
            return
        remaining_boxes = int(remaining_boxes_message.content)
        messages_to_delete.append(remaining_boxes_message)
    except asyncio.TimeoutError:
        timeout = await ctx.send("Tiempo de espera agotado. Vuelve a intentarlo.")
        messages_to_delete.append(timeout)
        await asyncio.sleep(3)
        await delete_messages()  # Delete all collected messages
        return

    remaining_fuel_prompt = await ctx.send("**Combustible restante (de 0 a 64): **")
    messages_to_delete.append(remaining_fuel_prompt)
    try:
        remaining_fuel_message = await bot.wait_for('message', timeout=60.0, check=lambda message: message.author == ctx.author)
        if not remaining_fuel_message.content.isdigit():
            correction = await ctx.send("Por favor introduce un número válido.")
            messages_to_delete.append(remaining_fuel_message)
            messages_to_delete.append(correction)
            await asyncio.sleep(3)
            await delete_messages()  # Delete the invalid message
            return
        remaining_fuel = int(remaining_fuel_message.content)
        messages_to_delete.append(remaining_fuel_message)
    except asyncio.TimeoutError:
        timeout = await ctx.send("Tiempo de espera agotado. Vuelve a intentarlo.")
        messages_to_delete.append(timeout)
        await asyncio.sleep(3)
        await delete_messages()  # Delete all collected messages
        return

    delivery_time_prompt = await ctx.send("**Hora de entrega (formato HH:mm): **")
    messages_to_delete.append(delivery_time_prompt)
    try:
        delivery_time_message = await bot.wait_for('message', timeout=60.0, check=lambda message: message.author == ctx.author)
        delivery_time = delivery_time_message.content
        messages_to_delete.append(delivery_time_message)
    except asyncio.TimeoutError:
        return await ctx.send("Tiempo de espera agotado. Vuelve a intentarlo.")

    receipt_image_prompt = await ctx.send("**Comprobante (por favor adjuntar una imagen): **")
    messages_to_delete.append(receipt_image_prompt)
    try:
        receipt_image_message = await bot.wait_for('message', timeout=60.0, check=lambda message: message.author == ctx.author and message.attachments)
        receipt_image = receipt_image_message.attachments[0].url
        messages_to_delete.append(receipt_image_message)
    except asyncio.TimeoutError:
        return await ctx.send("Tiempo de espera agotado. Vuelve a intentarlo.")

    employee_name_prompt = await ctx.send("**Nombre del empleado (por favor mencionar con @): **")
    messages_to_delete.append(employee_name_prompt)
    try:
        employee_name_message = await bot.wait_for('message', timeout=60.0, check=lambda message: message.author == ctx.author)
        employee_name = employee_name_message.content
        messages_to_delete.append(employee_name_message)

        # Extract mentioned users
        mentioned_users = employee_name_message.mentions

        # Increment invoices for mentioned users
        for mentioned_user in mentioned_users:
                fetchinfo.increment_user_invoices(mentioned_user.id)
                fetchinfo.increment_user_weekly(mentioned_user.id)
    except asyncio.TimeoutError:
        fetchinfo.decrease_user_invoices(mentioned_user.id)
        fetchinfo.decrease_user_weekly(mentioned_user.id)
        await asyncio.sleep(3)
        return await ctx.send("Tiempo de espera agotado. Vuelve a intentarlo.")


    # Displaying all the information
    specific_channel_id = 1138166549459517512
    specific_channel = bot.get_channel(specific_channel_id)
    activity_number += 1
    if specific_channel:
        await specific_channel.send(f"**/ Reparacion en Carretera N°: {activity_number}**\n"
                                    "**━━━━━━━━━━━━━━━━━━━━━━━━━━━━━**\n"
                                    f"**/ Nombre del empleado: **{employee_name}\n"
                                    f"**/ Hora de entrega: **{delivery_time}\n"
                                    f"**/ Patente vehiculo: **{car_plate}\n"
                                    f"**/ Gasolina restante: **{remaining_fuel}\n"
                                    f"**/ Cajas de herramientas restantes: **{remaining_boxes}\n"
                                    "**/ Comprobante:**")
        await specific_channel.send(receipt_image)
    else:
        await ctx.send("No se pudo encontrar el canal específico para publicar el recibo.")

    fetchinfo.update_roadfix_activity(activity_number)

    # Call the delete_messages function at the end of the command
    await delete_messages()

    try:
        await ctx.message.delete()
    except discord.NotFound:
        pass


bot.run(TOKEN)

