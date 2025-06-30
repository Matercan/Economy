import random
import discord
from discord.ext.commands import has_permissions
from datetime import timedelta
from discord.ext import commands, tasks
import json
import os
import nltk
from fuzzywuzzy import fuzz
import time
import asyncio
import sys
from economy import Bank, Income, Items, Offshore
from game_logic import BlackjackGame, CardflipGame, HackingGame 
from views_embeds import CommandsView, CooldownsView, HackingGameView
from nltk.corpus import words
import datetime
import math

import views_embeds

english_words = set(words.words())

english_words.add("fuck")
english_words.add("shit")
english_words.add("faggot")
english_words.add("boobies")
english_words.add("boobs")
english_words.add("bitch")
english_words.add('mrrrp')

english_words = sorted(english_words)

is_restarting_for_disconnect = False
RESTART_FLAG_FILE = "_restarting_flag.tmp"

can_load_sources = False

user_last_message_timestamps = {}


intents = discord.Intents.all()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='m!', intents=intents)
bot.remove_command('help')

# It's good practice to define these at the top or in a config.py
ONLINE_ROLE_ID = 1383129931541643295 # Role to ping when bot comes online
OFFLINE_ROLE_ID = 1383130035984142386 # Role to ping when bot goes offline
STATUS_CHANNEL_ID = 1368285968632778862 # Channel for online/offline pings
TARGET_GUILD_ID = 1331355137741950997

print(f"Current working directory: {os.getcwd()}") 
print(f"Absolute path of economy.py: {os.path.abspath(__file__)}")
print(f"Expected balance.json path: {os.path.join(os.path.dirname(__file__), 'balance.json')}")


@bot.command(name='commands', aliases=['help', 'economy'])
async def display_commands(ctx):
    """Display all available commands and their descriptions"""
    
    view = CommandsView()

    await ctx.send("commands", view=view, ephemeral=True)


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
    # Start your background tasks here
    if not ping_collect_income.is_running():
        ping_collect_income.start()
        print("DEBUG: ping_collect_income task started.")
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
    Offshore.load_balances() # Sets the balnaces variable to the one from the json file
    print("Economy data loaded/initialized for all classes.")

    # Syncs the bots I think
    await bot.tree.sync()

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
    if not ping_collect_income.is_running():
        ping_collect_income.start()
        print("DEBUG: ping_collect_income task started successfully (or was already running).")
    else:
        print("DEBUG: ping_collect_income task is already running. Skipping start.")       

    for guild in bot.guilds:
        print(f"- {guild.name} (id: {guild.id}) with {guild.member_count} members")

        for member in guild.members:
            if not member.bot:
                print(f"{member.name} ({member.display_name}, {member.id}) ")

async def check_guillotine_cooldown():
    global is_restarting_for_disconnect
    await bot.wait_until_ready()
    while not bot.is_closed():

        if is_restarting_for_disconnect:
            return

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
                        # cooldowns[guild_id]['guillotine'] = time.time()
                        # save_cooldowns(cooldowns)
        
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
                        # cooldowns[guild_id]['rob_bank'] = time.time()
                        # save_cooldowns(cooldowns)

        await asyncio.sleep(3600)


@tasks.loop(minutes=5) 
async def ping_collect_income():
    print(f"DEBUG: Running ping_collect_income task at {datetime.datetime.now()}")
    
    try:
        # Reload player incomes (which income sources users have)
        Income.playerincomes = Income.loadincomes()
    except FileNotFoundError:
        print("WARNING: playerincomes.json not found during task loop. Initializing empty.")
        Income.playerincomes = {} # Initialize empty if file doesn't exist
    except Exception as e:
        print(f"ERROR: Failed to load playerincomes in task loop: {e}")
        Income.playerincomes = {} # Fallback to empty to prevent further errors

    try:
        # Reload income source definitions (like Mining, Organized Crime details)
        # create_sources handles loading from incomesources.json or initializing
        Income.create_sources() 
    except FileNotFoundError:
        print("WARNING: incomesources.json not found during task loop. Initializing empty.")
        Income.income_sources = [] # Initialize empty if file doesn't exist
    except Exception as e:
        print(f"ERROR: Failed to load income sources in task loop: {e}")
        Income.income_sources = [] # Fallback to empty

    target_guild = bot.get_guild(TARGET_GUILD_ID)
    if not target_guild:
        print(f"ERROR: Guild with ID {TARGET_GUILD_ID} not found. Cannot send income reminders.")
        return

    reminder_channel = discord.utils.get(target_guild.text_channels, name="reminders")
    if not reminder_channel:
        print(f"ERROR: 'reminders' channel not found in guild '{target_guild.name}' ({TARGET_GUILD_ID}). Cannot send income reminders.")
        return

    collect_income_role = discord.utils.get(target_guild.roles, name="collect-income")
    if not collect_income_role:
        print(f"WARNING: Role 'collect-income' not found in guild '{target_guild.name}'. Skipping income reminders.")
        return
        
    for member in target_guild.members:
        if collect_income_role in member.roles:
            user_id_str = str(member.id)
            
            ready_income_data = Income.is_any_income_ready(user_id_str) # This returns a dictionary like {"name": "Knife", "status": "Ready to collect!", ...} or None
            
            if ready_income_data: # If ready_income_data is not None, it means an income is ready
                income_name_for_ping = ready_income_data.get("name", "your income")
                
                # Get the full source definition for this specific income by its name
                # Assuming Income.read_source(source_name=name) returns the list:
                # [name, is_interest, value, cooldown, goes_to_bank]

                source_definition = Income.read_source(rw=Income.get_source_index_by_name(income_name_for_ping))

                if source_definition and len(source_definition) > 2: # Ensure source_definition is valid and has a value at index 2
                    income_value = source_definition[2] # The income value is at index 2 in the source_definition list
                    
                    if income_value > 0 and member.status != discord.Status.offline: # Check if the income's value is positive
                        try:
                            await reminder_channel.send(
                                f"{member.mention}, Your income source '{income_name_for_ping}' can be collected! Use `!collect` to get it."
                            )
                            print(f"DEBUG: Sent income reminder to {member.display_name} for '{income_name_for_ping}' (Value: ${income_value}).")
                        except discord.HTTPException as e:
                            print(f"ERROR: Failed to send reminder to {member.display_name} in {reminder_channel.name}: {e}")
                    else:
                        print(f"DEBUG: Income '{income_name_for_ping}' for {member.display_name} is ready but has a non-positive value ({income_value}). Skipping ping.")
                else:
                    print(f"ERROR: Could not retrieve valid source definition for income '{income_name_for_ping}' for user {member.display_name}. Skipping ping.")
            else:
                print(f"DEBUG: {member.display_name} has the role but no income is ready yet.")
                

# This decorator ensures the task waits until the bot is fully ready before starting
@ping_collect_income.before_loop
async def before_ping_collect_income():
    await bot.wait_until_ready()
    print("DEBUG: ping_collect_income task is ready and waiting to start.")

@bot.event
async def on_command_error(ctx, error):
    """
    Handles errors that occur during command invocation.
    ctx: the conext of the command.
    error: the exception that was raised
    """

    if isinstance(error, commands.CommandNotFound):
        await ctx.send("That command doesn't exist - type m!help or m!commands for a list of available commands")
        return

    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"You're missing a rquired argument `{error.param.name}`")

    if isinstance(error, commands.BadArgument):
        await ctx.send(f"Invalid argument provided: `{error}`.")    

@bot.command()
async def hello(ctx):
    await ctx.send("Hello, world!")
                

@bot.command()
@commands.has_permissions(moderate_members=True)
async def timeout(ctx, member: discord.Member, minutes: int, ping: bool=True):
    try:
        
        if "Shield" in Items.get_user_items(str(member.id)):
            await ctx.send(f"user {member.display_name} couldn't be timed out - they have a shield")
            if random.randint(1, 3) == 1:
                await ctx.send(f"{member.mention} you're sheild has broken")
                Items.removefromitems(str(member.id), "Shield")
            return

        duration = timedelta(minutes=minutes)
        await member.timeout(duration, reason=f"Timed out by {ctx.author}")
        if ping: await ctx.send(f"{member.mention} has been timed out for {minutes} minute(s).")
    except discord.Forbidden:
        await ctx.send("I don't have permission to timeout this user.")
    except discord.HTTPException as e:
        await ctx.send(f"Failed to timeout user: {e} - Ping mater")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def addrole(ctx, member: discord.Member, role_name: str):
    """
    Gives a specified role to a member.
    Usage: !giverole @biotomatensaft knife
    """

    role = discord.utils.get(ctx.guild.roles, name=role_name)
    if role is None:
        await ctx.send(f"❌ Role '{role_name}' not found. Please ensure the role name is exact.")
        return

    # Check if the bot can modify the target member's roles (if the target member has a higher role than the bot)
    if ctx.guild.me.top_role <= member.top_role and ctx.author.id != ctx.guild.owner_id:
        await ctx.send(f"❌ I cannot assign roles to {member.display_name} because my highest role is not above their highest role.")
        return

    if role in member.roles:
        await ctx.send(f"✅ {member.display_name} already has the '{role.name}' role.")
        return

    try:
        await member.add_roles(role)
        await ctx.send(f"✅ Successfully gave '{role.name}' role to {member.display_name}.")
    except discord.Forbidden:
        await ctx.send("❌ I don't have the necessary permissions to manage roles. Make sure I have 'Manage Roles' permission and my role is higher than the role I'm trying to assign.")
    except discord.HTTPException as e:
        await ctx.send(f"An error occurred while trying to give the role: {e}")
    except Exception as e:
        await ctx.send(f"An unexpected error occurred: {e}")

@bot.command()
@commands.has_permissions(manage_roles=True) # Only users with 'Manage Roles' permission can use this
async def removerole(ctx, member: discord.Member, *, role_name: str):
    """
    Removes a specified role from a member.
    Usage: !removerole @MemberName Role Name Here
            !removerole 123456789012345678 "Another Role"
    """
    # Try to find the role by its name (case-insensitive for better usability)
    role = discord.utils.get(ctx.guild.roles, name=role_name)

    if role is None:
        await ctx.send(f"❌ Role '{role_name}' not found. Please ensure the role name is exact.")
        return

    # Check if the bot's role is higher than the role it's trying to remove
    # The bot cannot remove roles that are higher than or equal to its own top role
    if ctx.guild.me.top_role <= role:
        await ctx.send(f"❌ I cannot remove the role '{role.name}' because my highest role is not above it in the hierarchy.")
        return

    # Check if the target member actually has the role
    if role not in member.roles:
        await ctx.send(f"✅ {member.display_name} does not have the '{role.name}' role.")
        return

    try:
        await member.remove_roles(role)
        await ctx.send(f"✅ Successfully removed '{role.name}' role from {member.display_name}.")
    except discord.Forbidden:
        await ctx.send("❌ I don't have the necessary permissions to manage roles. Make sure I have 'Manage Roles' permission and my role is higher than the role I'm trying to remove.")
    except discord.HTTPException as e:
        await ctx.send(f"An error occurred while trying to remove the role: {e}")
    except Exception as e:
        await ctx.send(f"An unexpected error occurred: {e}")


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
    if ctx.author.display_name == "sulf":
        await ctx.send("sulf murdered the bot")
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
    if ctx.author.display_name == "sulf":
        is_restarting_for_disconnect = True # Set the flag to true for the *current* process's on_disconnect
        # --- IMPORTANT: Create the persistent flag file here ---
        # This file signals the *new* process's on_ready to skip the online ping.
        with open(RESTART_FLAG_FILE, 'w') as f:
            f.write('restarting')
        print(f"Created restart flag file: {RESTART_FLAG_FILE}")
        # --- End IMPORTANT ---
        await ctx.send("sulf is restarting the bot... Please wait a moment.")
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

    if member not in ctx.guild.members:
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
            await ctx.send("Unfortunately you don't have a bomb.")
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

@bot.command()
async def usebrick(ctx, member: discord.Member, target: discord.member):
    await ctx.send(f"{member.mention} used the brick!")

    
    await timeout(ctx, target, 5)
    await ctx.send(f"{target.mention} was hit by the brick!")



@bot.command()
async def stab(ctx, member: discord.Member):
    cooldown_msg = check_cooldown(ctx, 'stab')  # Cooldown time from dictionary
    if cooldown_msg:
        await ctx.send(cooldown_msg)
        return
    
    for role in ctx.author.roles:
        if role.name == "Knife":
            Items.addtoitems(str(ctx.author.id), "Knife")

    await ctx.send(f"{member.mention}, you've been stabbed!")
    
    if "Knife" not in Items.get_user_items(str(ctx.author.id)):
        await ctx.send("Unfortunately you don't have a knife.")
        return

    killer_id = str(ctx.author.id)
    if killer_id not in kill_counts:
        kill_counts[killer_id] = 0
    kill_counts[killer_id] += 1
    save_kill_counts()

    await timeout(ctx, member, 10)



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
            json.dump(cooldowns, f, indent=2)
        
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
    
    if not ishemater:
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

@bot.command(name='cooldowns', aliases=['cd', 'cooldown'])
async def cooldowns(ctx):
    """Check remaining cooldown time for all commands"""
    await ctx.send("Cooldowns for the server", view=CooldownsView(), ephemeral=True)


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

@bot.event
async def on_message(message):
    

    if "general" in message.channel.name and not message.content.startswith("m!"):
        return

    user_id = str(message.author.id)

    ctx = await bot.get_context(message)
    
    if isinstance(ctx.channel, discord.DMChannel):
        await ctx.send("THE BOT DOESN'T ACCEPT DMS!!!!!")
        return 

    if not can_load_sources and not message.author.bot:
        await ctx.send("I'm not willing to let all data be wiped.")
        return

    if message.author == bot.user:
        return  # Ignore bot's own messages

    if message.guild is None:
        return  # Ignore DMs

    if "hello" in message.content.lower():
        await message.channel.send("Hello! 👋")
        await ctx.send("Type m!commands to see all the commands")

    member = message.guild.get_member(message.author.id)  # Correct, no await needed  or just use message.author if intents are working

    if message.channel.name == "audit":
        return

    if member is None:
        print("Member is none")
        return
    
    has_knife = False
    has_tin = False
 
    # print(Income.playerincomes.get(user_id))
    
    for source_name, income_details in Income.playerincomes.get(user_id, {}).items():
        if income_details["index"] == Income.get_source_index_by_name("Organized crime") and Bank.read_balance(user_id)["cash"] > 10000 and not message.content.startswith("m!"):
            await ctx.send(f"The cops have found out about your dirty cash and that you have {source_name}; quickly deposit your cash now!")
            if random.randint(1, 10) < 4:
                # Calculate amount_lost as a percentage of cash, not as an absolute multiplier
                amount_lost_percentage = random.randrange(60, 100) # This will be 60-99
                user_cash = Bank.read_balance(user_id)["cash"]
                amount_lost = int(user_cash * amount_lost_percentage / 100) # Calculate as percentage
                
                if "A good lawyer" in Items.get_user_items(user_id) and random.randrange(1, 10) > 7:
                    amount_lost = 10000
                    await ctx.send(f"Though because of {message.author}'s lawyer")

                await ctx.send(f"They have also managed to take {amount_lost:,} cash from you!") # Added formatting and clarified what was taken
                Bank.addcash(user_id, -amount_lost)
            break


    for role in message.author.roles:
        if role.name == "Knife":
            has_knife = True
        if role.name == "tin":
            has_tin = True
    
    if has_tin and has_knife:
        await ctx.send("Oh, you think you can cheat by having tin and Knife at the same time \n smh my head")
        
        if message.guild:
            guild_ctx = bot.get_guild(message.guild.id) # This is a guild object, not a ctx
            if guild_ctx:
                # You'd need to create a dummy context or modify removerole to not require ctx
                # Or, as above, get ctx from message
                try:
                    # This line might still error if the generated 'ctx' is not fully fledged for permissions
                    await removerole(ctx, message.author, role_name="tin")
                except Exception as e: 
                    print(f"Error calling removerole from on_message: {e}")
                    await message.channel.send(f"An internal error occurred trying to remove the role: {e}")
            else:
                await message.channel.send("Could not determine guild context to remove role.")
        else:
            await message.channel.send("This action can only be performed in a guild channel.")
     
    if Bank.gettotal(user_id) >= 100000 and Income.readincomes(user_id, "Loan")["index"] != -1:
        await ctx.send("Congrats, you paid off your loan")
        Income.playerincomes[user_id]["Loan interest"]["since"] = 0
        Income.saveincomes()
        # await ctx.send(Income.playerincomes[user_id])

        # Income.collectincomes(user_id)
        Bank.addbank(user_id, -60000)
        # await ctx.send(Bank.read_balance(user_id))

        # Safely delete "Loan" income source
        # .pop() with a second argument (like None) will remove the key if it exists,
        # but will not raise an error if the key doesn't exist.
        Income.playerincomes[user_id].pop("Loan", None)
        
        # Safely delete "Loan interest" income source
        Income.playerincomes[user_id].pop("Loan interest", None)
        
        Income.saveincomes() # Save the updated incomes after deletion

    # if Bank.gettotal(user_id) <= 0 and not message.author.bot:
        # await take_loan(ctx)
 
    current_time = message.created_at # message.created_at is a datetime object

    if user_id not in user_last_message_timestamps:
        user_last_message_timestamps[user_id] = []

    # Add the new timestamp
    user_last_message_timestamps[user_id].append(current_time)

    # Keep only the last two timestamps
    if len(user_last_message_timestamps[user_id]) > 2:
        user_last_message_timestamps[user_id].pop(0) # Remove the oldest timestamp


    # Check if spellcheck is enabled for this user
    state = load_spellcheck_state()
    
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
            if random.randint(1, 2) <= 1:
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
        if ctx.author.bot or user_id != "503720029456695306":
            # await timeout(ctx, ctx.author, timeoutcount)
            # await ctx.send("No spamming")
            pass

    if timeoutcount == 5: 
        await timeout(ctx, user_id, 60)

    message_log[user_id].append(content)


    if "mater" in message.content.lower():
        await ctx.send("It's pronounceed 'matter' btw")

    if message.channel.name == "gays-only":
        print(message.content)

    if user_id not in Bank.bank_accounts and not ctx.author.bot:
        Bank.addcash(user_id=user_id, money=100) # Give 100 initial cash
        # Or Bank.bank_accounts[user_id_str] = {"bank": 0, "cash": 100} followed by Bank.save_balances()
        # await ctx.send(f"Welcome {ctx.author.mention}! Here's your starting cash!")

    if not ctx.author.bot and user_id in user_last_message_timestamps and len(user_last_message_timestamps[user_id]) >= 2:
        old_message_val = user_last_message_timestamps[user_id][0]
        new_message_val = user_last_message_timestamps[user_id][1]
        time_difference = new_message_val - old_message_val
        # print(time_difference)
        # print(f"DEBUG: Types in comparison: old_message_val={type(old_message_val)}, new_message_val={type(new_message_val)}")
        if time_difference >= datetime.timedelta(seconds=5):
            # print("Added cash")
            Bank.addcash(user_id=user_id, money=random.randrange(10, 100)) 

        # print(old_message_val)
        # print(new_message_val)

    # print(user_last_message_timestamps)
    
    for item_index, item_name in enumerate(Items.get_user_items(str(message.author.id))):
        if message.content.lower() == "!" + item_name.lower():
            await use_item(ctx, item_name)
    
    if message.content.startswith("m! "):
        message.content = "m!" + message.content[3:]

    await bot.process_commands(message)
    
@bot.command()
async def typeinallservers(ctx, message: str):
    ctx.message.delete()
    for role in ctx.author.roles:
        if role.name == "mater":
            # get the Announcements channel
            for guild in bot.guilds:
                print(guild.name)
                if guild.name == "The Official Chesecat Server":
                    print("no n on on on o o no not this server")
                    # continue

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
                                # await channel.send("Make an channel named 'Announcements' goddamnit or everytime my owner says something")
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
        json.dump(message_log, f, indent=2)

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

@bot.command(name='rank', aliases=[])
async def get_user_rank(ctx, member: discord.Member = None):
    """
    Shows the rank of a user (or yourself) based on their total money (cash + bank).
    Usage: !rank
           !rank @Username
    """
    target_member = member if member else ctx.author
    target_user_id = str(target_member.id) # User IDs are usually stored as strings in JSON keys

    # Ensure playerdata is loaded from the JSON file
    # Bank.playerdata will be populated by this call if it hasn't been already
     

    # Prepare a list to store (total_money, user_id) for sorting
    ranked_users = []
    for user_id, data in Bank.read_balance().items():
        try:
            # Safely get cash and bank amounts, defaulting to 0 if not present
            cash = data.get("cash", 0)
            bank = data.get("bank", 0)
            total_money = cash + bank
            ranked_users.append((total_money, user_id))
        except (TypeError, ValueError) as e:
            # Log any issues with specific user data without stopping the process
            print(f"WARNING: Skipping invalid balance data for user ID {user_id}: {data}. Error: {e}")
            continue

    # Sort the list by total_money in descending order (highest money first)
    ranked_users.sort(key=lambda x: x[0], reverse=True)

    # Find the rank of the target user
    rank = -1
    target_money = 0
    total_members_with_balance = len(ranked_users) # Total number of users who have a recorded balance

    for i, (money, user_id) in enumerate(ranked_users):
        if user_id == target_user_id:
            rank = i + 1 # Ranks are 1-based (first item is rank 1)
            target_money = money
            break
    
    if rank != -1:
        # Format the money with commas for readability
        await ctx.send(
            f"{target_member.display_name}'s rank: **#{rank}** "
            f"out of {total_members_with_balance} members with a balance. "
            f"Total money: {target_money:,.2f}"
        )
    else:
        await ctx.send(f"{target_member.display_name} does not have a recorded balance yet.")

# ... (rest of your bot.py code) ...

@bot.command(name='balance', aliases=['bal', 'money'])
async def balance(ctx, member: discord.Member = None):

    if member is None:
        target_member = ctx.author
    else:
        target_member = member

    user_id = str(target_member.id)
    cash = Bank.read_balance(user_id)["cash"]
    bank = Bank.read_balance(user_id)["bank"]
    
    ranked_members = []

    for user_id_str, data in Bank.read_balance().items():
        ranked_members.append((Bank.gettotal(user_id_str), user_id_str))

    ranked_members.sort(key=lambda x: x[0], reverse=True)
    rank = -1
    richens = len(ranked_members)

    for i, (money, user_id_str) in enumerate(ranked_members):
        if user_id_str == user_id:
            rank = i + 1
            break


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
    embed.add_field(name="Rank", value=f"#{rank} of {richens}", inline=False)

    embed.set_thumbnail(url=target_member.avatar.url if target_member.avatar else None)
    embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)


    await ctx.send(embed=embed)

@bot.command(name='economy-stats', aliases=['stats', 'economy-total', 'econ-stats', 'total'])
async def economy_stats_display(ctx):
    embed = discord.Embed(
        title="📊 Our economy's stats", 
        description="The total users, average wealth and combined wealth",
        color=discord.Color.green()
    )

    embed.add_field(
        name="Total tracked wealth (in the bank)",
        value=f"{Bank.get_bank_total():,.2f}",
        inline=False
    )

    embed.add_field(
        name="Across these many accounts",
        value=Bank.get_accounts_total(),
        inline=False
    )

    embed.add_field(
        name="GDP per capita",
        value=f"{Bank.get_bank_total() // Bank.get_accounts_total():,.2f}",
        inline=False
    )

    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1348325894577455125/1385894669602263100/image.png?ex=6857ba7d&is=685668fd&hm=9aa1469c22bedfdffd6ccb0fc9c5da63bfbec2bdf14fce6f6da46e21edec899d&")
    await ctx.send(embed=embed)

    await richest_member(ctx)


@bot.command(name='deposit', aliases=['dep'])
async def deposit(ctx, money: str="all"):
    user_id = str(ctx.author.id)

    if money == "all":
        money = Bank.read_balance(user_id=user_id)["cash"]
    try:
        money = float(money)
    except (ValueError):
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
async def withdraw(ctx, money: str="all"):
    user_id = str(ctx.author.id)

    if money == "all":
        money = Bank.read_balance(user_id=user_id)["bank"]
    try:
        money = float(money)
    except (ValueError):
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

@bot.command(name='incomesources', aliases=['list-incomes', 'income-info', 'ini'])
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
            
            cooldown_days = int(cooldown // 86400)
            cooldown_hours = int((cooldown % 86400) // 3600)
            cooldown_minutes = int((cooldown % 3600) // 60)
            cooldown_seconds = (cooldown % 60) 
            
            cooldown_display = f"{cooldown_days}d {cooldown_hours}h {cooldown_minutes}m, and {cooldown_seconds}s"

            embed.add_field(
                name=f"📈 {name}",
                value=(
                    f"Value: {value_display}\n"
                    f"Cooldown: {cooldown_display}"
                ),
                inline=False # Each income source gets its own line
            )
    
    await ctx.send(embed=embed)

@bot.command(name='offshore', aliases=['management', 'funds'])
async def offshore_bank_account_command(ctx):

    user_id = str(ctx.author.id)
    my_keys = Offshore.get_user_keys(user_id)
    print(f"KEYS: {my_keys}")
    my_items = Offshore.get_accounts_from_keys(my_keys)
    print(f"DATA: {my_items}")

    if my_items == []:
        await ctx.send("Peasant, you have no offshore funds to display")
        await balance(ctx)
        return

    view = views_embeds.OffshoreView(accounts=my_items)

    await ctx.send("Your funds sir/ma'am", view=view)
    view.message = ctx.message


@bot.command(name='owithdraw', aliases=['owith', 'owit'])
async def offshore_bank_account_withdraw(ctx, amount: float, key: str = "1"):
    user_keys = Offshore.get_user_keys(str(ctx.author.id))
    print(user_keys)
    Offshore.update_accounts_from_keyes(user_keys)
    print(user_keys)
    await ctx.message.delete()

    if key == "1":
        await ctx.send("Please specify a key")
        await offshore_bank_account_command(ctx)
        return
    if key not in user_keys:
        await ctx.send("Key not in your offshore keys \ntype oclear then your key  to generate a new account with the same amount of money")
        # return
    if amount >= Offshore.get_data_from_key(key)[2]:
        await ctx.send("You can't withdraw more money from you're offshore account than you have")
        return


    Offshore.withdraw(key, amount, str(ctx.author.id))
    await ctx.send(f"Withdrew {amount} money")
    await offshore_bank_account_command(ctx)


@bot.command(name='oclear')
async def duplicate_account_buskers(ctx, key: str):
    account_data = Offshore.get_data_from_key(key)
    
    Offshore.generate_account(ctx.author.id, account_data[2])
    
    del Offshore.balances[Offshore.get_index_from_key(key)]
    Offshore.save_balances()

@bot.command(name='odeposit', aliases=['odep'])
async def offshore_bank_account_deposit(ctx, amount="all", key: str = "1"):
    user_keys = Offshore.get_user_keys(str(ctx.author.id))
    Offshore.update_accounts_from_keyes(user_keys)
    
    await ctx.message.delete()

    if key == "1":
        await ctx.send("Please specify a key")
        await offshore_bank_account_command(ctx)
        return
    if key not in user_keys:
        await ctx.send("Key not in your offshore keys \nidk why you're giving them money??")
        # return
    if amount == "all":
        amount = Bank.read_balance(str(ctx.author.id))["bank"]
    else:
        try:
            amount = float(amount)
        except ValueError as e:
            await ctx.send(f"{e} - specify an actual amount s'il vous plait")
            return
    if amount > Bank.read_balance(str(ctx.author.id))["bank"]:
        await ctx.send("You can't deposit more money than you have in the bank")
        return
        

    Offshore.deposit(key, amount, str(ctx.author.id))
    await ctx.send(f"Deposited {amount} money")
    await offshore_bank_account_command(ctx)

@bot.command(name='oupdate', aliases=['oup'])
async def update_offshore_accounts(ctx):
    user_id = str(ctx.author.id)

    keys = Offshore.get_user_keys(user_id)
    Offshore.update_accounts_from_keyes(keys)

    await offshore_bank_account_command(ctx)

@bot.command(name='buy-offshore', aliases=['obuy', 'oacc'])
async def purchase_offshore_bank_account(ctx):
    """
    Let's a user purchase an offshore bank account for a million
    """

    user_id = str(ctx.author.id)

    if Bank.gettotal(user_id) <= 1e6:
        await ctx.send("You have not the money to purchase an offshore bank account")
        return

    Bank.addbank(user_id, -1e6)
    await ctx.send(views_embeds.OffshoreEmbed(Offshore.get_data_from_key(Offshore.generate_account(user_id, 1e6))))
     


@bot.command(name='incomes', aliases=['see-incomes', 'find-incomes', 'investments', 'in'])
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
            
            cooldown_days = int(cooldown // 86400)
            cooldown_hours = int((cooldown % 86400) // 3600)
            cooldown_minutes = int((cooldown % 3600) // 60)
            cooldown_seconds = (cooldown % 60) 


            # Show current status and detailed info
            field_value = (
                f"Status: `{status}`\n" # Displays if ready or cooldown remaining
                f"Value: {value_display}\n"
                f"Base Cooldown: {cooldown_days}d {cooldown_hours}h {cooldown_minutes}m {cooldown_seconds}s" # Base cooldown duration
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




@bot.command(name='collect', aliases=['getincome', 'claim', 'inc', 'clm'])
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
    "kakashi came by and killed the mood. You lose ____",
    "kakashi came and u partied really hard and u gain ____ ",
    "you failed you unfortunately lose your husband/or wife you lose ____",
    "you gained the attention of some rich furries at a party. You wake up sore on the ground, with no memory of what happened but with ____ in your underpants",
    "Your dazzling performance as the lead dancer at the 'Femboy Fantasy' cabaret captivated the crowd! You absolutely cleaned up, managing to gain ____ in tips and admirers.",
    "You charmed a particularly lonely group of forest creatures, and they bestowed upon you a trove of shiny trinkets, which you successfully pawned for a gain of ____. Who knew foxes were so generous?",
    "Your exceptional 'cuddle services' at the local furry convention were a massive hit! You successfully gained ____ and probably a few new lint rollers.",
    "You tried to seduce a stoic femboy barista for a free coffee, but he just gave you decaf and charged extra. You lost ____ and your faith in cheap thrills.",
    "While attempting to woo a wealthy fox, you tripped over a root and spilled your expensive elixir all over yourself. You lost ____, and now you smell faintly of wet dog.",
    "Your attempt to start a 'furry fashion advice' TikTok account flopped harder than a pancake. You lost ____ on props and frankly, your reputation."
]


@bot.command(name='slut')
async def slut(ctx):
    cooldown_msg = check_cooldown(ctx, 'slut')
    if cooldown_msg:
        await ctx.send(cooldown_msg)
        return
    
    user_id = str(ctx.author.id)
    amount_gained = random.randint(100, 1000)
    
    message = Slut_respondes[random.randint(0, len(Slut_respondes) - 1)]

    if 'gain' in message:
        Bank.addcash(user_id=user_id, money=amount_gained)
        message = message.replace('____', str(amount_gained))
    else:
        amount_lost = -Bank.gettotal(user_id=user_id) * random.randint(20, 60) // 100
        Bank.addcash(user_id=user_id, money=amount_lost)
        message = message.replace('____', str(amount_lost))

        if "A good lawyer" in Items.get_user_items(user_id):
            await ctx.send(message)
            await ctx.send("However, due to their good lawyer, the money was dealt with and troubles were sorted out behind the seens")
            
            if user_id not in crime_success_dict:
                crime_success_dict[user_id] = 0
            
            crime_success_dict[user_id] += 1
            
            if crime_success_dict[user_id] == 5:
                Income.addtoincomes(user_id, "Organised crime", 13)
    
            Bank.addbank(user_id, -10000)
            Bank.addbank(user_id, -amount_lost)
            return

        crime_success_dict[user_id] = 0
        

    await ctx.send(message)

crime_responses = [
    "You skillfully repossessed a femboy's prized collection of oversized hoodies and managed to gain ____ by selling them as 'vintage couture'!",
    "After a daring midnight raid on a local chicken coop (don't ask why), you made off with enough golden eggs to gain ____. Those foxes taught you well!",
    "Your elaborate scheme to 'borrow' all the squeaky toys from a furry daycare paid off! You expertly fenced them for a clean gain of ____. No one suspected the floofy mastermind.",
    "You attempted to pickpocket a femboy, but he was wearing leggings with no pockets. You tripped over your own feet in embarrassment and lost ____ in hospital bills for your bruised ego.",
    "Your master plan to 'liberate' snacks from a picnic went south when a territorial fox mistook you for a rival. You barely escaped with your dignity, but lost ____ in the ensuing chase.",
    "Trying to hack into the 'Furry Friend Finder' database, you accidentally signed yourself up for a lifetime supply of 'yarn for cats.' You didn't gain anything, but you lost ____ in the subscription fee!",
    "You skillfully exploited a zero-day vulnerability in a femboy streamer's custom Linux kernel, using Neovim to craft the perfect exploit. You stole all their rare in-game cosmetics and gained ____ by selling them on the dark web!",
    "Using a highly customized Arch Linux distro and your Neovim mastery, you infiltrated a 'Fox-themed NFT Farm' and minted enough new, unique 'pixelated furballs' to gain ____. Truly a digital art heist!",
    "You bypassed the security systems of a furry convention's main server by meticulously editing a configuration file with Neovim after gaining ssh access via a Linux live USB. You managed to siphon off enough 'con-cash' to gain ____!",
    "You tried to brute-force a femboy's secure SSH server, but your custom Neovim script had a typo. The server locked you out and simultaneously wiped your entire ~/.config/nvim folder. You lost ____ in therapy bills and the sheer horror of a default Neovim setup.",
    "Your attempt to 'sudo rm -rf /' the local animal shelter's antiquated Windows server (why?) was thwarted by a vigilant security fox who unplugged your Linux machine. You lost ____ in fines and had to reinstall your own OS.",
    "While attempting to exfiltrate data from a furry's laptop, you accidentally opened their very private Neovim config file. The cringe caused your system to crash, and you lost ____ when they charged you for 'emotional damages and Neovim support'.",
    "You skillfully convinced a group of squirrels that 'finders keepers' applied to all the local park's unattended wallets. You split the take 60/40 (in your favor, of course) and gained ____!",
    "Through sheer force of questionable charisma, you talked a highly secure bank vault into opening itself. The guards were too bewildered to react, and you walked out with a cool gain of ____.",
    "You pulled off the legendary 'Invisible Sandwich Heist,' stealing a chef's prize-winning, perfectly balanced lunch right off their plate without them ever noticing. The chef's confusion bought you enough time to fence the sandwich for a solid gain of ____."
]

crime_success_dict = {}


@bot.command(name='crime')
async def crime(ctx):
    global crime_success_dict
    print(crime_success_dict)

    

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

    if user_id not in crime_success_dict:
        crime_success_dict[user_id] = 0

    response_message = crime_responses[random.randint(0, len(crime_responses) - 1)]
    if 'gain' in response_message or 'Slippery gloves' in Items.get_user_items(user_id):
        if 'gain' in response_message:
            

            crime_success_dict[user_id] += 1

            response_message = response_message.replace('____', str(amount_gained))
            Bank.addcash(user_id=user_id, money=amount_gained)
        else:
            await ctx.send("Those slippery gloves prevented your capture, but you don't gain anything")
            if 'Slippery gloves' in Items.get_user_items(user_id):
                Items.removefromitems(user_id, 'Slipery gloves', 1)

        if crime_success_dict[user_id] == 3:
            
            await ctx.send("Due to the impressive amount of crimes you have succeeded in a row, criminals flock to you with you as their boss (check m!in)")
            Income.addtoincomes(user_id, "Organized crime ring leader", 13)

    else:
        response_message = response_message.replace('____', str(amount_lost))
        
        if "A good lawyer" in Items.get_user_items(user_id):
            await ctx.send("However, due to their good lawyer, the money was dealt with and troubles were sorted out behind the seens")
            
            if user_id not in crime_success_dict:
                crime_success_dict[user_id] = 0
            
            crime_success_dict[user_id] += 1
            
            if crime_success_dict[user_id] == 5:
                Income.addtoincomes(user_id, "Organised crime", 13)
    
            Bank.addbank(user_id, -10000)
            return

        Bank.addcash(user_id=user_id, money=amount_lost)
        crime_success_dict[user_id] = 0

    await ctx.send(response_message)

work_responses = [
    "You spent the day as a professional 'femboy hype man,' ensuring everyone was adequately glittered and confident. You earned a decent wage, plus a lifetime supply of self-esteem!",
    "Your shift involved herding unruly cartoon foxes through an obstacle course. You're exhausted, but your paycheck is foxy!",
    "You were employed as a 'chief tail floof manager' at a prestigious furry spa. It was surprisingly hard work, but your bank account is now as fluffy as your clients' tails!",
    "You spent the day as a 'Femboy's Neovim Configurator,' meticulously setting up plugins and themes to ensure maximum aesthetic appeal and productivity. You earned a surprisingly high wage and a newfound appreciation for Lua scripting.",
    "Your job was to teach a group of very fluffy, very enthusiastic foxes how to compile their own custom Linux kernels. You barely survived the 'segmentation fault' tantrums, but you earned enough to buy a new mechanical keyboard.",
    "You worked as a 'Bash Script Whisperer' for a tech startup run entirely by furries. Your task was to untangle their convoluted .bashrc files, all while exclusively using Neovim. Your hands ache, but your bank account is purring.",
    "You were hired to optimize the startup time of a Linux-powered robot that serves snacks at furry conventions. After hours in Neovim, tweaking systemd services, you got it down to under 2 seconds! You earned a hefty bonus and a lifetime supply of convention snacks.",
    "Your new gig: migrating a femboy's entire productivity workflow from VS Code to Neovim on their Arch Linux setup. It was a harrowing, caffeine-fueled journey, but you successfully completed the task and earned enough to pay off your technical debt."
]


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

        message = work_responses[random.randint(1, len(work_responses) - 1)] + f"You gain {earned_amount}"
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
        except (discord.NotFound, ValueError) as e:
            # This handles cases where user_id might be invalid or the member has left the guild
            print(f"Could not fetch member for user_id {user_id_str}: {e}") # Log the error

            member = await bot.fetch_user(int(user_id_str))
            name = member.name

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
                name=f"{medal} #{i} {name}",
                value=f"Total: `{total_wealth:,.2f}` (Cash: `{cash:,.2f}`, Bank: `{bank:,.2f}`)",
                inline=False
            )
            continue 
    
    await ctx.send(embed=embed)

@bot.command(name='rob', aliases=['steal', 'yoink'])
async def rob(ctx, target: discord.Member):
    global crime_success_dict
    print(crime_success_dict)

    cooldown_msg = check_cooldown(ctx, 'rob')
    if cooldown_msg:
        await ctx.send(cooldown_msg)
        return
    

    user_id_str = str(ctx.author.id)
    target_id_str = str(target.id)

    if user_id_str not in crime_success_dict:
        crime_success_dict[user_id_str] = 0

    amount_gained = random.randint(80, 90) * Bank.read_balance(target_id_str)["cash"] // 100
    amount_lost = -random.randint(20, 40) * Bank.gettotal(user_id_str) // 100

    if random.randint(1, 10) > 4 or 'Slippery gloves' in Items.get_user_items(user_id_str):

        crime_success_dict[user_id_str] += 1
            

        await ctx.send(f"You robbed {target.display_name} for {amount_gained}")
        Bank.addcash(user_id_str, amount_gained)
        Bank.addcash(target_id_str, -amount_gained)
        await balance(ctx)

        if crime_success_dict == 3:
            await ctx.send("Due to the impressive amount of crimes you have succeeded in a row, criminals flock to you with you as their boss (check m!in)")
        if 'Slippery gloves' in Items.get_user_items(user_id_str):
            Items.removefromitems(user_id_str, 'Slipery gloves', 1)


    else:
        

        await ctx.send(f"You were caught and pay {amount_lost} as fine")
        
        if "A good lawyer" in Items.get_user_items(user_id_str):
            await ctx.send("However, due to their good lawyer, the money was dealt with and troubles were sorted out behind the seens")
            
            if user_id_str not in crime_success_dict:
                crime_success_dict[user_id_str] = 0
            
            crime_success_dict[user_id_str] += 1
            
            if crime_success_dict[user_id_str] == 5:
                Income.addtoincomes(user_id_str, "Organised crime", 13)
    
            Bank.addbank(user_id_str, -10000)
            return

        Bank.addcash(user_id_str, amount_lost)
        crime_success_dict[user_id_str] = 0
        await balance(ctx)

@bot.command(name='followerboard', aliases=['poorest', 'follower'])
async def followerboard(ctx):
    # Ensure bank accounts are loaded before accessing them directly
    # Bank.read_balance() does this implicitly, but it's good to be sure if you manipulate Bank.bank_accounts directly
    Bank.read_balance() 

    embed = discord.Embed(
        title="💰 The Poverty-stricken Members", # Capitalized "Richest" for better title
        description="The most poorest, dumbest members of this economy!", # Slightly rephrased description
        color=discord.Color.green()
    )

    # --- FIX 1 & 2: Correct sorting key and unpacking ---
    # Sort by the sum of 'cash' and 'bank' values in the nested dictionary
    # x[0] is user_id, x[1] is the {'bank': X, 'cash': Y} dictionary
    sorted_members = sorted(
        Bank.bank_accounts.items(), 
        key=lambda x: x[1].get("cash", 0) + x[1].get("bank", 0), # Use .get() for safety
        reverse=False
    )

    for i, (user_id_str, account_data) in enumerate(sorted_members, 1):
        if i > 10: # Only show top 10
            break

        # Extract cash and bank from the unpacked account_data dictionary
        cash = account_data.get("cash", 0)
        bank = account_data.get("bank", 0)
        total_wealth = cash + bank

        try:
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
                name=f"{medal} #{Bank.get_accounts_total() - i} {name}", # Combine medal, rank, and name in the name field
                value=f"Total: `{total_wealth:,.2f}` (Cash: `{cash:,.2f}`, Bank: `{bank:,.2f}`)",
                inline=False # Each member gets their own line
            )
        except (discord.NotFound, ValueError) as e:
            # This handles cases where user_id might be invalid or the member has left the guild
            print(f"Could not fetch member for user_id {user_id_str}: {e}") # Log the error

            member = await bot.fetch_user(int(user_id_str))
            name = member.name

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
                name=f"{medal} #{Bank.get_accounts_total() - i} {name}",
                value=f"Total: `{total_wealth:,.2f}` (Cash: `{cash:,.2f}`, Bank: `{bank:,.2f}`)",
                inline=False
            )
            continue 
    
    await ctx.send(embed=embed)

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

    if user_id_str not in crime_success_dict:
        crime_success_dict[user_id_str] = 0

    embed.add_field(name="🏦 Bank total", value=f"{Bank.get_bank_total():,.2f}", inline=False)
    embed.add_field(name="✨ attempted robber", value=f"{ctx.author.display_name}", inline=False)

    embed.set_thumbnail(url=ctx.author.avatar.url)

    if user_id_str not in crime_success_dict:
        crime_success_dict[user_id_str] = 0

    Bank.rob_bank(user_id_str, 20, 60, 40)
    new_money = Bank.gettotal(user_id_str)
    if new_money - current_cash > 0:
        embed.add_field(name="Robbery successful",
                         value=f"{ctx.author.display_name} robbed the bank for {new_money - current_cash:,.2f}",
                         inline=False)
        await ctx.send(embed=embed)

        crime_success_dict[user_id_str] = 5
        await ctx.send("Do to your impressive crime of robbing the global monetary system, criminals flock to you (m!in)")
        Income.addtoincomes(user_id_str, "Organized crime", 13)

    else:
        if "A good lawyer" in Items.get_user_items(user_id_str):
            embed.add_field(
                name="They were defended by their lawyer",
                value=f"{ctx.author.display_name} lost 100000 in fines",
                inline=False
            )

            Bank.addbank(user_id_str, -10000)
            crime_success_dict[user_id_str] += 1

            if crime_success_dict[user_id_str] == 5:
                await ctx.send("A good of criminals flock to you")
                Income.addtoincomes(user_id_str, "Organized crime ring leader", 13)

            

        Bank.addcash(user_id_str, random.randint(20, 40) * current_cash // -100) if "A good lawyer" not in Items.get_user_items(user_id_str) else Bank.addcash(user_id_str, 1)
        embed.add_field(name="Robbery unsuccessful",
                        value=f"{ctx.author.display_name} lost {new_money - current_cash:,.2f} after being caught by the police",
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
   

    richest_user_id_str, richest_account_data = (Bank.get_richest_user_id(), Bank.read_balance(Bank.get_richest_user_id()))

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
        name="💰 Your personal gain from the revolution:",
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
    
    print("store")

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

            print(f"Item: {name}")

            if is_collectable:
                value_display = "A hiddden item "
                continue
            else:
                value_display = f"A(n) {name} "
            
            try:
                price = float(value_or_effect)
                value_display += f"for the low low price of {price:,.0f} "
            except ValueError:
                value_display += f"with {value_or_effect} "
            
            value_display += f"that {description} "
            
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
                name=f"{name} " + cash_emoji[random.randint(0, len(cash_emoji) - 1)],
                value=value_display,
                inline=False
            )

    embed.set_thumbnail(url="https://www.ulisses-ebooks.de/images/8135/_product_images/397725/DeanSpencer-filler-armourmerchant.jpg")

    await ctx.send(embed=embed)
            
@bot.command(name='buy', aliases=['purchase', 'get', 'buy-item'])
async def buy_item(ctx, *, item: str):
    """
    Let's a user buy an item
    Usage: !buy-item 
    """

    item = item[0].capitalize() + item[1:]
    print(item)
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
    except ValueError:
        await ctx.send("This item cannot be acquired from the store - I don't actually know why it's in there")
        return

    if Bank.read_balance(user_id_str)["cash"] < cost and Bank.gettotal(user_id_str) >= cost:
        await ctx.send("You cannot buy the item with your cash on hand - Withdraw from the bank first")
        return
    elif Bank.gettotal(user_id_str) <= cost:
        await ctx.send(f"you need {cost - Bank.gettotal(user_id_str)} more to purchase {item_data[0]}")
        return
    if item_data[7]:
        has_role = False
        for role in ctx.author.roles:
            if role.name.lower() == item_data[7].lower():
                has_role = True
        if not has_role:
            await ctx.send(f"This item requires role {item_data[7]}")
            return

    embed = discord.Embed(
        title=f"{ctx.author.display_name}",
        description=f"Bought {item_data[0]} for {item_data[2]}",
        color=discord.Color.blue()
    )

    Items.buyitem(user_id_str, index) 
 
    if item_data[5]:
        # Pass role_name as a keyword argument
        await addrole(ctx, ctx.author, role_name=item_data[5]) 
    
    if item_data[6]:
        # Pass role_name as a keyword argument
        await removerole(ctx, ctx.author, role_name=item_data[6]) 

    await ctx.send(embed=embed)

@bot.command(name='inventory', aliases=['inv', 'my-items'])
async def display_inventory(ctx):
    """
    Displays the items within the user's inventory
    Usage: !inventory
    """

    user_id_str = str(ctx.author.id)
    inventory_data = Items.get_user_items(user_id_str)

    embed = discord.Embed(
        title=f"{ctx.author.display_name}'s items ⛏️",
        description="The items you have acquired over your travels",
        color=discord.Color.brand_red()
    )

    item_emoji = ["🗡️", "⚔️", "🛡️", "💸"]

    for item, i in enumerate(inventory_data):
        print(item)
        print(i)
        item_data = Items.item_sources[Items.get_item_source_index_by_name(i)]
        print(item_data)
        if not item_data[1]: 
            embed.add_field(
                name=item_data[0],
                value=item_data[3] + " " + item_emoji[random.randint(0, len(item_emoji) - 1)],
                inline=False)
        else:
            print("DEBUG: not user key")
            print(item_data[2])
            print(item_data[3])
            embed.add_field(
                name=item_data[3],
                value=str(item_data[2]) + " " + item_emoji[random.randint(0, len(item_emoji) - 1)],
                inline=False)
        print("Added field")
    
    print(embed.to_dict())

    embed.set_thumbnail(url='https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTYjkNcpGalEIy9SRBVj8IO8YjAxOgtnR8uAg&s')

    await ctx.send(embed=embed)

@bot.command(name='use')
async def use_item(ctx, item: str, target: discord.Member = None):
    """
    Lets users use their items
    Usage: !use bomb
    """

    user_id_str = str(ctx.author.id)
    inventory_data = Items.get_user_items(user_id_str)

    item_index_int = inventory_data.get(item[0].capitalize() + item[1:], -1)

    print(item_index_int)

    if item_index_int == -1:
        await ctx.send("Item not found") 
        return
    
    if item_index_int == Items.get_item_source_index_by_name("Bomb"):
        await ctx.send("Used Bomb")
        await usebomb(ctx, ctx.author)
        Items.removefromitems(user_id_str, item[0].capitalize() + item[1:], -1)

    if item_index_int == Items.get_item_source_index_by_name("Brick"):
        await usebrick(ctx, ctx.author, target=target)
        Items.removefromitems(user_id_str, item[0].capitalize() + item[1:], -1)

@bot.command(name='lastmessagediff', aliases=['lmd', 'msgtime'])
async def last_message_difference(ctx, member: discord.Member = None):
    """
    Shows the time difference between the last two messages of a user.
    Usage: !lastmessagediff
           !lastmessagediff @MemberName
    """
    target_member = member if member else ctx.author
    target_user_id = target_member.id

    if target_user_id not in user_last_message_timestamps or \
       len(user_last_message_timestamps[target_user_id]) < 2:
        await ctx.send(f"{target_member.display_name} needs to send at least 2 messages for me to calculate the difference.")
        return

    # Get the last two timestamps
    oldest_msg_time = user_last_message_timestamps[target_user_id][0]
    latest_msg_time = user_last_message_timestamps[target_user_id][1]

    # --- DEBUG PRINT: Verify types retrieved from the list ---
    print(f"DEBUG - !lastmessagediff: Oldest message time: {oldest_msg_time} (Type: {type(oldest_msg_time)})")
    print(f"DEBUG - !lastmessagediff: Latest message time: {latest_msg_time} (Type: {type(latest_msg_time)})")
    # --- END DEBUG PRINT ---

    # --- CRITICAL: Ensure both are datetime.datetime objects ---
    if not isinstance(oldest_msg_time, datetime.datetime) or \
       not isinstance(latest_msg_time, datetime.datetime):
        await ctx.send(f"An internal error occurred: Stored message timestamps for {target_member.display_name} are corrupted or not in the expected format (datetime objects). Please try again later or contact the bot developer.")
        print(f"ERROR: Expected datetime.datetime objects, but found {type(oldest_msg_time)} and {type(latest_msg_time)} for user {target_user_id}. Resetting timestamps for this user.")
        # Optionally, clear the problematic data for this user to allow it to be re-populated correctly
        if target_user_id in user_last_message_timestamps:
            del user_last_message_timestamps[target_user_id]
        return
    # --- END CRITICAL ---

    time_difference = latest_msg_time - oldest_msg_time

    # Format the timedelta object into a human-readable string
    total_seconds = int(time_difference.total_seconds())
    
    days = total_seconds // (24 * 3600)
    total_seconds %= (24 * 3600)
    hours = total_seconds // 3600
    total_seconds %= 3600
    minutes = total_seconds // 60
    seconds = total_seconds % 60

    time_str_parts = []
    if days > 0:
        time_str_parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours > 0:
        time_str_parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0:
        time_str_parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if seconds > 0 or not time_str_parts: # Always show seconds if there's any time, or if everything else is zero
        time_str_parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")

    time_difference_str = ", ".join(time_str_parts)

    await ctx.send(f"The time difference between {target_member.display_name}'s last two messages was: **{time_difference_str}**.")

@bot.command(name='statuscheck', aliases=['checkstatus'])
async def check_user_status(ctx, member: discord.Member=None):
    """
    Checks the online/offline status of a specified member.
    Usage: !statuscheck @Username
    """
    if member is None:
        await ctx.send("Please mention a member to check their status.")
        return

    # member.status will be a discord.Status enum
    status = member.status

    if status == discord.Status.online:
        await ctx.send(f"{member.display_name} is currently **online**.")
    elif status == discord.Status.offline or status == discord.Status.invisible:
        await ctx.send(f"{member.display_name} is currently **offline**.")
    elif status == discord.Status.idle:
        await ctx.send(f"{member.display_name} is currently **idle**.")
    elif status == discord.Status.dnd:
        await ctx.send(f"{member.display_name} is currently on **Do Not Disturb**.")
    else:
        await ctx.send(f"{member.display_name} has an **unknown** status ({status}).")
    
@bot.command(name='loan', aliases=['lend', 'cash'])
async def take_loan(ctx):
    
   
    user_id_str = str(ctx.author.id)

    if "Loan" in Income.playerincomes[user_id_str]:
        await ctx.send("You already have a loan")
        return



    Bank.addbank(user_id_str, 50000)
    
    Income.playerincomes[user_id_str]["Loan"]["since"] = 0

    Income.saveincomes()

    # await ctx.send(Income.collectincomes(user_id_str))
    
 
    await ctx.send("Taken out loan of Value 50,000")

def create_blackjack_embed(game: BlackjackGame, player_id: int, bet_amount: int, show_dealer_full_hand: bool = False):
    print("DEBUG: Inside create_blackjack_embed.") # DEBUG PRINT CB1
    embed = discord.Embed(
        title="🃏 Blackjack Game",
        color=discord.Color.dark_green()
    )

    player_hand_str = ", ".join(str(card) for card in game.player_hand)
    player_score = game.calculate_hand_value(game.player_hand)
    print(f"DEBUG: Embed Player Hand String: '{player_hand_str}', Score: {player_score}") # DEBUG PRINT CB2

    embed.add_field(
        name=f"Your Hand ({player_score})",
        value=player_hand_str,
        inline=False
    )

    if show_dealer_full_hand:
        dealer_hand_str = ", ".join(str(card) for card in game.dealer_hand)
        dealer_score = game.calculate_hand_value(game.dealer_hand)
        print(f"DEBUG: Embed Dealer Full Hand String: '{dealer_hand_str}', Score: {dealer_score}") # DEBUG PRINT CB3
        embed.add_field(
            name=f"Dealer's Hand ({dealer_score})",
            value=dealer_hand_str,
            inline=False
        )
    else:
        # Show only dealer's first card initially
        dealer_hand_str = f"{game.dealer_hand[0]} and one hidden card" # This line was missing its assignment
        print(f"DEBUG: Embed Dealer Partial Hand String: '{dealer_hand_str}'") # DEBUG PRINT CB4
        embed.add_field(
            name="Dealer's Hand",
            value=dealer_hand_str,
            inline=False
        )
    
    embed.add_field(name="Bet", value=f"${bet_amount:,}", inline=False)

    if game.is_game_over:
        embed.description = f"**Game Over!** {game.result_message}"
        if "busts" in game.result_message.lower() or "dealer wins" in game.result_message.lower():
            embed.color = discord.Color.red()
        elif "Player wins" in game.result_message:
            embed.color = discord.Color.green()
        else: # Push
            embed.color = discord.Color.blue()
    else:
        embed.description = "Choose your next move: Hit or Stand?"

    embed.set_footer(text=f"Player ID: {player_id}")
    
    # NEW DEBUG PRINT: Print the entire embed as a dictionary
    print("DEBUG: Final Embed Dictionary:") # DEBUG PRINT CB5
    print(embed.to_dict()) # This will show the raw data sent to Discord

    return embed

class BlackjackView(discord.ui.View):
    def __init__(self, game: BlackjackGame, player_id: int, bet_amount: int):
        super().__init__(timeout=120) # Game times out after 2 minutes of inactivity
        self.game = game
        self.player_id = player_id
        self.bet_amount = bet_amount
        self.message = None

        # Check for immediate Blackjack after initial deal
        try:
            player_score = self.game.calculate_hand_value(self.game.player_hand)
            dealer_score = self.game.calculate_hand_value(self.game.dealer_hand)
        except Exception as e:
            print(f"ERROR: Exception during score calculation in BlackjackView.__init__: {e}")
            import traceback
            traceback.print_exc() # <-- PRINT THE FULL TRACEBACK
            self.game.is_game_over = True # Force game over to avoid further errors
            self.game.result_message = f"An internal error occurred: {e}"
            self.disable_buttons() # Disable buttons immediately
            return # Exit init


        if player_score == 21:
            self.game.is_game_over = True
            if dealer_score == 21:
                self.game.result_message = "Both have Blackjack! It's a push."
            else:
                self.game.result_message = "Blackjack! Player wins!"
        elif dealer_score == 21:
            self.game.is_game_over = True
            self.game.result_message = "Dealer has Blackjack! Dealer wins."



        if self.game.is_game_over:
            self.disable_buttons()
        
    def disable_buttons(self):
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True
    
    # Called when the view times out
    async def on_timeout(self):
        self.disable_buttons()
        # Optionally, notify the user or edit the message
        if self.message:
            try:
                await self.message.edit(content="Your Blackjack game timed out.", view=self)
            except discord.HTTPException:
                pass # Message might have been deleted
        print("DEBUG: Timed out")

    # Store the message the view is attached to, useful for editing
    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item):
        print(f"Error in BlackjackView: {error}")
        await interaction.followup.send("An error occurred during your game.", ephemeral=True)


    @discord.ui.button(label="Hit", style=discord.ButtonStyle.success)
    async def hit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Ensure only the player who started the game can interact
        if interaction.user.id != self.player_id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return
        
        await interaction.response.defer() # Acknowledge the button click

        if self.game.player_hit(): # Player hit and busted
            self.disable_buttons()
            self.is_game_over = True
            self.determine_winner()
        
        # Update the message with the new hand
        embed = create_blackjack_embed(self.game, self.player_id, self.bet_amount, show_dealer_full_hand=self.game.is_game_over)
        await interaction.edit_original_response(embed=embed, view=self)

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.danger)
    async def stand_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.player_id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return
        
        await interaction.response.defer() # Acknowledge the button click

        self.disable_buttons() # Disable buttons as player has stood

        # Dealer's turn
        self.game.dealer_play()

        # Determine winner and adjust balance
        if "Player wins" in self.game.result_message:
            Bank.addcash(str(self.player_id), self.bet_amount) # Win bet
        elif "Dealer wins" in self.game.result_message:
            Bank.addcash(str(self.player_id), -self.bet_amount) # Lose bet
        # No change for push

        embed = create_blackjack_embed(self.game, self.player_id, self.bet_amount, show_dealer_full_hand=True)
        await interaction.edit_original_response(embed=embed, view=self) # Show full dealer hand

@bot.command(name="blackjack", aliases=['bj'], help="Starts a game of Blackjack with your bet!")
async def blackjack_command(ctx: commands.Context, bet: str = "all"): # Changed to ctx and removed app_commands.describe
    """
    Starts a new game of Blackjack.
    """
    player_id_str = str(ctx.author.id) # Use ctx.author.id for prefix commands
    
    try:
        if bet == "all":
            bet = Bank.read_balance(player_id_str)["cash"]
        else:
            bet = int(bet)
    except ValueError:
        await ctx.send("This isn't an integer, you can only bet whole numbers")
        return

    # 1. Input Validation
    if bet <= 0:
        await ctx.send("You must bet a positive amount!")
        return
    
    # 2. Check Player's Balance
    user_balance = Bank.read_balance(player_id_str) 
    if user_balance["cash"] < bet:
        await ctx.send(f"You don't have enough cash! Your current cash: ${user_balance['cash']:,.2f}")
        return

    # Optional: Show typing indicator while preparing the game
    await ctx.defer() # This shows the bot is 'typing'

    # 3. Initialize Game
    game = BlackjackGame()
    game.deal_initial_hands()
    
    # await ctx.send("Blackjack initalised or something")
    # await ctx.send(str(game.player_hand))
    # await ctx.send(str(game.dealer_hand))

    # 4. Create the Interactive View
    view = BlackjackView(game, ctx.author.id, bet) # Pass ctx.author.id
    
    # await ctx.send("Blackjack view intialised or something")

    # 5. Check for immediate game over conditions (e.g., Blackjack on deal)
    if game.is_game_over:
        view.disable_buttons() # Disable Hit/Stand if game is already decided
    
    # 6. Check for immediate game over conditions (e.g., Blackjack on deal)
    embed = create_blackjack_embed(
        game, 
        ctx.author.id, # Pass ctx.uthor.id
        bet, 
        show_dealer_full_hand=game.is_game_over 
    )

    # 7. Send the initial message with buttons
    # For prefix commands, ctx.send returns the Message object 
    message = await ctx.send(embed=embed, view=view)
    view.message = message # Store the Message object in the view for future edits by buttons



@bot.command(name="cardflip", aliases=['cf', 'flip'])
async def card_flip_command(ctx, bet: str = "all"):
    """
    Starts a new game of cardflip
    """
    player_id_str = str(ctx.author.id)

    # Input validation
    try:
        if bet == "all":
            bet = Bank.read_balance(player_id_str)["cash"]
        else:
            bet = int(bet)
    except ValueError:
        ctx.send("Please input a valid amount of cash")
        return

    if bet <= 0:
        await ctx.send("Cash must be a positive amount")
        return

    # Check player's balance
    user_balance = Bank.read_balance(player_id_str)
    if user_balance["cash"] < bet:
        await ctx.send(f"You don't have enough cash! Your current cash ${user_balance['cash']:,.2f}")
        return

    # Show bot as typing
    await ctx.defer()

    # Initalisazation of the game
    game = CardflipGame()
    
    # Create the embed
    embed = discord.Embed(
        title="🃏 Cardflip game",
        color=discord.Color.dark_green()
    )

    player_hand_str = str(game.player_card)
    dealer_hand_str = str(game.dealer_card)

    embed.add_field(name="Bet", value=f"${bet}", inline=False)
    embed.add_field(name="Your hand", value=player_hand_str, inline=False)
    await ctx.send(embed=embed)
    await ctx.send("Revealing dealer's hand in 3 seconds")
    
    await asyncio.sleep(3)
    
    embed.add_field(name="Dealer's hand", value=dealer_hand_str, inline=False)
    
    print("DEBUG: we've goten here so far")
    # Determine and display winner
    try:
        game.determine_winner()
    except Exception as e:
        print(f"Error: {e}")
   
    embed.description = f"**GAME OVER!** {game.result_message}"
    if "player wins" in game.result_message.lower():
        embed.color = discord.Color.green()
        Bank.addcash(player_id_str, bet)
    elif "dealer wins" in game.result_message.lower():
        embed.color = discord.Color.red()
        Bank.addcash(player_id_str, -bet)
    else: # Push
        embed.color = discord.Color.blue()

    await ctx.send(embed=embed)
    
@bot.command(name='hackr', aliases=['hk'])
async def hacker_command(ctx):
    game = HackingGame(6, 200)
    embed = views_embeds.create_hacking_embed(game)
    view = HackingGameView(ctx.author.id, True, game) 
    await ctx.send("If you win this one, you gain a key to an offshore bank account", embed=embed, view=view) 

@bot.command(name='predictor', aliases=['pd'])
async def predictor_command(ctx, difficulty=1,bet="all"):

    if bet == "all":
        bet = Bank.read_balance(str(ctx.author.id))["cash"]
    else:
        try:
            bet = float(bet)
        except ValueError:
            await ctx.send("Invalid bet sucker")
            return

    game = HackingGame(int(10 * math.sqrt(difficulty)), int(100 * math.sqrt(difficulty)))
    print(game) 
    embed = views_embeds.create_hacking_embed(game=game)
    view = HackingGameView(ctx.author.id, False, game, bet=bet)
    await ctx.send(f"If you win this one you get {bet}", embed=embed, view=view)

@bot.command(name='remove-bank-account', aliases=['rm-b'])
async def removeaccount(ctx):
    del Bank.bank_accounts[str(ctx.author.id)]
    Bank.save_balances()


TOKEN = os.environ.get("BOT_TOKEN")

if TOKEN is None:
    print("Error: BOT_TOKEN environment variable not set.")
    print("Please set the BOT_TOKEN environment variable with your bot's authentication token.")
    sys.exit(1) # Exit if the token is not found

bot.run(TOKEN)
