# pokerpy
This is a poker bot project in python. It uses the poker framework at https://github.com/philipok-1/Poker.

There are several bots included, however the highest performing and most developed is monteCarloBot

monteCarloBot uses a Monte Carlo simulation to estimate its win probability and chooses a playstyle based on that.

sarsaBot is a reinforcement learning based approach using SARSA. I originally used Q-Learning and got similar results, it could easily be modified to use that update method or any other similar Q-Table based algorithm

trainer.py is a simple script to run a number of games, storing the results in a log file.

visualizer.py visualizes the results for analysis
