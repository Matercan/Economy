# Economy

Welcome to the economy. This is a bot that can be ran by setting an environment variable BOT_TOKEN to your actual bot token, then run python bot.py and the bot will work completely fine.

# File management
- The main user interaction is stored within the file `bot.py - This file is meant for managing commands and the likes
- The games such as blackjack are stored within `secondary_py/game_logic.py` - This file is meant for card games, store them as classes
- The views and embeds are stored within `secondary_py/views_embeds.py` - This file is meant for displaying information to the user
- The economy backend is stored within `secondary_py/economy.py` - This file is meant for manging the actual economy like transferring money or buying items
- The json files where the data is loaded up from is stored within `json_files/` - This directory is meant to keep all of the information in one concise plac

# economy.py explanation 
economy.py is used for managing the backend of the economy such as transferring items and money and incomes. There are a few classes in here to look at.
- `json_files/balance.json` stored all of the money in the bank and in cash for the user. This can be read with ``Bank.readbalance(user_id)`` and can be editted with ``Bank.addcash(user_id, amount)`` and ``Bank.addbank(user_id, amount)`` respectively. These are the preferred methods because they automatically handling reading from and writing to the json files
- Income is a class that is used for manging incomes. Income sources are stored within `json_files/incomesources.json`, they are how exactly each income should be interpreted and used, and can be given to the user with the method ``Income.addtoincomes(user_id, source_name, index)`` to be stored within `json_files/playerincomes.json`. Incomes are to give a user a certain amount of money, if a certain amount of time has passed.
- Items is a class that is used for managing items. Item sources are stored within `json_files/itemsources.json`, they are how eaxctly each item should be interpreted (yet importantly not used) and can be given to the user with ``Items.addtoitems(user_id, name, index)`` to be stored within `json_files/playerinventory.json`. Items are to be used as defined by the use_item method within bot.py
- Offshore bank accounts pretty much store money for a user not within the Bank so that it is very hard to edit, and are in fact not editted that often at all.
