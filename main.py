import discord
import json
import asyncio
import datetime

from discord.ext import commands
import get_receipt_info


intents = discord.Intents.all()

TOKEN = "MTEzNjQ1ODMwNTk5NzM4OTk2NA.G7569J.i_zMnD2njqhoFeV150pY-xaARYl9uG5i8vNp9M"

intents = discord.Intents().all()
client = discord.Client(intents = intents)
bot = commands.Bot(command_prefix='/', intents=intents)


@bot.command(name='mod_actividad')
@commands.check(get_receipt_info.is_allowed_role)
async def update_activity(ctx):
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
            get_receipt_info.update_activity_number(activity_number)
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
    with open('data.json', 'w') as file:
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