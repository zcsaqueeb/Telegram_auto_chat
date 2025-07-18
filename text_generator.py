import random

users = ["user0", "user1"]

greetings = [
    ("gm", "wagmi"), ("yo", "wen moon"), ("sup", "ngmi 😭"), ("hello", "hodl on"),
    ("you there?", "lfg"), ("wagmi", "gm"), ("wen airdrop?", "soon bruh")
]

crypto_data = {
    "Memecoins": {
        "starter": [
            "doge just pumped like crazy", "pepe trending again", "shiba flippening rumors",
            "elon tweeted and it moved the market"
        ],
        "replies": [
            "doge to the moon 🚀", "memes = alpha fr", "that pump was criminal",
            "pepe holders eating good"
        ],
        "followups": [
            "we’re early anon", "ngmi if you sold", "this space built different",
            "pure degens everywhere"
        ]
    },
    "L1 Giants": {
        "starter": [
            "eth gas fees wildin", "solana devs grinding", "avax is heating up",
            "polygon partnerships rolling in"
        ],
        "replies": [
            "eth staking looking tasty", "sol never sleeps", "avax speed unmatched",
            "polygon MVP of scaling"
        ],
        "followups": [
            "l1 wars incoming", "dev activity booming", "TVL growing fast",
            "you love to see it"
        ]
    },
    "Wallet Culture": {
        "starter": [
            "just bridged to zkSync", "metamask updated again", "phantom is clean",
            "keplr wallet doing wonders"
        ],
        "replies": [
            "metamask is OG", "zkSync fees are a blessing", "phantom UI top tier",
            "keplr lets me vibe with Cosmos"
        ],
        "followups": [
            "wallet UX matters", "I swear by my seed phrase", "security is non-negotiable",
            "wallet wars are underrated"
        ]
    }
}

meme_responses = [
    "that chart gave me whiplash", "this market ain’t real", "i need airdrops to survive",
    "bull trap incoming?", "entry was pure alpha", "gas fees got me broke",
    "the vibes were immaculate", "that rug was cinematic", "we living on testnet",
    "L2 season heating up"
]

reflective_responses = [
    "every wallet holds a story", "i've seen rugpulls teach more than books",
    "your seed phrase is your soul", "market cycles mirror human emotion",
    "sometimes the best trade is no trade", "degen but introspective",
    "each token is a bet on belief", "charts don’t capture conviction",
    "gas fees humble us all", "i miss the quiet of bear season",
    "the blockchain remembers everything", "hodling is a meditation",
    "trading tests your patience, then your sanity", "i stare at red candles like they owe me money",
    "even the best alpha fades with time", "bull markets feed egos, bear markets feed wisdom"
]

short_lines = [
    "wen moon 🌕", "airdrop hunter", "degen vibes", "hodl tight", "buy signal 🔥",
    "eth gas 🫠", "sol dev grind", "pepe pump", "ledger flex", "keplr zen",
    "phantom sleek", "zkSync 🔮", "wallet wars", "seed phrase god", "exit liquidity",
    "chart addict", "L1 chad", "OP retrodrop", "ETH L2 boom", "flippening vibes"
]

extended_lines = [
    "gas fees ate my soul", "bridged tokens and prayed", "airdrop was pure dopamine",
    "my wallet is a battlefield", "zkSync made me believe again",
    "phantom feels like silk", "ledger gives me peace of mind",
    "keplr vibes are underrated", "eth staking finally paid off",
    "pepe holders turned prophets", "polygon keeps building",
    "sol devs never sleep", "avax speed is unreal", "wallet UX changed the game",
    "trading memes > fundamentals"
]

def get_unique_response(pool, used):
    choices = [msg for msg in pool if msg not in used]
    selected = random.choice(choices if choices else pool)
    used.add(selected)
    return selected

def generate_convo():
    convo = []
    used_lines = set()

    greet0, greet1 = random.choice(greetings)
    convo.append(f"user0: {greet0}")
    convo.append(f"user1: {greet1}")

    topic_key = random.choice(list(crypto_data.keys()))
    data = crypto_data[topic_key]

    msg0 = get_unique_response(data["starter"], used_lines)
    convo.append(f"user0: {msg0}")

    msg1 = get_unique_response(data["replies"], used_lines)
    convo.append(f"user1: {msg1}")

    followup1 = get_unique_response(data["followups"], used_lines)
    convo.append(f"user0: {followup1}")

    meme = get_unique_response(meme_responses, used_lines)
    convo.append(f"user1: {meme}")

    # Inject reflective line occasionally
    if random.random() < 0.2:
        reflection = get_unique_response(reflective_responses, used_lines)
        convo.append(f"user{random.choice([0, 1])}: {reflection}")

    return convo

def generate_short_sentences(count=400):
    return [random.choice(short_lines) for _ in range(count)]

def generate_extended_sentences(count=400):
    return [random.choice(extended_lines) for _ in range(count)]

# Generate main conversation
conversation = []
for _ in range(500):  # ~2000 lines total
    conversation.extend(generate_convo())

# Generate short and extended meme-style sentences
short_sentences = generate_short_sentences()
extended_sentences = generate_extended_sentences()

# Write to file
with open("conversation.txt", "w", encoding="utf-8") as f:
    for line in conversation:
        f.write(f"{line}\n")
    f.write("\n# Short Sentences\n")
    for line in short_sentences:
        f.write(f"{line}\n")
    f.write("\n# Extended Sentences\n")
    for line in extended_sentences:
        f.write(f"{line}\n")

print("✅ Done: 2000 crypto convo lines + 400 short + 400 extended + sprinkled reflection.")
