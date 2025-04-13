import pickle
import os
import numpy as np
import random
from collections import OrderedDict

#Q-Learning model for poker

Q_FILE = 'sarsa.pkl'
META_FILE = 'meta.pkl'
MAX_QTABLE_SIZE = 1_000_000

def calc_bet(player):

                   
        max_bet=player.stack-player.to_play
        min_bet=player.to_play
        if max_bet<min_bet:
                print('max bet '+str(max_bet))
                print('min be  '+str(min_bet))
        
        

        if max_bet<0:
                max_bet=player.stack
                                
        bet_amount=random.randrange(min_bet,max_bet+1,5)
        
        
        return bet_amount
        

class Strategy():
        
        def __init__(self, player):
                
                self.tight=0
                self.aggression=0
                self.cool=0
                self.player=player
                self.name=str(self.__class__.__name__)

        
              
        @property
        
        def play_style(self):
                
                pass

        def decide_play(self, player, pot):
                
                pass
#original pokerstrat.py

class sarsaBot(Strategy):
    def __init__(self, player):
        super().__init__(player)
        self.alpha = 0.2
        self.gamma = 0.9
        self.epsilon = 0.5
        self.min_epsilon = 0.05
        self.epsilon_decay = 0.997
        self.meta = self.load_meta()

        #override from saved values
        self.epsilon = self.meta.get("epsilon", self.epsilon)
        self.alpha = self.meta.get("alpha", self.alpha)
        self.games_played = self.meta.get("games_played", 0)


        self.q_values = self.load_q_values()
        self.last_state = None
        self.last_action = None
        
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
            except (EOFError, pickle.UnpicklingError):
                print("[SARSA] Q-table file was empty or corrupt. Starting fresh.")
                return {}
        else:
            return {}
        
    def save_q_values(self):
        with open(Q_FILE, 'wb') as f:
            pickle.dump(self.q_values, f)  # <-- pass the file as second argument

    def get_q_value(self, state, action):
        return self.q_values.get((state, action), 0.0)
    
    def update_q_value(self, state, action, reward, next_state, next_action):
        current_q = self.get_q_value(state, action)
        next_q = self.get_q_value(next_state, next_action)  # SARSA: actual next action
        new_q = current_q + self.alpha * (reward + self.gamma * next_q - current_q)

        if not isinstance(self.q_values, OrderedDict):
            self.q_values = OrderedDict(self.q_values)

        self.q_values[(state, action)] = new_q

        while len(pickle.dumps(self.q_values)) > MAX_QTABLE_SIZE:
            self.q_values.popitem(last=False)

        self.save_q_values()
        
    def bucket_pot_size(self, pot):
        if pot < 50:
            return 0
        elif pot < 100:
            return 1
        elif pot < 200:
            return 2
        elif pot < 400:
            return 3
        else:
            return 4

    def bucket_rel_stack(self, stack_ratio):
        if stack_ratio < 0.5:
            return 0
        elif stack_ratio < 1:
            return 1
        elif stack_ratio < 2:
            return 2
        elif stack_ratio < 5:
            return 3
        else:
            return 4
        
    def bucket_gappers(self, g):
        if g == 0:
            return 0
        elif g == 1:
            return 1 
        elif g == 2:
            return 2
        else:
            return 3 
        
    def get_bet_amount(self, player, pot, action):
        pot_size = pot.total
        min_raise = max(10, pot.to_play * 2)
        stack = player.stack

        if action == 'bet_small':
            return min(stack, max(min_raise, int(pot_size * 0.3)))
        elif action == 'bet_medium':
            return min(stack, max(min_raise, int(pot_size * 0.6)))
        elif action == 'bet_large':
            return min(stack, max(min_raise, int(pot_size)))
        else:
            return min(stack, max(min_raise, 10))  # fallback

    def choose_action(self, state, pot):
        actions = [
            'fold',
            'check_call',
            'bet_small',    # ~20% pot
            'bet_medium',   # ~50% pot
            'bet_large',    # ~80% pot
            'all_in'        # max aggression
        ]

        # Epsilon-greedy: explore or exploit
        if random.random() < self.epsilon:
            return random.choice(actions)  # Explore
        else:
            # Exploit best Q-value
            q_vals = {a: self.get_q_value(state, a) for a in actions}
            return max(q_vals, key=q_vals.get)

    def decide_play(self, player, pot):
        self.last_stack = player.stack
        hand_value, rep, tie_break, raw_data = player.get_value()

        # state representation
        hand_strength = hand_value // 10
        pot_bucket = self.bucket_pot_size(pot.total)
        rel_stack_bucket = self.bucket_rel_stack(player.stack / (pot.total + 1))
        position = player.position % pot.table_size
        phase = pot.stage
        flush_score = raw_data[1]
        straight_detected = int(bool(raw_data[2]))
        gappers_bucket = self.bucket_gappers(raw_data[3])
        
        # Build current state tuple
        state = (
            hand_strength,
            pot_bucket,
            rel_stack_bucket,
            position,
            phase,
            flush_score,
            straight_detected,
            gappers_bucket
        )

        # Choose action using epsilon-greedy policy
        action = self.choose_action(state, pot)

        # Perform the selected action
        if action == 'fold':
            player.fold(pot)
        elif action == 'check_call':
            player.check_call(pot)
        elif action.startswith('bet'):
            bet_amount = self.get_bet_amount(player, pot, action)
            player.bet(pot, bet_amount)
        elif action == 'all_in':
            player.bet(pot, player.stack)

        # SARSA Q-value update
        if self.last_state is not None:
            reward = self.get_reward(player, pot, action)
            next_action = self.choose_action(state, pot)
            self.update_q_value(self.last_state, self.last_action, reward, state, next_action)
            self.last_action = next_action
        else:
            # First move: just record the action
            self.last_action = action

        # Update current state for next round
        self.last_state = state

        # decay epsilon
        if self.epsilon > self.min_epsilon:
            self.epsilon *= self.epsilon_decay

        #10% chance to reset epsilon t0 0.3 every 100 games to encourage continued learning
        if self.games_played % 100 == 0:
            if random.random() < 0.1:
                old_eps = self.epsilon
                self.epsilon = max(self.epsilon, 0.3)
                print(f"[Epsilon Reset] Game {self.games_played}: Epsilon reset from {old_eps:.4f} to {self.epsilon:.4f}")


        self.games_played += 1
        self.save_meta()
        
    def get_reward(self, player, pot, action, final=False):
        stack_diff = player.stack - self.last_stack
        reward = 0.0

        if final:
            if player.stack > self.last_stack:
                reward += 1.0
            elif player.stack < self.last_stack:
                reward -= 1.0

            reward += 0.1 * (pot.total / 100.0)  # scaled win bonus
            if action.startswith('bet') and player.stack > self.last_stack:
                reward += 0.2  # value bet success
        else:
            if action == 'fold' and player.to_play == 0:
                reward -= 0.05  # discourage weak folds
            elif action.startswith('bet'):
                reward += 0.05  # encourage aggression
            elif action == 'all_in':
                reward += 0.1   # boldness bonus

            if len(pot.active_players) == 1 and action.startswith('bet'):
                reward += 0.3  # bluff success

        # Add clipped stack_diff
        reward += max(-100, min(stack_diff, 100)) / 100.0

        return reward
