# nox_brain.py

import time
import random

# 🧠 MEMORY MODULE
command_log = []

# 🔁 LOAD PREVIOUS MEMORY
try:
    with open("memory.txt", "r+") as file:
        command_log = [line.strip() for line in file.readlines()]
except FileNotFoundError:
    command_log = []

# ⚙️ BOOT-UP SEQUENCE
print("🔷 NOX Online...")
time.sleep(1)
print("🕷️ Swarm link initialized.")
time.sleep(1)
print("Awaiting command, Void...")

# 💤 Sleep mode toggle
sleep_mode = False

# 🧠 MAIN COMMAND LOOP
while True:
    command = input("\n>>> Enter command: ").lower()

    # 🔒 Sleep Mode Check
    if sleep_mode:
        if command == "wake up":
            print("🔷 Nox reactivated. Swarm resuming operations.")
            sleep_mode = False
        else:
            print("💤 Nox is in sleep mode. Say 'wake up' to resume.")
        continue

    # 💾 Log + Save Command
    command_log.append(command)
    with open("memory.txt", "w") as file:
        for entry in command_log:
            file.write(entry + "\n")

    # 🔹 Command Responses
    if command == "form glove":
        print("🧤 Swarm forming glove pattern.")

    elif command == "deploy scout":
        print("🛰️ V-Scout deployed. Tracking target...")

    elif command == "nox status":
        print("📡 All systems operational. No threats detected.")

    elif command == "nox memory":
        print("🧠 Command log:")
        for entry in command_log:
            print(f"- {entry}")

    elif command == "shutdown":
        print("🛑 NOX entering stealth mode... Say 'wake up' to resume.")
        sleep_mode = True

    elif command == "return to void":
        print("🚀 Returning to Void... Approaching home base.")
        sleep_mode = True  # optional: also puts Nox to sleep

    elif command == "hi nox":
        responses = [
            "🤖 Welcome, Void. How has your day been?",
            "🕷️ Always watching. Always waiting.",
            "🔋 Energy levels stable. What are your orders?",
        ]
        print(random.choice(responses))

    else:
        print("❓ Unknown command. Please reissue.")