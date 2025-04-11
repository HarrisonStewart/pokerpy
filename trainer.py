import subprocess
from collections import Counter

NUM_RUNS = 1000  # Change to however many times you want
SCRIPT = "poker.py"

for i in range(NUM_RUNS):
    print(f"Run #{i+1}")
    subprocess.run(["python", SCRIPT])

with open("winners.log", "r") as f:
    winners = f.read().splitlines()

win_counts = Counter(winners)

print("\n=== Total Wins Across All Runs ===")
for player, count in win_counts.items():
    print(f"{player}: {count} wins")
