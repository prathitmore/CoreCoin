import subprocess, json

base, mid, jackpot = 0, 0, 0
print("Analyzing NEW blocks 432 to 831...")

for height in range(432, 832):
    try:
        output = subprocess.check_output(["./src/CoreCoin-cli", "-regtest", "getblockstats", str(height)])
        stats = json.loads(output)
        subsidy = stats.get("subsidy", 0) / 100000000
        if subsidy == 150: jackpot += 1
        elif subsidy == 75: mid += 1
        elif subsidy == 25: base += 1
    except: pass

print(f"\n=== NEW REWARD DISTRIBUTION ===\nBase: {base}\nMid: {mid}\nJackpot: {jackpot}")
