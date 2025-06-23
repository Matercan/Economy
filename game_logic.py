import random

from nltk.toolbox import TreeBuilder



class Card:
    def __init__(self, suit, rank) -> None:
        self.suit = suit
        self.rank = rank
        
        print(self.rank)
        print(self.suit)

        card_emojis = {
            "hearts": {
                "A": "🂱",
                "2": "🂲",
                "3": "🂳",
                "4": "🂴",
                "5": "🂵",
                "6": "🂶",
                "7": "🂷",
                "8": "🂸",
                "9": "🂹",
                "10": "🂺",
                "J": "🂻",
                "Q": "🂼",
                "K": "🂽"
            },
            "diamonds": {
                "A": "🃁",
                "2": "🃂",
                "3": "🃃",
                "4": "🃄",
                "5": "🃅",
                "6": "🃆",
                "7": "🃇",
                "8": "🃈",
                "9": "🃉",
                "10": "🃊",
                "J": "🃋",
                "Q": "🃍",
                "K": "🃎"
            },
            "clubs": {
                "A": "🃑",
                "2": "🃒",
                "3": "🃓",
                "4": "🃔",
                "5": "🃕",
                "6": "🃖",
                "7": "🃗",
                "8": "🃘",
                "9": "🃙",
                "10":"🃚",
                "J": "🃛",
                "Q": "🃜",
                "K": "🃝"
            },
            "spades": {
                "A": "🃁",
                "2": "🃂",
                "3": "🃃",
                "4": "🃄",
                "5": "🃅",
                "6": "🃆",
                "7": "🃇",
                "8": "🃈",
                "9": "🃉",
                "10": "🃊",
                "J": "🃋",
                "Q": "🃍",
                "K": "🃎"
            }
        }
        self.emoji = card_emojis[str(suit).lower()][str(rank)]

    def __str__(self) -> str:
        """Returns a string representation of the card, e.g., 'Ace of Spades' or '10 of Hearts'."""
        if self.rank == 'A':
            rank_str = 'Ace'
        elif self.rank == 'J':
            rank_str = 'Jack'
        elif self.rank == 'Q':
            rank_str = 'Queen'
        elif self.rank == 'K':
            rank_str = 'King'
        else:
            rank_str = str(self.rank) # For 2-10
        
        return f"{rank_str} of {self.suit} {self.emoji}"

    
    def get_value(self):
        if self.rank in ['J', 'Q', 'K']:
            return 10
        elif self.rank == 'A':
            return 11
        else: 
            return int(self.rank)

class Deck:
    def __init__(self):
        self.cards=[]
        self.build()

    def build(self):
        suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
        ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        for suit in suits:
            for rank in ranks:
                self.cards.append(Card(suit, rank))

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self):
        if not self.cards:
            print("Resuhffling deck")
            self.build()
            self.shuffle()
        return self.cards.pop()

class BlackjackGame:
    def __init__(self) -> None:
        self.deck = Deck()
        self.deck.shuffle()
        self.player_hand = []
        self.dealer_hand = []
        self.is_game_over = False
        self.result_message = ""

    def deal_initial_hands(self):
        self.player_hand.append(self.deck.deal())
        self.dealer_hand.append(self.deck.deal())
        self.player_hand.append(self.deck.deal())
        self.dealer_hand.append(self.deck.deal())

    def calculate_hand_value(self, hand):
        value = sum(card.get_value() for card in hand) 
        num_aces = sum(1 for card in hand if card.rank == 'A')
        
        while value > 21 and num_aces > 0:
            value -= 10
            num_aces -= 1
        return value
    
    def player_hit(self):
        self.player_hand.append(self.deck.deal())
        if self.calculate_hand_value(self.player_hand) > 21:
            self.is_game_over = True
            self.result_message = "Player busts! You went over 21"
            return True # Player busts
        return False # Player did not bust

    def dealer_play(self):
        # Dealer hits until score is 17 or more
        while self.calculate_hand_value(self.dealer_hand) < 17:
            self.dealer_hand.append(self.deck.deal())

        self.is_game_over = True
        self.determine_winner()

    def determine_winner(self):
        player_score = self.calculate_hand_value(self.player_hand)
        dealer_score = self.calculate_hand_value(self.dealer_hand)

        if player_score > 21:
            self.result_message = "Player busts! Dealer wins."
        elif dealer_score > 21:
            self.result_message = "Dealer busts! Player wins."
        elif player_score == dealer_score:
            self.result_message = "It's a push! You tie with the dealer."
        elif player_score > dealer_score:
            self.result_message = "Player wins!"
        else:
            self.results_message = "Dealer wins!"

class CardflipGame:
    def __init__(self) -> None:
        self.deck = Deck()
        self.deck.shuffle()
        self.is_game_over = False
        self.result_message = ""
        self.player_card = self.deck.deal()
        self.dealer_card = self.deck.deal()

    def determine_winner(self):
        player_value = 1
        if self.player_card == 'A':
            player_value = 14
        elif self.player_card == 'K':
            player_value = 13
        elif self.player_card == 'Q':
            player_value = 12
        elif player_value == 'J':
            player_value = 11
        else:
            player_value = Card.get_value(self.player_card)

        dealer_value = 1
        if self.dealer_card == 'A':
            dealer_value = 14
        elif self.dealer_card == 'K':
            dealer_value = 13
        elif self.dealer_card == 'Q':
            dealer_value = 12
        elif self.dealer_card == 'J':
            dealer_value = 11
        else:
            dealer_value = Card.get_value(self.dealer_card)

        print(dealer_value)
        print(player_value)

        if player_value > dealer_value:
            self.result_message = "Player wins!"
            return True
        elif dealer_value > player_value:
            self.result_message = "Dealer wins!"
            return False
        else:
            self.result_message = "It's a push! You tie with the dealer."
            return None

class RoulletteGame:
    def __init__(self) -> None:
        self.players: dict[str, dict] = {}
        self.pot = 0
        self.timer = 30
        self.is_game_over = False
        self.ball = -1
        self.winning_number = -1
        self._wheel_numbers =  [
            0, 32, 15, 19,
           4, 21, 2, 25,
           17, 34, 6, 27,
           13, 36, 11, 30,
           8, 23, 10, 5, 
           24, 16, 33, 1,
           20, 14, 31, 9,
           22, 18, 29, 7,
           28, 12, 35, 3, 26]
        
        self.winning_color = ""

    def add_player_bet(self, user_id: str, bet_amount: float, betted_on: str): # betted_on can be number or "red", "black", "even" etc.
        """Adds or updates a player's bet."""
        # Ensure bet_amount is treated as float for calculations
        bet_amount = float(bet_amount)

        if user_id not in self.players:
            self.players[user_id] = {"bet_amount": 0.0, "betted_on": []} # betted_on is a list to allow multiple bets
        
        # Update player's bet (can be refined for multiple bet types/amounts per player)
        self.players[user_id]["bet_amount"] += bet_amount
        if betted_on not in self.players[user_id]["betted_on"]:
            self.players[user_id]["betted_on"].append(betted_on) # Add to list of things they've bet on

        self.pot += bet_amount
        print(f"DEBUG: Player {user_id} added bet. Total pot: {self.pot}") # Debug print

    def spin_wheel(self):
        """Spins the wheel and sets the winning number/color."""
        self.winning_number = random.choice(self._wheel_numbers) # Pick directly from the valid numbers
        self.winning_color = self._get_number_color(self.winning_number)
        self.is_game_over = True
        return self.winning_number, self.winning_color


    def _get_number_color(self, number: int):

        """Helper to determine the color of a roulette number."""
        # Standard European Roulette colors (simplified for 0-36)
        if number == 0:
            return "green"
        red_numbers = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
        if number in red_numbers:
            return "red"
        return "black" # All other non-zero numbers are black
    
    def get_color_number(self):
        """Returns the current ball position and its color."""
        # This function should probably reflect the *spinning* or *final* number
        # rather than just incrementing 'ball' which is an index.
        # Let's adjust it to return the actual winning number and its color
        # based on self.winning_number set by spin_wheel().
        if self.winning_number != -1:
            return self.winning_number, self.winning_color
        else:

            return "Spinning...", "unknown"

    def determine_winners(self):
        """Determines which players won based on their bets and the winning number."""
        winners_info = {} # {user_id: winnings_amount}
        
        winning_number_actual, winning_color_actual = self.winning_number, self.winning_color
        
        for user_id, bet_data in self.players.items():
            betted_on_list = bet_data.get("betted_on", [])
            bet_amount_player = bet_data.get("bet_amount", 0.0)

            # Check for winning conditions
            player_won = False
            payout_multiplier = 0 # Base multiplier

            # Direct Number Bet
            if str(winning_number_actual) in betted_on_list:
                player_won = True
                payout_multiplier = 35 # Single number pays 35:1
                print(f"DEBUG: {user_id} won on number {winning_number_actual}")

            # Color Bet (Red/Black/Green for 0)
            elif winning_color_actual in betted_on_list:
                player_won = True
                payout_multiplier = 2 # Red/Black pays 1:1
                print(f"DEBUG: {user_id} won on color {winning_color_actual}")
            
            # Even/Odd Bet
            elif ("even" in betted_on_list and winning_number_actual % 2 == 0 and winning_number_actual != 0) or \
                 ("odd" in betted_on_list and winning_number_actual % 2 != 0):
                player_won = True
                payout_multiplier = 2 # Even/Odd pays 1:1
                print(f"DEBUG: {user_id} won on Even/Odd")

            # Dozens Bets (1st 12, 2nd 12, 3rd 12)
            elif ("1st12" in betted_on_list and 1 <= winning_number_actual <= 12) or \
                 ("2nd12" in betted_on_list and 13 <= winning_number_actual <= 24) or \
                 ("3rd12" in betted_on_list and 25 <= winning_number_actual <= 36):
                player_won = True
                payout_multiplier = 3 # Dozens pays 2:1
                print(f"DEBUG: {user_id} won on Dozens")

            # Other bets like High/Low, Columns etc. can be added similarly

            if player_won:
                winnings = bet_amount_player * payout_multiplier
                winners_info[user_id] = winnings
                print(f"DEBUG: {user_id} won {winnings}")
            else:
                print(f"DEBUG: {user_id} lost.")
        
        return winners_info # Returns {user_id: winnings_amount}

    def reset_game(self):
        self.players = {}
        self.pot = 0.0
        self.timer = 30
        self.is_game_over = False
        self.ball = -1
        self.winning_number = -1
        self.winning_color = ""

