import discord
import json
import asyncio
import datetime

from discord.ext import commands
import get_receipt_info
import sanction_check


intents = discord.Intents.all()

TOKEN = "MTEzNDIzNTI2NzM2NTA3NzAxMg.GnxWvG.9scY-X8iyEu-9pGpJH20hrtKH388kCLx5enmCI"

intents = discord.Intents().all()
client = discord.Client(intents = intents)
bot = commands.Bot(command_prefix='/', intents=intents)


@bot.event
async def on_member_join(member):
    channel = bot.get_channel(1091815853776978070) ## Change to NOS Tuners channel id
    greeting_message = (f"**¡Bienvenido a NOS Tuners!** {member.mention}.",
    f"Por favor solicita tu rol de civil en el canal <#1091815853776978071> y utiliza tu nombre IC para acceder al servidor.")

    await channel.send(greeting_message)


@bot.command(name='sancionar')
@commands.check(get_receipt_info.is_allowed_role)
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
    reason_list = "\n".join(f"{num}: {reason}" for num, reason in sanction_check.reasons_and_sanctions.items())
    reason_prompt = await ctx.send(f"Elige una razón para la sanción:\n{reason_list}")

    try:
        # Get the chosen reason number
        chosen_reason_message = await bot.wait_for('message', timeout=60.0, check=lambda message: message.author == ctx.author and message.channel == ctx.channel)
        chosen_reason = int(chosen_reason_message.content)

        # Validate if the chosen_reason is in the list
        if chosen_reason not in sanction_check.reasons_and_sanctions:
            raise ValueError("Razón inválida.")
    except (asyncio.TimeoutError, ValueError):
        await reason_prompt.delete()  # Delete the prompt for the reason
        return await ctx.send("Razón inválida o tiempo de espera agotado. Vuelve a intentarlo.")

    # Check if the user being sanctioned has received a sanction in the last 30 days
    sanctions_data = get_receipt_info.get_sanctions_data()
    user_sanctions = sanctions_data.get(str(user_to_sanction.id), [])
    current_timestamp = datetime.datetime.utcnow().isoformat()

    for sanction in user_sanctions:
        timestamp = datetime.datetime.fromisoformat(sanction['Fecha'])
        if (timestamp + datetime.timedelta(days=30)) > datetime.datetime.utcnow():
            return await ctx.send(f"{user_to_sanction.mention} ya ha recibido una sanción en los últimos 30 días.")


    # Update the user_sanctions list with the new sanction data
    user_sanctions.append({
        "Fecha": current_timestamp,
        "Razon": sanction_check.reasons_and_sanctions[chosen_reason]["reason"],
        "Color": sanction_check.reasons_and_sanctions[chosen_reason]["color"],
        "Monto": sanction_check.reasons_and_sanctions[chosen_reason]["amount"]
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
        f"{sanction_check.reasons_and_sanctions[chosen_reason]['color']}.\n"
        f"Deberá abonar a la organización (#Y00JZN) el monto de {sanction_check.reasons_and_sanctions[chosen_reason]['amount']} "
        f"antes de cumplirse las 48 hs.\n\n"
        f"Motivos:\n- {sanction_check.reasons_and_sanctions[chosen_reason]['reason']}\n\n"
        f"<@&1091815852959072301> Esta misma vence el {sanction_check.get_expiration_date(current_timestamp)} "
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


    # Delete the prompts after successful application
    await ctx.message.delete()  # Delete the original command message
    await user_to_sanction_message.delete()  # Delete the message mentioning the user
    await reason_prompt.delete()  # Delete the prompt for the reason
    await chosen_reason_message.delete()  # Delete the message where the user chose the reason
    await ctx.author.send("Sanción aplicada exitosamente.")  # Send a confirmation message to the server channel
@bot.command(name='ver_sanciones')
async def ver_sanciones(ctx, user: discord.Member = None):
    if not user:
        user = ctx.author

    user_id = user_id = str(user.id)
    sanctions_for_user = get_receipt_info.get_sanctions_for_user(user_id)

    if not sanctions_for_user:
        return await ctx.author.send(f"No se encontraron sanciones para el usuario {user.mention}.")

    await ctx.author.send(f"Sanciones para el usuario {user.mention}:")
    for sanction in sanctions_for_user:
        await ctx.author.send(f"Fecha: {sanction['Fecha']}")
        await ctx.author.send(f"Razón: {sanction['Razon']}")
        await ctx.author.send(f"Monto: {sanction['Monto']}")
        await ctx.author.send("**━━━━━━━━━━━━━━━━━━━━━━━━━━━━━**")

@bot.command(name='mod_actividad')
@commands.check(get_receipt_info.is_allowed_role)
async def update_activity(ctx):
    allowed_roles = [1133497390247182396, 1133495683270332498, 1091845677455245352, 1091822086848266270, 1136467799900962836]
    if not any(role.id in allowed_roles for role in ctx.author.roles):
        return await ctx.author.send("No tienes permiso para usar este comando.")

    current_activity = get_receipt_info.get_next_activity_number()
    await ctx.author.send(f"Cual es el numero de actividad correcto?: ")
    try:
        new_activity_number = await bot.wait_for('message', timeout=60.0, check=lambda message: message.author == ctx.author)
        new_activity_number = new_activity_number.content
    except asyncio.TimeoutError:
        return await ctx.author.send("Tiempo de espera agotado. Vuelve a intentarlo.")
    get_receipt_info.update_activity_number(new_activity_number)

    await ctx.send(f"Se ha cambiado el numero de actividad de {current_activity} a {new_activity_number}.")

    await ctx.message.delete()

@bot.command(name='ver_recibos')
@commands.check(get_receipt_info.is_allowed_role)
async def ver_recibos(ctx, *users: discord.Member):
    allowed_roles = [1133497390247182396, 1133495683270332498, 1091845677455245352, 1091822086848266270, 1136467799900962836]
    if not any(role.id in allowed_roles for role in ctx.author.roles):
        return await ctx.author.send("No tienes permiso para usar este comando.")

    if not users:
        users = [ctx.author]

    for user in users:
        user_id = user.id
        receipts_for_user = get_receipt_info.get_receipts_for_user(user_id)

        if not receipts_for_user:
            await ctx.author.send(f"No se encontraron recibos para el usuario con ID {user_id}.")
            continue

        await ctx.author.send(f"Recibos para el usuario {user.mention}:")
        for receipt in receipts_for_user:
            await ctx.author.send(f"Nombre del empleado: {receipt['Nombre']}")
            await ctx.author.send(f"Fecha: {receipt['Dia']}")
            await ctx.author.send(f"Hora: {receipt['Hora']}")
            await ctx.author.send(f"Cajas restantes: {receipt['Cajas']}")
            await ctx.author.send(f"Gasolina restante: {receipt['Gasolina']}")
            await ctx.author.send(f"Actividad semanal: {receipt['Actividad Semanal']}")
            await ctx.author.send(f"Comprobante: {receipt['Recibo']}")
            await ctx.author.send("**━━━━━━━━━━━━━━━━━━━━━━━━━━━━━**")


@bot.command(name='recibo')
async def subir_recibo(ctx):
    activity_number, receipts = get_receipt_info.get_next_activity_number()
    user = ctx.author
    messages_to_delete = []

    # Function to check if the user confirms deletion
    async def confirm_deletion():
        await ctx.author.send("¿Deseas cargar un recibo? (responde 'si' o 'no')")
        try:
            msg = await bot.wait_for('message', timeout=300.0, check=lambda message: message.author == user)
            return msg.content.lower() == 'no'
        except asyncio.TimeoutError:
            await ctx.author.send("Tiempo de espera agotado. El intento se eliminará.")
            return True

    async def delete_messages():
        try:
            for message in messages_to_delete:
                await message.delete()
        except discord.HTTPException:
            pass

    # Check if the user wants to delete the previous attempt
    if activity_number > 1:
        if await confirm_deletion():
            activity_number -= 1
            get_receipt_info.update_activity_number(activity_number,receipts)
            await ctx.author.send("El intento anterior ha sido eliminado. Vuelve a comenzar.")
            messages_to_delete.append(ctx.message)  # Delete the /recibo command message
            await delete_messages()
            return

    # Send the command message and add it to the list for deletion
    # messages_to_delete.append(await ctx.author.send("Comando /recibo"))

    await ctx.author.send(f"**Actividad N°: {activity_number}**")
    activity_number += 1
    get_receipt_info.update_activity_number(activity_number,receipts)

    await ctx.author.send("**Nombre del empleado (por favor mencionar con @): **")
    try:
        employee_name = await bot.wait_for('message', timeout=60.0, check=lambda message: message.author == ctx.author)
        employee_name = employee_name.content
    except asyncio.TimeoutError:
        return await ctx.author.send("Tiempo de espera agotado. Vuelve a intentarlo.")

    await ctx.author.send("**Matricula de la grua: **")
    try:
        car_plate = await bot.wait_for('message', timeout=60.0, check=lambda message: message.author == ctx.author)
        car_plate = car_plate.content
    except asyncio.TimeoutError:
        return await ctx.author.send("Tiempo de espera agotado. Vuelve a intentarlo.")

    await ctx.author.send("**Cajas restantes (de 0 a 6): **")
    try:
        remaining_boxes = await bot.wait_for('message', timeout=60.0, check=lambda message: message.author == ctx.author)
        remaining_boxes = int(remaining_boxes.content)
    except asyncio.TimeoutError:
        return await ctx.author.send("Tiempo de espera agotado. Vuelve a intentarlo.")

    await ctx.author.send("**Combustible restante (de 0 a 64): **")
    try:
        remaining_fuel = await bot.wait_for('message', timeout=60.0, check=lambda message: message.author == ctx.author)
        remaining_fuel = int(remaining_fuel.content)
    except asyncio.TimeoutError:
        return await ctx.author.send("Tiempo de espera agotado. Vuelve a intentarlo.")

    await ctx.author.send("**Hora de entrega (formato HH:mm): **")
    try:
        delivery_time = await bot.wait_for('message', timeout=60.0, check=lambda message: message.author == ctx.author)
        delivery_time = delivery_time.content
    except asyncio.TimeoutError:
        return await ctx.author.send("Tiempo de espera agotado. Vuelve a intentarlo.")

    await ctx.author.send("**Actividad semanal (de 1 a 100): **")
    try:
        weekly_activity = await bot.wait_for('message', timeout=60.0, check=lambda message: message.author == ctx.author)
        weekly_activity = int(weekly_activity.content)
    except asyncio.TimeoutError:
        return await ctx.author.send("Tiempo de espera agotado. Vuelve a intentarlo.")

    await ctx.author.send("**Comprobante (por favor adjuntar una imagen): **")
    try:
        receipt_image = await bot.wait_for('message', timeout=60.0, check=lambda message: message.author == ctx.author and message.attachments)
        receipt_image = receipt_image.attachments[0].url
    except asyncio.TimeoutError:
        return await ctx.author.send("Tiempo de espera agotado. Vuelve a intentarlo.")

    receipt_data = {
        "UserID": ctx.author.id,  # Store the User ID
        "Nombre": employee_name,
        "Dia": str(datetime.datetime.utcnow().date()),  # Store the date in string format
        "Hora": str(datetime.datetime.utcnow().time())[:8],  # Store the time in string format
        "Cajas": remaining_boxes,
        "Gasolina": remaining_fuel,
        "Actividad Semanal": weekly_activity,
        "Recibo": receipt_image
    }
    receipts.append(receipt_data)
    with open('reciept.json', 'w') as file:
        data = {
            "actividad_numero": activity_number,
            "recibos": receipts
        }
        json.dump(data, file)
    get_receipt_info.get_next_activity_number()


    # Displaying all the information
    await ctx.send(f"**/ Entrega de herramientas N°: {activity_number}**")
    await ctx.send("**━━━━━━━━━━━━━━━━━━━━━━━━━━━━━**")
    await ctx.send(f"**/ Nombre del empleado: **{employee_name}")
    await ctx.send(f"**/ Hora de entrega: **{delivery_time}")
    await ctx.send(f"**/ Patente grua: **{car_plate}")
    await ctx.send(f"**/ Gasolina restante: **{remaining_fuel}")
    await ctx.send(f"**/ Cajas restantes: **{remaining_boxes}")
    await ctx.send(f"**/ Actividad semanal: **{weekly_activity}")
    await ctx.send("**/ Comprobante:**")
    await ctx.send(receipt_image)

    # Delete the command message and prompt messages after the command is done
    messages_to_delete.append(employee_name)
    messages_to_delete.append(car_plate)
    messages_to_delete.append(remaining_boxes)
    messages_to_delete.append(remaining_fuel)
    messages_to_delete.append(delivery_time)
    messages_to_delete.append(weekly_activity)
    messages_to_delete.append(receipt_image)

    try:
        await ctx.message.delete()
    except discord.NotFound:
        pass


bot.run(TOKEN)