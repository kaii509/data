import MetaTrader5 as mt5
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Connect to MetaTrader 5
if not mt5.initialize():
    print("initialize() failed, error code:", mt5.last_error())
    quit()

account_info = mt5.account_info()
if account_info is None:
    print("Failed to get account info")
    mt5.shutdown()
    quit()

print(f"Connected to account: {account_info.login}, Balance: {account_info.balance}")

# Define time range
from_date = datetime(2023, 1, 1)
to_date = datetime.now()

# Pull symbol history (executed entries/exits)
deals = mt5.history_deals_get(from_date, to_date)
if deals is None or len(deals) == 0:
    print("No deals found.")
    mt5.shutdown()
    quit()
else:
    traded_sym = list(set([deal.symbol for deal in deals]))
    print("Traded Symbols:", traded_sym)


# Convert to DataFrame
df = pd.DataFrame(list(deals), columns=deals[0]._asdict().keys())
df = df[df['type'].isin([mt5.DEAL_TYPE_BUY, mt5.DEAL_TYPE_SELL])]
df['time'] = pd.to_datetime(df['time'], unit='s')
df['profit'] = df['profit'].astype(float)



# Group by position_id — each group = 1 trade
if 'position_id' in df.columns:
    group_field = 'position_id'
else:
    group_field = 'position'  # fallback

trades = df.groupby(group_field).agg({
    'time': 'min',
    'symbol': 'first',
    'profit': 'sum'
}).reset_index()

# Sort by time
trades = trades.sort_values('time')
trades['win'] = (trades['profit'] > 0).astype(int)
trades['loss'] = (trades['profit'] <= 0).astype(int)
trades['cumulative_wins'] = trades['win'].cumsum()
trades['cumulative_losses'] = trades['loss'].cumsum()
trades['cumulative_profit'] = trades['profit'].cumsum()

# Summary
total_trades = len(trades)
wins = trades['win'].sum()
losses = trades['loss'].sum()
winrate = (wins / total_trades) * 100 if total_trades > 0 else 0

print(f"\nCompleted Trades: {total_trades}")
print(f"Wins: {wins}")
print(f"Losses: {losses}")
print(f"Winrate: {winrate:.2f}%")

# Plot cumulative win/loss
plt.figure(figsize=(10, 5))
plt.plot(trades['time'], trades['cumulative_wins'], label='Wins', marker='o')
plt.plot(trades['time'], trades['cumulative_losses'], label='Losses', linestyle='--', marker='x')
plt.title(f"Cumulative Wins vs Losses Over Time\nWinrate: {winrate:.2f}%")
plt.xlabel("Date")
plt.ylabel("Number of Trades")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# Plot cumulative profit
plt.figure(figsize=(10, 5))
plt.plot(trades['time'], trades['cumulative_profit'], marker='o')
plt.title("Cumulative Profit Over Time")
plt.xlabel("Date")
plt.ylabel("Profit ($)")
plt.grid(True)
plt.tight_layout()
plt.show()

# Optional: Save to CSV
trades.to_csv("mt5_trades.csv", index=False)

# Shutdown
mt5.shutdown()
