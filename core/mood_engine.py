                            

"""
Robust MoodEngine for Mainmi.

- Seeds initial mood from persona (P) safely.
- Provides set_state(), blend_state(), current_summary(), snapshot(), reset().
"""



import time

from typing import Optional, Dict, Any

from core.utils.logging import log_action



                                

try:

    from core.personality_loader import P                

except Exception:

    P = {}



class MoodEngine:

    def __init__(self, initial: Optional[Dict[str, float]] = None):

        traits = {}

        if initial:

            traits = dict(initial)

        else:

            try:

                if isinstance(P, dict):

                    traits = (P.get("personality") or {}).get("initial_traits") or {}

                else:

                    pdata = getattr(P, "data", None)

                    if isinstance(pdata, dict):

                        traits = (pdata.get("personality") or {}).get("initial_traits") or {}

                    else:

                        per = getattr(P, "personality", None)

                        if isinstance(per, dict):

                            traits = per.get("initial_traits") or {}

            except Exception:

                traits = {}



        def _clamp_float(val, fallback=0.5):

            try:

                v = float(val)

                return max(0.0, min(1.0, v))

            except Exception:

                return float(fallback)



        self.curiosity = _clamp_float(traits.get("curiosity", 0.5))

        self.affection = _clamp_float(traits.get("affection", 0.5))

        self.energy = _clamp_float(traits.get("energy", 0.5))

        self.focus = _clamp_float(traits.get("focus", 0.5))



        self.last_update = time.time()

        self.decay_rate = 0.0006



    def _decay(self) -> None:

        now = time.time()

        delta = now - self.last_update

        if delta <= 0:

            return

        decay_amount = delta * self.decay_rate

        for attr in ("curiosity", "affection", "energy", "focus"):

            val = getattr(self, attr)

            if val > 0.5:

                val = max(0.5, val - decay_amount)

            elif val < 0.5:

                val = min(0.5, val + decay_amount)

            setattr(self, attr, val)

        self.last_update = now



    def set_state(self,

                  curiosity: Optional[float] = None,

                  affection: Optional[float] = None,

                  energy: Optional[float] = None,

                  focus: Optional[float] = None) -> None:

        self._decay()

        def clamp(x): return max(0.0, min(1.0, float(x))) if x is not None else None

        if curiosity is not None:

            self.curiosity = clamp(curiosity)

        if affection is not None:

            self.affection = clamp(affection)

        if energy is not None:

            self.energy = clamp(energy)

        if focus is not None:

            self.focus = clamp(focus)

        self.last_update = time.time()

        try:

            log_action("mood_state_update", self.snapshot(), "info")

        except Exception:

            pass



    def blend_state(self, curiosity: float, affection: float,

                    energy: float, focus: float, rate: float = 0.18) -> None:

        self._decay()

        def lerp(a, b, t): return a + (b - a) * t

        curiosity = float(curiosity) if curiosity is not None else self.curiosity

        affection = float(affection) if affection is not None else self.affection

        energy = float(energy) if energy is not None else self.energy

        focus = float(focus) if focus is not None else self.focus

        self.curiosity = max(0.0, min(1.0, lerp(self.curiosity, curiosity, rate)))

        self.affection = max(0.0, min(1.0, lerp(self.affection, affection, rate)))

        self.energy = max(0.0, min(1.0, lerp(self.energy, energy, rate)))

        self.focus = max(0.0, min(1.0, lerp(self.focus, focus, rate)))

        self.last_update = time.time()

        try:

            log_action("mood_blend_update", self.snapshot(), "info")

        except Exception:

            pass



    def current_summary(self) -> str:

        self._decay()

        return (

            f"Curiosity {int(self.curiosity * 100)}%, "

            f"Affection {int(self.affection * 100)}%, "

            f"Energy {int(self.energy * 100)}%, "

            f"Focus {int(self.focus * 100)}%"

        )



    def snapshot(self) -> Dict[str, Any]:

        self._decay()

        return {

            "curiosity": round(self.curiosity, 3),

            "affection": round(self.affection, 3),

            "energy": round(self.energy, 3),

            "focus": round(self.focus, 3),

            "last_update": round(self.last_update, 2)

        }



    def reset(self) -> None:

        self.curiosity = 0.5

        self.affection = 0.5

        self.energy = 0.5

        self.focus = 0.5

        self.last_update = time.time()

        try:

            log_action("mood_reset", self.snapshot(), "info")

        except Exception:

            pass



           

mood_engine = MoodEngine()

