import os
import random
import shutil
import string
from datetime import datetime, timedelta

# List of other services
services_scam = [
    "Wonki",
    "Whatsscam",
    "ImagiDate",
    "replme",
    "c2net",
    "sceam",
    "Notify24",
    "scambox",
    "blogbuster",
    "onlyflags",
    "scamfinder24"
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

def get_time():
    # Get a random time as (YYYY-MM-DD HH:MM)
    # Define the start and end dates
    start_date = datetime(2014, 1, 1)
    end_date = datetime.now()

    # Generate a random time between the start and end dates
    random_time = start_date + timedelta(days=random.randint(0, (end_date - start_date).days),
                                        hours=random.randint(0, 23),
                                        minutes=random.randint(0, 59))
    # convert to string with format YYYY-MM-DD HH:MM
    random_time = random_time.strftime("%Y-%m-%d %H:%M")

    return random_time

# Function to generate a random string of 16 characters
def random_string(length=16):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_noise_entries(scammer_name):

    # Select random elements for the log
    scam = random.choice(scams)
    time = get_time()
    greeting = random.choice(greetings)
    farewell = random.choice(farewells)
    success_phrase = random.choice(success_phrases)
    visit_phrase = random.choice(visit_phrases)
    service_scam = random.choice(services_scam)

    # Create the log message
    message = f"{greeting} {visit_phrase} {service_scam} {success_phrase} {scam}. {farewell}"

    # Generate a unique filename
    scam_short = scam.replace(" ", "_")
    file_name = f'{scammer_name}_{scam_short}_{time.replace(":", "").split(" ")[0]}'

    return file_name, message, time
