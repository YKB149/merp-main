import discord
from discord.ext import commands
from discord import app_commands
from discord.ext import commands, tasks
import asyncio
from datetime import datetime, timedelta
import pytz
import os
import psutil
import platform
from discord.ui import Modal, TextInput, View
from discord.ui import Select, View
        

intents = discord.Intents.default()
intents.members = True  
bot = commands.Bot(command_prefix="!", intents=intents)


AUTHORIZED_ROLE_ID = 1   #management role id
LOGGING_CHANNEL_ID = 1  #logging channel to send user whitelisted embed
WHITELIST_ROLE_ID = 1  # Replace with the ID of the whitelist role
APPROVAL_IMAGE_URL = "https://merpindia.in/gallery/whitelist_approved.png"  
REJECTION_IMAGE_URL = "https://merpindia.in/gallery/whitelist_rejected.png"

def has_required_role(interaction: discord.Interaction):
    return any(role.id == AUTHORIZED_ROLE_ID for role in interaction.user.roles)

def role_required():
    async def predicate(interaction: discord.Interaction):
        if not has_required_role(interaction):
            await interaction.response.send_message(
                "You are not authorized to use this bot.",
                ephemeral=True  
            )
            return False
        return True
    return app_commands.check(predicate)

# Slash command: Kick
@bot.tree.command(name="kick", description="Kick a user from the server.")
@role_required()
@app_commands.describe(member="The member to kick", reason="Reason for the kick")
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    if interaction.user.guild_permissions.kick_members:
        await member.kick(reason=reason)
        embed = discord.Embed(
            title="Member Kicked",
            description=f"{member.mention} has been kicked.",
            color=0xff0000
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_footer(text=f"Actioned by {interaction.user}")
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("You don't have permission to kick members.", ephemeral=True)

# Slash command: Ban
@bot.tree.command(name="ban", description="Ban a user from the server.")
@role_required()
@app_commands.describe(member="The member to ban", reason="Reason for the ban")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    if interaction.user.guild_permissions.ban_members:
        await member.ban(reason=reason)
        embed = discord.Embed(
            title="Member Banned",
            description=f"{member.mention} has been banned.",
            color=0x0000ff
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_footer(text=f"Actioned by {interaction.user}")
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("You don't have permission to ban members.", ephemeral=True)

# Slash command: Timeout
@bot.tree.command(name="timeout", description="Put a member in timeout.")
@role_required()
@app_commands.describe(member="The member to timeout", duration="Timeout duration in seconds")
async def timeout(interaction: discord.Interaction, member: discord.Member, duration: int):
    if interaction.user.guild_permissions.moderate_members:
        await member.edit(timeout_until=discord.utils.utcnow() + discord.timedelta(seconds=duration))
        embed = discord.Embed(
            title="Member Timed Out",
            description=f"{member.mention} is in timeout for {duration} seconds.",
            color=0xffff00
        )
        embed.set_footer(text=f"Actioned by {interaction.user}")
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("You don't have permission to moderate members.", ephemeral=True)

# Slash command: Custom Message
@bot.tree.command(name="announce", description="Create a custom announcement.")
@role_required()
@app_commands.describe(
    title="The title of the announcement",
    description="The description of the announcement",
    color="The color of the embed (hex format, e.g., #ff0000)",
    image_url="The image URL for the embed"
)
async def announce(interaction: discord.Interaction, title: str, description: str, color: str = None, image_url: str = None):
    color = int(color.lstrip('#'), 16) if color else 0x00ff00 
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text=f"Announced by {interaction.user}")
    if image_url:
        embed.set_image(url=image_url)
    await interaction.response.send_message(embed=embed)

# Slash command: Poll
@bot.tree.command(name="poll", description="Create a poll with multiple options.")
@role_required()
@app_commands.describe(question="The poll question", options="Comma-separated list of options")
async def poll(interaction: discord.Interaction, question: str, options: str):
    options_list = options.split(',')
    if len(options_list) < 2:
        await interaction.response.send_message("Please provide at least two options.", ephemeral=True)
        return

    embed = discord.Embed(title="Poll", description=question, color=0x3498db)
    reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣'][:len(options_list)]
    for idx, option in enumerate(options_list):
        embed.add_field(name=f"{reactions[idx]} Option", value=option.strip(), inline=False)
    message = await interaction.channel.send(embed=embed)
    for reaction in reactions:
        await message.add_reaction(reaction)

    await interaction.response.send_message("Poll created!", ephemeral=True)

# Slash command: Set Activity
@bot.tree.command(name="setactivity", description="Set a custom bot activity.")
@role_required()
@app_commands.describe(
    activity_type="Type of activity (playing, watching, listening)",
    description="The description of the activity"
)
async def setactivity(interaction: discord.Interaction, activity_type: str, description: str):
    activity_type = activity_type.lower()
    if activity_type == "playing":
        activity = discord.Game(name=description)
    elif activity_type == "watching":
        activity = discord.Activity(type=discord.ActivityType.watching, name=description)
    elif activity_type == "listening":
        activity = discord.Activity(type=discord.ActivityType.listening, name=description)
    else:
        await interaction.response.send_message("Invalid activity type. Choose from: playing, watching, listening, competing.", ephemeral=True)
        return

    await bot.change_presence(activity=activity)
    await interaction.response.send_message(f"Bot activity set to: {activity_type.capitalize()} {description}", ephemeral=True)

# Slash command: Help
@bot.tree.command(name="help", description="Show all available commands and their descriptions.")
@role_required()
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Help - List of Commands",
        description="Here are all the available commands in the bot:",
        color=0x00ff00
    )
    for command in bot.tree.get_commands():
        embed.add_field(name=f"/{command.name}", value=command.description, inline=False)
    embed.set_footer(text=f"Requested by {interaction.user}")
    await interaction.response.send_message(embed=embed)


# Slash command: Check Ping
@bot.tree.command(name="ping", description="Check the bot's latency.")
@role_required()
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000) 
    embed = discord.Embed(
        title="Pong! 🏓",
        description=f"The bot's latency is `{latency}ms`.",
        color=0x00ff00
    )
    await interaction.response.send_message(embed=embed)
    
    
# Slash command: System Info
@bot.tree.command(name="systeminfo", description="Check the bot's hosting system information.")
@role_required()
async def systeminfo(interaction: discord.Interaction):
    # Get system information
    process = psutil.Process(os.getpid())
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    memory_used = memory_info.used / (1024 ** 2)  # Convert bytes to MB
    memory_total = memory_info.total / (1024 ** 2)  # Convert bytes to MB
    memory_percent = memory_info.percent
    uptime_seconds = int(process.create_time())
    uptime = datetime.now() - datetime.fromtimestamp(uptime_seconds)

    # Create an embed
    embed = discord.Embed(
        title="Bot Hosting System Information",
        color=0x3498db
    )
    embed.add_field(name="CPU Usage", value=f"{cpu_usage}%", inline=False)
    embed.add_field(name="Memory Usage", value=f"{memory_used:.2f} MB / {memory_total:.2f} MB ({memory_percent}%)", inline=False)
    embed.add_field(name="Bot Uptime", value=str(uptime).split('.')[0], inline=False)
    embed.add_field(name="Platform", value=os.name, inline=False)
    embed.add_field(name="Python Version", value=os.sys.version.split(" ")[0], inline=False)
    embed.set_footer(text=f"Requested by {interaction.user}")

    # Send the embed
    await interaction.response.send_message(embed=embed)
    
# Timezone for IST
ist = pytz.timezone("Asia/Kolkata")


SCHEDULED_CHANNEL_ID = 1315896892156018769 

def get_ist_time():
    return datetime.now(ist)


@tasks.loop(seconds=60)  # Runs every minute
async def scheduled_task():
    now = get_ist_time()
    print(f"[DEBUG] Current IST Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")  # Debugging log
    if now.hour == 8 and now.minute == 5:
        channel = bot.get_channel(SCHEDULED_CHANNEL_ID)
        if channel:
            await channel.send("Test Morning 8:05")
        else:
            print("[ERROR] Scheduled channel not found or bot has no access.")
    elif now.hour == 20 and now.minute == 5:
        channel = bot.get_channel(SCHEDULED_CHANNEL_ID)
        if channel:
            await channel.send("test msg.")
        else:
            print("[ERROR] Scheduled channel not found or bot has no access.")
            
            
            
# --- Whitelist Approved Command ---
@bot.tree.command(name="whitelist_approved", description="Approve a user for the whitelist.")
@role_required()
@app_commands.describe(user="The user to approve for the whitelist.")
async def whitelist_approved(interaction: discord.Interaction, user: str):
    guild = interaction.guild
    member = discord.utils.get(guild.members, name=user)

    if member:
        role = guild.get_role(WHITELIST_ROLE_ID)
        if role:
            await member.add_roles(role)
            embed = discord.Embed(
                title="Whitelist Approved ✅",
                description=f"Congratulations **{member.mention}** has been approved for the whitelist.",
                color=discord.Color.green()
            )
            embed.set_footer(text=f"Approved by {interaction.user.display_name}")
            embed.set_image(url=APPROVAL_IMAGE_URL)

            logging_channel = guild.get_channel(LOGGING_CHANNEL_ID)
            if logging_channel:
                await logging_channel.send(content=f"{member.mention}", embed=embed)
            await interaction.response.send_message("Approval logged successfully.", ephemeral=True)
        else:
            await interaction.response.send_message("Whitelist role not found.", ephemeral=True)
    else:
        await interaction.response.send_message(f"User **{user}** not found in the server.", ephemeral=True)

# --- Whitelist Rejected Command ---
@bot.tree.command(name="whitelist_rejected", description="Reject a user from the whitelist.")
@role_required()
@app_commands.describe(user="The user to reject from the whitelist.")
async def whitelist_rejected(interaction: discord.Interaction, user: str):
    guild = interaction.guild
    member = discord.utils.get(guild.members, name=user)

    if member:
        embed = discord.Embed(
            title="Whitelist Rejected ❌",
            description=f"Sorry! **{member.mention}** has been rejected from the whitelist.",
            color=discord.Color.red()
        )
        embed.set_footer(text=f"Rejected by {interaction.user.display_name}")
        embed.set_image(url=REJECTION_IMAGE_URL)

        logging_channel = guild.get_channel(LOGGING_CHANNEL_ID)
        if logging_channel:
            await logging_channel.send(content=f"{member.mention}", embed=embed)
        await interaction.response.send_message("Rejection logged successfully.", ephemeral=True)
    else:
        await interaction.response.send_message(f"User **{user}** not found in the server.", ephemeral=True)

# --- Autocomplete for Whitelist Approved ---
@whitelist_approved.autocomplete("user")
async def whitelist_approved_autocomplete(interaction: discord.Interaction, current: str):
    guild = interaction.guild
    members = [member for member in guild.members if not member.bot]
    suggestions = [member for member in members if current.lower() in member.name.lower()]
    return [app_commands.Choice(name=member.name, value=member.name) for member in suggestions]

# --- Autocomplete for Whitelist Rejected ---
@whitelist_rejected.autocomplete("user")
async def whitelist_rejected_autocomplete(interaction: discord.Interaction, current: str):
    guild = interaction.guild
    members = [member for member in guild.members if not member.bot]
    suggestions = [member for member in members if current.lower() in member.name.lower()]
    return [app_commands.Choice(name=member.name, value=member.name) for member in suggestions]


# --- Custom Embed Command ---
class AnnounceModal(Modal):
    def __init__(self, channel: discord.TextChannel, color: discord.Color = None, image_url: str = None):
        super().__init__(title="Announcement Form")
        self.channel = channel
        self.color = color or discord.Color.blue()
        self.image_url = image_url

        self.title_input = TextInput(label="Title", placeholder="Enter the announcement title", max_length=256)
        self.add_item(self.title_input)

        self.description_input = TextInput(
            label="Description",
            placeholder="Enter the announcement description",
            style=discord.TextStyle.paragraph,
            max_length=2000,
        )
        self.add_item(self.description_input)

        self.mention_input = TextInput(
            label="Mention @everyone? (yes/no)",
            placeholder="Type 'yes' or 'no'",
            max_length=3,
        )
        self.add_item(self.mention_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            title = self.title_input.value
            description = self.description_input.value
            mention_everyone = self.mention_input.value.lower() in ["yes", "y"]

            embed = discord.Embed(
                title=title,
                description=description,
                color=self.color
            )

            if self.image_url:
                embed.set_image(url=self.image_url)

            message_content = "@everyone" if mention_everyone else None
            await self.channel.send(content=message_content, embed=embed)
            await interaction.response.send_message("Announcement sent successfully!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)

@bot.tree.command(name="embed", description="Create and send an embed.")
@role_required()
@app_commands.describe(channel="Channel to send the embed to.", color="Optional embed color in hex (e.g., #ff5733).", image_url="Optional image URL for the embed.")
async def announce(interaction: discord.Interaction, channel: discord.TextChannel, color: str = None, image_url: str = None):
    try:
        parsed_color = None
        if color:
            try:
                parsed_color = discord.Color(int(color.strip('#'), 16))
            except ValueError:
                await interaction.response.send_message("Invalid color format. Use hex format, e.g., #ff5733.", ephemeral=True)
                return

        modal = AnnounceModal(channel=channel, color=parsed_color, image_url=image_url)
        await interaction.response.send_modal(modal)

    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)


        
        
        
# --- Command for faqs ---        
@bot.tree.command(name="faq", description="Provides FAQs based on categories")
async def faq_command(interaction: discord.Interaction):
    
    options = [
        discord.SelectOption(label="Discord", description="FAQs about Discord"),
        discord.SelectOption(label="In-game", description="FAQs about the game")
    ]

    select = Select(
        placeholder="Choose a category...",
        options=options
    )

    async def select_callback(select_interaction: discord.Interaction):
        if select.values[0] == "In-game":
            
            in_game_options = [
                discord.SelectOption(label="faq1", description="desp"),
                discord.SelectOption(label="faq2", description="desp"),
                discord.SelectOption(label="faq3", description="desp"),
                discord.SelectOption(label="faq4", description="desp"),
                discord.SelectOption(label="faq5", description="desp"),
                discord.SelectOption(label="faq6", description="desp"),
                discord.SelectOption(label="faq7", description="desp"),
                discord.SelectOption(label="faq8", description="desp"),
                discord.SelectOption(label="faq9", description="desp"),
                discord.SelectOption(label="faq10", description="desp"),
                discord.SelectOption(label="faq11", description="desp"),
                discord.SelectOption(label="faq12", description="desp"),
                discord.SelectOption(label="faq13", description="desp"),
                discord.SelectOption(label="faq14", description="desp"),
                discord.SelectOption(label="faq15", description="desp"),
                discord.SelectOption(label="faq16", description="desp"),
                discord.SelectOption(label="faq17", description="desp"),
                discord.SelectOption(label="faq18", description="desp"),
                discord.SelectOption(label="faq19", description="desp"),
                discord.SelectOption(label="faq20", description="desp")
            ]

            unique_links = {
                "faq1": "https://example.com/",
                "faq2": "https://example.com/",
                "faq3": "https://example.com/",
                "faq4": "https://example.com/",
                "faq5": "https://example.com/",
                "faq6": "https://example.com/",
                "faq7": "https://example.com/",
                "faq8": "https://example.com/",
                "faq9": "https://example.com/",
                "faq10": "https://example.com/",
                "faq11": "https://example.com/",
                "faq12": "https://example.com/",
                "faq13": "https://example.com/",
                "faq14": "https://example.com/",
                "faq15": "https://example.com/",
                "faq16": "https://example.com/",
                "faq17": "https://example.com/",
                "faq18": "https://example.com/",
                "faq19": "https://example.com/",
                "faq20": "https://example.com/"
            }

            in_game_select = Select(
                placeholder="Choose an in-game FAQ...",
                options=in_game_options
            )

            async def in_game_select_callback(in_game_interaction: discord.Interaction):
                selected_option = in_game_select.values[0]
                link = unique_links.get(selected_option, "https://example.com/default")
                embed = discord.Embed(
                    title="Tutorial",
                    description=f"Click here to watch the tutorial for {selected_option}",
                    color=discord.Color.blue()
                )
                embed.add_field(name="Link", value=f"[Click here]({link})")
                await in_game_interaction.response.send_message(embed=embed, ephemeral=True)

            in_game_select.callback = in_game_select_callback
            in_game_view = View()
            in_game_view.add_item(in_game_select)

            await select_interaction.response.send_message(
                content="Please select an in-game FAQ:",
                view=in_game_view,
                ephemeral=True
            )
        else:
            
            discord_options = [
                discord.SelectOption(label="faq1", description="desp"),
                discord.SelectOption(label="faq2", description="desp"),
                discord.SelectOption(label="faq3", description="desp"),
                discord.SelectOption(label="faq4", description="desp"),
                discord.SelectOption(label="faq5", description="desp")
            ]

            discord_links = {
                "faq1": "https://example.com/",
                "faq2": "https://example.com/",
                "faq3": "https://example.com/",
                "faq4": "https://example.com/",
                "faq5": "https://example.com/"
            }

            discord_select = Select(
                placeholder="Choose a Discord FAQ...",
                options=discord_options
            )

            async def discord_select_callback(discord_interaction: discord.Interaction):
                selected_option = discord_select.values[0]
                link = discord_links.get(selected_option, "https://example.com/default")
                embed = discord.Embed(
                    title="Tutorial",
                    description=f"Click here to watch the tutorial for {selected_option}",
                    color=discord.Color.green()
                )
                embed.add_field(name="Link", value=f"[Click here]({link})")
                await discord_interaction.response.send_message(embed=embed, ephemeral=True)

            discord_select.callback = discord_select_callback
            discord_view = View()
            discord_view.add_item(discord_select)

            await select_interaction.response.send_message(
                content="Please select a Discord FAQ:",
                view=discord_view,
                ephemeral=True
            )

    select.callback = select_callback
    view = View()
    view.add_item(select)

    await interaction.response.send_message(
        content="Choose a category for FAQs:",
        view=view,
        ephemeral=True
    )

    
    
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}!")
    print(f"[INFO] Scheduled task started.")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands successfully.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    print(f"Logged in as {bot.user}")
    if not scheduled_task.is_running():
        scheduled_task.start()


bot.run("")
