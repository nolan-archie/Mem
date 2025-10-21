                                                                                                                                                                                         



import time

from datetime import datetime

from .brain import brain

from .mood_engine import mood_engine

from .autonomy import decide_action

from .memory_rag import MR



LOG_FILE = "../logs/scheduler.log"                



def log(msg):

    ts = datetime.now().isoformat()

    with open(LOG_FILE, "a") as f:

        f.write(f"{ts} {msg}\n")



def morning_routine():

    brain.chat("Good morning! What's on today?")

    mood_engine.adjust(energy_delta=0.1)

    log("Morning greet")



def midday_routine():

    action = decide_action()

    if action["action"] != "idle":

        brain.chat(action["text"])

    log("Midday tick")



def evening_routine():

    recent = [m["text"] for m in MR.list_memories(limit=10)]

    summary = " ".join(recent[:5])

    mood_engine.reflect_and_log(summary)

    mood_engine.adjust(energy_delta=-0.2)

    log("Evening reflection")



while True:

    now = datetime.now()

    hour = now.hour

    if 6 <= hour < 9:

        morning_routine()

    elif 12 <= hour < 15:

        midday_routine()

    elif 18 <= hour < 21:

        evening_routine()

    else:

        action = decide_action()

        if action["action"] == "explore":

            log(f"Autonomy: {action['text']}")

    time.sleep(60)            
