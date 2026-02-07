import random
import sys

# =========================
# USERS (LOCKED)
# =========================
USER0 = "user0"
USER1 = "user1"

# =========================
# CONTENT POOLS
# =========================
greetings = [
    ("gm", "wagmi"),
    ("yo", "wen moon"),
    ("sup", "ngmi 😭"),
    ("hello", "hodl on"),
    ("wen airdrop?", "soon bruh"),
]

topics = {
    "starter": [
        "eth gas fees wildin",
        "solana devs grinding",
        "pepe trending again",
        "doge just pumped",
        "just bridged to zkSync",
    ],
    "reply": [
        "yeah market heating up",
        "volume confirms it",
        "that move was criminal",
        "ecosystem looking strong",
        "fees finally reasonable",
    ],
    "followup": [
        "we’re early anon",
        "ngmi if you fade this",
        "dev activity booming",
        "pure degen energy",
        "you love to see it",
    ],
    "meme": [
        "this market ain’t real",
        "airdrops keeping me alive",
        "charts got hands",
        "L2 season loading",
        "testnet vibes",
    ],
    "reflect": [
        "sometimes the best trade is no trade",
        "market cycles mirror human emotion",
        "hodling is a meditation",
        "bulls build ego, bears build skill",
    ],
}

# =========================
# HELPERS
# =========================
def pick(pool, used):
    available = [x for x in pool if x not in used]
    msg = random.choice(available if available else pool)
    used.add(msg)
    return msg

# =========================
# CORE LOGIC
# =========================
def generate_conversation(n: int):
    convo = []
    used = set()

    # Mandatory greeting pair
    g0, g1 = random.choice(greetings)
    convo.append(f"{USER0}: {g0}")
    convo.append(f"{USER1}: {g1}")

    i = 2
    while len(convo) < n * 2:
        speaker = USER0 if i % 2 == 0 else USER1

        if i % 4 == 0:
            msg = pick(topics["starter"], used)
        elif i % 4 == 1:
            msg = pick(topics["reply"], used)
        elif i % 4 == 2:
            msg = pick(topics["followup"], used)
        else:
            msg = pick(
                topics["reflect"] if random.random() < 0.2 else topics["meme"],
                used
            )

        convo.append(f"{speaker}: {msg}")
        i += 1

    return convo[: n * 2]

# =========================
# ENTRY POINT
# =========================
def main():
    try:
        n = int(input("How many messages per user? : ").strip())
        if n <= 0:
            raise ValueError
    except:
        print("Invalid number")
        sys.exit(1)

    conversation = generate_conversation(n)

    with open("conversation.txt", "w", encoding="utf-8") as f:
        for line in conversation:
            f.write(line + "\n")

    print(f"Generated perfect 2-user conversation: {n} ↔ {n}")

if __name__ == "__main__":
    main()
