import random

from pokerhands import evaluate_hand

class Strategy():
    def __init__(self, player):
        self.tight = 0
        self.aggression = 0
        self.cool = 0
        self.player = player
        self.name = str(self.__class__.__name__)

    @property
    def play_style(self):
        pass

    def decide_play(self, player, pot):
        pass

#an intelligent Monte Carlo based bot with several addition toggleable strategies
class monteCarloBot(Strategy):
    def __init__(self, player):
        super().__init__(player)

    def estimate_win_probability(self, player, pot, board_cards=None, simulations=1000):
        if board_cards is None:
            board_cards = []

        if not player.cards:
            return 0.0

        CardClass = type(player.cards[0])
        full_deck = [CardClass(rank, suit) for rank in CardClass.RANKS for suit in CardClass.SUITS]
        known_cards = player.cards + board_cards
        deck = [card for card in full_deck if str(card) not in [str(c) for c in known_cards]]

        num_opponents = len(pot.active_players) - 1
        wins = 0

        for _ in range(simulations):
            random.shuffle(deck)

            opponent_hands = [deck[i * 2:(i + 1) * 2] for i in range(num_opponents)]
            next_idx = num_opponents * 2

            remaining_community = deck[next_idx:next_idx + (5 - len(board_cards))]
            full_board = board_cards + remaining_community

            my_hand = player.cards + full_board
            my_value, *_ = evaluate_hand(my_hand)

            beat_all = True
            for opp_cards in opponent_hands:
                opp_hand = opp_cards + full_board
                opp_value, *_ = evaluate_hand(opp_hand)
                if opp_value >= my_value:
                    beat_all = False
                    break

            if beat_all:
                wins += 1

        return wins / simulations

    def decide_play(self, player, pot):
        board_cards = pot.table.cards if hasattr(pot, 'table') else []
        
        if pot.stage == 0:      # Preflop
            simulations = 4000
        elif pot.stage == 1:    # Flop
            simulations = 4000
        elif pot.stage == 2:    # Turn
            simulations = 2000
        else:                   # River
            simulations = 2000
  
        win_prob = self.estimate_win_probability(player, pot, board_cards, simulations)

        pot_size = pot.total
        min_raise = max(10, pot.to_play * 2)
        stack = player.stack
        
        # Simple win-prob-based decision logic
        if win_prob < 0.2:
            player.fold(pot)
        elif win_prob < 0.4:
            player.check_call(pot)
        elif win_prob < 0.6:
            player.bet(pot, min(stack, max(min_raise, int(pot_size * 0.5))))
        elif win_prob < 0.8:
            player.bet(pot, min(stack, max(min_raise, int(pot_size * 1))))
        elif win_prob < 0.95:
            player.bet(player.stack)
        else:
            player.bet(pot, stack)
