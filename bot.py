from functools import cmp_to_key
import random
import discord
from discord.ext.commands import BucketType, has_permissions
from datetime import timedelta
from discord.ext import commands
from discord.utils import get
import json
import os
import nltk
from fuzzywuzzy import fuzz
import time
import subprocess
from PIL import Image
from pytesseract import pytesseract
import enum
import asyncio
#from pynput.keyboard import Controller, Key
#import pyautogui
import webbrowser
import sys
from economy import Bank, Income, Items
from mss import mss
from nltk.corpus import words
import locale

english_words = set(words.words())

english_words.add("fuck")
english_words.add("shit")
english_words.add("faggot")
english_words.add("boobies")
english_words.add("boobs")
english_words.add("bitch")

english_words = sorted(english_words)

is_restarting_for_disconnect = False 
RESTART_FLAG_FILE = "_restarting_flag.tmp" 

can_load_sources = False


intents = discord.Intents.all()
intents.message_content = True
intents.members = True 

bot = commands.Bot(command_prefix='!', intents=intents)
bot.remove_command('help') 

# It's good practice to define these at the top or in a config.py
ONLINE_ROLE_ID = 1383129931541643295 # Role to ping when bot comes online
OFFLINE_ROLE_ID = 1383130035984142386 # Role to ping when bot goes offline
STATUS_CHANNEL_ID = 1368285968632778862 # Channel for online/offline pings

print(f"Current working directory: {os.getcwd()}")
print(f"Absolute path of economy.py: {os.path.abspath(__file__)}")
print(f"Expected balance.json path: {os.path.join(os.path.dirname(__file__), 'balance.json')}")


class OS(enum.Enum):
    WINDOWS = 0
    MAC = 1
    LINUX = 2


class Language(enum.Enum):
    ENG = 'eng'
    NL = 'nl'

lang = Language.ENG

class OCR:

    def __init__(self, operating_system: OS):
        # Get the absolute path to the project directory
        self.project_dir = os.path.abspath(os.path.dirname(__file__))
        
        if operating_system == OS.WINDOWS:
            self.tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            # Use local tessdata directory with absolute path
            self.tessdata_prefix = os.path.join(self.project_dir, "tessdata")
            
            # Ensure tessdata directory exists
            os.makedirs(self.tessdata_prefix, exist_ok=True)
            
            # Set environment variables
            os.environ['TESSDATA_PREFIX'] = self.tessdata_prefix
            pytesseract.tesseract_cmd = self.tesseract_path
            
            print(f"Project directory: {self.project_dir}")
            print(f"Tesseract path set to: {self.tesseract_path}")
            print(f"TESSDATA_PREFIX set to: {self.tessdata_prefix}")
        elif operating_system == OS.MAC:
            print("Using system Tesseract installation for Mac")
            self.tessdata_prefix = "/usr/share/tessdata"
        elif operating_system == OS.LINUX:
            print("Using system Tesseract installation for Linux")
            self.tessdata_prefix = "/usr/share/tessdata"
            # On Linux, pytesseract will find the system installation automatically
        
        # Debug information
        print(f"Current TESSDATA_PREFIX: {os.getenv('TESSDATA_PREFIX')}")
        print(f"Checking if tessdata directory exists: {os.path.exists(self.tessdata_prefix)}")
        
        try:
            version = pytesseract.get_tesseract_version()
            print(f"Tesseract version: {version}")
        except Exception as e:
            print(f"Error getting Tesseract version: {e}")
            print("Please ensure Tesseract is installed correctly")

    def ocr_core(self, image_path: str, lang: str) -> str:
        try:
            # Convert to absolute path if not already
            image_path = os.path.abspath(image_path)
            
            if not os.path.exists(image_path):
                print(f"Error: Image file not found at {image_path}")
                return ""
                
            image = Image.open(image_path)
            # Add preprocessing to improve OCR accuracy
            image = image.convert('L')  # Convert to grayscale
            
            extracted_text = pytesseract.image_to_string(image, lang=lang, config='--psm 6')
            return extracted_text.strip()
        except Exception as e:
            print(f"Error performing OCR: {e}")
            print(f"Current working directory: {os.getcwd()}")
            print(f"Image path: {image_path}")
            print(f"Language: {lang}")
            return ""


if os.path.exists('kill_counts.json'):
    with open('kill_counts.json', 'r') as f:
        kill_counts = json.load(f)
else:
    kill_counts = {}

def save_kill_counts():
    try:
        file_path = os.path.abspath('kill_counts.json')
        # Create directory if it doesn't existmember mater
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Use a temporary file to prevent corruption
        temp_path = file_path + '.tmp'
        with open(temp_path, 'w') as f:
            json.dump(kill_counts, f)
        
        # Safely replace the old file with the new one
        if os.path.exists(file_path):
            os.replace(temp_path, file_path)
        else:
            os.rename(temp_path, file_path)
    except (PermissionError, OSError) as e:
        print(f"Error saving kill counts: {e}")

@bot.event
async def on_ready():
    """
    Event that fires when the bot has successfully connected to Discord.
    Handles initial setup, data loading, and sends the 'bot online' ping
    conditionally based on whether it's a restart.
    """
    print(f"Logged in as {bot.user}")
    global can_load_sources

    # Check for restart flag file. If it exists, it means the bot is restarting.
    is_previous_process_restarting = os.path.exists(RESTART_FLAG_FILE)

    # Make the user only process information when the bot has finished initializing
    can_load_sources = True


    # Load economy data. Do this once on_ready.
    Bank.read_balance()
    Income.loadincomes()
    Income.create_sources() # Also ensures sources are initialized/loaded
    Items.load_player_inventory()
    Items.create_item_sources() # Also ensures item sources are initialized/loaded
    print("Economy data loaded/initialized for all classes.")

    # --- Send Bot Online Ping (Conditional) ---
    status_channel = bot.get_channel(STATUS_CHANNEL_ID)
    if status_channel:
        if not is_previous_process_restarting:
            # If the flag file does NOT exist, it's a fresh start (not a restart)
            try:
                # Ping the role by its ID
                await status_channel.send(f"✅ Bot is now online! <@&{ONLINE_ROLE_ID}>")
                print("Sent 'bot online' ping.")
            except discord.Forbidden:
                print(f"Error: Bot does not have permission to send messages or ping role in channel {STATUS_CHANNEL_ID}.")
            except Exception as e:
                print(f"An unexpected error occurred sending online ping: {e}")
        else:
            # If the flag file DOES exist, it's a restart, so skip the online ping
            print("Skipping 'bot online' ping due to restart flag.")
            # Immediately remove the flag file after detecting it
            try:
                os.remove(RESTART_FLAG_FILE)
                print(f"Removed restart flag file: {RESTART_FLAG_FILE}")
            except OSError as e:
                print(f"Error removing restart flag file {RESTART_FLAG_FILE}: {e}")
    else:
        print(f"Status channel with ID {STATUS_CHANNEL_ID} not found.")

    # Start recurring tasks
    bot.loop.create_task(check_guillotine_cooldown())
    bot.loop.create_task(checkbankrobery())

    # Logging guild and member info (for debugging/monitoring)
    for guild in bot.guilds:
        print(f"- {guild.name} (id: {guild.id}) with {guild.member_count} members")

    for guild in bot.guilds:
        print(f"- {guild.name} (id: {guild.id}) with {guild.member_count} members")

        for member in guild.members:
            if not member.bot:
                print(f"{member.name} ({member.display_name}, {member.id}) ")

async def check_guillotine_cooldown():
    await bot.wait_until_ready()
    while not bot.is_closed():
        for guild in bot.guilds:
            cooldowns = load_cooldowns()
            guild_id = str(guild.id)
            
            if guild_id in cooldowns and 'guillotine' in cooldowns[guild_id]:
                last_used = cooldowns[guild_id]['guillotine']
                cooldown_time = command_cooldowns.get('guillotine', 86400)
                
                # If cooldown has expired
                if time.time() - last_used >= cooldown_time:
                    reminder_channel = discord.utils.get(guild.text_channels, name="reminders")
                    if reminder_channel:
                        await reminder_channel.send("The richest person in the server *can* be guillotined!")
                        # Update the cooldown to prevent spam
                        cooldowns[guild_id]['guillotine'] = time.time()
                        save_cooldowns(cooldowns)
        
        # Check every hour
        await asyncio.sleep(3600)

async def checkbankrobery():
    await bot.wait_until_ready()
    while not bot.is_closed():
        for guild in bot.guilds:
            cooldowns = load_cooldowns()
            guild_id = str(guild.id)

            if guild_id in cooldowns and 'rob_bank' in cooldowns[guild_id]:
                last_used = cooldowns[guild_id]['rob_bank']
                cooldown_time = command_cooldowns.get('rob_bank', 86400)

                if time.time() - last_used >= cooldown_time:
                    reminder_channel = discord.utils.get(guild.text_channels, name="reminders")
                    if reminder_channel:
                        await reminder_channel.send("The bank is being robbed!")
                        # Update the cooldown to prevent spam
                        cooldowns[guild_id]['rob_bank'] = time.time()
                        save_cooldowns(cooldowns)

        await asyncio.sleep(3600)


@bot.command()
async def hello(ctx):
    await ctx.send("Hello, world!")


@bot.command()
@commands.has_permissions(moderate_members=True)
async def timeout(ctx, member: discord.Member, minutes: int, ping: bool=True):
    try:
        duration = timedelta(minutes=minutes)
        await member.timeout(duration, reason=f"Timed out by {ctx.author}")
        if ping: await ctx.send(f"{member.mention} has been timed out for {minutes} minute(s).")
    except discord.Forbidden:
        await ctx.send("I don't have permission to timeout this user.")
    except discord.HTTPException as e:
        await ctx.send(f"Failed to timeout user: {e} - Ping mater")

@bot.command()
@commands.has_permissions(administrator=True)
async def shutdown(ctx):
    await ctx.send("Shutting down...")
    await bot.close()

@bot.command()
async def end(ctx):
    for role in ctx.author.roles:
        if role.name == "mater":
            await ctx.send("Mater is shooting the bot in the face, too long of a coding adevnture ig")
            await bot.close()
            return
    await ctx.send("You don't have permission to use this command.")
    return

@bot.command()
async def restart(ctx):
    """Restarts the bot."""
    global is_restarting_for_disconnect # Access the global flag
    for role in ctx.author.roles:
        if role.name == "mater": # Check for the specific role
            is_restarting_for_disconnect = True # Set the flag to true for the *current* process's on_disconnect
            
            # --- IMPORTANT: Create the persistent flag file here ---
            # This file signals the *new* process's on_ready to skip the online ping.
            with open(RESTART_FLAG_FILE, 'w') as f:
                f.write('restarting')
            print(f"Created restart flag file: {RESTART_FLAG_FILE}")
            # --- End IMPORTANT ---

            await ctx.send("Mater is restarting the bot... Please wait a moment.")
            await bot.close() # This will trigger on_disconnect (which will see is_restarting_for_disconnect=True)
            
            # This replaces the current process with a new one, effectively restarting the script
            os.execv(sys.executable, ['python'] + sys.argv)
            # Code after os.execv will not be reached in this process
            return # Ensure the command handler exits
    await ctx.send("You don't have permission to use this command.")

@bot.event
async def on_disconnect():
    """
    Event that fires when the bot disconnects from Discord.
    Handles saving data and sending the 'bot offline' ping, unless restarting.
    """
    global is_restarting_for_disconnect # Access the global flag

    print("Bot disconnected.")
    
    # Save balances one last time on disconnect
    Bank.save_balances()
    Income.saveincomes()
    Items.save_player_inventory()
    print("All economy data saved on disconnect.")

    # --- Send Bot Offline Ping (conditional) ---
    if not is_restarting_for_disconnect: # Only send if not intentionally restarting
        status_channel = bot.get_channel(STATUS_CHANNEL_ID)
        if status_channel:
            try:
                # Ping the role by its ID
                await status_channel.send(f"❌ Bot is now offline! <@&{OFFLINE_ROLE_ID}>")
                print("Sent 'bot offline' ping.")
            except discord.Forbidden:
                print(f"Error: Bot does not have permission to send messages or ping role in channel {STATUS_CHANNEL_ID}.")
            except Exception as e:
                print(f"An unexpected error occurred sending offline ping: {e}")
        else:
            print(f"Status channel with ID {STATUS_CHANNEL_ID} not found for offline ping.")
    else:
        print("Bot is restarting, skipping offline ping.")
    
    # The is_restarting_for_disconnect flag will implicitly be reset when the new process starts
    # (as it's a global variable in a new process), or if the current process fully exits.


@bot.command()
async def kill(ctx, member: discord.Member):
    cooldown_msg = check_cooldown(ctx, 'kill')  # Cooldown time from dictionary
    if cooldown_msg:
        await ctx.send(cooldown_msg)
        return

    killer_id = str(ctx.author.id)
    if killer_id not in kill_counts:
        kill_counts[killer_id] = 0
    kill_counts[killer_id] += 1
    save_kill_counts()

    if not member in ctx.guild.members:
        await ctx.send("Member not found. Please try again.")
        return
    
    if member == ctx.author:
        await ctx.send("there's 20% chance of suicide you know if you have a knife")

    try:
        duration = timedelta(minutes=360)
        if random.randint(1, 100) == 1:
            await member.timeout(duration, reason=f"Killed by {ctx.author}")
            await ctx.send(f"💀 {member.mention} has been killed (timed out for {duration}).")
        else:
            await ctx.send(f"{member.mention} survived... this time.")
        if not any(role.name == "Knife" for role in ctx.author.roles):
            await ctx.send(f"Unfortunately you don't have a bomb.")
        else:
            if random.randint(1, 10) == 1:
                await member.timeout(duration, reason=f"Killed by {ctx.author}")
                await ctx.send(f"💀 {member.mention} has been killed (timed out for {duration}) because they have a knife!.")
        
        print(f"{ctx.author} has used !kill {kill_counts[killer_id]} time(s)")
        return
    except discord.Forbidden:
        await ctx.send("I don't have permission to timeout this user.")
    except discord.HTTPException as e:
        await ctx.send(f"Failed to timeout user: {e} ping mater")


@bot.command()
async def random_kill(ctx):
    cooldown_msg = check_cooldown(ctx, 'random_kill')  # Cooldown time from dictionary
    if cooldown_msg:
        await ctx.send(cooldown_msg)
        return

    members = [m for m in ctx.guild.members if not m.bot and m != ctx.author]
    killer_id = str(ctx.author.id)
    if killer_id not in kill_counts:
        kill_counts[killer_id] = 0
    kill_counts[killer_id] += 1
    save_kill_counts()

    if not members:
        await ctx.send("No valid members to kill.")
        return

    victim = random.choice(members)
    duration = timedelta(minutes=360)

    try:
        if random.randint(1, 100) == 1:
            await victim.timeout(duration, reason=f"Randomly killed by {ctx.author}")
            await ctx.send(f"💀 {victim.mention} has been randomly killed (timed out for 6 hours).")
        else:
            await ctx.send(f"{victim.mention} dodged death this time.")
    except discord.Forbidden:
        await ctx.send("I don't have permission to timeout that user.")
    except discord.HTTPException as e:
        await ctx.send(f"Failed to timeout user: {e} - ping mater")

@bot.command()
async def random_member(ctx):
    members = [member for member in ctx.guild.members if not member.bot]  # Exclude bots (optional)
    if not members:
        await ctx.send("No members found.")
        return

    chosen = random.choice(members)
    await ctx.send(f"🎯 Random member: {chosen.mention}")
    return chosen

@bot.command()
@commands.has_permissions(manage_roles=True)
async def removerole(ctx, member: discord.Member, *, role_name):
    await remove_role_by_name(ctx, member, role_name)

async def remove_role_by_name(ctx, member: discord.Member, role_name: str):
    role = discord.utils.get(ctx.guild.roles, name=role_name)
    print(role)
    print("trying to remove role")
    if role is None:
        await ctx.send(f"Role '{role_name}' not found.")
        return False

    try:
        await member.remove_roles(role, reason=f"Removed by {ctx.author}")
        return True
    except discord.Forbidden:
        await ctx.send("I don't have permission to remove that role.")
        return False

@bot.command()
async def killcount(ctx, member: discord.Member = None):
    member = member or ctx.author
    count = kill_counts.get(member.id, kill_counts.get(str(member.id), 0))
    await ctx.send(f"{member.display_name} has tried to kill {count} time(s).")



@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"Pong! Latency: {latency}ms")

@bot.command()
async def usebomb(ctx, member: discord.Member):

    killer_id = str(ctx.author.id)

    if killer_id not in kill_counts:
        kill_counts[killer_id] = 0

    kill_counts[killer_id] += 1
    save_kill_counts()

    
    if not any(role.name == "Bomb" for role in member.roles):
        await ctx.send(f"Unfortunately you don't have a bomb.")
        return

    await remove_role_by_name(ctx, member, "Bomb")

    
    await ctx.send(f"{member.mention} used the bomb!")
    if random.randint(1, 10) == 1:
        await ctx.send(f"{member.mention} blew up yourself!")
        await timeout(ctx, member, 10)
    elif random.randint(1, 10) == 1:
        await ctx.send(f"{member.mention} blew up someone else!")
        members = [member for member in ctx.guild.members if not member.bot]
        chosen_one = random.choice(members)
        await ctx.send(f"{chosen_one.mention} was blown up!")
        await timeout(ctx, chosen_one, 10)
    else:
        await ctx.send(f"{member.mention} missed!")

async def usebrick(ctx, member: discord.Member, target: discord.member):
    await ctx.send(f"{member.mention} used the brick!")

    if not any(role.name == "Brick" for role in member.roles):
        await ctx.send(f"Unfortunately you don't have a brick.")
        return

    await remove_role_by_name(ctx, member, "Brick")
    await timeout(ctx, target, 5)
    await ctx.send(f"{target.mention} was hit by the brick!")

@bot.command()
async def brick(ctx, member: discord.Member):
    usebrick(ctx, ctx.author, member)
    await ctx.send("That is unfortunately not the correct chain of commands. You first need to type '!buy brick' to buy a brick, once you then use  '!use brick', it will then give u the brick role. Finally use !brick @user then you will throw your brick at them :)")

@bot.command()
async def stab(ctx, member: discord.Member):
    cooldown_msg = check_cooldown(ctx, 'stab')  # Cooldown time from dictionary
    if cooldown_msg:
        await ctx.send(cooldown_msg)
        return

    await ctx.send(f"{member.mention}, you've been stabbed!")
    
    if not any(role.name == "Knife" for role in ctx.author.roles):
        await ctx.send(f"Unfortunately you don't have a knife.")
        return

    killer_id = str(ctx.author.id)
    if killer_id not in kill_counts:
        kill_counts[killer_id] = 0
    kill_counts[killer_id] += 1
    save_kill_counts()

    await timeout(ctx, member, 10)

# Define your View class (put this at the top level of your bot.py, not inside a command)
class CommandsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180) # The view will expire after 3 minutes of inactivity

    # This creates a button labeled "Economy Commands"
    @discord.ui.button(label="Economy Commands", style=discord.ButtonStyle.success, emoji="💰")
    async def economy_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Callback for the Economy Commands button.
        When clicked, it sends the economy commands embed.
        """
        await send_economy_commands_embed(interaction)

    @discord.ui.button(label="Violent Commands", style=discord.ButtonStyle.danger, emoji="🔪")
    async def violent_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Callback for the Violent Commands button.
        When clicked, it sends the violent commands embed.
        """
        await send_violent_commands(interaction)

async def send_economy_commands_embed(interaction: discord.Interaction):
    help_embed = discord.Embed(
        title="The commands",
        description="The list of all commands relating to the economy",
    )

    help_embed.add_field(
        name="!balance [member]",
        value="Shows balance of yourself/another user",
        inline=False
    )

    help_embed.add_field(
        name="!deposit/withdraw <amount>",
        value="Self explanatory",
        inline=False
    )

    help_embed.add_field(
        name="!work",
        value="Gives money based on your current net worth",
        inline=False
    )

    help_embed.add_field(
        name="!give [user] <amount>",
        value="Gives user an amount of cash",
        inline=False
    )

    help_embed.add_field(
        name="!collect",
        value="Collects your available income",
        inline=False
    )

    help_embed.add_field(
        name="!incomes",
        value="Displays all income sources and cooldowns",
        inline=False
    )

    help_embed.add_field(
        name="!incomesources",
        value="Displays info about your specific income sources",
        inline=False
    )

    help_embed.add_field(
        name="!richest-member",
        value="Displays the richest member this side of the economy",
        inline=False
    )

    help_embed.add_field(
        name="!store",
        value="Gets all the items within the store",
        inline=False
    )

    await interaction.response.send_message(embed=help_embed, ephemeral=True)

async def send_violent_commands(interaction: discord.Interaction):
    help_embed = discord.Embed(
        title="Violent commands",
        description="List of all commands that modify your kill_count (or display it)"
    )

    help_embed.add_field(
        name="!stab [user]",
        value="Stab another user, You can only stab once every hour and if you have a knife. Has a cooldown.",
        inline=False
    )

    help_embed.add_field(
        name="!use bomb",
        value="Use a bomb item. 1/10 chance to kill a random user and a 1/10 chance to kill yourself. Has a cooldown.",
        inline=False
    )

    help_embed.add_field(
        name="!use brick", 
        value="Use a brick item, gives you the brick role. Now if you type !use brick or !brick you can time someone out for 10 minutes",
        inline=False
    )

    help_embed.add_field(
        name="!kill [user]",
        value="Kill a user with a 1/10 chance (1/5 if you have a knife). Has a cooldown.",
        inline=False
    )

    help_embed.add_field(
        name="!killcount [user]",
        value="Check the targetted attack count of a user.",
        inline=False
    )

    help_embed.add_field(
        name="!kill_leaderboard",
        value="Check the top 10 most prolific attackers.",
        inline="False"
    )

    help_embed.add_field(
        name="!topkill_leaderboard",
        value="Checks the top 10 killers across all servers with economy in it",
        inline=False
    )

    await interaction.response.send_message(embed=help_embed, ephemeral=True)


@bot.command(name='commands', aliases=['help', 'economy'])
async def commands(ctx):
    """Display all available commands and their descriptions"""
    help_embed = discord.Embed(
        title="Bot Commands",
        description="Here are all the available commands:",
        color=discord.Color.blue()
    )

    

    help_embed.add_field(
        name="!guillotine ",
        value="Execute the richest and take their money to be divided among all members.",
        inline=False
    )

    help_embed.add_field(
        name="!rob_bank",
        value="Attempt to rob the bank. Has a 10% success rate and 24 hour cooldown. If successful, money is robbed from all people it can find.",
        inline=False
    )

    
    help_embed.add_field(
        name="!toggle_spellcheck",
        value="Toggle spellcheck functionality for yourself.",
        inline=False
    )

    help_embed.add_field(
        name="!seven_d6",
        value="Roll a 7d6 and see if you can nearly kill a Richter. Times someone out for 456 minutes if you roll a 35 or higher.",
        inline=False
    )

    help_embed.add_field(
        name="!cooldowns",
        value="Check the cooldowns of all commands.",
        inline=False
    )

    help_embed.add_field(
        name="!addtodictionary",
        value="Add a word to the dictionary.",
        inline=False
    )

    help_embed.add_field(
        name="!removetodictionary",
        value="Remove a word from the dictionary.",
        inline=False
    )

    help_embed.add_field(
        name="!englishwords",
        value="Get a list of english words that start with a certain letter.",
        inline=False
    )

    help_embed.add_field(
        name="!indictionary",
        value="Check if a word is in the dictionary.",
        inline=False
    )
    
    view = CommandsView()

    await ctx.send(embed=help_embed, view=view)

@bot.command()
async def kill_leaderboard(ctx):
    """Display a leaderboard of users with the most kills"""
    # Load kill counts from JSON file
    try:
        with open('kill_counts.json', 'r') as f:
            kill_counts = json.loads(f.read())
    except (FileNotFoundError, json.JSONDecodeError):
        await ctx.send("No kill counts found! - ping mater")
        return

    # Sort users by kill count
    sorted_kills = sorted(kill_counts.items(), key=lambda x: x[1], reverse=True)

    # Create embed
    embed = discord.Embed(
        title="🔪 Kill Count Leaderboard 💀",
        description="The most prolific killers in the server",
        color=discord.Color.red()
    )
    

    # Add top killers to embed
    for i, (user_id, kills) in enumerate(sorted_kills, 1):
        if i > 10:
            break

        try:
            member = await ctx.guild.fetch_member(int(user_id))
            name = member.display_name if member else "Unknown User"
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "☠️"
            embed.add_field(
                name=f"{medal} #{i}",
                value=f"{name}: {kills} kills",
                inline=False
            )
        except discord.NotFound:
            continue

    await ctx.send(embed=embed)

@bot.command()
async def topkill_leaderboard(ctx):
    """Display a leaderboard of users with the most kills"""
    # Load kill counts from JSON file
    try:
        with open('kill_counts.json', 'r') as f:
            kill_counts = json.loads(f.read())
    except (FileNotFoundError, json.JSONDecodeError):
        await ctx.send("No kill counts found! - ping mater")
        return

    # Sort users by kill count
    sorted_kills = sorted(kill_counts.items(), key=lambda x: x[1], reverse=True)

    print(sorted_kills)    

    # Create embed
    embed = discord.Embed(
        title="🔪 Kill Count Leaderboard 💀",
        description="The most prolific killers in the server",
        color=discord.Color.red()
    )

    if embed:
        print(embed)

    for i, (user_id, kills) in enumerate(sorted_kills, 1):
        try:
            user = await bot.fetch_user(user_id)
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "☠️"

            shared_servers = []
            for guild in bot.guilds:
                try:
                    member = await guild.fetch_member(user_id)
                    if member:
                        shared_servers.append(guild.name)
                except discord.NotFound:
                    continue
                except discord.Forbidden:
                    continue

            server_text = ", ".join(shared_servers) if shared_servers else "no shared servers"

            embed.add_field(
                name=f"{medal} #{i}",
                value=f"{user.name}: {kills} kills in {server_text}",
                inline=False
            )

        except discord.NotFound:
            continue



    await ctx.send(embed=embed)


@bot.command()
async def list_monitors(ctx):
    """List all available monitors and their positions"""
    try:
        # Use xrandr to get monitor information on Linux
        process = await asyncio.create_subprocess_exec(
            "xrandr", "--listmonitors",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            await ctx.send("Failed to get monitor information")
            return
            
        await ctx.send(f"Monitor information:\n```{stdout.decode()}```")
    except Exception as e:
        await ctx.send(f"Error getting monitor information: {e}")

@bot.command()
async def mousepos(ctx):
    """Get the current mouse position"""
    try:
        # Get mouse position using xdotool
        process = await asyncio.create_subprocess_exec(
            "xdotool", "getmouselocation",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            await ctx.send("Failed to get mouse position")
            return
            
        # Parse the output (format: x:123 y:456 screen:0 window:1234567)
        pos = stdout.decode().strip()
        await ctx.send(f"Mouse position: {pos}")
    except Exception as e:
        await ctx.send(f"Error getting mouse position: {e}")

nltk.download('words')

def load_cooldowns():
    try:
        file_path = os.path.abspath('cooldowns.json')
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        return {}
    except (FileNotFoundError, json.JSONDecodeError, PermissionError) as e:
        print(f"Error loading cooldowns: {e} - ping mater")
        return {}

def save_cooldowns(cooldowns):
    try:
        file_path = os.path.abspath('cooldowns.json')
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Use a temporary file to prevent corruption
        temp_path = file_path + '.tmp'
        with open(temp_path, 'w') as f:
            json.dump(cooldowns, f, indent=4)
        
        # Safely replace the old file with the new one
        if os.path.exists(file_path):
            os.replace(temp_path, file_path)
        else:
            os.rename(temp_path, file_path)
    except (PermissionError, OSError) as e:
        print(f"Error saving cooldowns: {e}")

# Dictionary of command cooldown times in seconds
command_cooldowns = {
    'kill': 86400,        # 24 hours
    'random_kill': 86400, # 24 hours
    'stab': 7200,        # 2 hour
    'guillotine': 604800, # 7 days
    'rob_bank': 604800,   # 7 days
    'seven_d6': 25560,   # 7 hours and 6 minutes
    '911': 14400,         # 4 hours
    'work': 86400,         # 24 hours
    'suicude': 14400,      # 4 hours
    'slut': 14400,         # 4 hours
    'crime': 14400,        # 4 hours
    'rob': 14400           # 4 hours
}

def check_cooldown(ctx, command_name, cooldown_time=86400, user_dependent=True):
    guild_id = str(ctx.guild.id)
    user_id = str(ctx.author.id)
    cooldowns = load_cooldowns()
    
    # Get the cooldown time from the dictionary, default to 24h if not found
    cooldown_time = command_cooldowns.get(command_name, 86400)
    
    # Initialize guild and user structure if needed
    if guild_id not in cooldowns:
        cooldowns[guild_id] = {}
    if user_dependent:
        if 'users' not in cooldowns[guild_id]:
            cooldowns[guild_id]['users'] = {}
        if user_id not in cooldowns[guild_id]['users']:
            cooldowns[guild_id]['users'][user_id] = {}
    
    # Check cooldown based on whether it's user-dependent or not
    if user_dependent:
        if command_name in cooldowns[guild_id]['users'][user_id]:
            last_used = cooldowns[guild_id]['users'][user_id][command_name]
            if time.time() - last_used < cooldown_time:
                remaining = cooldown_time - (time.time() - last_used)
                hours = int(remaining // 3600)
                minutes = int((remaining % 3600) // 60)
                return f"This command is on cooldown. Please wait {hours} hours and {minutes} minutes."
        
        # Update cooldown
        cooldowns[guild_id]['users'][user_id][command_name] = time.time()
    else:
        if command_name in cooldowns[guild_id]:
            last_used = cooldowns[guild_id][command_name]
            if time.time() - last_used < cooldown_time:
                remaining = cooldown_time - (time.time() - last_used)
                hours = int(remaining // 3600)
                minutes = int((remaining % 3600) // 60)
                return f"This command is on cooldown. Please wait {hours} hours and {minutes} minutes."
        
        # Update cooldown
        cooldowns[guild_id][command_name] = time.time()
    
    save_cooldowns(cooldowns)
    return None

@bot.command()
@has_permissions(administrator=True)
async def resetcooldowns(ctx, member: discord.Member = None, command: str = None):
    statecooldowns = load_cooldowns()
    guild_id = str(ctx.guild.id)

    if guild_id not in statecooldowns:
        await ctx.send("This guild has no cooldown data.")
        return

    # Reset cooldowns for the guild (no member specified)
    if member is None:
        if command:
            # Reset a specific *guild-wide* command
            if command in statecooldowns[guild_id]:
                statecooldowns[guild_id][command] = 0
                await ctx.send(f"Guild-wide cooldown for `{command}` reset.")
            else:
                await ctx.send(f"No cooldown data for command `{command}`.")
        else:
            # Reset all *guild-wide* cooldowns (not user-specific)
            for key in list(statecooldowns[guild_id].keys()):
                if key != "users":
                    statecooldowns[guild_id][key] = 0
            await ctx.send("All guild-wide cooldowns reset.")
        save_cooldowns(statecooldowns)
        return

    # Reset cooldowns for a specific user
    user_id = str(member.id)
    if "users" not in statecooldowns[guild_id] or user_id not in statecooldowns[guild_id]["users"]:
        await ctx.send("This user has no cooldown data.")
        return

    user_cooldowns = statecooldowns[guild_id]["users"][user_id]

    if command:
        if command in user_cooldowns:
            user_cooldowns[command] = 0
            await ctx.send(f"Cooldown for `{command}` reset for {member.display_name}.")
        else:
            await ctx.send(f"No cooldown for `{command}` found for {member.display_name}.")
    else:
        for cmd in user_cooldowns:
            user_cooldowns[cmd] = 0
        await ctx.send(f"All cooldowns reset for {member.display_name}.")

    save_cooldowns(statecooldowns)

@bot.command()
async def removecooldown(ctx, command: str, member: discord.Member):
    
    ishemater = False

    for role in ctx.author.roles:
        if role.name == "mater":
            ishemater = True
    
    if ishemater == False:
        await ctx.send("You're not matercan")
        return

    cooldowns = load_cooldowns()
    guild_id = str(ctx.guild.id)

    if guild_id not in cooldowns:
        await ctx.send("This guild has no cooldown data.")
        return

    # Reset cooldowns for the guild (no member specified)
    if member is None:
        if command:
            # Reset a specific *guild-wide* command
            if command in cooldowns[guild_id]:
                cooldowns[guild_id][command] = 0
                await ctx.send(f"Guild-wide cooldown for `{command}` reset.")
            else:
                await ctx.send(f"No cooldown data for command `{command}`.")
        else:
            ctx.send("Specify a command")
    
    # Reset cooldowns for a specific user
    user_id = str(member.id)
    if "users" not in cooldowns[guild_id] or user_id not in cooldowns[guild_id]["users"]:
        await ctx.send("This user has no cooldown data.")
        return

    user_cooldowns = cooldowns[guild_id]["users"][user_id]

    if command:
        if command in user_cooldowns:
            user_cooldowns[command] = 0
            await ctx.send(f"Cooldown for `{command}` reset for {member.display_name}.")
        else:
            await ctx.send(f"No cooldown for `{command}` found for {member.display_name}.")
    else:
        await ctx.send("Gimme a command")

    save_cooldowns(cooldowns)

@bot.command()
async def seven_d6(ctx, member: discord.Member = None):
    await ctx.send("7d6")

    cooldown_msg = check_cooldown(ctx, 'seven_d6')
    if cooldown_msg:
        await ctx.send(cooldown_msg)
        return

    rolls = []
    for i in range(7):
        roll = random.randint(1, 6)
        rolls.append(roll)

    total = sum(rolls)

    await ctx.send(f"You rolled a {rolls} for a total of {total}")

    if total >= 35:
        await ctx.send("4/5 of a Richter would've died here")
        await timeout(ctx, member, 456)

@bot.command()
async def a911(ctx):
    cooldown_msg = check_cooldown(ctx, "911", False)  # Cooldown time from dictionary
    if cooldown_msg:
        await ctx.send(cooldown_msg)
        return

    for member in ctx.guild.members:
        if not member.bot:
            print(member.name)
            await timeout(ctx, member, 10, ping=False)
    
    await timeout(ctx, ctx.author, 260, ping=False)

    await ctx.send("a second plane has hit the server (all users timed out for 10 minutes)")
    await ctx.send(f"Perpetrator {ctx.author.display_name} has been excecuted for 4 hours")

    killer_id = str(ctx.author.id)
    if killer_id not in kill_counts:
        kill_counts[killer_id] = 0
    kill_counts[killer_id] += len([member for member in ctx.guild.members if not member.bot])

@bot.command()
async def cooldowns(ctx):
    """Check remaining cooldown time for all commands"""
    cooldowns = load_cooldowns()
    guild_id = str(ctx.guild.id)
    user_id = str(ctx.author.id)
    
    if guild_id not in cooldowns:
        await ctx.send("No commands are currently on cooldown.")
        return
    
    message = "**Your Command Cooldowns:**\n"
    has_cooldowns = False
    
    # Check user-specific cooldowns
    if 'users' in cooldowns[guild_id] and user_id in cooldowns[guild_id]['users']:
        user_cooldowns = cooldowns[guild_id]['users'][user_id]
        for command_name, last_used in user_cooldowns.items():
            time_passed = time.time() - last_used
            cooldown_time = command_cooldowns.get(command_name, 86400)  # Default to 24h if not specified
            if time_passed < cooldown_time:
                remaining = cooldown_time - time_passed
                hours = int(remaining // 3600)
                minutes = int((remaining % 3600) // 60)
                message += f"`{command_name}`: {hours}h {minutes}m remaining\n"
                has_cooldowns = True
    
    # Check guild-wide cooldowns (like guillotine)
    for command_name, last_used in cooldowns[guild_id].items():
        if command_name != 'users':  # Skip the users dictionary
            time_passed = time.time() - last_used
            cooldown_time = command_cooldowns.get(command_name, 86400)  # Default to 24h if not specified
            if time_passed < cooldown_time:
                remaining = cooldown_time - time_passed
                hours = int(remaining // 3600)
                minutes = int((remaining % 3600) // 60)
                message += f"`{command_name}` (guild-wide): {hours}h {minutes}m remaining\n"
                has_cooldowns = True
    
    if not has_cooldowns:
        await ctx.send("No commands are currently on cooldown.")
        return
        
    await ctx.send(message)

def load_spellcheck_state():
    try:
        file_path = os.path.abspath('spellcheck_state.json')
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        return {}
    except (FileNotFoundError, json.JSONDecodeError, PermissionError) as e:
        print(f"Error loading spellcheck state: {e} - ping mater")
        return {}

def save_spellcheck_state(state):
    try:
        file_path = os.path.abspath('spellcheck_state.json')
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Use a temporary file to prevent corruption
        temp_path = file_path + '.tmp'
        with open(temp_path, 'w') as f:
            json.dump(state, f)
        
        # Safely replace the old file with the new one
        if os.path.exists(file_path):
            os.replace(temp_path, file_path)
        else:
            os.rename(temp_path, file_path)
    except (PermissionError, OSError) as e:
        print(f"Error saving spellcheck state: {e} - ping mater")

@bot.command()
async def toggle_spellcheck(ctx):
    """Toggle spellcheck functionality for yourself"""
    state = load_spellcheck_state()
    user_id = str(ctx.author.id)
    
    # Toggle the state
    current_state = state.get(user_id, True)  # Default to True if not set
    state[user_id] = not current_state
    
    # Save the new state
    save_spellcheck_state(state)
    
    status = "enabled" if state[user_id] else "disabled"
    await ctx.send(f"Spellcheck has been {status} for you.")

async def take_screenshot(region=None):
    """Take a screenshot using mss"""
    try:
        screenshot_path = os.path.abspath("screenshot.png")
        
        with mss() as sct:
            if region:
                # Take screenshot of a specific region
                screenshot = sct.grab(region)
            else:
                # Take full screenshot of primary monitor
                screenshot = sct.grab(sct.monitors[1])
            
            # Convert to PIL Image
            image = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
            image.save(screenshot_path)
            
        return screenshot_path
    except Exception as e:
        raise Exception(f"Screenshot error: {e}")

@bot.event
async def on_message(message):

    

    ctx = await bot.get_context(message)

    if not can_load_sources:
        await ctx.send("I'm not willing to let all data be wiped.")
        return

    if message.author == bot.user:
        return  # Ignore bot's own messages

    if message.guild is None:
        return  # Ignore DMs

    if "hello" in message.content.lower():
        await message.channel.send("Hello! 👋")
        await ctx.send("Type !commands to see all the commands")

    member = message.guild.get_member(message.author.id)  # Correct, no await needed  or just use message.author if intents are working

    if message.channel.name == "audit":
        return

    if member is None:
        print("Member is none")
        return
    
    # Check if spellcheck is enabled for this user
    state = load_spellcheck_state()
    user_id = str(message.author.id)
    if state.get(user_id, False):  # Default to True if not set
        # Check for non-English words and suggest corrections
        words = message.content.lower().split()
        corrections_needed = False
        corrected_words = []
        
        for word in words:
            
            # Strip punctuation for checking
            clean_word = ''.join(c for c in word if c.isalnum())
            if clean_word:
                # Try both singular and plural forms
                if clean_word not in english_words and clean_word + 's' not in english_words and clean_word + 'es' not in english_words:
                    corrections_needed = True
                    # Find closest English word
                    best_match = None
                    best_score = 0
                    for eng_word in english_words:
                        # Check similarity with word and its plural forms
                        score1 = fuzz.ratio(clean_word, eng_word)
                        score2 = fuzz.ratio(clean_word, eng_word + 's')
                        score3 = fuzz.ratio(clean_word, eng_word + 'es')
                        score = max(score1, score2, score3)
                        
                        if score > best_score and score > 60:  # 60% similarity threshold
                            best_score = score
                            best_match = eng_word
                            # Use plural form if it was the best match
                            if score2 > score1 and score2 > score3:
                                best_match = eng_word + 's'
                            elif score3 > score1 and score3 > score2:
                                best_match = eng_word + 'es'
                    
                    if best_match:
                        # Preserve original punctuation
                        for i, char in enumerate(word):
                            if not char.isalnum():
                                best_match = best_match[:i] + char + best_match[i:]
                        corrected_words.append(best_match)
                    else:
                        corrected_words.append(word)  # Keep original if no good match
                else:
                    corrected_words.append(word)
        
        if corrections_needed and corrected_words != words:
            corrected_sentence = ' '.join(corrected_words)
            await message.channel.send(f"Did you mean: {corrected_sentence}")
        if corrected_words == words and corrections_needed:
            print("I have no clue what you just said")

    print(member.name)

    if "house" in message.content.lower():
        houseometer = json.load(open('house.json'))
        with open('house.json', 'w') as f:
            if member.name not in houseometer:
                houseometer[member.name] = 0

        houseometer[member.name] += 1
        with open('house.json', 'w') as f:
            json.dump(houseometer, f)

        if houseometer[member.name] == 10:
            if random.randint(1, 2) < 1:
                await ctx.send("You win!")
                Bank.addcash(user_id, random.randrange(1000, 10000))
                houseometer[member.name] = 0
                with open('house.json', 'w') as f:
                    json.dump(houseometer, f)
            else:
                await ctx.send("You lose!")
                Bank.addbank(user_id, -random.randrange(1000, 10000))
                houseometer[member.name] = 0
                with open('house.json', 'w') as f:
                    json.dump(houseometer, f)

    content = message.content
    
    if user_id not in message_log:
        message_log[user_id] = []

    
    message_log[user_id] = message_log[user_id][-5:]

    save_message_log()

    timeoutcount = 0
    for lastmessages in message_log[user_id]:
        
        if lastmessages.startswith("!"):
            continue

        if content.lower() == lastmessages.lower():
            timeoutcount += 1
        
    if timeoutcount > 1:
            if not ctx.author.bot or user_id == "503720029456695306":
                await timeout(ctx, ctx.author, timeoutcount)
                await ctx.send("No spamming")

    if timeoutcount == 5:
        await timeout(ctx, user_id, 60)

    message_log[user_id].append(content)


    if message.content == "!use bomb":
        await usebomb(ctx, member)

    if message.content.startswith("!use brick"):
        target = message.mentions[0]
        print(target)
        await usebrick(ctx, member, target)

    if "mater" in message.content.lower():
        await ctx.send("It's pronounceed 'matter' btw")

    if message.channel.name == "gays-only":
        print(message.content)

    if user_id not in Bank.bank_accounts and not ctx.author.bot:
        Bank.addcash(user_id=user_id, money=100) # Give 100 initial cash
        # Or Bank.bank_accounts[user_id_str] = {"bank": 0, "cash": 100} followed by Bank.save_balances()
        await ctx.send(f"Welcome {ctx.author.mention}! Here's your starting cash!")

    if not ctx.author.bot:
        Bank.addcash(user_id=user_id, money=random.randrange(10, 100)) 

    
    try:
        await bot.process_commands(message)
    except KeyError:
        await ctx.send("Incorrect inputs")
    except ValueError:
        await ctx.send("Incorrect inputs try again")
    except:
        await ctx.send("Something unexpected happend - Most likely command not found")
        await commands(ctx)


@bot.command()
async def typeinallservers(ctx, message: str):
    
    for role in ctx.author.roles:
        if role.name == "mater":
            # get the Announcements channel
            for guild in bot.guilds:
                print(guild.name)
                if guild.name == "The Official Chesecat Server":
                    print("no n on on on o o no not this server")
                    #continue

                anncouncements = discord.utils.get(guild.text_channels, name="anncounements")
                if not anncouncements:
                    print(f'guild {guild} (id: {guild.id}) does not have a channel named announcements')

                    for channel in guild.text_channels:
                        print(channel.name)
                        if "general" or "𝔤𝔢𝔫𝔢𝔯𝔞𝔩" in channel.name.lower():
                            anncouncements = channel
                            print(anncouncements.name)
                            break
                    if not anncouncements:
                        print("fuck you")
                        return
                

                if anncouncements:
                    perms = anncouncements.permissions_for(guild.me)
                    if perms.send_messages:
                        try:
                            await anncouncements.send(message)
                        except discord.anncouncements:
                            print(f"Missing permission to send in {guild.name}#{anncouncements.name}")
                    else:
                        print(f"No permission to send messages in {guild.name}#{anncouncements.name}")
                        for channel in guild.text_channels:
                            if channel.name == "✨-𝔤𝔢𝔫𝔢𝔯𝔞𝔩-✨":
                                #await channel.send("Make an channel named 'Announcements' goddamnit or everytime my owner says something")
                                await channel.send("The bot owner has some words for ye:")
                                await channel.send(message)
            return

    await ctx.send("You don't have permission to use this command")
    return


last5messages = "last5messages.json"

if os.path.exists(last5messages):
    with open(last5messages, "r") as f:
        message_log = json.load(f)
else:
    message_log = {}


def save_message_log():
    with open(last5messages, "w") as f:
        json.dump(message_log, f, indent=4)

@bot.command()
async def indictionary(ctx, word: str):
    if word.lower() not in english_words:
        await ctx.send("That's not a word")
        return
    
    await ctx.send("That's a word")

@bot.command()
async def addtodictionary(ctx, word: str):
    english_words.append(word)
    await ctx.send("Added to dictionary")

@bot.command()
async def removetodictionary(ctx, word: str):
    english_words.remove(word)
    await ctx.send("Removed from dictionary")

@bot.command()
async def englishwords(ctx, starting_letter: str = None):
    message = ""
    if starting_letter:
        for word in english_words:
            if word.startswith(starting_letter):
                if len(message) + len(word) > 2000:
                    await ctx.send(message)
                    message = ''
                message += f'{word} '

    else:
        for word in english_words:
            await ctx.send(word)
    await ctx.send(f'{ctx.author.mention} done!')

@bot.command(name='balance', aliases=['bal', 'money'])
async def balance(ctx, member: discord.Member = None):

    if member == None:
        target_member = ctx.author
    else:
        target_member = member

    user_id = str(target_member.id)
    cash = Bank.read_balance(user_id)["cash"]
    bank = Bank.read_balance(user_id)["bank"]
    
    # Using an embed for better presentation
    embed = discord.Embed(
        title=f"{target_member.display_name}'s Balance",
        color=discord.Color.blue()
    )
    embed.add_field(name="💰 Cash", value=f"{cash:,.2f}", inline=False)
    embed.add_field(name="🏦 Bank", value=f"{bank:,.2f}", inline=False)
    
    # Calculate and display total worth using your gettotal method
    total_worth = Bank.gettotal(user_id)
    embed.add_field(name="✨ Total Worth", value=f"{total_worth:,.2f}", inline=False)
    
    embed.set_thumbnail(url=target_member.avatar.url if target_member.avatar else None)
    embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)

    await ctx.send(embed=embed)

@bot.command(name='deposit', aliases=['dep'])
async def deposit(ctx, money: str):
    user_id = str(ctx.author.id)

    if money == "all":
        money = Bank.read_balance(user_id=user_id)["cash"]
    try:
        money = float(money)
    except (ValueError) as e:
        await ctx.send("Invalid cash amount, either type all or a number")
        return
    
    if Bank.read_balance(user_id=user_id)["cash"] < money:
        await ctx.send("You don't have that much money in your bank")
        return

    Bank.movetobank(user_id=user_id, money=money)
    
    embed = discord.Embed(
        color=discord.Color.blue()
    )

    embed.set_footer(text=f"deposited {money:,.2f} cash to bank", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)

    await ctx.send(embed=embed)

@bot.command()
async def suicide(ctx):
    cooldown_msg = command_cooldowns.get('suicide')

    if cooldown_msg:
        await ctx.send("You can only aquire one suicide bomb per 4 hours")
        await ctx.send(cooldown_msg)
        return

    if random.randint(1, 10) == 1:
        for user in ctx.guild.members:
            await timeout(ctx, user, 10)
            await ctx.send("guild deleted")
    else:
        await timeout(ctx, ctx.author, 10)
        await ctx.send("bomber defeated")

    killer_id = str(ctx.author.id)
    if killer_id not in kill_counts:
        kill_counts[killer_id] = 0
    kill_counts[killer_id] += len([member for member in ctx.guild.members if not member.bot])

@bot.command(name='withdraw', aliases=['wit', 'with'])
async def withdraw(ctx, money: str):
    user_id = str(ctx.author.id)

    if money == "all":
        money = Bank.read_balance(user_id=user_id)["bank"]
    try:
        money = float(money)
    except (ValueError) as e:
        await ctx.send("Invalid cash mount, either type all or a number")
        return

    if Bank.read_balance(user_id=user_id)["bank"] < money:
        await ctx.send("You don't have that much money in the bank")
        return

    Bank.movetocash(user_id=user_id, money=money)
    
    embed = discord.Embed(
        color=discord.Color.blue()
    )

    embed.set_footer(text=f"withdrew {money:,.2f} from bank to cash", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)

    await ctx.send(embed=embed)

@bot.command()
async def give(ctx, member: discord.Member, money: float):
    user_id = str(ctx.author.id)
    target_id = str(member.id)

    user_cash = Bank.read_balance(user_id=user_id)["cash"]


    if money > user_cash:
        await ctx.send(f"❌ {ctx.author.mention}, you don't have enough cash to give {money:,.2f}. You only have {user_cash:,.2f} cash.")
        return # Return after sending the message

    if money <= 0:
        await ctx.send(f"❌ {ctx.author.mention}, you must give a positive amount of money.")
        return

    try:
        Bank.addcash(user_id=target_id, money=money)
        Bank.addcash(user_id=user_id, money=-money)
        await ctx.send(f"{member.display_name} has recieved your money")
        await balance(ctx, member=member)
        await balance(ctx, member=ctx.author)
        
    except (KeyError) as e:
        print(f"An error occurred in !give command: {e}") # Log the actual error for debugging
        await ctx.send(f"❌ An unexpected error occurred during the transaction. Tell me when this happens. (Error: {e})")

@bot.command(name='incomesources', aliases=['list-incomes', 'income-info'])
async def list_income_sources(ctx):
    """
    Displays information about all available income sources.
    Usage: !incomesources
    """
    Income.create_sources() # Ensure sources are loaded (or created if file is new)

    if not Income.income_sources:
        await ctx.send("❌ No income sources defined yet. Please configure them in economy.py.")
        return

    embed = discord.Embed(
        title="📊 Available Income Sources",
        description="Here's a list of all defined income sources and their details:",
        color=discord.Color.purple()
    )

    # Filter out placeholder sources (where name is 0)
    active_sources = [s for s in Income.income_sources if s and s[0] != 0]

    if not active_sources:
        embed.description = "No active income sources found. Add some using `Income.create_source()` in your script."

    for i, source_data in enumerate(active_sources):
        # Ensure source_data has enough elements to avoid IndexError
        if len(source_data) >= 5:
            name = source_data[0]
            is_interest = source_data[1]
            value = source_data[2]
            cooldown = source_data[3]
            goes_to_bank = source_data[4]

            value_display = ""
            if is_interest:
                value_display = f"**{value * 100:,.2f}%** interest on your {'bank' if goes_to_bank else 'cash'}."
            else:
                value_display = f"**{value}** {'to bank' if goes_to_bank else 'to cash'}."
            
            cooldown_display = f"{cooldown} seconds"

            embed.add_field(
                name=f"📈 {name}",
                value=(
                    f"Value: {value_display}\n"
                    f"Cooldown: {cooldown_display}"
                ),
                inline=False # Each income source gets its own line
            )
    
    await ctx.send(embed=embed)

@bot.command(name='incomes', aliases=['see-incomes', 'find-incomes'])
async def display_incomes(ctx):
    """
    Displays your currently assigned income sources and their cooldown status.
    Usage: !incomes
    """
    user_id_str = str(ctx.author.id)

    # Call the new method to get the user's income status list
    user_income_status_list = Income.get_user_income_status(user_id=user_id_str)

    embed = discord.Embed(
        title=f"💰 Your Income Sources for {ctx.author.display_name}",
        color=discord.Color.green()
    )

    if not user_income_status_list: # If the list is empty, user has no assigned incomes
        embed.add_field(name="No Incomes Found", value="You don't have any income sources assigned yet. You might need to buy items that grant income!")
        await ctx.send(embed=embed) # Send the embed and return
        return
    
    # Iterate through the list of income statuses and add fields to the embed
    for inc_status in user_income_status_list:
        name = inc_status["name"]
        status = inc_status["status"]
        
        field_value = ""
        if inc_status["details_valid"]: # Display full details if source data is valid
            is_interest = inc_status["is_interest"]
            value = inc_status["value"]
            cooldown = inc_status["cooldown"] # This is the base cooldown
            goes_to_bank = inc_status["goes_to_bank"]

            value_display = ""
            if is_interest:
                value_display = f"**{value * 100:,.2f}%** interest on your {'bank' if goes_to_bank else 'cash'}"
            else:
                value_display = f"**{value}** {'to bank' if goes_to_bank else 'to cash'}"
            
            # Show current status and detailed info
            field_value = (
                f"Status: `{status}`\n" # Displays if ready or cooldown remaining
                f"Value: {value_display}\n"
                f"Base Cooldown: {cooldown} seconds" # Base cooldown duration
            )
        else:
            # For invalid or malformed sources, just show the error status
            field_value = f"Status: `{status}`"

        embed.add_field(
            name=f"📈 {name}",
            value=field_value,
            inline=False # Each income source gets its own line
        )
    
    await ctx.send(embed=embed) # Send the completed embed


import discord
from discord.ext import commands
# Ensure your economy import is correct
from economy import Bank, Income, Items 

# ... (your bot setup and other commands) ...

@bot.command(name='collect', aliases=['getincome', 'claim'])
async def collect_income_command(ctx):
    """
    Collects available income from your sources and shows their updated status.
    Usage: !collect
    """
    user_id_str = str(ctx.author.id)
    
    # 1. Call Income.collectincomes() to perform the collection
    # This method updates timestamps for collected incomes and returns messages
    collection_results = Income.collectincomes(user_id_str)
    
    # 2. Create the main embed for the collection summary
    embed = discord.Embed(
        title=f"💰 Income Collection for {ctx.author.display_name}",
        color=discord.Color.green()
    )
    
    # Add the summary of what was collected (or not collected)
    if collection_results:
        embed.add_field(name="Collection Summary", value="\n".join(collection_results), inline=False)
    else:
        # This case handles when the user has no incomes or collectincomes returned nothing specific
        # (e.g., if there are no incomes to collect at all for the user)
        embed.add_field(name="No Income Collected", value="You don't have any active incomes or they are all on cooldown.", inline=False)

    # 3. Call Income.get_user_income_status() to get the updated status of all incomes
    # This reflects the cooldowns *after* the collection attempt
    user_income_status_list = Income.get_user_income_status(user_id=user_id_str)
    
    # 4. Prepare a concise summary of current income statuses
    if user_income_status_list:
        status_summary_lines = []
        for inc_status in user_income_status_list:
            name = inc_status["name"]
            status = inc_status["status"] # e.g., "Ready to collect!" or "On cooldown (Xs remaining)"
            cooldown_remaining = inc_status["cooldown_remaining"]
            
            if "Ready to collect!" in status:
                status_summary_lines.append(f"• `{name}`: Ready to collect!")
            elif cooldown_remaining > 0:
                # Format remaining time nicely
                status_summary_lines.append(f"• `{name}`: Cooldown: {cooldown_remaining:.0f}s")
            else:
                # Catch-all for invalid/malformed sources, showing their specific status message
                status_summary_lines.append(f"• `{name}`: {status}")

        if status_summary_lines: # Only add this field if there's actual status info
            embed.add_field(name="Current Income Statuses", value="\n".join(status_summary_lines), inline=False)
    else:
        # If the user has no incomes assigned (or get_user_income_status returns empty)
        embed.add_field(name="No Assigned Incomes", value="You don't have any income sources assigned to you.", inline=False)

    # 5. Add current balance to the footer for quick reference
    current_cash = Bank.read_balance(user_id_str)['cash']
    current_bank = Bank.read_balance(user_id_str)['bank']
    embed.set_footer(text=f"Current Cash: {current_cash:,.2f}, Bank: {current_bank:,.2f}")
    
    await ctx.send(embed=embed) # Send the final embed

Slut_respondes = [
    "kakashi came by and killed the mood. You lose ___",
    "kakashi came and u partied really hard and u gain ___ ",
    "you failed you unfortunately lose your husband/or wife you lose ___",
    "you gained the attention of some rich furries at a party. You wake up sore on the ground, with no memory of what happened but with ___ in your underpants"
]

@bot.command(name='slut')
async def slut(ctx):
    cooldown_msg = check_cooldown(ctx, 'slut')
    if cooldown_msg:
        await ctx.send(cooldown_msg)
        return
    
    user_id = str(ctx.author.id)
    amount_gained = random.randint(100, 1000)
    
    message = Slut_respondes[random.randint(0, len(Slut_respondes)-1)]

    if 'gain' in message:
        Bank.addcash(user_id=user_id, money=amount_gained)
        message = message.replace('___', str(amount_gained))
    else:
        amount_lost = -Bank.gettotal(user_id=user_id)*random.randint(20, 60)//100
        Bank.addcash(user_id=user_id, money=amount_lost)
        message = message.replace('___', str(amount_lost))
        

    await ctx.send(message)

@bot.command(name='crime')
async def crime(ctx):
    cooldown_msg = check_cooldown(ctx, 'crime')
    if cooldown_msg:
        await ctx.send("Unfortunately, all the places are robbed :)")
        await ctx.send(cooldown_msg)
        return
    
    user_id = str(ctx.author.id)
    user_total = Bank.gettotal(user_id=user_id)
    amount_gained = random.randint(1000, 10000)
    amount_lost = -user_total * random.randint(20, 40) // 100
    amount_lost = int(amount_lost)

    if random.randint(1, 10) > 6:
        Bank.addcash(user_id=user_id, money=amount_gained)
        await ctx.send(f"Crime successful, gain {amount_gained}")
    else:
        Bank.addcash(user_id=user_id, money=amount_lost)
        await ctx.send(f"You were caught, lose {amount_lost}")


@bot.command(name='work')
async def work(ctx):
    """
    Allows a user to work and earn money based on their current total worth.
    Usage: !work
    """
    
    cooldown_msg = check_cooldown(ctx, 'work')
    if cooldown_msg:
        await ctx.send(cooldown_msg)
        return


    user_id_str = str(ctx.author.id) # Ensure user ID is a string

    user_total = Bank.gettotal(user_id=user_id_str) # Get the user's total money

    if user_total == 0:
        # For new users or those with no money, give a fixed base amount
        earned_amount = random.randint(50, 150) # Example: Earn between 50 and 150 cash
        message = f"💰 You worked hard and earned {earned_amount} cash!"
    else:
        # Calculate min and max earnings based on a percentage of their total worth
        # Ensure percentages are reasonable and `mini` is not zero for calculation purposes
        min_percent = 0.05 # 5% of total worth
        max_percent = 0.15 # 15% of total worth

        mini_earnings = user_total * min_percent
        maxi_earnings = user_total * max_percent

        # Ensure a reasonable minimum, especially if user_total is very small
        if mini_earnings < 20: # Example: Ensure at least 20 cash if calculated percentage is too low
            mini_earnings = 20
        
        # Calculate a random amount between mini_earnings and maxi_earnings
        earned_amount = random.uniform(mini_earnings, maxi_earnings)
        earned_amount = int(earned_amount) # Convert to an integer for currency

        message = f"💰 You worked diligently and earned {earned_amount:,.2f} cash!"

    # Add the earned cash to the user's balance
    Bank.addcash(user_id=user_id_str, money=earned_amount) # Corrected parameter name to user_id

    # Create and send the embed
    embed = discord.Embed(
        title="💼 Work Report",
        description=message,
        color=discord.Color.blue() # Corrected to call the color method
    )
    
    # Optionally, show current balance in the footer
    current_cash = Bank.read_balance(user_id_str)["cash"]
    current_bank = Bank.read_balance(user_id_str)["bank"]
    embed.set_footer(text=f"Your current balance: Cash: {current_cash}, Bank: {current_bank}")

    await ctx.send(embed=embed)

@bot.command(name='leaderboard', aliases=['richest', 'leader'])
async def leaderboard(ctx):
    # Ensure bank accounts are loaded before accessing them directly
    # Bank.read_balance() does this implicitly, but it's good to be sure if you manipulate Bank.bank_accounts directly
    Bank.read_balance() 

    embed = discord.Embed(
        title="💰 The Richest Members", # Capitalized "Richest" for better title
        description="The most wealthy, formidable members of this economy!", # Slightly rephrased description
        color=discord.Color.green()
    )

    # --- FIX 1 & 2: Correct sorting key and unpacking ---
    # Sort by the sum of 'cash' and 'bank' values in the nested dictionary
    # x[0] is user_id, x[1] is the {'bank': X, 'cash': Y} dictionary
    sorted_members = sorted(
        Bank.bank_accounts.items(), 
        key=lambda x: x[1].get("cash", 0) + x[1].get("bank", 0), # Use .get() for safety
        reverse=True
    )

    for i, (user_id_str, account_data) in enumerate(sorted_members, 1):
        if i > 10: # Only show top 10
            break

        # Extract cash and bank from the unpacked account_data dictionary
        cash = account_data.get("cash", 0)
        bank = account_data.get("bank", 0)
        total_wealth = cash + bank

        try:
            # Convert user_id_str to int before fetching member
            member = await ctx.guild.fetch_member(int(user_id_str))
            name = member.display_name if member else f"Unknown User ({user_id_str})" # Show ID if user not found/left
            
            # Determine medal emoji
            if i == 1:
                medal = "🥇"
            elif i == 2:
                medal = "🥈"
            elif i == 3:
                medal = "🥉"
            else:
                medal = "💎" # Using a different emoji for ranks 4-10
            
            embed.add_field(
                name=f"{medal} #{i} {name}", # Combine medal, rank, and name in the name field
                value=f"Total: `{total_wealth:,.2f}` (Cash: `{cash:,.2f}`, Bank: `{bank:,.2f}`)",
                inline=False # Each member gets their own line
            )
        # --- FIX 3: Catch ValueError for int() conversion, and ensure discord.NotFound is caught ---
        except (discord.NotFound, ValueError) as e:
            # This handles cases where user_id might be invalid or the member has left the guild
            print(f"Could not fetch member for user_id {user_id_str}: {e}") # Log the error
            # Optionally add a field for skipped members or just continue
            continue 
    
    # --- FIX 4: Add await to ctx.send() ---
    await ctx.send(embed=embed)

@bot.command(name='rob', aliases=['steal', 'yoink'])
async def rob(ctx, target: discord.Member):
    cooldown_msg = check_cooldown(ctx, 'rob')
    if cooldown_msg:
        await ctx.send(cooldown_msg)
        return
    

    user_id_str = str(ctx.author.id)
    target_id_str = str(target.id)

    amount_gained = random.randint(80, 90) * Bank.read_balance(target_id_str)["cash"] // 100
    amount_lost = -random.randint(20, 40) * Bank.gettotal(user_id_str) // 100

    if random.randint(1, 10) > 4:
        await ctx.send(f"You robbed {target.display_name} for {amount_gained}")
        Bank.addcash(user_id_str, amount_gained)
        Bank.addcash[target_id_str, -amount_gained]
        await balance(ctx)
    else:
        await ctx.send(f"You were caught and pay {amount_lost} as fine")
        Bank.addcash(user_id_str, amount_lost)
        await balance(ctx)

@bot.command()
async def slap(ctx, member: discord.Member):
    try:
        amount_lost = random.randint(10, 30) / 100
        Bank.addcash(str(member.id), -amount_lost)
        await ctx.send(f"user {member.display_name} lost {amount_lost * 100:.0f} cents")
    except Exception as e:
        await ctx.send(f"Something went wrong here: {e} - ping mater or something")

@bot.command(name='rob-bank', aliases=['steal-bank'])
async def rob_bank(ctx):
    cooldown_msg = check_cooldown(ctx, 'rob_bank', user_dependent=False)
    if cooldown_msg:
        await ctx.send(cooldown_msg)
        return

    user_id_str = str(ctx.author.id)
    current_cash = Bank.gettotal(user_id_str)

    embed = discord.Embed(
        title="Bank robbery",
        description="Robs the bank",
        color=discord.Color.red()
    )

    embed.add_field(name="🏦 Bank total", value=f"{Bank.get_bank_total():,.2f}", inline=False)
    embed.add_field(name="✨ attempted robber", value=f"{ctx.author.display_name}", inline=False)

    embed.set_thumbnail(url=ctx.author.avatar.url)

  
    Bank.rob_bank(user_id_str, 20, 60, 40)
    new_money = Bank.gettotal(user_id_str)
    if new_money - current_cash > 0:
        embed.add_field(name="Robbery successful",
                         value=f"{ctx.author.display_name} robbed the bank for {new_money-current_cash:,.2f}",
                         inline=False)
        await ctx.send(embed=embed)
    else:
        Bank.addcash(user_id_str, random.randint(20, 40) * current_cash // -100)
        embed.add_field(name="Robbery unsuccessful",
                        value=f"{ctx.author.display_name} lost {new_money-current_cash:,.2f} after being caught by the police",
                        inline=False)
        await ctx.send(embed=embed)
    
@bot.command(name='richest-member', aliases=['toprich', 'whoisrichest'])
async def richest_member(ctx):
    """
    Displays the wealthiest member in the server.
    Usage: !richest_member
    """
    # Ensure bank accounts are loaded
    Bank.read_balance() 

    # Sort all members by their total wealth (cash + bank)
    # x[0] is user_id_str, x[1] is the {'bank': X, 'cash': Y} dictionary
    sorted_members = sorted(
        Bank.bank_accounts.items(),
        key=lambda x: x[1].get("cash", 0) + x[1].get("bank", 0),
        reverse=True
    )

    if not sorted_members:
        await ctx.send("There are no financial records to determine the richest member yet.")
        return

    # The first element in the sorted list is the richest member
    richest_user_id_str, richest_account_data = sorted_members[0]

    cash = richest_account_data.get("cash", 0)
    bank = richest_account_data.get("bank", 0)
    total_wealth = cash + bank

    try:
        # Fetch the Discord member object
        richest_member_obj = await ctx.guild.fetch_member(int(richest_user_id_str))
        name = richest_member_obj.display_name if richest_member_obj else f"Unknown User ({richest_user_id_str})"
        
        embed = discord.Embed(
            title="👑 The Richest Member",
            description=f"Our server's top earner is **{name}**!",
            color=discord.Color.gold()
        )
        embed.add_field(
            name="💎 Total Wealth",
            value=f"`{total_wealth:,.2f}`", # Formatted with comma and 2 decimal places
            inline=False
        )
        embed.add_field(
            name="💵 Cash",
            value=f"`{cash:,.2f}`",
            inline=True
        )
        embed.add_field(
            name="🏦 Bank",
            value=f"`{bank:,.2f}`",
            inline=True
        )
        
        # Set thumbnail to the richest member's avatar if available
        if richest_member_obj and richest_member_obj.avatar:
            embed.set_thumbnail(url=richest_member_obj.avatar.url)

        await ctx.send(embed=embed)

    except (discord.NotFound, ValueError):
        await ctx.send(f"Couldn't find the richest member's Discord profile (ID: `{richest_user_id_str}`). They might have left the server.")
    except Exception as e:
        print(f"An unexpected error occurred in !richest_member: {e}")
        await ctx.send("An error occurred while trying to find the richest member.")

@bot.command(name='guillotine', aliases=['guill', 'guollotine'])
async def guillotine(ctx):
    cooldown_msg = check_cooldown(ctx, 'guillotine', user_dependent=False)
    if cooldown_msg:
        await ctx.send("We can only kill so many capitalists per day")
        await ctx.send(cooldown_msg)
        return

    user_id_str = str(ctx.author.id)

    # Load initial balance for the command executor (saviour)
    saviour_balance_before = Bank.read_balance(user_id_str)
    saviour_total_wealth_before = saviour_balance_before.get("cash", 0) + saviour_balance_before.get("bank", 0)

    # Get sorted members to identify the richest
    # Ensure bank accounts are loaded for the sort
    Bank.read_balance() # This ensures Bank.bank_accounts is up-to-date
    sorted_members = sorted(
        Bank.bank_accounts.items(),
        key=lambda x: x[1].get("cash", 0) + x[1].get("bank", 0),
        reverse=True
    )

    if not sorted_members:
        await ctx.send("There are no accounts to guillotine!")
        return

    richest_user_id_str, richest_account_data = sorted_members[0]

    richest_cash = richest_account_data.get("cash", 0)
    richest_bank = richest_account_data.get("bank", 0)
    richest_total_wealth = richest_cash + richest_bank
    
    # Try to fetch the richest member's object for display and thumbnail
    richest_member_obj = None
    try:
        richest_member_obj = await ctx.guild.fetch_member(int(richest_user_id_str))
    except (discord.NotFound, ValueError):
        # Handle cases where member left or ID is invalid
        pass # Will use default display_name below

    richest_name = richest_member_obj.display_name if richest_member_obj else f"Unknown User ({richest_user_id_str})"

    embed = discord.Embed(
        title="🔪 Guillotine Executed! ✊",
        description="The wealth of the oppressors has been redistributed!",
        color=discord.Color.red() # Changed color to red for "guillotine"
    )

    embed.add_field(
        name=f"👑 The Fallen Capitalist: {richest_name}",
        value=f"They once hoarded a vile wealth of `{richest_total_wealth:,.2f}`",
        inline=False
    )
    
    embed.add_field(
        name=f"✨ The Revolutionary: {ctx.author.display_name}",
        value=f"With but a value of `{saviour_total_wealth_before:,.2f}`, you guillotined them!",
        inline=False
    )

    if richest_member_obj and richest_member_obj.avatar:
        embed.set_thumbnail(url=richest_member_obj.avatar.url)
    else:
        # Fallback thumbnail if richest member's avatar can't be fetched
        # You might want a default guillotine image here
        embed.set_thumbnail(url="https://i.imgur.com/your_default_thumbnail_url.png") # Replace with a suitable URL


    # --- Execute the guillotine operation ---
    Bank.guillotine() # This method should handle the redistribution logic

    # --- Calculate money gained by the executor (ctx.author) ---
    saviour_balance_after = Bank.read_balance(user_id_str)
    saviour_total_wealth_after = saviour_balance_after.get("cash", 0) + saviour_balance_after.get("bank", 0)
    money_gained_by_saviour = saviour_total_wealth_after - saviour_total_wealth_before

    embed.add_field(
        name=f"💰 Your personal gain from the revolution:",
        value=f"You gained `{money_gained_by_saviour:,.2f}`!",
        inline=False
    )
    
    # Optionally, you might want to show a summary of what everyone gained (if Bank.guillotine returns it)
    # Or state a generic message like "All loyal citizens gained a portion of the wealth!"

    await ctx.send(embed=embed)

@bot.command(name='store', aliases=['shop', 'items'])
async def list_items(ctx):
    """
    Displays information about all available items.
    Usage: !store
    """

    items = Items.load_item_sources()

    if not items:
        await ctx.send("Someone ping mater because her code isn't working")
        return
    
    embed = discord.Embed(
        title="💈Shop💈",
        description="All of our beautiful items ⛏️",
        color=discord.Color.purple()
    )

    for i, source_data in enumerate(items):
        if len(source_data) >= 5:
            name = source_data[0]
            is_collectable = source_data[1]
            value_or_effect = source_data[2]
            description = source_data[3]
            associated_income_source = source_data[4]
            role_added = source_data[5]
            role_removed = source_data[6]
            role_required = source_data[7]

            if is_collectable:
                value_display = f"A collectable {name} "
            else:
                value_display = f"A(n) {name} "
            
            try:
                price = float(value_or_effect)
                value_display += f"for the low low price of {price} "
            except ValueError:
                value_display += f"with {value_or_effect} "
            
            value_display += f"that is {description} "
            
            if associated_income_source:
                value_display += f"which gives you {associated_income_source} income "
            
            if role_added and not associated_income_source:
                value_display += f"which gives you {role_added} role "
            elif role_added:
                value_display += f"and {role_added} role "

            if role_removed:
                value_display += f"However, it removes role {role_removed} "
            
            if role_required and not role_removed:
                value_display += f"However, it can only be acquired with {role_required} role "
            elif role_required:
                value_display += f"and can only be acquired with role {role_required} "

            cash_emoji = ['💸', '🏦', '💰', '💶', '💵']

            embed.add_field(
                name=f"{name} " + cash_emoji[random.randint(0, len(cash_emoji)-1)],
                value=value_display,
                inline=False
            )

    await ctx.send(embed=embed)
            
@bot.command(name='buy', aliases=['purchase', 'get', 'buy-item'])
async def buy_item(ctx, item: str):
    """
    Let's a user buy an item
    Usage: !buy-item 
    """

    items = Items.load_item_sources()
    user_id_str = str(ctx.author.id)

    if not items:
        await ctx.send("Someone ping mater because her code isn't working")
        return
    
    
    index = Items.get_item_source_index_by_name(item)

    if index == -1:
        await ctx.send("Item doesn't exist")
        await ctx.send("Check items with the !store command")
        return

    item_data = Items.item_sources[index]
    cost = 0

    try:
        cost = float(item_data[2])
    except ValueError as e:
        await ctx.send("This item cannot be acquired from the store - I don't actually now why it's in there")
        return

    if Bank.read_balance(user_id_str)["cash"] < cost and Bank.gettotal(user_id_str) >= cost:
        await ctx.send("You cannot buy the item with your cash on hand - Withdraw from the bank first")
        return
    elif Bank.gettotal(user_id_str) <= cost:
        await ctx.send(f"you need {cost - Bank.gettotal(user_id_str)} more to purchase {item_data[0]}")
        return
    
    embed = discord.Embed(
        title=f"{ctx.author.display_name}",
        description=f"Bought {item_data[0]} for {item_data[2]}",
        color=discord.Color.blue()
    )

    Items.addtoitems(user_id_str, item_data[0])

    await ctx.send(embed=embed)

@bot.command(name='inventory')
async def display_inventory(ctx):
    """
    Displays the items within the user's inventory
    Usage: !inventory
    """

    user_id_str = str(ctx.author.id)
    inventory_data = Items.get_user_items(user_id_str)

    embed = discord.Embed(
        title=f"{ctx.author.display_name}'s items",
        description="The items you have acquired over your travels",
        color=discord.Color.brand_red()
    )

    for item, i in enumerate(inventory_data):
        item_data = Items.item_sources[Items.get_item_source_index_by_name(i)]
        embed.add_field(name=item_data[0], value=item_data[3], inline=False)

    await ctx.send(embed=embed)


bot.run('MTM2OTAwMzAxNDY3NzA2OTkxNQ.GIJa-G.0RBT_gSpQPXFOVAFAWGKgTZYva7tusECIOayZM')
