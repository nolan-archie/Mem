

import sys

import time

import select

import subprocess

from pathlib import Path

from typing import Optional, Callable



                            

PROJECT_ROOT = Path(__file__).resolve().parent

if str(PROJECT_ROOT) not in sys.path:

    sys.path.insert(0, str(PROJECT_ROOT))



                        

from core.brain import Brain

from core.personality_loader import P



                                        

def start_server() -> subprocess.Popen:

    """
    Start the Uvicorn server in the background.
    Returns the subprocess.Popen instance.
    """

    print("Starting server in the background...")

    server_cmd = [

        sys.executable, "-m", "uvicorn",

        "core.api_server:app",

        "--host", "127.0.0.1",

        "--port", "8000",

        "--reload"

    ]

                                                

    return subprocess.Popen(server_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)



server_process = start_server()

time.sleep(2)                             



                               

brain = Brain()





def print_welcome() -> None:

    """Display Mainmi's identity and short instructions."""

    meta = P.get("meta") or {}

    personality = P.get("personality") or {}

    name = meta.get("name", "Mainmi")

    pron = meta.get("pronunciation", "")

    archetypes = personality.get("archetype", []) or []

    archetype = ", ".join(archetypes) if archetypes else "Unknown archetype"

    pron_text = f" ({pron})" if pron else ""

    print(f"Welcome to {name}{pron_text}'s CLI chat! Archetype: {archetype}")

    print("Type your message and press Enter.")

    print("Commands: /mood (check mood), /happy, /sad, /quit (exit)\n")





def chat_loop() -> None:

    """Main chat loop with streaming removed and idle/autonomy handled."""

    mood_engine = brain.mood



    def autonomy_notify(message: str) -> None:

        """Called by Brain during idle ticks."""

        print(f"\n[Autonomy] {message}\nYou: ", end="", flush=True)



                                               

    brain.notify_callback = autonomy_notify



    last_action_time = time.time()                          

    auto_interval = 30                                     

    tick_timeout = 1.0                      



    try:

        while True:

                                      

            ready = select.select([sys.stdin], [], [], tick_timeout)[0]

            current_time = time.time()



            if ready:

                user_input = sys.stdin.readline().strip()

                last_action_time = current_time              



                if not user_input:

                    continue



                cmd = user_input.lower()

                if cmd in {"/quit", "/exit"}:

                    print("Goodbye!")

                    break

                elif cmd == "/mood":

                    try:

                        mood = mood_engine.snapshot()

                        print("Current mood:", ", ".join(f"{k}={v:.2f}" for k, v in mood.items()))

                    except Exception:

                        print("Mood unavailable.")

                    continue

                elif cmd == "/happy":

                    mood_engine.adjust(affection_delta=0.05)

                    print("Mood nudged happier.")

                    continue

                elif cmd == "/sad":

                    mood_engine.adjust(affection_delta=-0.05)

                    print("Mood nudged sadder.")

                    continue



                             

                try:

                    reply = brain.chat(user_input)                         

                    print(f"Mainmi: {reply}\n")

                except Exception as e:

                    print(f"\n[Error] {e} (Check network/API key.)")



            else:

                                    

                if current_time - last_action_time > auto_interval:

                    brain._autonomy_tick()

                    last_action_time = current_time                    



            time.sleep(0.1)                                  



    except (EOFError, KeyboardInterrupt):

        print("\nGoodbye!")

    finally:

        brain.notify_callback = None                    

                              

        server_process.terminate()

        server_process.wait()

        print("Server stopped.")





if __name__ == "__main__":

    print_welcome()

    chat_loop()

