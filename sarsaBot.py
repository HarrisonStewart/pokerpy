import pickle
import os
import numpy as np
import random
from collections import OrderedDict

from pokerhands import evaluate_hand

# Q-Learning model for poker with stage-specific Q-tables

Q_FILE = 'sarsa.pkl'
META_FILE = 'meta.pkl'
MAX_QTABLE_SIZE = 1_000_000


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

class sarsaBot(Strategy):
    def __init__(self, player):
        super().__init__(player)
        self.alpha = 0.1
        self.gamma = 0.9
        self.epsilon = 0.8
        self.min_epsilon = 0.05
        self.epsilon_decay = 0.995
        self.meta = self.load_meta()

        self.epsilon = self.meta.get("epsilon", self.epsilon)
        self.alpha = self.meta.get("alpha", self.alpha)
        self.games_played = self.meta.get("games_played", 0)

        self.q_values = self.load_q_values()
        self.last_state = None
        self.last_action = None
        
        self.trajectory = []

    def load_meta(self):
        if os.path.exists(META_FILE):
            try:
                with open(META_FILE, 'rb') as f:
                    return pickle.load(f)
            except:
                print("[META] Corrupt meta file, starting fresh.")
                return {}
        return {}

    def save_meta(self):
        data = {
            "epsilon": self.epsilon,
            "alpha": self.alpha,
            "games_played": self.games_played
        }
        with open(META_FILE, 'wb') as f:
            pickle.dump(data, f)

    def load_q_values(self):
        if os.path.exists(Q_FILE):
            try:
                with open(Q_FILE, 'rb') as f:
                    return pickle.load(f)
            except:
                print("[SARSA] Q-table file was empty or corrupt. Starting fresh.")
        return {0: OrderedDict(), 1: OrderedDict(), 2: OrderedDict(), 3: OrderedDict()}

    def save_q_values(self):
        with open(Q_FILE, 'wb') as f:
            pickle.dump(self.q_values, f)

    def get_q_value(self, phase, state, action):
        if phase not in self.q_values:
            print(f"[WARN] Phase {phase} not in Q-table. Initializing it.")
            self.q_values[phase] = OrderedDict()
        return self.q_values[phase].get((state, action), 0.0)

    def update_q_value(self, phase, state, action, reward, next_state, next_action):
        if phase not in self.q_values:
            print(f"[WARN] Phase {phase} not in Q-table during update. Initializing it.")
            self.q_values[phase] = OrderedDict()

        current_q = self.get_q_value(phase, state, action)
        next_q = self.get_q_value(phase, next_state, next_action)
        new_q = current_q + self.alpha * (reward + self.gamma * next_q - current_q)

        self.q_values[phase][(state, action)] = new_q

        while len(pickle.dumps(self.q_values[phase])) > MAX_QTABLE_SIZE:
            self.q_values[phase].popitem(last=False)

        self.save_q_values()

    def choose_action(self, phase, state, pot, win_prob):
        actions = ['fold', 'check_call', 'bet_small', 'bet_medium', 'bet_large', 'all_in']
        
        if win_prob is not None and win_prob < 0.4:
            actions.remove('all_in')
        
        if random.random() < self.epsilon:
            return random.choice(actions)
        
        
        q_vals = {a: self.get_q_value(phase, state, a) for a in actions}
        max_val = max(q_vals.values())
        best_actions = [a for a, q in q_vals.items() if q == max_val]
        return random.choice(best_actions)

    def bucket_pot_size(self, pot):
        if pot < 50: return 0
        elif pot < 100: return 1
        elif pot < 200: return 2
        elif pot < 400: return 3
        else: return 4

    def bucket_rel_stack(self, stack_ratio):
        if stack_ratio < 0.5: return 0
        elif stack_ratio < 1: return 1
        elif stack_ratio < 2: return 2
        elif stack_ratio < 5: return 3
        else: return 4

    def get_bet_amount(self, player, pot, action):
        pot_size = pot.total
        min_raise = max(10, pot.to_play * 2)
        stack = player.stack
        if action == 'bet_small': return min(stack, max(min_raise, int(pot_size * 0.3)))
        elif action == 'bet_medium': return min(stack, max(min_raise, int(pot_size * 0.6)))
        elif action == 'bet_large': return min(stack, max(min_raise, int(pot_size)))
        else: return min(stack, max(min_raise, 10))
        
    def estimate_win_probability(self, player, pot, board_cards=None, simulations=1000):
        """
        Monte Carlo simulation to estimate win rate vs. actual number of opponents.
        Wins only if the bot beats all opponents in each simulation.
        """
        if board_cards is None:
            board_cards = []

        if not player.cards:
            return 0.0  # Player has no cards yet

        CardClass = type(player.cards[0])

        full_deck = [CardClass(rank, suit) for rank in CardClass.RANKS for suit in CardClass.SUITS]
        known_cards = player.cards + board_cards
        deck = [card for card in full_deck if str(card) not in [str(c) for c in known_cards]]

        num_opponents = len(pot.active_players) - 1
        wins = 0

        for _ in range(simulations):
            random.shuffle(deck)

            # Deal two cards per opponent
            opponent_hands = [deck[i*2:(i+1)*2] for i in range(num_opponents)]
            next_idx = num_opponents * 2

            # Fill out the board to 5 cards
            remaining_community = deck[next_idx:next_idx + (5 - len(board_cards))]
            full_board = board_cards + remaining_community

            my_hand = player.cards + full_board
            my_value, *_ = evaluate_hand(my_hand)

            beat_all = True
            for opp_cards in opponent_hands:
                opp_hand = opp_cards + full_board
                opp_value, *_ = evaluate_hand(opp_hand)
                if opp_value > my_value:
                    beat_all = False
                    break
                elif opp_value == my_value:
                    beat_all = False
                    break  # ties not counted as win

            if beat_all:
                wins += 1

        return wins / simulations

    def decide_play(self, player, pot):
        
        hand_value, rep, tie_break, raw_data = player.get_value()
                
        pot_bucket = self.bucket_pot_size(pot.total)
        rel_stack_bucket = self.bucket_rel_stack(player.stack / (pot.total + 1))
        num_opponents = len(pot.active_players)
        phase = pot.stage
        
        board_cards = pot.table.cards if hasattr(pot, 'table') else []
        
        if pot.stage == 0:      # Preflop
            simulations = 3000
        elif pot.stage == 1:    # Flop
            simulations = 2000
        elif pot.stage == 2:    # Turn
            simulations = 1500
        else:                   # River
            simulations = 1000

        
        win_prob = self.estimate_win_probability(player, pot, board_cards, simulations)

        if phase == 0:
            self.last_stack = player.stack
            
        if self.last_state is not None and self.last_action is not None and pot.stage != 0:
            self.trajectory.append((phase, self.last_state, self.last_action)) #append intermediate moves

        state = (
            hand_value,
            int(win_prob*100) // 20,
            pot_bucket,
            rel_stack_bucket,
            num_opponents,
            phase,
            rep
        )

        action = self.choose_action(phase, state, pot, win_prob)

        if action == 'fold':
            player.fold(pot)
        elif action == 'check_call':
            player.check_call(pot)
        elif action.startswith('bet'):
            amount = self.get_bet_amount(player, pot, action)
            player.bet(pot, amount)
        elif action == 'all_in':
            player.bet(pot, player.stack)

        if self.last_state is not None:
            if pot.stage == 3 or len(pot.active_players) <= 1:
                reward = self.get_reward(player, pot, action, phase)
                next_action = self.choose_action(phase, state, pot, win_prob)

                # Add final step to trajectory
                self.trajectory.append((phase, self.last_state, self.last_action))

                # Update Q-values for every phase from this hand
                for (p, s, a) in self.trajectory:
                    self.update_q_value(p, s, a, reward, state, next_action)

                self.trajectory = []  # Reset for next hand
                self.last_action = next_action
            else:
                self.last_action = action
        else:
            self.last_action = action

        self.last_state = state

        if self.epsilon > self.min_epsilon:
            self.epsilon *= self.epsilon_decay

        if self.games_played % 100 == 0:
            if random.random() < 0.1:
                old_eps = self.epsilon
                self.epsilon = max(self.epsilon, 0.3)
                print(f"[Epsilon Reset] Game {self.games_played}: Epsilon reset from {old_eps:.4f} to {self.epsilon:.4f}")

        self.games_played += 1
        self.save_meta()

    def get_reward(self, player, pot, action, phase):
        """
        Called once per hand (after it's ended).
        Gives reward based on chip gain/loss, with shaping to penalize aggressive low-probability plays.
        """
        final_stack = player.stack
        stack_change = final_stack - self.last_stack

        # Re-estimate win probability for shaping
        board_cards = pot.table.cards if hasattr(pot, 'table') else []
        win_prob = self.estimate_win_probability(player, pot, board_cards, simulations=50)

        # Base reward from stack change
        if stack_change > 0:
            reward = stack_change / 100.0
        elif stack_change < 0:
            reward = stack_change / 50.0
        else:
            reward = -0.05

        # Mild penalty for preflop folds
        if action == 'fold' and phase == 0:
            reward -= 0.1

        # 🔻 Penalty for overly aggressive play with weak hand
        if action in ['bet_small', 'bet_medium', 'bet_large', 'all_in'] and win_prob < 0.3:
            penalty_scale = (0.3 - win_prob) * 5  # higher penalty the worse the hand
            reward -= penalty_scale
        
        if action == 'all_in':
            if win_prob < 0.6:
                reward -= (0.6 - win_prob) * 8  # Steeper slope for bad all-ins
            
        if action in ['bet_large', 'all_in'] and win_prob > 0.9:
            reward += 0.5  # reward confident aggression

        return reward