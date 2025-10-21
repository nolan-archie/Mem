                                

                                     



import os

import json

import datetime



LOG_FILE = os.path.expanduser("~/Mainmi/logs/mainmi.log")

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)



def log_action(action: str, data: dict = None, level: str = "info") -> None:

    """
    Record structured logs to file and print to console.
    Args:
        action (str): Name of the action or event.
        data (dict): Optional contextual data.
        level (str): Log level: "info", "warn", "error".
    """

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    entry = {

        "time": timestamp,

        "level": level.upper(),

        "action": action,

        "data": data or {}

    }



                                       

    color = {

        "INFO": "\033[94m",

        "WARN": "\033[93m",

        "ERROR": "\033[91m"

    }.get(entry["level"], "\033[0m")

    print(f"{color}[{entry['time']}] {entry['level']}: {entry['action']} - {entry['data']}\033[0m")



                                      

    try:

        with open(LOG_FILE, "a", encoding="utf-8") as f:

            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    except Exception as e:

        print(f"\033[91m[LOGGING ERROR]\033[0m Could not write log: {e}")

