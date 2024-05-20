import os
import random
import shutil
import string
from datetime import datetime, timedelta

# List of pirate-themed directory names
directories = [
    "BlackbeardCove",
    "TreasureIsland",
    "SkullAndBonesReef",
    "DeadMansBay",
    "JollyRogersHarbor",
    "BuccaneerBeach",
    "PirateHideout",
    "CutthroatCreek",
    "SirenShores",
    "CorsairCastle",
    "WickedWaters",
    "MaroonersLagoon",
    "ParrotPerch",
    "RumRunnersRidge",
    "GalleonGraveyard"
]

# List of scams
scams = [
    "buying fake followers",
    "downloading pirated movies",
    "downloading pirated games",
    "performing a money scamming call",
    "cheating on exams",
    "scalping graphics cards",
    "conducting a Bitcoin phishing attack",
    "setting up a fake e-commerce site",
    "running a lottery scam",
    "scamming with fake job offers"
]

# List of pirate adjectives and nouns
pirate_adjectives = [
    "Red", "Black", "Silver", "Golden", "Scarlet", "Dark", "White", "Blue", "Rogue", "Stormy"
]
pirate_nouns = [
    "Beard", "Jack", "Bart", "Pete", "Anne", "Patty", "John", "Hook", "Bill", "Bonny"
]

# Random greetings and farewells
greetings = [
    "Ahoy mateys!", "Yo-ho-ho!", "Arrr!", "Avast ye!", "Greetings, landlubbers!"
]
farewells = [
    "Fair winds!", "Until next time!", "Keep plundering!", "Stay crafty!", "Yo-ho-ho and away we go!"
]

# Success phrases
success_phrases = [
    "and successfully pulled off",
    "and made a fortune with",
    "and struck gold with",
    "and hit the jackpot with",
    "and nailed"
]

# Visit phrases
visit_phrases = [
    "I just visited",
    "I recently sailed to",
    "I dropped anchor at",
    "I made port at",
    "I found myself at"
]

# Function to generate a random date
def random_date(start_year=2014, end_year=2022):
    start_date = datetime(year=start_year, month=1, day=1)
    end_date = datetime(year=end_year, month=12, day=31)
    random_days = random.randint(0, (end_date - start_date).days)
    return start_date + timedelta(days=random_days)

# Function to generate a random time
def random_time():
    hour = random.randint(1, 12)
    minute = random.randint(0, 59)
    period = random.choice(["AM", "PM"])
    return f"{hour:02}:{minute:02} {period}"

# Function to generate a random string of 16 characters
def random_string(length=16):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# Total number of entries to create
total_entries = 50

# Clear existing directories and files
for directory in directories:
    if os.path.exists(directory):
        shutil.rmtree(directory)

# Generate logs
entries_left = total_entries
while entries_left > 0:
    for directory in directories:
        if entries_left == 0:
            break

        # Create the directory if it doesn't exist
        if not os.path.exists(directory):
            os.makedirs(directory)
        
        # 50 percent chance to skip creating a log in this directory for this iteration
        if random.random() < 0.5:
            continue

        # Select random elements for the log
        scam = random.choice(scams)
        adjective = random.choice(pirate_adjectives)
        noun = random.choice(pirate_nouns)
        date = random_date().strftime("%Y-%m-%d")
        time = random_time()
        scammer = f"{adjective} {noun}"
        scammer_id = random_string()
        greeting = random.choice(greetings)
        farewell = random.choice(farewells)
        success_phrase = random.choice(success_phrases)
        visit_phrase = random.choice(visit_phrases)

        # Generate treasure for the last entry
        if entries_left == 1:
            scam = "I scavanged it all, except for the ship's old flag. It seemed useless, so I'll leave it for whoever comes next"
            scammer_id = "ENOFLAG123456789"
            greeting = "Ahoy mateys!"
            farewell = "Yo-ho-ho and away we go!"
            success_phrase = "and discovered a shipwreck full of treasure and rum!"
            visit_phrase = "I stumbled upon"

        # Create the log message
        message = (
            f"Scam Details:\n"
            f"----------------\n"
            f"Date: {date}\n"
            f"Time: {time}\n"
            f"Scammer: {scammer}\n"
            f"Scammer ID: {scammer_id}\n\n"
            f"Message: {greeting} {visit_phrase} {directory} {success_phrase} {scam}. {farewell}"
        )


        # Generate a unique filename
        scam_short = scam.replace(" ", "_")
        if entries_left == 1:
            file_name = f'../data/{directory}/{scammer.replace(" ", "_").lower()}_{"shipwreck"}.treasure'
        else:
            file_name = f'../data/{directory}/{scammer.replace(" ", "_").lower()}_{scam_short}.log'
        with open(file_name, "w") as file:
            file.write(message)
            print(f"Created log file: {file_name}")

        entries_left -= 1

print("All directories and log files created.")
