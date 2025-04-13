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

summary_lines = ["\n=== Total Wins Across All Runs ==="]
for player, count in win_counts.items():
    line = f"{player}: {count} wins"
    print(line)
    summary_lines.append(line)

# Append summary to the winners.log file
with open("winners.log", "a") as f:
    f.write("\n" + "\n".join(summary_lines) + "\n")
