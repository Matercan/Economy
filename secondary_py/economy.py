from math import log
import os
import json
import random
import time

current_script_dir = os.path.dirname(os.path.abspath(__file__))
project_root_dir = os.path.join(current_script_dir, os.pardir)

JSON_FILES_DIR = os.path.join(project_root_dir, "json_files")


class Bank:

    bank_accounts = {}
    _DATA_FILE = os.path.join(JSON_FILES_DIR, "balance.json")

    @staticmethod
    def read_balance(user_id: str = None):
        if os.path.exists(Bank._DATA_FILE): # Use the absolute path
            with open(Bank._DATA_FILE, "r") as f:
                try:
                    Bank.bank_accounts = json.load(f)
                except json.JSONDecodeError:
                    print(f"Error reading {Bank._DATA_FILE}: File might be empty or corrupted. Initializing empty.")
                    Bank.bank_accounts = {}
        else:
            print(f"Bank accounts file non-existent at {Bank._DATA_FILE}. Initializing empty.")
            Bank.bank_accounts = {}

        if user_id:
            return Bank.bank_accounts.get(user_id, {"bank": 0, "cash": 0})
        return Bank.bank_accounts

    @staticmethod
    def save_balances():
        # Ensure the directory exists before saving (optional, but good practice)
        os.makedirs(os.path.dirname(Bank._DATA_FILE), exist_ok=True)
        with open(Bank._DATA_FILE, "w") as f:
            json.dump(Bank.bank_accounts, f, indent=2)


    @staticmethod
    def addtobank(user_id: str, money):
        if user_id not in Bank.bank_accounts:
            Bank.bank_accounts[user_id] = {"bank": 0, "cash": 0}
        Bank.bank_accounts[user_id]["cash"] += money
        Bank.save_balances()

    @staticmethod
    def addcash(user_id: str, money):
        if user_id not in Bank.bank_accounts:
            Bank.bank_accounts[user_id] = {"bank": 0, "cash": money}
            Bank.save_balances()
            return
        
        Bank.bank_accounts[user_id]["cash"] += money
        Bank.save_balances()

    @staticmethod
    def addbank(user_id: str, money):
        if user_id not in Bank.bank_accounts:
            Bank.bank_accounts[user_id] = {"bank": money, "cash": 0}
            Bank.save_balances()
            return
        
        Bank.bank_accounts[user_id]["bank"] += money
        Bank.save_balances()

    @staticmethod
    def movetobank(user_id: str, money):
        if user_id not in Bank.bank_accounts:
            Bank.bank_accounts[user_id] = {"bank": money, "cash": 0}
            Bank.save_balances()
            return
        
        current_cash = Bank.bank_accounts[user_id].get("cash", 0)
        if current_cash < money:
            print(f"Error: Not enough cash to move {money} to bank. Current cash: {current_cash}")
            return
            
        Bank.addbank(user_id=user_id, money=money)
        Bank.addcash(user_id=user_id, money=-money)

    @staticmethod
    def movetocash(user_id: str, money):
        if user_id not in Bank.bank_accounts:
            Bank.bank_accounts[user_id] = {"bank": 0, "cash": money}
            Bank.save_balances()
            return
        
        current_bank = Bank.bank_accounts[user_id].get("bank", 0)
        if current_bank < money:
            print(f"Error: Not enough bank balance to move {money} to cash. Current bank: {current_bank}")
            return

        Bank.addbank(user_id=user_id, money=-money)
        Bank.addcash(user_id=user_id, money=money)

    @staticmethod
    def gettotal(user_id):
        if user_id not in Bank.bank_accounts:
            Bank.addtobank(user_id=user_id, money=0)
            Bank.save_balances()
        
        inbank = Bank.read_balance(user_id=user_id)["bank"]
        incash = Bank.read_balance(user_id=user_id)["cash"]
        return inbank + incash 

    @staticmethod
    def get_bank_total():
        Bank.read_balance() 
        return sum(acc.get("bank", 0) for acc in Bank.bank_accounts.values())

    @staticmethod
    def get_accounts_total():
        Bank.read_balance()
        return len(Bank.bank_accounts)

    @staticmethod
    def rob_bank(user_id: str, min_percent: float, max_percent: float, successchance: float):
        Bank.read_balance()
        banktotal = Bank.get_bank_total()
        
        if random.uniform(0, 100) < successchance:
            print("Succeeded")
 
            percentstolen = random.uniform(min_percent, max_percent) / 100
            amount_stolen = int(percentstolen * banktotal)

            if banktotal == 0:
                print("No money in the bank to steal.")
                return

            if user_id not in Bank.bank_accounts:
                Bank.addtobank(user_id, 0)
            Bank.bank_accounts[user_id]["bank"] += amount_stolen

            other_users_uids = [uid for uid in Bank.bank_accounts if uid != user_id]
            num_other_users = len(other_users_uids)

            if num_other_users > 0:
                steal_each = amount_stolen // num_other_users
                for uid in other_users_uids:
                    Bank.bank_accounts[uid]["bank"] = max(
                        0, Bank.bank_accounts[uid].get("bank", 0) - steal_each
                    )
            elif amount_stolen > 0:
                print("No other users to steal from.")

            Bank.save_balances()
        else:
            print("Failed")
    
    @staticmethod
    def get_richest_user_id():
        accounts = Bank.bank_accounts # Assuming this is a dict of user_id to bank balance
        total_balances = {} # Use a better name for clarity

        for user_id in accounts: # Iterate directly over user_ids
            try:
                # Initialize total balance for this user
                current_user_total = 0

                # 1. Add bank balance
                current_user_total += Bank.gettotal(user_id)

                # 2. Add offshore balances (if any)
                user_keys = Offshore.get_user_keys(user_id)
                print(user_keys)
                if user_keys: # Check if the list is not empty
                    for key in user_keys:
                        offshore_data = Offshore.get_data_from_key(key)
                        print(offshore_data)
                        if offshore_data is not None and len(offshore_data) > 2: # Ensure data exists and has a balance
                            current_user_total += offshore_data[2]
                            print(current_user_total)
                
                print(current_user_total)
                
                total_balances[user_id] = current_user_total

            except Exception as e:
                print(f"DEBUG ERROR for user {user_id}: {e}") # Include user_id for better debugging
        
        # Handle case where no accounts exist or all failed
        if not total_balances:
            return None # Or raise an exception, or return a default ID

        # Sort by balance (x[1]) in descending order
        sorted_users = sorted(
            total_balances.items(),
            key=lambda x: x[1],  # Sort by the total balance (the value)
            reverse=True         # Richest first (descending order)
        )
        
        # Return the user_id of the richest user
        # sorted_users[0] gives the tuple (user_id, balance)
        # [0] on that tuple gives the user_id
        richest_user_id = sorted_users[0][0]
        return richest_user_id



    @staticmethod
    def targetted_guillotine(target_id: str):
        Bank.read_balance() # Makes sure everything is loaded

        # 1. Identify the balance of the target user and store it
        target_wealth_to_distribute = Bank.gettotal(target_id) # Corrected variable name
        
        # Handle the case where they have no money to distribute
        if target_wealth_to_distribute <= 0:
            print("Everyone has no money or target has no money to distribute.")
            return

        # Determine the recipients
        all_account_ids = list(Bank.bank_accounts.keys())
        recipient_ids = [uid for uid in all_account_ids if uid != target_id]
        num_recipients = len(recipient_ids)
        
        # Handle the case where there are no other recipients
        if num_recipients <= 0:
            print("There are no other people to distribute wealth to.")
            # Zero out the target's wealth even if no recipients
            Bank.bank_accounts[target_id]["cash"] = 0
            Bank.bank_accounts[target_id]["bank"] = 0
            Bank.save_balances()
            return

        # 2. Zero out the target's wealth
        Bank.bank_accounts[target_id]["cash"] = 0
        Bank.bank_accounts[target_id]["bank"] = 0

        # 3. Calculate the share each other member receives
        money_per_recipients = target_wealth_to_distribute / num_recipients

        # Distribute the money
        for user_id_distribute in recipient_ids:
            Bank.addbank(user_id_distribute, money_per_recipients)

        Bank.save_balances()
        # Corrected f-string formatting: .sf -> .2f
        print(f"Guillotined {target_id} (wealth: {target_wealth_to_distribute:,.2f}) and distributed {money_per_recipients:,.2f} to {num_recipients} other members")

class Income:
    
    PLAYER_DATA_FILE = os.path.join(JSON_FILES_DIR, "playerincomes.json")
    SOURCES_DATA_FILE = os.path.join(JSON_FILES_DIR, "incomesources.json")

    income_sources = []
    playerincomes = {}

    @staticmethod
    def create_sources():
        try:
            Income.income_sources = Income.loadsources()
        except FileNotFoundError:
            print("incomesources.json not found. Initializing with empty list.")
            Income.income_sources = []

        if not Income.income_sources:
            for _ in range(5):
                Income.income_sources.append([0, 0, 0, 0, 0])
        
        Income.savesources()

    @staticmethod
    def loadsources():
        if os.path.exists(Income.SOURCES_DATA_FILE):
            with open(Income.SOURCES_DATA_FILE, "r") as f:
                return json.load(f)
        else:
            raise FileNotFoundError("incomesources.json not found.")

    @staticmethod
    def savesources():
        with open(Income.SOURCES_DATA_FILE, "w") as f:
            json.dump(Income.income_sources, f, indent=2)

    @staticmethod
    def loadincomes():
        if os.path.exists(Income.PLAYER_DATA_FILE):
            with open(Income.PLAYER_DATA_FILE, "r") as f:
                return json.load(f)
        else:
            return {}
    
    @staticmethod
    def saveincomes():
        with open(Income.PLAYER_DATA_FILE, "w") as f:
            json.dump(Income.playerincomes, f, indent=2)

    @staticmethod
    def readincomes(user_id: str, income_type: str): 
        if not Income.playerincomes:
            Income.playerincomes = Income.loadincomes()

        user_data = Income.playerincomes.get(user_id)

        if user_data:
            income_data = user_data.get(income_type)
            
            if income_data:
                index_value = income_data.get("index", 0)
                since_value = income_data.get("since", 0.0)
                return {"index": index_value, "since": since_value}
            else:
                return {"index": -1, "since": 0.0}
        else:
            return {"index": -1, "since": 0.0}

    @staticmethod
    def read_source(rw: int = None, collum: int = None):
        if not Income.income_sources:
            Income.create_sources()

        if collum is None and rw is not None:
            if 0 <= rw < len(Income.income_sources):
                return Income.income_sources[rw]
            else:
                print(f"Error: Row {rw} is out of bounds.")
                return None
        elif rw is None and collum is not None:
            result = []
            for row in Income.income_sources:
                if 0 <= collum < len(row):
                    result.append(row[collum])
                else:
                    result.append(None)
            return result
        elif rw is not None and collum is not None:
            if 0 <= rw < len(Income.income_sources) and 0 <= collum < len(Income.income_sources[rw]):
                return Income.income_sources[rw][collum]
            else:
                print(f"Error: Row {rw} or Collum {collum} is out of bounds.")
                return None
        else:
            return Income.income_sources

    @staticmethod
    def replace_source(row: int, collum: int, val: float):
        if not Income.income_sources:
            Income.create_sources()

        if 0 <= row < len(Income.income_sources) and 0 <= collum < len(Income.income_sources[row]):
            Income.income_sources[row][collum] = val
            Income.savesources()
        else:
            print(f"Error: Cannot replace source. Row {row} or Collum {collum} is out of bounds.")

    @staticmethod
    def create_source(name: str, interest: bool, value: float, cooldown: float, bank: bool):
        if not Income.income_sources:
            Income.create_sources()

        for row in Income.income_sources:
            if row[0] == name:
                print(f"Source '{name}' already exists. Skipping creation.")
                return

        found_empty_row = False
        for i, row_data in enumerate(Income.income_sources):
            if row_data == [0, 0, 0, 0, 0]: 
                Income.income_sources[i] = [name, interest, value, cooldown, bank]
                found_empty_row = True
                break

        if not found_empty_row:
            Income.income_sources.append([name, interest, value, cooldown, bank])
        
        Income.savesources()
    
    @staticmethod
    def addtoincomes(user_id: str, source_name: str, index: int):
        if not Income.playerincomes:
            Income.playerincomes = Income.loadincomes()

        if user_id not in Income.playerincomes:
            Income.playerincomes[user_id] = {}

        Income.playerincomes[user_id][source_name] = {
            "index": index,
            "since": time.time()
        }

        Income.saveincomes()

    @staticmethod
    def removefromincomes(user_id: str, source_name: str):
        if not Income.playerincomes:
            Income.playerincomes = Income.loadincomes()

        if user_id not in Income.playerincomes:
            Income.playerincomes[user_id] = {}

        del Income.playerincomes[user_id][source_name]

        Income.saveincomes()

    @staticmethod
    def collectincomes(user_id: str):
        Income.loadincomes() # Load player incomes (crucial for latest timestamps)
        Income.create_sources() # Ensure income sources are loaded

        # Get the dictionary of incomes for this user (e.g., {"Work": {"index": 0, "since": X}})
        user_incomes_data = Income.playerincomes.get(user_id, {})
        collection_messages = []

        if not user_incomes_data: # Check if the dictionary is empty
            return ["You don't have any income sources assigned."]

        # Iterate over the items (source_name and its details dictionary)
        for source_name_key, details in user_incomes_data.items():
            index = details.get("index")
            last_collected = details.get("since", 0) # Get 'since' from details dictionary

            # Validate the income source index and existence in Income.income_sources
            if index is None or not (0 <= index < len(Income.income_sources)):
                collection_messages.append(f"❌ Income source '{source_name_key}' (index {index}) is invalid or out of bounds in global sources.")
                continue
            
            income_source_data = Income.income_sources[index]
            
            # Validate the structure of the income source data (must have at least 5 elements)
            if not income_source_data or len(income_source_data) < 5:
                collection_messages.append(f"❌ Income source '{source_name_key}' at index {index} has malformed data.")
                continue

            # Extract details using their list indices
            cooldown = income_source_data[3]
            value = income_source_data[2]
            goes_to_bank = income_source_data[4] # True if goes to bank, False if cash
            is_interest = income_source_data[1] # True if it's an interest-based income

            # Determine income type string (lowercase for comparison)
            income_destination_type = "cash" if not goes_to_bank else "bank"

            time_since_last_collected = time.time() - last_collected

            if time_since_last_collected >= cooldown:
                # Perform the transaction
                if income_destination_type == "cash":
                    if is_interest and value < 1: # Assume value is a percentage (e.g., 0.05 for 5%)
                        user_cash_balance = Bank.read_balance(user_id).get("cash", 0)
                        amount_gained = user_cash_balance * value
                        Bank.addcash(user_id, amount_gained) # Pass user_id
                        collection_messages.append(f"✅ Collected `${amount_gained:,.2f}` (Interest) to bank from '{source_name_key}'!")
                    else: 
                        Bank.addcash(user_id, value) # Pass user_id
                        collection_messages.append(f"✅ Collected `${value:,.2f}` cash from '{source_name_key}'!")
                elif income_destination_type == "bank":
                    # For bank income, if 'is_interest' is true and value is a percentage, calculate it from user's current bank balance
                    if is_interest and value < 1: # Assume value is a percentage (e.g., 0.05 for 5%)
                        user_bank_balance = Bank.read_balance(user_id).get("bank", 0)
                        amount_gained = user_bank_balance * value
                        Bank.addbank(user_id, amount_gained) # Pass user_id
                        collection_messages.append(f"✅ Collected `${amount_gained:,.2f}` (Interest) to bank from '{source_name_key}'!")
                    else: # Assume value is a fixed amount for bank
                        Bank.addbank(user_id, value) # Pass user_id
                        collection_messages.append(f"✅ Collected `${value:,.2f}` to bank from '{source_name_key}'!")
                
                # Update the timestamp in the in-memory playerincomes dictionary
                details["since"] = time.time() # Correctly update the 'since' key in the details dictionary
            else:
                remaining_cooldown = cooldown - time_since_last_collected
                # Format remaining time for better display (consistent with get_user_income_status)
                m, s = divmod(remaining_cooldown, 60)
                h, m = divmod(m, 60)
                if h > 0:
                    cooldown_display = f"{int(h)}h {int(m)}m {int(s)}s"
                elif m > 0:
                    cooldown_display = f"{int(m)}m {int(s)}s"
                else:
                    cooldown_display = f"{int(s)}s"
                collection_messages.append(f"⏳ '{source_name_key}' is on cooldown. Collectable in {cooldown_display}.")
        
        Income.saveincomes() # Save the updated timestamps after all collection attempts
        return collection_messages

    @staticmethod
    def get_source_index_by_name(source_name: str):
        if not Income.income_sources:
            Income.create_sources()

        for i, source_data in enumerate(Income.income_sources):
            if source_data and source_data[0] == source_name:
                return i
        return -1
    
    @staticmethod
    def get_user_income_status(user_id: str):
        """
        Retrieves the status of all income sources assigned to a specific user,
        including their cooldown status.
        """
        Income.playerincomes = Income.loadincomes() # Ensure player incomes are loaded
        Income.create_sources() # Ensure global income sources are loaded/initialized

        user_incomes_status = [] # List to store dictionaries of income statuses
        user_assigned_incomes = Income.playerincomes.get(user_id, {}) # Correctly gets a dictionary

        if not user_assigned_incomes:
            return [] # No incomes assigned to this user

        # Iterate over the key (source_name) and value (details dictionary)
        for source_name_key, details in user_assigned_incomes.items():
            index = details.get("index")
            last_collected = details.get("since")

            # Validate the income source index and existence
            if index is None or not (0 <= index < len(Income.income_sources)):
                user_incomes_status.append({
                    "name": source_name_key, # Use the key from playerincomes if source is invalid
                    "status": "Invalid Source (index out of bounds)",
                    "details_valid": False, # Flag to indicate detailed source data is not available
                    "cooldown_remaining": 0
                })
                continue

            source_data = Income.income_sources[index]
            # Validate the structure of the income source data (must have at least 5 elements)
            if not source_data or len(source_data) < 5:
                user_incomes_status.append({
                    "name": source_name_key, # Still use the key if source data is malformed
                    "status": "Malformed Source Data",
                    "details_valid": False,
                    "cooldown_remaining": 0
                })
                continue

            # Extract details from the source definition
            # income_source_data: [name, interest, value, cooldown, bank]
            cooldown = source_data[3]
            
            time_since_last_collected = time.time() - last_collected
            
            # Determine cooldown status
            if time_since_last_collected >= cooldown:
                status = "Ready to collect!"
                cooldown_remaining = 0
            else:
                cooldown_remaining = cooldown - time_since_last_collected
                # Format remaining time for better display
                m, s = divmod(cooldown_remaining, 60)
                h, m = divmod(m, 60)
                if h > 0:
                    status = f"On cooldown ({int(h)}h {int(m)}m {int(s)}s remaining)"
                elif m > 0:
                    status = f"On cooldown ({int(m)}m {int(s)}s remaining)"
                else:
                    status = f"On cooldown ({int(s)}s remaining)"

            # Append comprehensive status for this income source
            user_incomes_status.append({
                "name": source_data[0], # Use the name from the actual source data for display
                "is_interest": source_data[1],
                "value": source_data[2],
                "cooldown": source_data[3],
                "goes_to_bank": source_data[4],
                "status": status,
                "cooldown_remaining": cooldown_remaining,
                "details_valid": True # Flag to indicate detailed source data is valid
            })
        return user_incomes_status

    @staticmethod
    def is_any_income_ready(user_id: str):
        """
        Checks if a user has at least one income source that is 'Ready to collect!'.
        Returns the dictionary of the FIRST ready income found, or None if none are ready.
        """
        all_income_statuses = Income.get_user_income_status(user_id) # Get the full list

        for income_status in all_income_statuses:
            if income_status.get("status") == "Ready to collect!":
                return income_status # Return the specific ready income data
        return None # No ready income found    
    



class Items:
    PLAYER_DATA_FILE = os.path.join(JSON_FILES_DIR, "playerinventory.json")
    SOURCES_DATA_FILE = os.path.join(JSON_FILES_DIR, "itemsources.json")

    item_sources = [] # List of item definitions: [name, is_collectible, value_or_effect, description, associated_income_source_name, role_added, role_removed, role_required]
    player_inventory = {} # {"user_id": {"item_name": index, ...}}

    @staticmethod
    def create_item_sources():
        try:
            Items.item_sources = Items.load_item_sources()
        except FileNotFoundError:
            print("itemsources.json not found. Initializing with empty list.")
            Items.item_sources = []
        
        Items.save_item_sources()

    @staticmethod
    def load_item_sources():
        if os.path.exists(Items.SOURCES_DATA_FILE):
            with open(Items.SOURCES_DATA_FILE, "r") as f:
                return json.load(f)
        else:
            raise FileNotFoundError("itemsources.json not found.")

    @staticmethod
    def save_item_sources():
        with open(Items.SOURCES_DATA_FILE, "w") as f:
            json.dump(Items.item_sources, f, indent=2)

    @staticmethod
    def create_source(name: str, is_collectible: bool, value_or_effect: any, description: str, associated_income_source_name: list = None, role_added: list = None, role_removed: list = None, role_required: list = None, associated_incomes_removed_names: list = None):
        """
        Creates a new item source, optionally linking it to an income source and roles.

        Args:
            name (str): The name of the item.
            is_collectible (bool): True if the item can be collected, False otherwise.
            value_or_effect (any): The value of the item or its effect (e.g., price, or a descriptive string).
            description (str): A brief description of the item.
            associated_income_source_name (str, optional): The name of an Income sources
                                                            that this item provides. Defaults to None.
            role_added (str, optional): The name of the role given to owners of this item. Defaults to None.
            role_removed (str, optional): The name of the role removed from the owners of this item. Defaults to None.
            role_required (str, optional): The name of the role required to own this item. Defaults to None.
            associated_incomes_removed (str, optional): The name of the incomes that it removes
        """
        if not Items.item_sources:
            Items.create_item_sources()

        for row in Items.item_sources:
            if row and row[0] == name:
                print(f"Item source '{name}' already exists. Skipping creation.")
                return

        Items.item_sources.append([name, is_collectible, value_or_effect, description, associated_income_source_name, role_added, role_removed, role_required])
        
        Items.save_item_sources()

    @staticmethod
    def get_item_source_index_by_name(item_name: str):
        if not Items.item_sources:
            Items.create_item_sources()

        for i, source_data in enumerate(Items.item_sources):
            if source_data and source_data[0] == item_name:
                return i
        return -1


    @staticmethod
    def load_player_inventory():
        if os.path.exists(Items.PLAYER_DATA_FILE):
            with open(Items.PLAYER_DATA_FILE, "r") as f:
                return json.load(f)
        else:
            return {}
 
    @staticmethod
    def correct_item_source():
        if not Items.player_inventory:
            Items.player_inventory = Items.load_player_inventory()
        
        # Ensure Bank.bank_accounts is loaded/updated
        Bank.read_balance()
        
        # Iterate through each user's bank account (to get user_id_str)
        for user_id_str in list(Bank.bank_accounts):
            # Check if the user has an inventory entry; if not, create an empty one
            if user_id_str not in Items.player_inventory:
                Items.player_inventory[user_id_str] = {}
            
            # Get the list of item names for the current user
            current_user_items_keys = list(Items.player_inventory[user_id_str].keys())

            # Iterate through each item name in the user's inventory
            for item_name in current_user_items_keys:
                # Assign the correct source index to the item in the player's inventory
                # This is the critical fix: use '=' for assignment
                correct_index = Items.get_item_source_index_by_name(item_name)
                if correct_index != -1: # Add a check in case item name isn't found
                    Items.player_inventory[user_id_str][item_name] = correct_index
                else:
                    del Items.player_inventory[user_id_str][item_name]
                    print(f"Warning: Item '{item_name}' not found in item sources for user {user_id_str}. Skipping update for this item.")
                    # You might want to handle this differently, e.g., remove the item, log an error.
        
        Items.save_player_inventory()

    @staticmethod
    def save_player_inventory():
        with open(Items.PLAYER_DATA_FILE, "w") as f:
            json.dump(Items.player_inventory, f, indent=2)

    @staticmethod
    def addtoitems(user_id: str, item_name: str):
        """
        Adds an item to a user's inventory and automatically adds any associated income source.

        Args:
            user_id (str): The ID of the user.
            item_name (str): The name of the item to add.
        """
        if not Items.player_inventory:
            Items.player_inventory = Items.load_player_inventory()

        Items.correct_item_source()

        if not Items.item_sources:
            Items.create_item_sources() # Ensure item sources are loaded to find item details

        item_index = Items.get_item_source_index_by_name(item_name)
        if item_index == -1:
            print(f"Error: Item '{item_name}' not found in item sources. Cannot add to inventory.")
            return

        # Get the full item source data
        item_source_data = Items.item_sources[item_index]
        
        # Ensure the item_source_data has enough elements to check for associated income
        if len(item_source_data) > 4: # index 4 is for associated_income_source_name
            associated_income_source_name = item_source_data[4]
            
        else:
            associated_income_source_name = None # No associated income defined for this item
        if len(item_source_data) > 8:
            associated_income_source_removed = item_source_data[8]
        else:
            associated_income_source_removed = None

        if user_id not in Items.player_inventory:
            Items.player_inventory[user_id] = {}

        # Add the item to the user's inventory

        Items.player_inventory[user_id][item_name] = item_index
        Items.save_player_inventory()
        print(f"Item '{item_name}' added to {user_id}'s inventory.")

        # If there's an associated income source, add it to the user's incomes
        if associated_income_source_name:
            for source in associated_income_source_name:
                income_source_index = Income.get_source_index_by_name(source)
                if income_source_index != -1:
                    Income.addtoincomes(user_id, Income.read_source(income_source_index, 0), income_source_index)
                    print(f"Automatically added income source '{Income.read_source(income_source_index, 0)}' to {user_id}.")
                else:
                    print(f"Warning: Associated income source '{Income.read_source(income_source_index, 0)}' for item '{item_name}' not found.")
        if associated_income_source_removed:
            for source in associated_income_source_removed:
                print(source)
                income_source_index = Income.get_source_index_by_name(source)
                if income_source_index != -1:
                    print(f"Well {source} exists??")
                    Income.removefromincomes(user_id, source)
                    print(f"Automatically removed income source '{Income.read_source(income_source_index, 0)}' from {user_id}")
                else:
                    print(f"Automatically removed income source '{Income.read_source(income_source_index, 0)}' for item '{item_name}' not found")

    @staticmethod
    def buyitem(user_id: str, index: int):
        try:
            # Get the item's data using the provided index
            item_data = Items.item_sources[index]
            item_name = item_data[0] # Item name is at index 0
            item_price = item_data[2] # Item price/value is at index 2
            print(item_data) 
            print(f"Item price: {item_price}") 

            if Bank.read_balance(user_id=user_id)["cash"] >= item_price: # Use >= for sufficient funds
                Items.addtoitems(user_id=user_id, item_name=item_name) # Pass the string name
                Bank.addcash(user_id=user_id, money=-item_price)
                print(f"User {user_id} purchased '{item_name}' for {item_price} cash.")
            elif Bank.gettotal(user_id=user_id) >= item_price: # If total amount of money user has is greater than cost
                print(f"User {user_id} has enough total money but needs to withdraw {item_price - Bank.read_balance(user_id=user_id)['cash']} cash from bank first to buy '{item_name}'.")
            else:
                print(f"User '{user_id}' does not have enough money to purchase '{item_name}'. Cost: {item_price}, Current Cash: {Bank.read_balance(user_id=user_id)['cash']}, Total: {Bank.gettotal(user_id=user_id)}")
        except (TypeError, IndexError) as e: # Catch IndexError if index is out of bounds
            # Check if the error is due to non-numeric price
            if isinstance(e, TypeError) and (isinstance(item_price, str) or item_price is None):
                print(f"Item '{item_name}' does not have a valid numeric pricetag (value was {item_price}).")
            else:
                print(f"An error occurred while buying item at index {index}: {e}")
                print(f"Debug: Item source data might be malformed at index {index}. Current item_sources length: {len(Items.item_sources)}")

    @staticmethod
    def read_item_index(user_id: str, item_name: str):
        if not Items.player_inventory:
            Items.player_inventory = Items.load_player_inventory()

        Items.correct_item_source()
        user_items = Items.player_inventory.get(user_id, {})
        item_index = user_items.get(item_name, -1)
        return item_index

    @staticmethod
    def get_user_items(user_id: str):
        if not Items.player_inventory:
            Items.player_inventory = Items.load_player_inventory()
        Items.correct_item_source()
        return Items.player_inventory.get(user_id, {})
    
    @staticmethod
    def removefromitems(user_id: str, item_name: str, quantity: int = 1) -> bool:
        """
        Removes a specified quantity of an item from a user's inventory.
        Returns True if removal was successful, False otherwise (e.g., not enough items).
        """
        Items.load_player_inventory() # Ensure inventory is loaded
        Items.correct_item_source()

        if user_id not in Items.player_inventory:
            print(f"DEBUG: User {user_id} has no inventory.")
            return False # User has no inventory
        
        item_key = item_name[0].capitalize() + item_name[1:] # Use lowercased key for lookup and consistency
        print(item_key)
        print(Items.player_inventory[user_id])

        if item_key not in Items.player_inventory[user_id]:
            print(f"DEBUG: Item '{item_name}' not found for user {user_id}.")
            return False # Item not in inventory
        
        del Items.player_inventory[user_id][item_name]
        print(f"DEBUG: Removed '{item_name}' from {user_id}'s inventory as count reached 0.")
            
        Items.save_player_inventory()
        Items.correct_item_source()
        return True
        
    @staticmethod
    def generate_user_specific_item(user_id: str, item_index: int, value_effect):
        item_name = ""
        letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g',
                       'h', 'i', 'j', 'k', 'l', 'm', 'n',
                       'o', 'p', 'q', 'r', 's', 't', 'u',
                       'v', 'w', 'x', 'y', 'z']


        for letter in letters:
            item_name += letters[((random.randint(0, item_index) + random.randint(0, 26)) % 26) - 1]
            print(((random.randint(0, item_index) + random.randint(0, 26)) % 26) - 1)
            if random.randint(0, random.randint(1, 8)) == 7:
                break
                            
        Items.create_source(item_name, True, value_effect, f"{user_id}'s {Items.item_sources[item_index][0]}")
        Items.addtoitems(user_id, item_name)
        Items.save_item_sources()
        Items.save_player_inventory()
        

class Offshore:
    
    DATA_PATH = os.path.join(JSON_FILES_DIR, "offshore.json")
    balances = [] 

    # Balances will be stored as follows: [key (lets things interact with it), interest, startbalance, lastupdate]
    # The amount of money in the balance will be calculated as a geometric series
    # The amount of money will be calculated everytime we update the account whether it be by withdrawing or depositing
    # The amount of interest will be calculated based on this formula: 1 + 9log_10(balance)days / 20 so that an account with 10K for 10 years will yield a 10% interest rate
    # The interest can never reduce

    @staticmethod
    def load_balances():
        if os.path.exists(Offshore.DATA_PATH):
            with open(Offshore.DATA_PATH, "r") as f:
                Offshore.balances = json.load(f)
        else:
            Offshore.balances = []

    @staticmethod
    def save_balances():
        if os.path.exists(Offshore.DATA_PATH):
            with open(Offshore.DATA_PATH, "w") as f:
                json.dump(Offshore.balances, f, indent=2)


    @staticmethod
    def clear_balance():
        print("Starting clear_balance process...")
        Offshore.load_balances() # Make sure this loads Offshore.balances (a list of tuples)
        Items.load_item_sources() # Make sure this loads Items.item_sources (a list of lists/tuples for item definitions)
        Items.player_inventory = Items.load_player_inventory() # Make sure this loads Items.player_inventory (dict of dicts)
        
        Bank.read_balance() # Ensure Bank.bank_accounts is up-to-date (list of tuples)

        # --- Phase 1: Identify and Remove Redundant Offshore Accounts and their Item Sources ---
        print("Phase 1: Clearing redundant offshore accounts...")
        valid_offshore_keys = []
        
        # Collect all valid offshore keys from actual user inventories
        for user_id_str in list(Bank.bank_accounts): # Bank.bank_accounts contains (money, user_id_str)
            user_id = user_id_str  
            user_offshore_keys = Offshore.get_user_keys(user_id) # This should return a list of keys for this user
            for key in user_offshore_keys:
                valid_offshore_keys.append(key)

        print(valid_offshore_keys)
        # Prepare new lists for Offshore.balances and Items.item_sources
        new_offshore_balances = []
        offshore_keys_to_remove_from_item_sources = set()
        

        for account_key in [account[0] for account in Offshore.balances]: # Iterate through current balances
            if account_key in valid_offshore_keys:
                new_offshore_balances.append(Offshore.get_data_from_key(account_key))
            else:
                # This offshore account key is redundant, mark its corresponding item source for deletion
                offshore_keys_to_remove_from_item_sources.add(account_key)
                print(f"Marked redundant offshore account: {account_key}")

        Offshore.balances = new_offshore_balances # Replace with the filtered list
        

        # Filter Items.item_sources based on whether it has 'S offshore bank accoutn in the name, and is not within the Offshore.new_offshore_balances
 

        new_item_sources = []
        for item_source_data in Items.item_sources:
            print(f"Item data 3 for {item_source_data[0]}: {item_source_data[3]}")
            if len(item_source_data) > 0 and item_source_data[0]:
                # Check if this item is one of the redundant offshore account items
                if item_source_data[0] not in valid_offshore_keys:
                    print(f"{item_source_data[0]} not in valid offshore keys")
                if "'s Offshore bank account" in item_source_data[3] and item_source_data[0] not in valid_offshore_keys:
                    print(f"Removing redundant item source for offshore account: {item_source_data[0]}")
                    continue # Skip adding this item source to the new list
            new_item_sources.append(item_source_data)
        
        Items.item_sources = new_item_sources # Replace with the filtered list

        # --- Phase 2: Clear redundant Items from player_inventory ---
        print("Phase 2: Clearing redundant items from player inventories...")
        # Create a copy of player_inventory to modify
        new_player_inventory = {}

        # First, gather all existing user_ids from bank accounts
        all_present_user_ids = list(Bank.bank_accounts) 

        for user_id_str, user_items_dict in Items.player_inventory.items():
            if user_id_str not in all_present_user_ids:
                print(f"Removing inventory for user {user_id_str} as they are not in bank accounts.")
                continue # Skip this user's inventory entirely

            # Create a new dictionary for the current user's valid items
            new_user_items_dict = {}
            for item_name, item_index in user_items_dict.items():
                # Check if the item_name exists in the current Items.item_sources
                # Assuming Items.get_item_source_index_by_name can handle non-existent names by returning None
                if Items.get_item_source_index_by_name(item_name) is not None:
                    # Item exists in global sources, keep it
                    new_user_items_dict[item_name] = item_index
                else:
                    print(f"Removing non-existent item '{item_name}' from {user_id_str}'s inventory.")
            
            new_player_inventory[user_id_str] = new_user_items_dict
        
        Items.player_inventory = new_player_inventory # Replace with the cleaned inventory


        # --- Phase 3: Final cleanup and Save ---
        print("Phase 3: Finalizing and saving...")
        Items.correct_item_source() # Re-index all existing items

        Offshore.save_balances()
        Items.save_item_sources()
        Items.save_player_inventory()
        print("clear_balance process complete.")

    @staticmethod
    def calculate_interest(account: list) -> float:
        if len(account) < 4:
            print("ERROR: malformed offshore bank account")
            print(account)
            return -1
        
        if account[2] == 0:
            account[2] = 1

        days = (time.time() - account[3]) / 86400
        print(days)
        amount = account[2]
        print(amount)
        log_amount = log(amount, 10)
        print(log_amount)
        log_days = log(days, 10) + 1 if days > 0 else 1
        print(log_days)
        multiplier = 9 / 20

        print(log_days * log_amount * multiplier)
        return log_days * log_amount * multiplier

    @staticmethod
    def calculate_balance(account: list) -> float:
        if len(account) < 4:
            print("ERROR: malformed offshore bank account")
            print(account)
            return -1
        
        multiplier = 1 + account[1] / 100
        return account[2] * pow(multiplier, (time.time() - account[3]) / 86400)

    @staticmethod
    def generate_account(user_id: str, balance: float) -> str:
        
        Items.generate_user_specific_item(user_id, Items.get_item_source_index_by_name("Offshore bank account"), balance)
        balanceKey = Items.item_sources[len(Items.item_sources) - 1][0]
        interest = log(balance, 10) / 2

        Offshore.balances.append([balanceKey, interest, balance, time.time()]) 
        Offshore.save_balances()
        Items.save_player_inventory()
        Items.save_item_sources()
        return balanceKey

    @staticmethod
    def update_account(index: int):
        
        account = Offshore.balances[index]
        print(f"Updating account: {account}")

        if len(account) < 4:
            print("Error: malformed offshore bank account")
            print(account)
            return

        interest = Offshore.calculate_interest(account)
        
        if account[1] <= interest: account[1] = interest
        account[3] = time.time()
        
        Offshore.balances[index] = account
        Offshore.save_balances()
    
    @staticmethod
    def get_index_from_key(key: str) -> int:
        balance = ([], 0)

        i = 0
        for account in Offshore.balances:
            if account[0] == key:
                balance = (account, i)
                break
            i += 1
        

        if len(balance[0]) < 4:
            print("Error: malformed offshore bank account")
            print(balance)
            return -1

        return i


    @staticmethod
    def withdraw(key: str, amount: float, user_id: str):

        balance = ([], 0)
        i = 0

        print(f"withdraw amount: {amount}")

        for account in Offshore.balances:
            if account[0] == key:
                balance = (account, i)
                break
            i += 1
        
        print(f"INDEX: {i}")

        if len(balance[0]) < 4:
            print("Error malformed offshore bank account")
            print(balance)
            return

        print(f"START BALANCE: {balance}")
        balance[0][2] -= amount
        Bank.addbank(user_id, amount)
        Items.item_sources[Items.get_item_source_index_by_name(balance[0][0])][2] = balance[0][2]
        Offshore.balances[i] = balance[0]
        print(f"END BALANCE: {balance}")
        Offshore.update_account(i)
        Offshore.save_balances()
        Items.save_item_sources()
        
    @staticmethod
    def deposit(key: str, amount: float, user_id: str):
        balance = ([], 0)
        i = 0
        
        print(f"deposit  amount: {amount}")

        for account in Offshore.balances:
            if account[0] == key:
                balance = (account, i)
                break
            i += 1
        
        print(i)

        if len(balance[0]) < 4:
            print("Error: malformed offshore bank account")
            print(balance)
            return

        print(f"START BALANCE: {balance}") 
        balance[0][2] += amount
        Bank.addbank(user_id, -amount)
        Items.item_sources[Items.get_item_source_index_by_name(balance[0][0])][2] = balance[0][2]
        print(f"END BALANCE: {balance}")
        Offshore.update_account(balance[1]) 
        Offshore.save_balances()
        Items.save_item_sources()

    @staticmethod
    def get_data_from_key(key: str):
        balance = []

        for account in Offshore.balances:
            if account[0] == key:
                balance = account

        return balance

    @staticmethod
    def get_user_keys(user_id: str):
        keys = []

        for item in Items.get_user_items(user_id):
            # print(f"ITEM: {Items.get_user_items(user_id)[item]}")
            index = Items.get_item_source_index_by_name(item)
            if not Items.item_sources[index][1]:
                print("Continuing")
                continue
            
            for account in Offshore.balances:
                # print(item)
                # print(account[0])
                if item == account[0]:
                    keys.append(account[0])
        
        # print(f"KEYS: {keys}")
        return keys

    @staticmethod
    def get_accounts_from_keys(keys: list):
        accounts = []

        for key in keys: accounts.append(Offshore.get_data_from_key(key))
        return accounts

    @staticmethod
    def update_accounts_from_keyes(keys: list):
        for key in keys:
            print(f"key updating: {key}")
            Offshore.update_account(Offshore.get_index_from_key(key))

def main():
    print("Expected all files should be in cwd/json_files/<file>")
    print(f"Balances data file: {Bank._DATA_FILE}")
    if os.path.exists(Bank._DATA_FILE):
        print("Bank data file exists")
    else:
        print("Bank data file does not exist")


    print(f"Income data files: {Income.SOURCES_DATA_FILE}, {Income.PLAYER_DATA_FILE}")
    if os.path.exists(Income.SOURCES_DATA_FILE):
        print("Income sources data file exists")
    else:
        print("Income sources data file does not exist")
    if os.path.exists(Income.PLAYER_DATA_FILE):
        print("Player incomes data file exists")
    else:
        print("Player incomes data file does not exist")
    
    print(f"Inventory data files: {Items.SOURCES_DATA_FILE}, {Items.PLAYER_DATA_FILE}")
    if os.path.exists(Items.SOURCES_DATA_FILE):
        print("Item sources data file exists")
        Items.load_item_sources()
        print(Items.item_sources)
    else:
        print("Item sources data does not exist")
    if os.path.exists(Items.PLAYER_DATA_FILE):
        print("Player inventory data file exists")
        Items.load_player_inventory()
        print(Items.player_inventory)
    else:
        print("Player inventory data file does not exist")

    print(f"Offshore data file: {Offshore.DATA_PATH}")
    if os.path.exists(Offshore.DATA_PATH):
        print("Offshore data file exists")
    else:
        print("Offshore data does not exist")

if __name__ == '__main__':
    main()
