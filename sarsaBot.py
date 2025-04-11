import pickle
import os
import numpy as np
import random
from collections import OrderedDict

#SARSA model for poker

Q_FILE = 'sarsa.pkl'
MAX_QTABLE_SIZE = 1_000_000

#Original pokerstrat.py
##poker player strategy and i/o

import random

def evaluate(player):
        
        value=player.get_value()
        
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
        self.epsilon = 0.2
        self.q_values = self.load_q_values()
        self.last_state = None
        self.last_action = None
        
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
        next_q = self.get_q_value(next_state, next_action)
        new_q = current_q + self.alpha * (reward + self.gamma * next_q - current_q)

        # Use OrderedDict for automatic ordering
        if not isinstance(self.q_values, OrderedDict):
            self.q_values = OrderedDict(self.q_values)

        self.q_values[(state, action)] = new_q

        # Shrink Q-table if needed
        while len(pickle.dumps(self.q_values)) > MAX_QTABLE_SIZE:
            self.q_values.popitem(last=False)  # Remove oldest

        self.save_q_values()

    def choose_action(self, state, pot):
        actions = ['fold', 'check_call', 'bet']

        # Epsilon-greedy: explore or exploit
        if random.random() < self.epsilon:
            return random.choice(actions)  # Explore
        else:
            # Exploit best Q-value
            q_vals = {a: self.get_q_value(state, a) for a in actions}
            best_action = max(q_vals, key=q_vals.get)
            return best_action

    def decide_play(self, player, pot):
        self.last_stack = player.stack

        # Define the state based on hand strength and stack
        hand_value, rep, tie_break, raw_data = player.get_value()
        state = (
            hand_value // 10,
            player.stack // 50,
            pot.total // 50
        )

        # Choose the action using the policy
        action = self.choose_action(state, pot)

        # Perform the chosen action
        if action == 'fold':
            player.fold(pot)
        elif action == 'check_call':
            player.check_call(pot)
        elif action == 'bet':
            bet_amount = min(player.stack, max(10, pot.to_play + 10))
            player.bet(pot, bet_amount)
            
        hand_value, rep, tie_break, raw_data = player.get_value()
        next_state = (
            hand_value // 10,
            player.stack // 50,
            pot.total // 50
        )

        # Update Q-values if a previous state-action exists
        if self.last_state is not None:
            reward = self.get_reward(player, pot, action)
            next_action = self.choose_action(next_state, pot)
            self.update_q_value(self.last_state, self.last_action, reward, next_state, next_action)

        # Update last state and action
        self.last_state = state
        self.last_action = action

    def get_reward(self, player, pot, action):
        # Core reward: net chip gain/loss
        reward = player.stack - self.last_stack

        return reward