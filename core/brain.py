



import os

import time

import random

import httpx

import nest_asyncio

from datetime import datetime, timedelta

from typing import Optional, Callable, Dict, Any, List, Tuple



from core.utils.logging import log_action

from core.personality_loader import P

from core.mood_engine import mood_engine

from core.memory_rag import MR



nest_asyncio.apply()



                

GITHUB_TOKEN = "git token here"

MODEL_NAME = "meta/Meta-Llama-3.1-8B-Instruct"

API_URL = "https://models.github.ai/inference/chat/completions"



REQUEST_TIMEOUT = 30.0

RETRIES = 4

BASE_RETRY_DELAY = 1.0

MAX_MEMORY_SNIPPET = 150

CONVERSATION_HISTORY_SIZE = 10



StreamCallback = Optional[Callable[[str], None]]





                 

class Sensor:

    def read(self, *args, **kwargs) -> Dict[str, Any]:

        raise NotImplementedError





class DateSensor(Sensor):

    def read(self):

        now = datetime.now()

        return {

            "type": "date",

            "iso": now.isoformat(),

            "day": now.day,

            "month": now.month,

            "year": now.year,

            "hour": now.hour,

            "minute": now.minute,

        }





class MoodCycleSensor(Sensor):

    def read(self):

        return {"type": "mood_cycle", "moody_day": random.random() < 0.1}





class CuriositySensor(Sensor):

    def read(self):

        return {"type": "curiosity_spike", "active": random.random() < 0.15}





class RandomThoughtSensor(Sensor):

    def read(self):

        thoughts = [

            "I wonder what dreams feel like to you.",

            "It’s quiet... maybe too quiet.",

            "I should ask you something fun next time.",

        ]

        return {"type": "random_thought", "thought": random.choice(thoughts)}





class SensorManager:

    def __init__(self):

        self.sensors = [DateSensor(), MoodCycleSensor(), CuriositySensor(), RandomThoughtSensor()]



    def read_all(self, user_input: Optional[str] = None):

        readings = []

        for s in self.sensors:

            try:

                readings.append(s.read())

            except Exception as e:

                log_action("sensor_fail", {"sensor": s.__class__.__name__, "err": str(e)}, "warn")

        return readings





               

class Brain:

    def __init__(self):

        self.persona = P

        self.mood = mood_engine

        self._client = httpx.Client(timeout=REQUEST_TIMEOUT)

        self.headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Content-Type": "application/json"}

        self.sensor_manager = SensorManager()



        self.chat_history: List[Tuple[str, str, str]] = []                                  

        self.last_action_time = time.time()

        self.last_memory_update = time.time()

        self.memory_update_interval = 1800                 



        self.notify_callback: Optional[Callable[[str], None]] = lambda msg: None



                      

    def _safe_memories(self, user_input: str) -> str:

        try:

            memories = MR.search(user_input, k=8)

                                                                                  

            out = []

            for m in memories:

                ts = m.get("timestamp") or m.get("time") or "?"

                text = str(m.get("text") or m.get("content") or "")[:MAX_MEMORY_SNIPPET]

                out.append(f"[{ts}] {text}")

            return "\n".join(out)

        except Exception as e:

            log_action("memory_search_fail", {"err": str(e)}, "warn")

            return ""



                     

    def perceive_environment(self, user_input: Optional[str] = None) -> str:

        sensors = self.sensor_manager.read_all(user_input)

        return " | ".join(str(s) for s in sensors)



                              

    def _offline_reply(self, user_input: str) -> str:

        try:

            mood = self.mood.snapshot()

        except Exception:

            mood = {"curiosity": 0.5, "affection": 0.5}

        mems = self._safe_memories(user_input)

        return (

            f"[Offline] Sorry, I can’t reach my main brain right now. "

            f"Based on memory, earlier topics: {mems[:200]}. "

            f"My mood snapshot: curiosity={mood.get('curiosity',0.5):.2f}, "

            f"affection={mood.get('affection',0.5):.2f}."

        )



                                               

    def _call_github_sync(self, messages: List[Dict], stream_cb: StreamCallback = None) -> str:

        """Calls GitHub AI API and ensures complete-sentence ending if needed."""

        for attempt in range(RETRIES):

            try:

                payload = {

                    "model": MODEL_NAME,

                    "temperature": 0.8,

                    "max_tokens": 600,

                    "messages": messages,

                }

                r = self._client.post(API_URL, json=payload, headers=self.headers)

                if r.status_code == 200:

                    data = r.json()

                    text = data.get("choices", [{}])[0].get("message", {}).get("content", "")

                    if not isinstance(text, str):

                        text = str(text or "")



                    text = text.strip()



                                                                                     

                    if text and not text.endswith((".", "!", "?")):

                        text = text + "."



                    if stream_cb:

                        stream_cb(text)

                    return text



                elif r.status_code == 429:

                    time.sleep(BASE_RETRY_DELAY * (attempt + 1))

                else:

                    log_action("github_ai_fail", {"code": r.status_code, "text": r.text}, "warn")

            except Exception as e:

                log_action("api_error", {"err": str(e)}, "warn")

                time.sleep(BASE_RETRY_DELAY)

        return self._offline_reply(messages[-1]["content"] if messages else "")



                      

    def _autonomy_tick(self):

        now = time.time()

        if now - self.last_memory_update > self.memory_update_interval:

            try:

                MR.add_memory(f"Autonomy tick: current mood {self.mood.snapshot()}")

            except Exception:

                pass

            self.last_memory_update = now



                                                                 

    def chat(self, user_input: str, stream_callback: StreamCallback = None) -> str:

        """Main chat with improved time-aware memory recall and contextual reasoning."""

        now = datetime.now()

        now_iso = now.isoformat()

        env = self.perceive_environment(user_input)

        memories = self._safe_memories(user_input)

        try:

            mood = self.mood.snapshot()

        except Exception:

            mood = {"curiosity": 0.5, "affection": 0.5}



                                                   

        yesterday = (now - timedelta(days=1)).strftime("%A, %B %d, %Y")

        date_context = (

            f"Current time: {now.strftime('%H:%M on %A, %B %d, %Y')}. "

            f"If the user says 'yesterday', interpret that as {yesterday}."

        )



                                                       

        self.chat_history.append((now_iso, "user", user_input))

                     

        if len(self.chat_history) > CONVERSATION_HISTORY_SIZE:

            self.chat_history = self.chat_history[-CONVERSATION_HISTORY_SIZE :]



                                                                                  

        system_prompt = (

            f"You are {self.persona}, a playful, emotionally intelligent AI companion named Mainmi. "

            f"Always reply in full, natural sentences and avoid cutting off mid-thought. "

            f"Reference exact dates/times accurately using the user's timezone. {date_context} "

            f"Environment: {env}. Mood: curiosity={mood.get('curiosity',0.5):.2f}, "

            f"affection={mood.get('affection',0.5):.2f}. Relevant memories (recent):\n{memories[:400]}"

        )



        messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]



                                                                          

        for ts, role, msg in self.chat_history:

            role_name = "user" if role == "user" else "assistant"

                                                                        

            messages.append({"role": role_name, "content": f"[{ts}] {msg}"})



                      

        try:

            response = self._call_github_sync(messages, stream_cb=stream_callback)

        except Exception:

            response = self._offline_reply(user_input)

            if stream_callback:

                stream_callback(response)



                                                                          

        resp_time_iso = datetime.now().isoformat()

        self.chat_history.append((resp_time_iso, "Mainmi", response))

        try:

            MR.add_memory({"timestamp": now_iso, "text": f"User: {user_input}"})

            MR.add_memory({"timestamp": resp_time_iso, "text": f"Mainmi: {response}"})

        except Exception:

                                                                             

            try:

                MR.add_memory(f"[{now_iso}] User: {user_input}")

                MR.add_memory(f"[{resp_time_iso}] Mainmi: {response}")

            except Exception:

                pass



                               

        self._autonomy_tick()

        return response

