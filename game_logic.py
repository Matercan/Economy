import random

from nltk.toolbox import TreeBuilder

class Card:
    def __init__(self, suit, rank) -> None:
        self.suit = suit
        self.rank = rank

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

        return f"{rank_str} of {self.suit}"
    
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
        self.players = []
        self.pot = 0
        self.betee = []
        self.timer = 30
        self.is_game_over = False
        self.ball = 0

    def addplayaer(self, user_id: str, bet: float, betted: int):
        self.players.append(user_id)
        self.pot += bet
        self.betee.append(betted)

    def decrease_timer(self):
        self.timer -= 1
        self.ball += random.randint(1, 37)
        self.ball = self.ball % 38

        if self.timer == 0:
            self.is_game_over = True

        return not self.is_game_over


    def get_color_number(self):
        wheel = [0, 32, 15, 19,
                 4, 21, 2, 25,
                 17, 34, 6, 27,
                 13, 36, 11, 30,
                 8, 23, 10, 5,
                 24, 16, 33, 1,
                 20, 14, 13, 9,
                 22, 18, 29, 7,
                 28, 12, 35, 3, 6]

        wheel_number = wheel[self.ball]
        if self.ball // 2 == int(self.ball // 2) and wheel_number != 0:
            color = "black"
        elif wheel_number != 0:
            color = "red"
        else:
            color = "nought"
        
        return (wheel_number, color)

    def determine_winners(self):

        i = 0
        winners = []

        for user_id in self.players:
            
            if self.betee[i] == self.get_color_number()[0] or self.get_color_number()[1]:
                winners.append(user_id)
            i += 1

        return winners
        
