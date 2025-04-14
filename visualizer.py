import pickle
import os
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

Q_FILE = 'sarsa.pkl'
ACTIONS = ['fold', 'check_call', 'bet_small', 'bet_medium', 'bet_large', 'all_in']

def load_q_values():
    if os.path.exists(Q_FILE):
        with open(Q_FILE, 'rb') as f:
            return pickle.load(f)
    else:
        raise FileNotFoundError(f"Q-table not found: {Q_FILE}")

def group_q_by_win_prob(q_table):
    grouped = defaultdict(lambda: defaultdict(list))  # {win_prob_bucket: {action: [q-values]}}

    for (state, action), q in q_table.items():
        win_prob_bucket = state[0]  # This is int(win_prob*100)//20 from your bot
        grouped[win_prob_bucket][action].append(q)

    # Average Q-values
    averaged = defaultdict(dict)
    for bucket, action_dict in grouped.items():
        for action, values in action_dict.items():
            averaged[bucket][action] = np.mean(values)
    return averaged

def plot_q_heatmap(phase, avg_qs):
    win_buckets = sorted(avg_qs.keys())  # typically 0–4 (for 0–100% win prob in 20% steps)
    data = []

    for action in ACTIONS:
        row = [avg_qs.get(b, {}).get(action, 0) for b in win_buckets]
        data.append(row)

    data = np.array(data)

    plt.figure(figsize=(10, 5))
    plt.imshow(data, cmap='viridis', aspect='auto')
    plt.colorbar(label="Avg Q-value")
    plt.xticks(ticks=range(len(win_buckets)), labels=[f"{b*20}-{(b+1)*20}%" for b in win_buckets])
    plt.yticks(ticks=range(len(ACTIONS)), labels=ACTIONS)
    plt.xlabel("Estimated Win Probability Bucket")
    plt.ylabel("Action")
    plt.title(f"Q-Value Heatmap – Phase {phase}")
    plt.tight_layout()

    output_dir = "q_visuals"
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, f"q_heatmap_phase_{phase}.png")
    plt.savefig(path)
    print(f"Saved: {path}")
    plt.close()

def main():
    q_all_phases = load_q_values()

    for phase in range(4):
        q_table = q_all_phases.get(phase, {})
        if not q_table:
            print(f"No Q-values found for phase {phase}")
            continue
        avg_q = group_q_by_win_prob(q_table)
        plot_q_heatmap(phase, avg_q)

if __name__ == "__main__":
    main()
