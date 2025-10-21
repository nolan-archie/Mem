                  

                                          

                                                                      



from fastapi import FastAPI

from pydantic import BaseModel

import os

import typing as t



app = FastAPI(title="Mainmi Local Embed Service")



                                                                                               

try:

    from sentence_transformers import SentenceTransformer

    import numpy as np

    ST_AVAILABLE = True

except Exception:

    SentenceTransformer = None

    np = None

    ST_AVAILABLE = False



                                      

_EMBED_MODEL = None

EMBED_MODEL_NAME = os.environ.get("MAINMI_EMBED_MODEL", "all-MiniLM-L6-v2")

DEFAULT_DIM = 384



class EmbedReq(BaseModel):

    texts: t.List[str]



def _ensure_model():

    global _EMBED_MODEL

    if _EMBED_MODEL is not None:

        return

    if ST_AVAILABLE:

        try:

            _EMBED_MODEL = SentenceTransformer(EMBED_MODEL_NAME)

            return

        except Exception:

            _EMBED_MODEL = None

                                                                      

    _EMBED_MODEL = None



def _embed_with_model(texts: t.List[str]) -> t.List[t.List[float]]:

    """
    Returns list of float lists (numpy arrays converted) normalized.
    """

    _ensure_model()

    if _EMBED_MODEL is not None:

        arr = _EMBED_MODEL.encode(texts, convert_to_numpy=True)

                        

        norms = (arr**2).sum(axis=1, keepdims=True)**0.5 + 1e-12

        arr = (arr / norms).astype("float32")

        return arr.tolist()

                                                            

    out = []

    for t in texts:

        vec = [0.0] * DEFAULT_DIM

        for i, ch in enumerate(t[:DEFAULT_DIM]):

            vec[i] = (ord(ch) % 100) / 100.0

                   

        s = sum(x*x for x in vec) ** 0.5 + 1e-12

        out.append([x / s for x in vec])

    return out



@app.get("/")

def root():

    return {"ok": True, "service": "embed_service", "st_available": ST_AVAILABLE}



@app.post("/embed")

def embed(req: EmbedReq):

    if not req.texts:

        return {"embeddings": []}

    try:

        embs = _embed_with_model(req.texts)

        return {"embeddings": embs}

    except Exception as e:

                                                              

        return {"embeddings": _embed_with_model(req.texts), "warning": str(e)}

