import discord
from discord.ext import commands
from discord import app_commands
import random
import aiohttp
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

warnings = {}  # store warnings in memory

# Sync slash commands when bot starts
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(e)
    print(f"Logged in as {bot.user}")

# -------------------------
# MODERATION COMMANDS
# -------------------------

@bot.tree.command(name="kick", description="Kick a member from the server")
@app_commands.describe(member="User to kick", reason="Reason for kick")
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    await member.kick(reason=reason)
    await interaction.response.send_message(f"👢 Kicked {member} | Reason: {reason}", ephemeral=True)

@bot.tree.command(name="ban", description="Ban a member from the server")
@app_commands.describe(member="User to ban", reason="Reason for ban")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    await member.ban(reason=reason)
    await interaction.response.send_message(f"🔨 Banned {member} | Reason: {reason}", ephemeral=True)

@bot.tree.command(name="tempban", description="Temporarily ban a user")
@app_commands.describe(member="User to ban", duration="Ban duration in minutes", reason="Reason for ban")
async def tempban(interaction: discord.Interaction, member: discord.Member, duration: int, reason: str = "No reason provided"):
    await member.ban(reason=reason)
    await interaction.response.send_message(f"⛔ Temporarily banned {member} for {duration} minutes. Reason: {reason}", ephemeral=True)

    await asyncio.sleep(duration * 60)
    await interaction.guild.unban(member)

@bot.tree.command(name="unban", description="Unban a user from the server")
@app_commands.describe(user="The username#0000 or user ID to unban")
async def unban(interaction: discord.Interaction, user: str):
    banned_users = await interaction.guild.bans()

    user_name, user_discriminator = None, None
    if "#" in user:
        user_name, user_discriminator = user.split("#")

    for ban_entry in banned_users:
        banned_user = ban_entry.user

        if (user_name and banned_user.name == user_name and banned_user.discriminator == user_discriminator) or \
           (user.isdigit() and int(user) == banned_user.id):
            await interaction.guild.unban(banned_user)
            return await interaction.response.send_message(f"✅ Unbanned {banned_user}", ephemeral=True)

    await interaction.response.send_message("❌ User not found in ban list.", ephemeral=True)

@bot.tree.command(name="mute", description="Mute a member")
@app_commands.describe(member="User to mute")
async def mute(interaction: discord.Interaction, member: discord.Member):
    mute_role = discord.utils.get(interaction.guild.roles, name="Muted")
    if mute_role is None:
        mute_role = await interaction.guild.create_role(name="Muted")
        for channel in interaction.guild.channels:
            await channel.set_permissions(mute_role, speak=False, send_messages=False)

    await member.add_roles(mute_role)
    await interaction.response.send_message(f"🔇 Muted {member}", ephemeral=True)

@bot.tree.command(name="unmute", description="Unmute a member")
@app_commands.describe(member="User to unmute")
async def unmute(interaction: discord.Interaction, member: discord.Member):
    mute_role = discord.utils.get(interaction.guild.roles, name="Muted")
    if mute_role is None:
        return await interaction.response.send_message("There is no Muted role.", ephemeral=True)

    await member.remove_roles(mute_role)
    await interaction.response.send_message(f"🔊 Unmuted {member}", ephemeral=True)

@bot.tree.command(name="addrole", description="Add a role to a member")
@app_commands.describe(member="User", role="Role to add")
async def addrole(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    await member.add_roles(role)
    await interaction.response.send_message(f"✅ Added {role.name} to {member}", ephemeral=True)

@bot.tree.command(name="removerole", description="Remove a role from a member")
@app_commands.describe(member="User", role="Role to remove")
async def removerole(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    await member.remove_roles(role)
    await interaction.response.send_message(f"❌ Removed {role.name} from {member}", ephemeral=True)

@bot.tree.command(name="purge", description="Delete messages in a channel")
@app_commands.describe(amount="Number of messages to delete")
async def purge(interaction: discord.Interaction, amount: int):
    await interaction.channel.purge(limit=amount)
    await interaction.response.send_message(f"🧹 Deleted {amount} messages", ephemeral=True)

# -------------------------
# WARNING SYSTEM
# -------------------------

@bot.tree.command(name="warn", description="Warn a user")
@app_commands.describe(member="User to warn", reason="Reason for warning")
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str):
    if member.id not in warnings:
        warnings[member.id] = []
    warnings[member.id].append(reason)

    await interaction.response.send_message(f"⚠️ Warned {member}: {reason}", ephemeral=True)

@bot.tree.command(name="removewarn", description="Remove a user's warning")
@app_commands.describe(member="User", index="Warning number to remove")
async def removewarn(interaction: discord.Interaction, member: discord.Member, index: int):
    if member.id not in warnings or index < 1 or index > len(warnings[member.id]):
        return await interaction.response.send_message("Invalid warning number.", ephemeral=True)

    removed = warnings[member.id].pop(index - 1)
    await interaction.response.send_message(f"🗑 Removed warning from {member}: {removed}", ephemeral=True)

@bot.tree.command(name="warnings", description="Check a user's warnings")
@app_commands.describe(member="User to check")
async def warnings_cmd(interaction: discord.Interaction, member: discord.Member):
    if member.id not in warnings or len(warnings[member.id]) == 0:
        return await interaction.response.send_message(f"{member} has no warnings.", ephemeral=True)

    warn_list = "\n".join([f"{i+1}. {w}" for i, w in enumerate(warnings[member.id])])
    await interaction.response.send_message(f"⚠️ Warnings for {member}:\n{warn_list}", ephemeral=True)

# -------------------------
# FUN COMMANDS
# -------------------------

@bot.tree.command(name="8ball", description="Ask the magic 8ball a question")
@app_commands.describe(question="Your question")
async def eightball(interaction: discord.Interaction, question: str):
    responses = [
        "Yes", "No", "Definitely", "Absolutely not", 
        "Ask again later", "Probably", "I doubt it", "100% yes"
    ]
    await interaction.response.send_message(f"🎱 {random.choice(responses)}")

@bot.tree.command(name="meme", description="Get a random meme")
async def meme(interaction: discord.Interaction):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://meme-api.com/gimme") as resp:
            data = await resp.json()
            await interaction.response.send_message(data["url"])

@bot.tree.command(name="joke", description="Get a random joke")
async def joke(interaction: discord.Interaction):
    jokes = [
        "Why don’t skeletons fight each other? They don’t have the guts.",
        "I told my computer I needed a break, and it said 'No problem — I’ll go to sleep.'",
        "Why did the scarecrow win an award? Because he was outstanding in his field.",
        "I tried to catch fog yesterday. Mist."
    ]
    await interaction.response.send_message(random.choice(jokes))

@bot.tree.command(name="fact", description="Get a random fact")
async def fact(interaction: discord.Interaction):
    facts = [
        "Honey never spoils — archaeologists found 3000-year-old honey that was still edible.",
        "Bananas are berries, but strawberries are not.",
        "Octopuses have three hearts.",
        "A day on Venus is longer than a year on Venus.",
        "Your brain uses about 20% of your body's oxygen.",
        "Sharks existed before trees.",
        "There are more stars in the universe than grains of sand on Earth."
    ]
    await interaction.response.send_message(random.choice(facts))

@bot.tree.command(name="slap", description="Slap someone")
@app_commands.describe(member="User to slap")
async def slap(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.send_message(f"🤚 {interaction.user} slapped {member}!")

@bot.tree.command(name="bite", description="Bite someone")
@app_commands.describe(member="User to bite")
async def bite(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.send_message(f"🦷 {interaction.user} bit {member}!")

@bot.tree.command(name="hug", description="Hug someone")
@app_commands.describe(member="User to hug")
async def hug(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.send_message(f"🤗 {interaction.user} hugged {member}!")

@bot.tree.command(name="roast", description="Roast someone")
@app_commands.describe(member="User to roast")
async def roast(interaction: discord.Interaction, member: discord.Member):
    roasts = [
        "You're not stupid — you just have bad luck thinking.",
        "If I wanted to kill myself, I'd climb your ego and jump to your IQ.",
        "You're like a cloud. Once you disappear, it's a beautiful day.",
        "You're proof that evolution can go in reverse."
    ]
    await interaction.response.send_message(f"🔥 {member}, {random.choice(roasts)}")

@bot.tree.command(name="kill", description="Playfully 'kill' someone (not real)")
@app_commands.describe(member="User to kill")
async def kill(interaction: discord.Interaction, member: discord.Member):
    deaths = [
        f"{member} slipped on a banana peel and dramatically died.",
        f"{member} died of cringe overload.",
        f"{member} was jump‑scared by a butterfly and passed away instantly.",
        f"{member} exploded from too much rizz.",
        f"{member} died after losing a staring contest with {interaction.user}.",
        f"{member} vanished into the void after touching grass.",
        f"{member} died because they forgot to drink water for 0.2 seconds."
    ]
    await interaction.response.send_message(f"💀 {random.choice(deaths)}")

@bot.tree.command(name="say", description="Make the bot say something")
@app_commands.describe(message="Message for the bot to say")
async def say(interaction: discord.Interaction, message: str):
    await interaction.response.send_message("Message sent!", ephemeral=True)
    await interaction.channel.send(message)

# -------------------------

bot.run("MTQ3MjEwODM2MDE3MzA5Mjk0Ng.GlRudk.pvhchJOgxtH1kSgNhj9rs2eX9TrNtAAdsUsAus")

