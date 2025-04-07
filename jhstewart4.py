import random
import pickle
import os
import numpy as np

#SARSA model for poker

Q_FILE = 'jhstewart4.pkl'

class jhstewart4(Strategy):
    def __init__(self, player):
        super().__init__(player)
        self.alpha = 0.1
        self.gamma = 0.9
        self.epsilon = 0.1
        self.q_values = self.load_q_values()
        self.last_state = None
        self.last_action = None
        
    def load_q_values(self):
        if os.path.exists(Q_FILE):
            with open(Q_FILE, 'rb') as f:
                return pickle.load(f)
        else:
            return {}
        
    def save_q_values(self):
        with open(Q_FILE, 'wb') as f:
            pickle.dump(self.q_values)
            
    def get_q_value(self, state, action):
        return self.q_values.get((state, action), 0.0)
    
    def update_q_value(self, state, action, reward, next_state, next_action):
        current_q = self.get_q_value(state, action)
        next_q = self.get_q_value(next_state, next_action)
        new_q = current_q + self.alpha * (reward + self.gamma * next_q - current_q)
        self.q_values[(state, action)] = new_q
        self.save_q_values()

    def decide_play(self, player, pot):
        # Define the state based on hand strength and stack
        hand_value, rep, tie_break, raw_data = player.get_value()
        state = (hand_value, player.stack, pot.total)

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

        # Update Q-values if a previous state-action exists
        if self.last_state is not None:
            reward = self.get_reward(player, pot)
            self.update_q_value(self.last_state, self.last_action, reward, state, action)

        # Update last state and action
        self.last_state = state
        self.last_action = action

    def get_reward(self, player, pot):
        # Basic reward calculation
        if player.is_folded:
            return -10  # Penalty for folding
        elif player.stack > pot.total:
            return 20  # Reward for winning a pot
        else:
            return -5  # Small penalty for losing
