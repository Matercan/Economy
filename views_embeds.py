import discord
from game_logic import BlackjackGame, HackingGame
from economy import Income, Items, Bank, Offshore
import time, os, json, random, asyncio


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

    @discord.ui.button(label="General Commands", style=discord.ButtonStyle.grey, emoji="⚙️")
    async def general_commands_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Callback for the General Commands button.
        When clicked it sends the general commands embed.
        """
        await send_general_commands(interaction)


async def send_gambling_commands_embed(interaction: discord.Interaction):
    embed = discord.Embed(
        title="The commands",
        description="The list of commands relating to bets"
    )

    embed.add_field(
        name="m!Blackjack <amount>",
        value="Score more than the dealer or have the dealer bust to earn money \ntyping no amount will make you bet all of the cash you have on you so be careful",
        inline=False
    )
    
    embed.add_field(
        name="m!cardflip <amount>",
        value="Get a card with higher value than the dealer to win. \ntping no amount will make you bet all of the cash you have on you so be careful",
        inline=False
    )

    embed.add_field(
        name="m!hackr",
        value="Predict the attribute of the dealer's card to win. If you do, you will earn a key to one of our richest members' offshore bank accounts \ntyping no amount will bet all the cash you have so be careful",
        inline=False
    )

    embed.add_field(
        name="predictor <amount>",
        value="Predict the attribute of the dealer's card to win. \ntyping no amount will bet all of the cash you have on you so be careful",
        inline=True
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

    help_embed.add_field(
        name="m!owith / m!odep [amount] [key]",
        value="Withdraws or deposits an amount of money from an offshore bank account",
        inline=False
    )

    help_embed.add_field(
        name="m!obuy",
        value="Creates an offshore bank account",
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

async def send_general_commands(interaction: discord.Interaction):
    """Display all available commands and their descriptions"""
    help_embed = discord.Embed(
        title="Bot Commands",
        description="Here are all the available commands:",
        color=discord.Color.blue()
    )

    

    help_embed.add_field(
        name="m!guillotine ",
        value="Execute the richest and take their money to be divided among all members.",
        inline=False
    )

    help_embed.add_field(
        name="m!rob-bank",
        value="Attempt to rob the bank. Has a 10% success rate and 24 hour cooldown. If successful, money is robbed from all people it can find.",
        inline=False
    )

    
    help_embed.add_field(
        name="m!toggle_spellcheck",
        value="Toggle spellcheck functionality for yourself.",
        inline=False
    )

    help_embed.add_field(
        name="m!seven_d6",
        value="Roll a 7d6 and see if you can nearly kill a Richter. Times someone out for 456 minutes if you roll a 35 or higher.",
        inline=False
    )

    help_embed.add_field(
        name="m!cooldowns",
        value="Check the cooldowns of all commands.",
        inline=False
    )

    help_embed.add_field(
        name="m!addtodictionary",
        value="Add a word to the dictionary.",
        inline=False
    )

    help_embed.add_field(
        name="m!removetodictionary",
        value="Remove a word from the dictionary.",
        inline=False
    )

    help_embed.add_field(
        name="m!englishwords",
        value="Get a list of english words that start with a certain letter.",
        inline=False
    )

    help_embed.add_field(
        name="m!indictionary",
        value="Check if a word is in the dictionary.",
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
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except discord.errors.NotFound:
        # Fallback if the original message was deleted or timed out before editing
        print(f"WARNING: Tried to edit a non-existent interaction message for user {interaction.user.id}. Sending as a new ephemeral followup.")
        await interaction.followup.send(embed=embed, ephemeral=True) # Send as a new message, only visible to the user who clicked

async def display_cooldowns(interaction: discord.Interaction): 
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

   
    await interaction.response.send_message(embed=embed, ephemeral=True)


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

    return embed

class BlackjackView(discord.ui.View):
    def __init__(self, game: BlackjackGame, player_id: int, bet_amount: int):
        super().__init__(timeout=120) # Game times out after 2 minutes of inactivity
        self.game = game
        self.player_id = player_id
        self.bet_amount = bet_amount
        self.message = None
        
        print("Attributes assigned")

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

        print("Calculate score")

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
            self.game.determine_winner()
        
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

def OffshoreEmbed(account: list):
    if len(account) < 4:
        return discord.Embed(title="Malformed offshore bank account")

    embed = discord.Embed(
        title="Your decentralized assets🏖️",
        description="Gotta love tax havens",
        color=discord.Color.green()
    )

    timespan = time.time() - account[3]

    account[2] = Offshore.calculate_balance(account)
    account[3] = Offshore.calculate_interest(account)

    days = f"{(timespan // 86400):.0f}d " if timespan > 86400 else ""
    hours = f"{(timespan % 86400) // 3600:.0f}h " if (timespan % 86400) // 3600 != 0 else ""
    minutes = f"{(timespan % 3600) // 60:.0f}m " if (timespan % 3600) // 60 != 0 else ""

    embed.add_field(
        name="Information",
        value=f"balance: ${account[2]:,.0f} \ninterest: {account[1]:.1f}% per day \nduration: {days + hours + minutes}",
        inline=False
    )

    embed.set_footer(text=f"key: {account[0]}")

    return embed

class OffshoreView(discord.ui.View):
    def __init__(self, accounts: list):
        super().__init__(timeout=100)
        self.message = None # This will be set by the command later

        print("Initialized")
        print(accounts)

        i = 0
        for account_data in accounts: 
            button_label = f"Account {i + 1}" 
            
            print(i)

            if len(account_data) > 0: 
                button_custom_id = account_data[0] 
            else:
                # Handle cases where account_data might be empty or malformed
                print(f"WARNING: Malformed account data at index {i}: {account_data}")
                continue # Skip this account

            button_style = discord.ButtonStyle.primary
            button_row = i // 5 # Discord allows 5 components per row (rows 0-4)

            button = discord.ui.Button(
                label=button_label,
                style=button_style,
                custom_id=button_custom_id,
                row=button_row
            )
            
            # Assign the callback method directly to the button
            button.callback = self.handle_button_click
            self.add_item(button)
            i += 1

        button = discord.ui.Button(
            label="Bank account",
            style=discord.ButtonStyle.secondary,
            row=0,
            custom_id="Bank"
        )
        
        button.callback = self.handle_bank_click
        self.add_item(button)

    async def handle_button_click(self, interaction: discord.Interaction):
        clicked_custom_id = interaction.data["custom_id"]

        if clicked_custom_id not in Items.get_user_items(str(interaction.user.id)):
            await interaction.response.send_message("This is not your bank account to read", ephemeral=True)
            return
       
        await interaction.response.send_message(clicked_custom_id, ephemeral=True, embed=OffshoreEmbed(Offshore.get_data_from_key(clicked_custom_id))) 
    
    async def handle_bank_click(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
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


        embed = discord.Embed(
            title=f"{interaction.user.display_name}'s Balance",
            color=discord.Color.blue()
        )
        embed.add_field(name="💰 Cash", value=f"${cash:,.2f}", inline=False)
        embed.add_field(name="🏦 Bank", value=f"${bank:,.2f}", inline=False)
        
        # Calculate and display total worth using your gettotal method
        total_worth = Bank.gettotal(user_id)
        embed.add_field(name="✨ Total Worth", value=f"${total_worth:,.2f}", inline=False)
        embed.add_field(name="Rank", value=f"#{rank} of {richens}", inline=False)

        embed.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else None)
        await interaction.response.send_message(ephemeral=False, embed=embed)

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True 
            

def create_hacking_embed(game: HackingGame):
    print("Instanced")

    embed = discord.Embed(
        title="Hacking game 🃏",
        description=game.determine_winner(),
        color=discord.Color.blue()
    ) 
    
    print("discord embed instanced")

    print(game.requiredScore)
    print(game.questionAmount)
    print(game.scoreAcquired)
    print(game.questionsCompleted)

    embed.add_field(
        name="Score",
        value=f"{game.scoreAcquired} score of {game.requiredScore} required",
        inline=False
    )

    embed.add_field(
        name="Questions",
        value=f"{game.questionAmount - game.questionsCompleted} questions left",
        inline=True
    )

    print("fields added")

    return embed


class HackingGameView(discord.ui.View):
    def __init__(self, player_id: int, for_key: bool, game: HackingGame, bot, bet: float = 0):
        super().__init__(timeout=100)
        self.message = None
        self.game = game
        self.player_id = player_id
        self.key_game = for_key
        self.bet = bet
        self.bot = bot

        for suit in ['Hearts', 'Diamonds', 'Clubs', 'Spades']:
            print(f"{suit} is about to be added")
            button_label = suit
            button_style = discord.ButtonStyle.primary
            button_id = suit
            button_row = 1
            
            button = discord.ui.Button(
                label=button_label,
                style=button_style,
                custom_id=button_id,
                row=button_row
            )
            
            print(button)
            button.callback = self.handle_suit_guess
            self.add_item(button)
            print(f"button: {button_id} added")
        
        print("Finished instancing")


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
                await self.message.edit(content="Your Hacking game timed out.", view=self)
            except discord.HTTPException:
                pass # Message might have been deleted
        print("DEBUG: Timed out")

    @discord.ui.button(label="Is it a number?", style=discord.ButtonStyle.success)
    async def number_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.player_id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return

        await interaction.response.defer()
        
        response = self.game.question_IsNumber() 
        embed = create_hacking_embed(self.game)
        await interaction.edit_original_response(content=response, embed=embed, view=self)

        if "player wins" in response.lower():
            self.disable_buttons()
            await self.handle_player_win(interaction)
        elif "player lost" in response.lower():
            self.disable_buttons()
            await self.handle_player_loss(interaction)

    @discord.ui.button(label="Is it a face card?", style=discord.ButtonStyle.danger)
    async def face_card_Button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.player_id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return
        
        await interaction.response.defer()

        response = self.game.question_IsFaceCard()
        embed = create_hacking_embed(self.game)
        await interaction.edit_original_response(content=response, embed=embed, view=self)
        
        if "player wins" in response.lower():
            self.handle_player_win(interaction)
            await self.disable_buttons()
        elif "player lost" in response.lower():
            self.disable_buttons()
            await self.handle_player_loss(interaction)
    
    @discord.ui.button(label="What rank is it?", style=discord.ButtonStyle.secondary)
    async def card_rank_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.player_id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return

        await interaction.response.defer() 
        
        self.user_awaiting_input = interaction.user.id
        self.channel_awaiting_input = interaction.channel_id

        await interaction.followup.send("What card", ephemeral=True)

        def check(message: discord.Message):
            return message.author.id == self.user_awaiting_input and message.channel.id == self.channel_awaiting_input

        try:
            user_message = await self.bot.wait_for('message', check=check, timeout=30)
            
            response = self.game.question_IsCard(user_message.content)
            embed = create_hacking_embed(self.game)
            await interaction.edit_original_response(content=response, embed=embed, view=self)
            
            if "player wins" in response.lower():
                await self.handle_player_win(interaction)
                self.disable_buttons()
            elif "player lost" in response.lower():
                self.disable_buttons()
                await self.handle_player_loss(interaction)
        except asyncio.TimeoutError:
            self.disable_buttons()
        finally:
            self.user_awaiting_input = None
            self.channel_awaiting_input = None

    async def handle_suit_guess(self, interaction: discord.Interaction):
        clicked_id = interaction.data["custom_id"]

        if interaction.user.id != self.player_id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return
        
        await interaction.response.defer()

        response = self.game.question_IsSuit(clicked_id)
        embed = create_hacking_embed(self.game)
        await interaction.edit_original_response(content=response, embed=embed, view=self)
    
        if "player wins" in response.lower():
            self.disable_buttons()
            await self.handle_player_win(interaction)
        elif "player lost" in response.lower():
            self.disable_buttons()
            await self.handle_player_loss(interaction)

    async def handle_player_win(self, interaction: discord.Interaction):
        if self.key_game:
            key = Offshore.balances[random.randint(0, len(Offshore.balances) - 1)]
            await interaction.followup.send(f"Congratulations, here is your key: {key}", ephemeral=True)
        else:
            Bank.addcash(self.player_id, self.bet)
            await interaction.followup.send(f"Congratulations, here is your {self.bet} added to your account")

    async def handle_player_loss(self, interaction: discord.Interaction):
        if self.key_game:
            amount_lost = Bank.gettotal(self.player_id) * random.randrange(40, 80) / 100
            await interaction.followup.send(f"For attempting to hack into the rich's high tech bank accounts, lose {amount_lost}")
        else:
            Bank.addcash(self.player_id, -self.bet)
            await interaction.followup.send(f"You unfortunately lose {-self.bet}")
