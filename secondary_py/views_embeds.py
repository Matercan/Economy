import discord
from game_logic import BlackjackGame, HackingGame
from economy import Income, Items, Bank, Offshore
import time, os, json, random, asyncio, math
import economy

AUDIT_CHANNEL = 1368552599539810314

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
        file_path = os.path.join(economy.JSON_FILES_DIR, 'cooldowns.json')
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        return {}
    except (FileNotFoundError, json.JSONDecodeError, PermissionError) as e:
        print(f"Error loading cooldowns: {e} - ping mater")
        return {}

command_cooldowns = {
    'kill': 86400,         # 24 hours
    'random_kill': 86400,  # 24 hours
    'stab': 7200,          # 2 hour
    'guillotine': 604800,  # 7 days
    'rob_bank': 604800,    # 7 days
    'seven_d6': 25560,     # 7 hours and 6 minutes
    '911': 14400,          # 4 hours
    'work': 86400,         # 24 hours
    'suicude': 14400,      # 4 hours
    'slut': 14400,         # 4 hours
    'crime': 14400,        # 4 hours
    'rob': 14400,          # 4 hours
    'guillotine-user': 604800 # 7 days
}

def create_blackjack_embed(game: BlackjackGame, player_id: int, bet_amount: int, show_dealer_full_hand: bool = False):
    embed = discord.Embed(
        title="🃏 Blackjack Game",
        color=discord.Color.dark_green()
    )

    player_hand_str = ", ".join(str(card) for card in game.player_hand)
    player_score = game.calculate_hand_value(game.player_hand)

    embed.add_field(
        name=f"Your Hand ({player_score})",
        value=player_hand_str,
        inline=False
    )

    if show_dealer_full_hand:
        dealer_hand_str = ", ".join(str(card) for card in game.dealer_hand)
        dealer_score = game.calculate_hand_value(game.dealer_hand)
        embed.add_field(
            name=f"Dealer's Hand ({dealer_score})",
            value=dealer_hand_str,
            inline=False
        )
    else:
        # Show only dealer's first card initially
        dealer_hand_str = f"{game.dealer_hand[0]} and one hidden card" # This line was missing its assignment
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
    

    return embed

class BlackjackView(discord.ui.View):
    def __init__(self, game: 'BlackjackGame', player_id: int, bet_amount: int, bot_instance): # Added bot_instance
        super().__init__(timeout=120) 
        self.game = game
        self.player_id = player_id
        self.bet_amount = bet_amount
        self.message = None # This will be set by the command after sending the message
        self.bot = bot_instance # Store bot instance for create_balance_embed

        # CRITICAL FIX: Use str(self.player_id) for Bank operations
        self.starting_bal = Bank.read_balance(str(self.player_id))["cash"] 
        
        print("DEBUG: BlackjackView attributes assigned.")

        # Check for immediate Blackjack after initial deal
        # This logic determines the game state but DOES NOT transfer money yet.
        # Money transfer will happen in _end_game or on_timeout.
        try:
            player_score = self.game.calculate_hand_value(self.game.player_hand)
            dealer_score = self.game.calculate_hand_value(self.game.dealer_hand)
        except Exception as e:
            print(f"ERROR: Exception during score calculation in BlackjackView.__init__: {e}")
            import traceback
            traceback.print_exc() 
            self.game.is_game_over = True 
            self.game.result_message = f"An internal error occurred during game setup: {e}"
            self.disable_buttons() 
            return 

        print("DEBUG: Scores calculated in BlackjackView.__init__.")

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
            self._end_game()
            print("DEBUG: Game immediately over in __init__.")
            
    def disable_buttons(self):
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True
    
    # New helper method to finalize the game and update the message
    async def _end_game(self):

        for item in self.children:
            if isinstance(item, discord.ui.Button):
                if item.disabled:
                    print("You've already won")
                    return

        self.disable_buttons() # Ensure buttons are disabled
        
        # Determine winner and adjust balance
        if "Blackjack!" in self.game.result_message:
            blackjackMultiplier = 1.25
            if "player wins" in self.game.result_message.lower():
                Bank.addcash(str(self.player_id), 2 * blackjackMultiplier * self.bet_amount) # Win gives you your money back and more
                money_change = (2 * blackjackMultiplier - 1) * self.bet_amount
                print(f"DEBUG: Player {self.player_id} wins {money_change} and got blackjack")
            elif "dealer wins" in self.game.result_message.lower():
                Bank.addcash(str(self.player_id), -(blackjackMultiplier - 1) * self.bet_amount) # Take away extra money for blackjack
                money_change = - self.bet_amount * blackjackMultiplier
                print(f"DEBUG: Player {self.player_id} lost {money_change}")
            else:
                Bank.addcash(str(self.player_id), self.bet_amount)
                money_change = 0
                print(f"DEBUG: Player {self.player_id} pushes")
            pass
        else: 
            if "player wins" in self.game.result_message.lower():
                Bank.addcash(str(self.player_id), 2 * self.bet_amount) # Win bet (cancels out money lost at start)
                money_change = self.bet_amount
                print(f"DEBUG: Player {self.player_id} wins {self.bet_amount}")
            elif "dealer wins" in self.game.result_message.lower():
                Bank.addcash(str(self.player_id), 0) # Lose bet (money is already deducted at start)
                money_change = -self.bet_amount
                print(f"DEBUG: Player {self.player_id} loses {self.bet_amount}")
            else: # Push
                money_change = 0
                Bank.addcash(str(self.player_id), self.bet_amount)
                print(f"DEBUG: Player {self.player_id} pushes.")

        # Update the main blackjack embed to show full dealer hand and result
        blackjack_embed = create_blackjack_embed(self.game, self.player_id, self.bet_amount, show_dealer_full_hand=True)
        
        # Create and send the balance embed
        balance_embed = await create_balance_embed(str(self.player_id), self.bot, amountAddedToCash=money_change)
        
        if self.message:
            try:
                await self.message.edit(embed=blackjack_embed, view=self) # Update main message
                await self.message.channel.send(embed=balance_embed) # Send balance embed in the same channel
            except discord.HTTPException as e:
                print(f"ERROR: Failed to edit message or send balance embed: {e}")
        else:
            print("WARNING: self.message not set, cannot edit or send balance embed.")

    async def on_timeout(self):
        print("DEBUG: Blackjack game timed out.")
        if not self.game.is_game_over: # Only determine winner if game wasn't already over
            self.game.is_game_over = True
            self.game.result_message = "Player loses due to timeout." # Or "No action taken due to timeout"
            # Bank.addcash(str(self.player_id), -self.bet_amount) 
        await self._end_game() # Finalize the game state and update embeds

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item):
        print(f"Error in BlackjackView: {error}")
        import traceback
        traceback.print_exc()
        await interaction.followup.send("An unexpected error occurred during your game. The game has ended.", ephemeral=True)
        self.game.is_game_over = True
        self.game.result_message = "An unexpected error occurred."
        await self._end_game() # Attempt to finalize the game

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.success)
    async def hit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.player_id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return
        
        await interaction.response.defer()

        if self.game.is_game_over: # Prevent actions if game is already over
            await interaction.followup.send("This game is already over!", ephemeral=True)
            return

        player_busted = self.game.player_hit() 
        
        if player_busted: # Player hit and busted
            self.game.is_game_over = True
            self.game.result_message = "Player busts! Dealer wins." # Set result message directly
            await self._end_game() # Finalize the game
        else:
            # Update the message with the new hand (dealer hand still hidden)
            embed = create_blackjack_embed(self.game, self.player_id, self.bet_amount, show_dealer_full_hand=False)
            await interaction.edit_original_response(embed=embed, view=self)

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.danger)
    async def stand_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        print(f"DEBUG: Entering stand_button. self.game: {self.game}")
        if interaction.user.id != self.player_id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return
        
        await interaction.response.defer()

        print(self.game.is_game_over)
        if self.game.is_game_over: # Prevent actions if game is already over
            await interaction.followup.send("This game is already over!", ephemeral=True)
            return

        
        self.game.dealer_play() # Dealer plays until 17+ or busts
        print("DEBUG: Dealer played.")       
        print(f"DEBUG: Winner determined. Result: {self.game.result_message}")
        
        await self._end_game() # Finalize the game and update embeds
    


def OffshoreEmbed(account: list):
    if len(account) < 4:
        return discord.Embed(title="Malformed offshore bank account")

    embed = discord.Embed(
        title="Your decentralized assets🏖️",
        description="Gotta love tax havens",
        color=discord.Color.green()
    )

    timespan = time.time() - account[3]
    print(account[3])

    account[2] = Offshore.calculate_balance(account)
    account[1] = Offshore.calculate_interest(account) if Offshore.calculate_interest(account) > account[1] else account[1]

    real_account = Offshore.get_data_from_key(account[0]) 

    days = f"{(timespan // 86400):.0f}d " if timespan > 86400 else ""
    hours = f"{(timespan % 86400) // 3600:.0f}h " if (timespan % 86400) // 3600 != 0 else ""
    minutes = f"{(timespan % 3600) // 60:.0f}m " if (timespan % 3600) // 60 != 0 else ""

    balance_display = f"**${account[2]:,.2f}**"
    interest_display = f"**{account[1]:,.2f}%** intest per day"
    duration_display = f"**{days + hours + minutes}**" 

    if account[1] > real_account[1]:
        interest_display += " when modified"

    embed.add_field(
        name="Information",
        value=f"balance: {balance_display} \ninterest: {interest_display} \nlast modified: {duration_display} ago",
        inline=False
    ) 

    embed.set_footer(text=f"key: {account[0]}")

    return embed

class OffshoreView(discord.ui.View):
    def __init__(self, accounts: list, bot):
        super().__init__(timeout=100)
        self.message = None # This will be set by the command later
        self.bot = bot

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

        if clicked_custom_id not in list(Items.get_user_items(str(interaction.user.id))):
            await interaction.response.send_message("This is not your bank account to read", ephemeral=True)
            return
       
        await interaction.response.send_message(clicked_custom_id, ephemeral=True, embed=OffshoreEmbed(Offshore.get_data_from_key(clicked_custom_id))) 
    
    async def handle_bank_click(self, interaction: discord.Interaction):
        embed = await create_balance_embed(str(interaction.user.id), self.bot)

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
    print(game.cardsUsed)

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

    embed.add_field(
        name="Cards",
        value=f"{[(card.get_value(), card.suit[0]) for card in game.cardsUsed]} have been used", 
        inline=False
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

        if self.key_game:
            Bank.addcash(player_id, Bank.gettotal(self.player_id))

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
            user_message.delete()

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
            key = Offshore.balances[random.randint(0, len(Offshore.balances) - 1)][0]
            await interaction.followup.send(f"Congratulations, here is your key: {key}", ephemeral=True)
        else:
            Bank.addcash(self.player_id, self.bet)
            await interaction.followup.send(await create_balance_embed(self.player_id, self.bot, amountAddedToCash=self.bet))

    async def handle_player_loss(self, interaction: discord.Interaction):
        if self.key_game:
            amount_lost = Bank.gettotal(self.player_id) * random.randrange(40, 80) / 100
            await interaction.followup.send(f"For attempting to hack into the rich's high tech bank accounts, lose {amount_lost}")
        else:
            Bank.addcash(self.player_id, -self.bet)
            await interaction.followup.send(await create_balance_embed(self.player_id, self.bot, amountAddedToCash=-self.bet))

async def create_balance_embed(user_id: str, bot, amountAddedToCash: float = 0, amountAddedToBank: float = 0):
    user = bot.get_user(int(user_id))
    
    # Get the initial numeric balances
    initial_cash = Bank.read_balance(user_id)["cash"]
    initial_bank = Bank.read_balance(user_id)["bank"]
    initial_balance = Bank.gettotal(user_id)

    cash_display_value = initial_cash - amountAddedToCash 
    bank_display_value = initial_bank - amountAddedToBank
    balance_display_value = initial_balance - (amountAddedToBank + amountAddedToCash)

    # Get current (actual) balances from Bank (after any prior transaction that led to calling this embed)
    cash_now = Bank.read_balance(user_id)["cash"]
    bank_now = Bank.read_balance(user_id)["bank"] 
    balance_now = Bank.gettotal(user_id)

    # Format the display values *just before* adding them to the embed
    formatted_cash_display = f"**${cash_display_value:,.2f}**"
    formatted_bank_display = f"**${bank_display_value:,.2f}**"
    formatted_total_display = f"**${balance_display_value:,.2f}**"

    formatted_cash_now = f" -> **${cash_now:,.2f}**" if amountAddedToCash != 0 else ""
    formatted_bank_now = f" -> **${bank_now:,.2f}**" if amountAddedToBank != 0 else ""
    formatted_balance_now = f" -> **${balance_now:,.2f}**" if amountAddedToBank + amountAddedToCash != 0 else ""

    print(f"DEBUG BALANCE: {formatted_cash_display}, {formatted_bank_display}, {formatted_total_display}")

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
        title=f"{user.display_name}'s Balance",
        color=discord.Color.blue()
    )

    cashAddedStr = ""
    bankAddedStr = ""
    totalAddedStr = ""

    if amountAddedToCash < 0:
        cashAddedStr = f" \n(${amountAddedToCash:,.0f})" # Added parentheses for clarity
    elif amountAddedToCash > 0:
        cashAddedStr = f" \n(+${amountAddedToCash:,.0f})" # Added parentheses for clarity

    if amountAddedToBank < 0:
        bankAddedStr = f" \n(${amountAddedToBank:,.0f})" # Added parentheses for clarity
    elif amountAddedToBank > 0:
        bankAddedStr = f" \n(+${amountAddedToBank:,.0f})" # Added parentheses for clarity
    
    total_change_delta = amountAddedToCash + amountAddedToBank
    if total_change_delta > 0:
        totalAddedStr = f" \n(+${total_change_delta:,.0f})"
    elif total_change_delta < 0:
        totalAddedStr = f" \n(${total_change_delta:,.0f})"

    print(f"DEBUG: cash added: {cashAddedStr}, {bankAddedStr}, {totalAddedStr}")

    # Use the formatted string variables here
    embed.add_field(name="💰 Cash", value=f"{formatted_cash_display}{formatted_cash_now} {cashAddedStr}", inline=True)
    embed.add_field(name="🏦 Bank", value=f"{formatted_bank_display}{formatted_bank_now} {bankAddedStr}", inline=True)

    
    embed.add_field(name="✨ Total Worth", value=f"{formatted_total_display}{formatted_balance_now} {totalAddedStr}", inline=False)
    embed.add_field(name="Rank", value=f"**#{rank}** of {richens}", inline=False)

    embed.set_thumbnail(url=user.avatar.url if user.avatar else None)

    audit_channel = bot.get_channel(AUDIT_CHANNEL)
    await audit_channel.send(embed=embed)

    return embed

def format_items_list(items_list: list):
    if not items_list:
        return ""  # Return empty string for an empty list
    elif len(items_list) == 1:
        return f"'{items_list[0]}'" # Just one item
    elif len(items_list) == 2:
        return f"'{items_list[0]}' and '{items_list[1]}'" # Exactly two items
    else:
        # For more than two items, join all but the last with a comma, then add "and LastItem"
        quoted_items = [f"'{item}'" for item in items_list] # Add quotes to each item
        return ", ".join(quoted_items[:-1]) + f" and {quoted_items[-1]}"


class ShopView(discord.ui.View):
    def __init__(self):    
        super().__init__(timeout=180)

        self.page = 0
        self.itemsPerPage = 10 # Keep your original 10 items per page

        # Load all items once during initialization
        self.all_items = Items.load_item_sources()
        
        # Filter items that are actually meant for the shop
        # Assuming item[1] is `is_collectable` (True for collectable, False for purchasable)
        self.shop_items = [item for item in self.all_items if len(item) > 1 and not item[1]] 
        
        # Calculate pages based on shop_items
        self.pages = math.ceil(len(self.shop_items) / self.itemsPerPage) if self.shop_items else 1 # Handle case of no shop items

        # Add page buttons
        for i in range(self.pages):
            button_label = f"Page {i + 1}"    
            button_style = discord.ButtonStyle.primary
            button_id = f"page_{i}" # Use a prefix like 'page_' for safety
            button_row = i // 5 # Max 5 buttons per row for Discord UI (0-4, 5-9 etc.)

            button = discord.ui.Button(
                label=button_label,
                style=button_style,
                custom_id=button_id,
                row=button_row
            )

            print(f"Adding button for {button_id} to view.") # Debug print
            button.callback = self.handle_click_page
            self.add_item(button)
            # No need for the "button: X added" print inside loop, the above is sufficient.

    async def handle_click_page(self, interaction: discord.Interaction):
        clicked_id = interaction.data["custom_id"]
        await interaction.response.defer() # Defer immediately

        try:
            # Parse the page number from the custom_id (e.g., "page_0" -> 0)
            pageClicked = int(clicked_id.replace("page_", ""))
        except ValueError:
            print(f"Error parsing page ID: {clicked_id}")
            await interaction.followup.send("Invalid page button clicked. Please try again.", ephemeral=True)
            return

        # Update the current page
        self.page = pageClicked

        # Calculate start and end indices for the current page's items
        startNum = self.page * self.itemsPerPage
        endNum = min(startNum + self.itemsPerPage, len(self.shop_items))

        # Get the slice of items for the current page
        items_for_current_page = self.shop_items[startNum:endNum]
        
        # Pass the sliced list directly to create_store_embed
        embed = create_store_embed(items_for_current_page) 

        await interaction.edit_original_response(embed=embed, view=self)

    async def on_timeout(self) -> None:
        # This will disable all buttons when the view times out
        for item in self.children:
            item.disabled = True
        # You might also want to edit the message to indicate it's timed out
        await self.message.edit(content="This shop view has timed out.", view=self)



def create_store_embed(items_on_page: list): # <--- Changed parameter name
    print(f"create_store_embed called with {len(items_on_page)} items for the page.")

    embed = discord.Embed(
        title="💈Shop💈",
        description="All of our beautiful items ⛏️",
        color=discord.Color.purple()
    )

    if not items_on_page: # Handle empty page (e.g., if no items fit criteria)
        embed.description = "No items available on this page."
        return embed

    # Loop directly over the items provided for this page
    for i, source_data in enumerate(items_on_page):
        print(f"Processing item index {i} on page: {source_data[0]}")
        
        # Ensure minimum length for basic item properties (adjust if your schema varies)
        if len(source_data) < 5:
            print(f"Skipping malformed item source: {source_data} (too short for basic info)")
            continue 

        name = source_data[0]
        is_collectable = source_data[1]
        value_or_effect = source_data[2]
        description = source_data[3]
        
        associated_income_sources = format_items_list(source_data[4])
        
        # Safely access higher indices using conditional checks
        income_sources_removed = format_items_list(source_data[8]) if len(source_data) > 8 and source_data[8] else None
        role_added = format_items_list(source_data[5]) if len(source_data) > 5 and source_data[5] else None
        role_removed = format_items_list(source_data[6]) if len(source_data) > 6 and source_data[6] else None
        role_required = format_items_list(source_data[7]) if len(source_data) > 7 and source_data[7] else None

        print(f"Item: {name}")

        if is_collectable:
            # If a collectable item shouldn't be shown in the shop, `continue` here
            print(f"Skipping collectable item: {name}")
            continue # This will skip adding this particular item to the embed
        else:
            value_display = f"A(n) {name} "
        
        try:
            price = float(value_or_effect)
            value_display += f"for the low low price of ${price:,.0f} "
        except ValueError:
            value_display += f"with {value_or_effect} "
        
        value_display += f"that {description} "
        
 
        parts = []
        if associated_income_sources:
            parts.append(f"which gives you {associated_income_sources} income(s)")
        
        if income_sources_removed:
            if associated_income_sources:
                parts.append(f"but takes away {income_sources_removed} income(s)")
            else:
                parts.append(f"that takes away {income_sources_removed} income(s)")

        if role_added:
            if not parts:
                parts.append(f"which gives you {role_added} role(s)")
            else:
                parts.append(f"and {role_added} role(s)")

        if role_removed:
            if not parts:
                parts.append(f"that removes {role_removed} role(s)")
            else:
                parts.append(f"but removes {role_removed} role(s)")

        if role_required:
            if not parts:
                parts.append(f"requires {role_required} role(s) to acquire")
            else:
                parts.append(f"and requires {role_required} role(s) to acquire")

        if parts:
            value_display += " ".join(parts) + ". "


        cash_emoji = ['💸', '🏦', '💰', '💶', '💵']

        embed.add_field(
            name=f"{name} " + cash_emoji[random.randint(0, len(cash_emoji) - 1)],
            value=value_display,
            inline=False
        )

    embed.set_thumbnail(url="https://www.ulisses-ebooks.de/images/8135/_product_images/397725/DeanSpencer-filler-armourmerchant.jpg")

    return embed
