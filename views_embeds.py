import discord
from game_logic import BlackjackGame, RoulletteGame
from economy import Income, Items
import time, os, json

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

    @discord.ui.button(label="Gambling Commands", style=discord.ButtonStyle.success, emoji="🃏")
    async def Gambling_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Callback for the Gambling commands button.
        When clicked it sends the gambling commands embed.
        """
        await send_gambling_commands_embed(interaction)


async def send_gambling_commands_embed(interaction: discord.Interaction):
    embed = discord.Embed(
        title="The commands",
        description="The list of commands relating to bets"
    )

    embed.add_field(
        name="Blackjack <amount>",
        value="Score more than the dealer or have the dealer bust to earn money \ntyping no amount will make you bet all of the cash you have on you so be careful",
        inline=False
    )
    
    embed.add_field(
        name="cardflip <amount>",
        value="Get a card with higher value than the dealer to win. \ntping no amount will make you bet all of the cash you have on you so be careful",
        inline=False
    )

    await interaction.response.edit_message(embed=embed)


async def send_economy_commands_embed(interaction: discord.Interaction):
    help_embed = discord.Embed(
        title="The commands",
        description="The list of all commands relating to the economy",
    )

    help_embed.add_field(
        name="m!balance [member]",
        value="Shows balance of yourself/another user",
        inline=False
    )

    help_embed.add_field(
        name="m!deposit/withdraw <amount>",
        value="Self explanatory",
        inline=False
    )

    help_embed.add_field(
        name="m!work",
        value="Gives money based on your current net worth",
        inline=False
    )

    help_embed.add_field(
        name="m!give [user] <amount>",
        value="Gives user an amount of cash",
        inline=False
    )

    help_embed.add_field(
        name="m!collect",
        value="Collects your available income",
        inline=False
    )

    help_embed.add_field(
        name="m!incomes",
        value="Displays all income sources and cooldowns",
        inline=False
    )

    help_embed.add_field(
        name="m!incomes",
        value="Displays info about your specific income sources",
        inline=False
    )

    help_embed.add_field(
        name="m!richest-member",
        value="Displays the richest member this side of the economy",
        inline=False
    )
 
    help_embed.add_field(
        name="m!store",
        value="Gets all the items within the store",
        inline=False
    )

    help_embed.add_field(
        name="m!loan",
        value="Takes out a 50000 loan for the user",
        inline=False
    )

    await interaction.response.edit_message(embed=help_embed)

async def send_violent_commands(interaction: discord.Interaction):
    help_embed = discord.Embed(
        title="Violent commands",
        description="List of all commands that modify your kill_count (or display it)"
    )

    help_embed.add_field(
        name="m!stab [user]",
        value="Stab another user, You can only stab once every hour and if you have a knife. Has a cooldown.", 
        inline=False
    )

    help_embed.add_field(
        name="m!use bomb",
        value="Use a bomb item. 1/10 chance to kill a random user and a 1/10 chance to kill yourself. Has a cooldown.",
        inline=False
    )

    help_embed.add_field(
        name="m!use brick", 
        value="Use a brick item, gives you the brick role. Now if you type !use brick or !brick you can time someone out for 10 minutes",
        inline=False
    )

    help_embed.add_field(
        name="m!kill [user]",
        value="Kill a user with a 1/10 chance (1/5 if you have a knife). Has a cooldown.",
        inline=False
    )

    help_embed.add_field(
        name="m!killcount [user]",
        value="Check the targetted attack count of a user.",
        inline=False
    )

    help_embed.add_field(
        name="m!kill_leaderboard",
        value="Check the top 10 most prolific attackers.",
        inline=False
    )

    help_embed.add_field(
        name="m!topkill_leaderboard",
        value="Checks the top 10 killers across all servers with economy in it",
        inline=False
    )

    await interaction.response.edit_message(embed=help_embed)

async def display_incomes_interaction(interaction: discord.Interaction):
    """
    Displays the user's income sources and their status using an embed.
    This function is designed to be called from an interaction (like a button click).
    """
    # --- Crucial: Get the correct user ID ---
    user_id_str = str(interaction.user.id) # Correctly gets the numeric user ID as a string

    # --- Handle interactions outside of a guild (e.g., DMs) if necessary ---
    # Although income sources are usually guild-bound, this check is good practice.
    if not interaction.guild:
        await interaction.response.send_message(
            "This command should be used in a server to display income sources.",
            ephemeral=True # Makes the message visible only to the user who clicked
        )
        return

    # Call the method to get the user's income status list
    # Assuming Income.get_user_income_status correctly returns a list of dictionaries
    user_income_status_list = Income.get_user_income_status(user_id=user_id_str)

    embed = discord.Embed(
        title=f"💰 Your Income Sources for {interaction.user.display_name}",
        color=discord.Color.green()
    )

    if not user_income_status_list: # If the list is empty, user has no assigned incomes
        embed.add_field(
            name="No Incomes Found",
            value="You don't have any income sources assigned yet. You might need to buy items that grant income!",
            inline=False
        )
    else:
        # Iterate through the list of income statuses and add fields to the embed
        for inc_status in user_income_status_list:
            # Use .get() for safer dictionary access in case keys are missing
            name = inc_status.get("name", "Unknown Income")
            status = inc_status.get("status", "Status Unavailable")
            
            field_value = ""
            # Check if 'details_valid' is True (or present) before trying to access details
            if inc_status.get("details_valid", False): 
                is_interest = inc_status.get("is_interest", False)
                value = inc_status.get("value", 0)
                cooldown = inc_status.get("cooldown", 0) # This is the base cooldown in seconds
                goes_to_bank = inc_status.get("goes_to_bank", False)

                value_display = ""
                if is_interest:
                    # Format percentage with 2 decimal places
                    value_display = f"**{value * 100:,.2f}%** interest on your {'bank' if goes_to_bank else 'cash'}"
                else:
                    # Format value with commas for readability
                    value_display = f"**{value:,}** {'to bank' if goes_to_bank else 'to cash'}"
                
                # Calculate and format cooldown display (assuming cooldown is in seconds)
                cooldown_days = int(cooldown // 86400)
                cooldown_hours = int((cooldown % 86400) // 3600)
                cooldown_minutes = int((cooldown % 3600) // 60)
                cooldown_seconds = int(cooldown % 60) # Ensure integer for display

                # Show current status and detailed info
                field_value = (
                    f"Status: `{status}`\n" # Displays if ready or cooldown remaining
                    f"Value: {value_display}\n"
                    f"Base Cooldown: {cooldown_days}d {cooldown_hours}h {cooldown_minutes}m {cooldown_seconds}s" # Base cooldown duration
                )
            else:
                # For invalid or malformed sources, just show the error status and a hint
                field_value = f"Status: `{status}`\n_Source details invalid or not found._"

            embed.add_field(
                name=f"📈 {name}",
                value=field_value,
                inline=False # Each income source gets its own line
            )
    
    # --- Respond to the Interaction ---
    # This edits the message the button was clicked on. It also serves as the initial response.
    try:
        await interaction.response.edit_message(embed=embed)
    except discord.errors.NotFound:
        # Fallback if the original message was deleted or timed out before editing
        print(f"WARNING: Tried to edit a non-existent interaction message for user {interaction.user.id}. Sending as a new ephemeral followup.")
        await interaction.followup.send(embed=embed, ephemeral=True) # Send as a new message, only visible to the user who clicked

async def display_cooldowns(interaction: discord.Interaction): # Corrected type hint
    """
    Displays the cooldowns for bot commands (personal and server-wide).
    This function is designed to be called from an interaction (like a button click).
    """
    embed = discord.Embed(
        title="Command Cooldowns",
        description="Here are the active cooldowns for bot commands:",
        color=discord.Color.blue()
    )

    # --- Crucial: Handle interactions outside of a guild (e.g., DMs) ---
    if not interaction.guild:
        await interaction.response.send_message(
            "This command for displaying cooldowns can only be used in a server!",
            ephemeral=True # Makes the message visible only to the user who clicked
        )
        return

    guild_id = str(interaction.guild.id)
    user_id = str(interaction.user.id)

    cooldowns = load_cooldowns() # Load the latest cooldown data

    # Get guild-specific cooldowns or an empty dict if none exist for this guild
    guild_cooldown_data = cooldowns.get(guild_id, {})
    user_cooldowns_data = guild_cooldown_data.get('users', {}).get(user_id, {})

    # --- Populate User-Specific Cooldowns ---
    user_cooldowns_field_value = ""
    for command_name, last_used in user_cooldowns_data.items():
        time_passed = time.time() - last_used
        cooldown_time = command_cooldowns.get(command_name, 86400) # Default to 24h if not specified

        if time_passed < cooldown_time:
            remaining = cooldown_time - time_passed
            days = int(remaining // 86400)
            hours = int((remaining % 86400) // 3600) # Corrected hours calculation
            minutes = int((remaining % 3600) // 60)
            seconds = int(remaining % 60) # Include seconds for precision
            user_cooldowns_field_value += f"**`{command_name}`**: {days}d {hours}h {minutes}m {seconds}s\n"

    if user_cooldowns_field_value:
        embed.add_field(name="Your Personal Cooldowns", value=user_cooldowns_field_value, inline=False)
    else:
        embed.add_field(name="Your Personal Cooldowns", value="No active personal command cooldowns.", inline=False)

    # --- Populate Guild-Wide Cooldowns ---
    guild_wide_cooldowns_field_value = ""
    for command_name, last_used in guild_cooldown_data.items():
        if command_name != 'users': # Skip the 'users' sub-dictionary
            time_passed = time.time() - last_used
            cooldown_time = command_cooldowns.get(command_name, 86400) # Default to 24h if not specified

            if time_passed < cooldown_time:
                remaining = cooldown_time - time_passed
                days = int(remaining // 86400)
                hours = int((remaining % 86400) // 3600) # Corrected hours calculation
                minutes = int((remaining % 3600) // 60)
                seconds = int(remaining % 60) # Include seconds for precision
                guild_wide_cooldowns_field_value += f"**`{command_name}`**: {days}d {hours}h {minutes}m {seconds}s\n"
    
    if guild_wide_cooldowns_field_value:
        embed.add_field(name="Server-Wide Cooldowns", value=guild_wide_cooldowns_field_value, inline=False)
    else:
        embed.add_field(name="Server-Wide Cooldowns", value="No active server-wide cooldowns.", inline=False)

   
    await interaction.response.edit_message(embed=embed)


class CooldownsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=100) # Timeout after 100 seconds of inactivity

    @discord.ui.button(label="Command Cooldowns", style=discord.ButtonStyle.success)
    async def command_cooldowns_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Callback for the Command Cooldowns button.
        When clicked, it calls display_cooldowns to show command cooldowns.
        """
        # Call the standalone function
        await display_cooldowns(interaction)

    @discord.ui.button(label="Income Cooldowns", style=discord.ButtonStyle.danger)
    async def income_cooldowns_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Callback for the Income Cooldown button.
        When clicked, it calls display_incomes_interaction to show income cooldowns.
        """
       
        await display_incomes_interaction(interaction)


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
