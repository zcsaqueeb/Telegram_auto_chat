import random

users = ["user0", "user1"]

greetings = [
    ("yo", "what’s up"), ("sup", "heyyy"), ("hello", "yo"), ("hii", "hey"),
    ("you there?", "yeah what’s up"), ("heyyy", "hello"), ("yo", "sup")
]

wwe_data = {
    "Attitude Era": {
        "starter": [
            "stone cold just stunned everyone", "the rock’s promo had me dying",
            "undertaker’s entrance gave me chills", "dx was pure chaos"
        ],
        "replies": [
            "bro smashed beers mid-match", "that promo was peak disrespect",
            "i still hear the glass shatter", "triple h was ruthless"
        ],
        "followups": [
            "wrestling hasn’t been the same", "they had no chill back then",
            "felt like watching a street fight", "every episode was wild"
        ]
    },
    "Ruthless Aggression": {
        "starter": [
            "john cena’s debut was iconic", "batista vs undertaker was brutal",
            "brock lesnar was a beast", "edge cashed in MITB like a villain"
        ],
        "replies": [
            "cena really said: you can’t see me", "batista bomb hit different",
            "lesnar broke the ring once", "edge was the ultimate opportunist"
        ],
        "followups": [
            "that era was pure intensity", "every feud felt personal",
            "wrestlers had actual grit", "storylines were top tier"
        ]
    },
    "Golden Era": {
        "starter": [
            "hulkamania ran wild", "andre the giant was unstoppable",
            "macho man’s promos were legendary", "ultimate warrior was electric"
        ],
        "replies": [
            "hogan lifted andre like it was nothing", "those entrances were epic",
            "macho man had unmatched energy", "warrior sprinted like a maniac"
        ],
        "followups": [
            "wrestling was pure spectacle", "they built legends back then",
            "felt like watching superheroes", "crowds were insane"
        ]
    }
}

meme_responses = [
    "bro that match was pure chaos", "i still quote that promo daily",
    "wrestling used to hit different", "they don’t make entrances like that anymore",
    "i paused just to scream", "that chair shot was criminal",
    "peak storytelling fr", "i miss those pyro intros",
    "every match felt like a movie", "they animated pain in real life"
]

short_lines = [
    "glass shatter 💥", "dx wildin", "cena GOAT", "rip kayfabe", "edge sneaky",
    "rock promo 🔥", "undertaker 😱", "lesnar beast", "batista bomb", "hogan flex",
    "macho vibes", "warrior sprint", "pipebomb 💣", "chair shot", "MITB cash-in",
    "heel turn", "popcorn match", "no chill", "pure heat", "legend vibes"
]

extended_lines = [
    "stone cold stunned the whole roster", "the rock cooked that promo to perfection",
    "undertaker’s entrance was cinematic", "cena’s debut had the crowd roaring",
    "edge cashed in like a true villain", "batista bomb shook the ring",
    "lesnar broke the ring with big show", "dx made every segment chaotic",
    "macho man’s energy was unmatched", "hogan vs andre was pure spectacle",
    "warrior sprinted like a superhero", "pipebomb changed wrestling forever",
    "every feud felt personal back then", "pyro intros were next level",
    "wrestling was peak drama in that era"
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

    topic_key = random.choice(list(wwe_data.keys()))
    data = wwe_data[topic_key]

    msg0 = get_unique_response(data["starter"], used_lines)
    convo.append(f"user0: {msg0}")

    msg1 = get_unique_response(data["replies"], used_lines)
    convo.append(f"user1: {msg1}")

    followup1 = get_unique_response(data["followups"], used_lines)
    convo.append(f"user0: {followup1}")

    meme = get_unique_response(meme_responses, used_lines)
    convo.append(f"user1: {meme}")

    return convo

def generate_short_sentences(count=1000):
    return [random.choice(short_lines) for _ in range(count)]

def generate_extended_sentences(count=1000):
    return [random.choice(extended_lines) for _ in range(count)]

# Generate main conversation
conversation = []
for _ in range(2500):  # ~10,000 lines total
    conversation.extend(generate_convo())

# Generate short and extended meme-style sentences
short_sentences = generate_short_sentences(1000)
extended_sentences = generate_extended_sentences(1000)

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

print("✅ Done: 10,000+ WWE convo lines + 1000 short + 1000 extended meme shots saved.")
