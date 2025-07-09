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
    def guillotine():
        Bank.read_balance()

        # 1. Identify the richest and store their total wealth to be distributed
        richest_user_id_str = Bank.get_richest_user_id()
        richest_total_wealth_to_distribute = Bank.gettotal(richest_user_id_str)

        # Handle case where richest has no money to distribute
        if richest_total_wealth_to_distribute <= 0:
            print(f"Richest member ({richest_user_id_str}) has no wealth to distribute.")
            return

        # Determine the recipients (all members except the richest)
        all_account_ids = list(Bank.bank_accounts.keys())
        recipients_ids = [uid for uid in all_account_ids if uid != richest_user_id_str]
        num_recipients = len(recipients_ids)

        # If there are no other members to distribute to, just zero out the richest
        if num_recipients <= 0:
            print("Not enough other accounts to distribute wealth. Zeroing out richest only.")
            Bank.bank_accounts[richest_user_id_str]["cash"] = 0
            Bank.bank_accounts[richest_user_id_str]["bank"] = 0
            Bank.save_balances()
            return

        # 2. Zero out the richest member's account *before* distribution
        Bank.bank_accounts[richest_user_id_str]["cash"] = 0
        Bank.bank_accounts[richest_user_id_str]["bank"] = 0

        # 3. Calculate the share each other member receives
        money_per_recipient = richest_total_wealth_to_distribute / num_recipients

        # 4. Distribute money to all other accounts
        for user_id_distribute in recipients_ids:
            # Add the money to their bank account (or cash, depending on desired outcome)
            # Adding to bank is consistent with your original code's intent
            Bank.addbank(user_id_distribute, money_per_recipient)

        Bank.save_balances() # Save all changes after distribution
        print(f"Guillotined {richest_user_id_str} (wealth: {richest_total_wealth_to_distribute:,.2f}) and distributed {money_per_recipient:,.2f} to {num_recipients} other members.")

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

    item_sources = [] # List of item definitions: [name, is_collectible, value_or_effect, description, associated_income_source_name, role_added, role_removed, role_required, associated_incomes_removed_names]
    # New structure for player_inventory:
    # {"user_id": {"item_name": {"index": index, "quantity": quantity}, ...}}
    player_inventory = {}

    @staticmethod
    def create_item_sources():
        try:
            Items.item_sources = Items.load_item_sources()
        except FileNotFoundError:
            print(f"{Items.SOURCES_DATA_FILE} not found. Initializing with empty list.")
            Items.item_sources = []
        Items.save_item_sources()

    @staticmethod
    def load_item_sources():
        if os.path.exists(Items.SOURCES_DATA_FILE):
            with open(Items.SOURCES_DATA_FILE, "r") as f:
                return json.load(f)
        else:
            raise FileNotFoundError(f"{Items.SOURCES_DATA_FILE} not found.")

    @staticmethod
    def save_item_sources():
        with open(Items.SOURCES_DATA_FILE, "w") as f:
            json.dump(Items.item_sources, f, indent=2)

    @staticmethod
    def create_source(name: str, is_collectible: bool, value_or_effect: any, description: str, associated_income_source_names: list = None, role_added: list = None, role_removed: list = None, role_required: list = None, associated_incomes_removed_names: list = None):
        """
        Creates a new item source, optionally linking it to income sources and roles.

        Args:
            name (str): The name of the item.
            is_collectible (bool): True if the item can be collected, False otherwise.
            value_or_effect (any): The value of the item or its effect (e.g., price, or a descriptive string).
            description (str): A brief description of the item.
            associated_income_source_names (list, optional): List of names of Income sources this item provides. Defaults to None.
            role_added (list, optional): List of names of roles given to owners of this item. Defaults to None.
            role_removed (list, optional): List of names of roles removed from the owners of this item. Defaults to None.
            role_required (list, optional): List of names of roles required to own this item. Defaults to None.
            associated_incomes_removed_names (list, optional): List of names of incomes that this item removes. Defaults to None.
        """
        if not Items.item_sources:
            Items.create_item_sources()

        for row in Items.item_sources:
            if row and row[0] == name:
                print(f"Item source '{name}' already exists. Skipping creation.")
                return

        Items.item_sources.append([
            name,
            is_collectible,
            value_or_effect,
            description,
            associated_income_source_names if associated_income_source_names is not None else [], # Ensure list
            role_added if role_added is not None else [], # Ensure list
            role_removed if role_removed is not None else [], # Ensure list
            role_required if role_required is not None else [], # Ensure list
            associated_incomes_removed_names if associated_incomes_removed_names is not None else [] # Ensure list
        ])
        
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
                loaded_data = json.load(f)
            
            # --- MIGRATION LOGIC ---
            migrated_data = {}
            for user_id, user_items in loaded_data.items():
                migrated_data[user_id] = {}
                for item_name, item_value in user_items.items():
                    if isinstance(item_value, dict) and "index" in item_value and "quantity" in item_value:
                        # Already in new format
                        migrated_data[user_id][item_name] = item_value
                    else:
                        # Old format: {"item_name": index}
                        # Assume quantity is 1 for migrated items
                        # Ensure the index is actually an integer
                        try:
                            index = int(item_value)
                            migrated_data[user_id][item_name] = {"index": index, "quantity": 1}
                            print(f"Migrated item '{item_name}' for user {user_id} to new format with quantity 1.")
                        except (ValueError, TypeError):
                            print(f"WARNING: Skipping malformed item '{item_name}' (value: {item_value}) for user {user_id} during migration.")
            Items.player_inventory = migrated_data
            Items.save_player_inventory() # Save the migrated data
            return Items.player_inventory
        else:
            return {} # Return empty dict if file doesn't exist
    
    # Renamed and refactored the old correct_item_source
    @staticmethod
    def _ensure_inventory_consistency():
        """
        Ensures all items in player_inventory have correct indices based on item_sources
        and removes items whose sources no longer exist.
        This function is primarily for cleanup and should be called less frequently
        than load_player_inventory (e.g., on bot startup or periodically).
        """
        if not Items.item_sources:
            Items.create_item_sources() # Ensure item sources are loaded

        if not Items.player_inventory:
            Items.player_inventory = Items.load_player_inventory()

        users_to_remove_if_empty = []
        for user_id_str, user_items_data in Items.player_inventory.items():
            items_to_remove = []
            for item_name, item_info in user_items_data.items():
                correct_index = Items.get_item_source_index_by_name(item_name)
                
                # Check if item_info is a dict and has 'index' and 'quantity'
                if not isinstance(item_info, dict) or "index" not in item_info or "quantity" not in item_info:
                    print(f"WARNING: Malformed item data for '{item_name}' for user {user_id_str}. Removing item.")
                    items_to_remove.append(item_name)
                    continue

                if correct_index == -1:
                    print(f"Warning: Item '{item_name}' not found in item sources for user {user_id_str}. Removing from inventory.")
                    items_to_remove.append(item_name)
                elif item_info["index"] != correct_index:
                    print(f"Correction: Updating index for '{item_name}' for user {user_id_str} from {item_info['index']} to {correct_index}.")
                    item_info["index"] = correct_index
            
            for item_name in items_to_remove:
                del user_items_data[item_name]
            
            if not user_items_data: # If user has no items left after cleanup
                users_to_remove_if_empty.append(user_id_str)
        
        for user_id_str in users_to_remove_if_empty:
            del Items.player_inventory[user_id_str]
            print(f"Removed empty inventory for user {user_id_str}.")

        Items.save_player_inventory()


    @staticmethod
    def save_player_inventory():
        with open(Items.PLAYER_DATA_FILE, "w") as f:
            json.dump(Items.player_inventory, f, indent=2)

    @staticmethod
    def addtoitems(user_id: str, item_name: str, quantity: int = 1):
        """
        Adds an item (or quantity of an item) to a user's inventory
        and automatically handles any associated income/role changes.

        Args:
            user_id (str): The ID of the user.
            item_name (str): The name of the item to add.
            quantity (int): The quantity to add. Defaults to 1.
        """
        if not Items.player_inventory:
            Items.player_inventory = Items.load_player_inventory()
        
        if not Items.item_sources:
            Items.create_item_sources() # Ensure item sources are loaded

        item_index = Items.get_item_source_index_by_name(item_name)
        if item_index == -1:
            print(f"Error: Item '{item_name}' not found in item sources. Cannot add to inventory.")
            return

        item_source_data = Items.item_sources[item_index]
        
        # Call the dedicated add_item_to_inventory method
        Items.add_item_to_inventory(user_id, item_name, item_index, quantity)
        Items.save_player_inventory()
        print(f"Item '{item_name}' (x{quantity}) added to {user_id}'s inventory.")

        # Handle associated incomes/roles (based on your existing logic)
        # Ensure your item_source_data has consistent length or use .get() for safety
        associated_income_source_names = item_source_data[4] if len(item_source_data) > 4 else []

        # role_required = item_source_data[7] if len(item_source_data) > 7 else [] # role_required is a pre-condition, not an effect of adding
        associated_incomes_removed_names = item_source_data[8] if len(item_source_data) > 8 else []
        
        # Add associated incomes
        for source_name in associated_income_source_names:
            income_source_index = Income.get_source_index_by_name(source_name)
            if income_source_index != -1:
                Income.addtoincomes(user_id, source_name, income_source_index)
                print(f"Automatically added income source '{source_name}' to {user_id}.")
            else:
                print(f"Warning: Associated income source '{source_name}' for item '{item_name}' not found.")

        # Remove associated incomes
        for source_name in associated_incomes_removed_names:
            income_source_index = Income.get_source_index_by_name(source_name) # You might not need index for remove, but for validation
            if income_source_index != -1: # Check if source exists before attempting to remove
                Income.removefromincomes(user_id, source_name)
                print(f"Automatically removed income source '{source_name}' from {user_id}.")
            else:
                print(f"Warning: Associated income source to be removed '{source_name}' for item '{item_name}' not found.")


    @staticmethod
    def removefromitems(user_id: str, item_name: str, quantity: int = 1):
        """
        Removes an item (or quantity of an item) from a user's inventory
        and automatically handles any associated income/role changes
        if the item quantity drops to zero.

        Args:
            user_id (str): The ID of the user.
            item_name (str): The name of the item to remove.
            quantity (int): The quantity to remove. Defaults to 1.
        """
        if not Items.player_inventory:
            Items.player_inventory = Items.load_player_inventory()

        if user_id not in Items.player_inventory or item_name not in Items.player_inventory[user_id]:
            print(f"Warning: User {user_id} does not have item '{item_name}' to remove.")
            return

        current_quantity = Items.player_inventory[user_id][item_name]["quantity"]
        
        # Call the dedicated remove_item_from_inventory method
        Items.remove_item_from_inventory(user_id, item_name, quantity)
        Items.save_player_inventory()

        # Only handle associated income/role removal if the item quantity
        # *becomes* zero or less after this removal operation.
        new_quantity = Items.get_user_item_quantity(user_id, item_name) # Get updated quantity
        
        if current_quantity > 0 and new_quantity <= 0: # Item was present and now it's gone
            item_index = Items.get_item_source_index_by_name(item_name)
            if item_index != -1:
                item_source_data = Items.item_sources[item_index]
                associated_income_source_names = item_source_data[4] if len(item_source_data) > 4 else []
                associated_incomes_removed_names = item_source_data[8] if len(item_source_data) > 8 else []

                # Remove incomes that the item granted
                for source_name in associated_income_source_names:
                    Income.removefromincomes(user_id, source_name)
                    print(f"Automatically removed income source '{source_name}' from {user_id} as item '{item_name}' is gone.")
                
                # Add incomes that the item used to suppress
                for source_name in associated_incomes_removed_names:
                    income_source_index = Income.get_source_index_by_name(source_name)
                    if income_source_index != -1:
                        Income.addtoincomes(user_id, source_name, income_source_index)
                        print(f"Automatically restored income source '{source_name}' to {user_id} as item '{item_name}' is gone.")
                



    @staticmethod
    def buyitem(user_id: str, index: int):
        if not Items.item_sources:
            Items.create_item_sources() # Ensure sources are loaded

        try:
            item_data = Items.item_sources[index]
            item_name = item_data[0]
            item_price = item_data[2] # Assuming value_or_effect is price for buyable items
 

            if Bank.read_balance(user_id=user_id)["cash"] >= item_price:
                Items.addtoitems(user_id=user_id, item_name=item_name, quantity=1) # Add 1 quantity
                Bank.addcash(user_id=user_id, money=-item_price)
                print(f"User {user_id} purchased '{item_name}' for {item_price} cash.")
            elif Bank.gettotal(user_id=user_id) >= item_price:
                print(f"User {user_id} has enough total money but needs to withdraw {item_price - Bank.read_balance(user_id=user_id)['cash']} cash from bank first to buy '{item_name}'.")
            else:
                print(f"User '{user_id}' does not have enough money to purchase '{item_name}'. Cost: {item_price}, Current Cash: {Bank.read_balance(user_id=user_id)['cash']}, Total: {Bank.gettotal(user_id=user_id)}")
        except (TypeError, IndexError) as e:
            item_name = "Unknown Item" # Default if item_data fails
            if index < len(Items.item_sources):
                item_name = Items.item_sources[index][0]
            print(f"An error occurred while buying item at index {index} ('{item_name}'): {e}")
            print(f"Debug: Item source data might be malformed at index {index}. Current item_sources length: {len(Items.item_sources)}")


    @staticmethod
    def read_item_index(user_id: str, item_name: str):
        """
        Retrieves the index of a specific item for a user.
        This now calls get_user_item_index directly.
        """
        # Ensure player_inventory is loaded
        if not Items.player_inventory:
            Items.player_inventory = Items.load_player_inventory()
        
        return Items.get_user_item_index(user_id, item_name)
    
    # Existing get_user_item_indexes (already migrated)
    @staticmethod
    def get_user_item_indexes(user_id: str) -> dict[str, int]:
        if not Items.player_inventory:
            Items.player_inventory = Items.load_player_inventory()
        
        user_items_data = Items.get_user_items(user_id) 
        
        item_indexes_map = {} 
        for item_name, item_info in user_items_data.items():
            if isinstance(item_info, dict) and "index" in item_info:
                item_indexes_map[item_name] = item_info["index"]
            else:
                print(f"WARNING: Malformed item data for '{item_name}' for user {user_id}: {item_info}")
        return item_indexes_map
    
    # New helper methods (from previous response, already in your code)
    @staticmethod
    def get_user_item_data(user_id: str, item_name: str) -> dict | None:
        user_inventory = Items.player_inventory.get(user_id)
        if user_inventory:
            return user_inventory.get(item_name)
        return None

    @staticmethod
    def get_user_item_index(user_id: str, item_name: str) -> int | None:
        item_data = Items.get_user_item_data(user_id, item_name)
        if item_data:
            return item_data.get("index")
        return None

    @staticmethod
    def get_user_item_quantity(user_id: str, item_name: str) -> int:
        item_data = Items.get_user_item_data(user_id, item_name)
        if item_data:
            return item_data.get("quantity", 0)
        return 0

    @staticmethod
    def add_item_to_inventory(user_id: str, item_name: str, item_index: int, quantity: int = 1):
        if user_id not in Items.player_inventory:
            Items.player_inventory[user_id] = {}
        user_items = Items.player_inventory[user_id]
        if item_name in user_items:
            user_items[item_name]["quantity"] += quantity
        else:
            user_items[item_name] = {"index": item_index, "quantity": quantity}
        
        if user_items[item_name]["quantity"] <= 0: # Ensure cleanup if adding negative quantity
            del user_items[item_name]
            if not user_items: del Items.player_inventory[user_id]

    @staticmethod
    def remove_item_from_inventory(user_id: str, item_name: str, quantity: int = 1):
        if user_id in Items.player_inventory:
            user_items = Items.player_inventory[user_id]
            if item_name in user_items:
                user_items[item_name]["quantity"] -= quantity
                if user_items[item_name]["quantity"] <= 0:
                    del user_items[item_name]
                    if not user_items: del Items.player_inventory[user_id]
            else: print(f"Warning: Item '{item_name}' not found in {user_id}'s inventory to remove.")
        else: print(f"Warning: User '{user_id}' has no inventory to remove from.")
    
    @staticmethod
    def get_user_items(user_id: str) -> dict:
        return Items.player_inventory.get(user_id, {})

    @staticmethod
    def check_user_has_item(user_id: str, item_name: str, required_quantity: int = 1) -> bool:
        item_data = Items.get_user_item_data(user_id, item_name)
        return item_data is not None and item_data.get("quantity", 0) >= required_quantity

    @staticmethod
    def generate_user_specific_item(user_id: str, item_index: int, value_effect):
        if not Items.item_sources:
            Items.create_item_sources() # Ensure item sources are loaded

        item_name_base = Items.item_sources[item_index][0]
        generated_suffix = ""
        letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n',
                   'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']

        # Generate a random suffix for uniqueness
        for _ in range(random.randint(3, 7)): # Generate a suffix between 3 and 7 chars long
            generated_suffix += random.choice(letters)
        
        unique_item_name = f"{item_name_base} of {generated_suffix.capitalize()}" # Example: "Sword of Xyz"

        # Ensure this unique item name is added to item_sources if it doesn't exist
        # This prevents duplicate sources for dynamically generated items.
        # However, for user-specific items, you might *not* want to add them to global sources.
        # This implies a new type of item (personal/temporary) or a different way to store them.
        # For simplicity, assuming it *is* added to item_sources for now.
        if Items.get_item_source_index_by_name(unique_item_name) == -1:
            Items.create_source(unique_item_name, True, value_effect, f"{user_id}'s unique {item_name_base}")
        
        # Now, add it to the user's inventory using the correct add_item_to_inventory method
        new_item_source_index = Items.get_item_source_index_by_name(unique_item_name)
        if new_item_source_index != -1:
            Items.add_item_to_inventory(user_id, unique_item_name, new_item_source_index, quantity=1)
            Items.save_player_inventory() # Save after adding to player inventory
            print(f"Generated and added unique item '{unique_item_name}' to {user_id}'s inventory.")
        else:
            print(f"Error: Could not find source index for generated item '{unique_item_name}'. Item not added.")
        

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
        # load_player_inventory already handles the migration if needed
        Items.player_inventory = Items.load_player_inventory() 
        
        Bank.read_balance() # Ensure Bank.bank_accounts is up-to-date (dict of user_id -> balance dict)

        # --- Phase 1: Identify and Remove Redundant Offshore Accounts and their Item Sources ---
        print("Phase 1: Clearing redundant offshore accounts...")
        valid_offshore_keys = []
        
        # Collect all valid offshore keys from actual user inventories
        # Assuming Bank.bank_accounts keys are the user_id strings
        for user_id_str in list(Bank.bank_accounts.keys()): 
            user_offshore_keys = Offshore.get_user_keys(user_id_str) # This should return a list of keys for this user
            for key in user_offshore_keys:
                valid_offshore_keys.append(key)

        print(f"Valid offshore keys found across all users: {valid_offshore_keys}")

        # Prepare new list for Offshore.balances
        new_offshore_balances = []
        offshore_keys_to_remove_from_item_sources = set() # This set seems to be unused, but kept for context if it had a later purpose
        
        # Filter Offshore.balances to keep only those that are still associated with a user
        # or are otherwise considered valid.
        current_offshore_keys_in_balances = [account[0] for account in Offshore.balances] # Extract just the keys
        
        for account_key in current_offshore_keys_in_balances:
            # Get the full account data (key, user_id, balance)
            account_data = Offshore.get_data_from_key(account_key) 
            if account_data and account_key in valid_offshore_keys:
                new_offshore_balances.append(account_data)
            else:
                # This offshore account key is redundant/not found, mark its corresponding item source for deletion
                # The user-owned offshore key might no longer exist if the user was removed, or if the key itself is orphaned.
                # Here, we mark it if it's not in `valid_offshore_keys` (meaning no user has it, or it was never associated correctly)
                offshore_keys_to_remove_from_item_sources.add(account_key)
                print(f"Marked redundant offshore account for removal: {account_key}")

        Offshore.balances = new_offshore_balances # Replace with the filtered list
        
        # Filter Items.item_sources based on whether it is an offshore account item AND
        # its name (which is the key) is in the set of `offshore_keys_to_remove_from_item_sources`.
        new_item_sources = []
        for item_source_data in Items.item_sources:
            if len(item_source_data) > 0 and item_source_data[0]:
                item_name = item_source_data[0]
                item_description = item_source_data[3] if len(item_source_data) > 3 else ""

                # Check if this item source represents an offshore bank account AND
                # if its name (the key) is in our set of keys to be removed.
                if "'s Offshore bank account" in item_description and item_name in offshore_keys_to_remove_from_item_sources:
                    print(f"Removing redundant item source for offshore account: {item_name}")
                    continue # Skip adding this item source to the new list
            new_item_sources.append(item_source_data)
        
        Items.item_sources = new_item_sources # Replace with the filtered list

        # --- Phase 2: Clear redundant Items from player_inventory ---
        print("Phase 2: Clearing redundant items from player inventories...")
        # Create a copy of player_inventory to modify
        new_player_inventory = {}

        # First, gather all existing user_ids from bank accounts
        all_present_user_ids = list(Bank.bank_accounts.keys()) # Use .keys() for dict

        for user_id_str, user_items_dict in Items.player_inventory.items():
            if user_id_str not in all_present_user_ids:
                print(f"Removing inventory for user {user_id_str} as they are not in bank accounts.")
                continue # Skip this user's inventory entirely

            # Create a new dictionary for the current user's valid items
            new_user_items_dict = {}
            for item_name, item_info in user_items_dict.items(): # item_info is now {"index": X, "quantity": Y}
                # Check if the item_name exists in the current Items.item_sources
                if Items.get_item_source_index_by_name(item_name) != -1: # Use != -1 for existence
                    # Item exists in global sources, keep it along with its index and quantity
                    new_user_items_dict[item_name] = item_info # Assign the whole dictionary
                else:
                    print(f"Removing non-existent item '{item_name}' from {user_id_str}'s inventory (source not found).")
            
            # Only add user to new inventory if they have items left
            if new_user_items_dict:
                new_player_inventory[user_id_str] = new_user_items_dict
            else:
                print(f"User {user_id_str}'s inventory is now empty after cleanup.")
        
        Items.player_inventory = new_player_inventory # Replace with the cleaned inventory

        # --- Phase 3: Final cleanup and Save ---
        print("Phase 3: Finalizing and saving...")
        # This ensures all remaining items in player_inventory have correct indices
        # and removes any remaining malformed entries.
        Items._ensure_inventory_consistency() 

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
        amount = account[2]
        log_amount = log(amount, 10)
        log_days = log(days, 10) + 1 if days > 0 else 1
        multiplier = 9 / 20

        print(f"interest for {account[0]}: {log_days * log_amount * multiplier}")
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
        # Items.get_user_item_indexes(user_id) returns a dict like {item_name: item_source_index}
        user_item_name_to_index_map = Items.get_user_item_indexes(user_id)

        for item_name, item_source_index in user_item_name_to_index_map.items():
            # 1. Validate the item_source_index
            if not (0 <= item_source_index < len(Items.item_sources)):
                print(f"Warning: Item '{item_name}' for user {user_id} has an invalid item_source_index {item_source_index}. Skipping.")
                continue

            item_source_data = Items.item_sources[item_source_index]
            print(f"item source data: {item_source_data}") 
            print(f"item name: {item_name}")
            # 2. Check if this item source represents an offshore bank account
            # We assume the name of the item is the offshore key.
            # Identification is based on the description containing "'s Offshore bank account".


            is_offshore_item_source = (
                len(item_source_data) > 3 and "'s Offshore bank account".lower() in item_source_data[3].lower() and item_name == item_source_data[0]
            )



            print(f"Is it an offshore bank account?: {'s Offshore bank account'.lower() in item_source_data[3].lower()} ")
            print(f"Is the data length greater length > 3?: {len(item_source_data) > 3}")
            print(f"Is the data name the item name?: {item_source_data[0] == item_name}")

            if not is_offshore_item_source:
                continue # Skip if it's not an item representing an offshore account

            # At this point, item_name is believed to be an offshore_key.
            offshore_key_from_item = item_name 

            # 3. Verify that this offshore_key (from the item) is actually present
            #    in Offshore.balances AND belongs to the specified user_id.
            for account_data in Offshore.balances:
                account_key_in_offshore = account_data[0]
                                
                if (offshore_key_from_item == account_key_in_offshore):
                    keys.append(offshore_key_from_item)
                    break # Found this key for this user, move to the next item_name

        # print(f"KEYS: {keys}") # Uncomment for debugging
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

class Economy:
    data_loaded = False

    def main():
        # Load economy data. Do this once on_ready.
        Bank.read_balance()
        Income.loadincomes()
        Income.create_sources() # Also ensures sources are initialized/loaded
        Items.load_player_inventory() 
        Items._ensure_inventory_consistency() # Makes sure all of the indexes are correct for the inventory 
        Items.create_item_sources() # Also ensures item sources are initialized/loaded
        Offshore.load_balances() # Sets the balnaces variable to the one from the json file
        Offshore.clear_balance() # Removes balances that nobody have
        print("Economy data loaded/initialized for all classes.")
        Economy.data_loaded = True

   

if __name__ == '__main__':
    Economy.main()
