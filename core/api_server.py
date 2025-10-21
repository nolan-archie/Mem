

from fastapi import FastAPI, HTTPException, BackgroundTasks

from pydantic import BaseModel

from typing import Optional, List, Any

from .utils.logging import log_action

from core.brain import Brain



brain = Brain()



from .memory_rag import MR

from .mood_engine import mood_engine  

from .pmgr import pmgr



app = FastAPI(title="Mainmi Local API", version="0.1")

class ChatRequest(BaseModel):

    text: str

    memory_limit: Optional[int] = 6



class MemoryAddReq(BaseModel):

    text: str

    tags: Optional[List[str]] = None



class ApprovalReq(BaseModel):

    action: str

    reason: str

    ttl_seconds: Optional[int] = None

@app.post("/chat")

async def chat(req: ChatRequest):

    log_action("api_request", {"endpoint": "/chat", "text_len": len(req.text)})

    if not req.text:

        raise HTTPException(400, "empty text")

    try:

        reply = brain.chat(req.text, req.memory_limit)

        log_action("api_response", {"endpoint": "/chat", "ok": True})

    except Exception as e:

        log_action("api_error", {"endpoint": "/chat", "err": str(e)}, "error")

        raise HTTPException(500, f"brain error: {e}")

    return {"reply": reply}





@app.get("/memories/search")

async def memories_search(q: str, k: int = 5):

    log_action("api_request", {"endpoint": "/memories/search", "query_len": len(q)})

    return {"results": MR.search(q, k=k)}



@app.post("/memories/add")

async def memories_add(req: MemoryAddReq):

    log_action("api_request", {"endpoint": "/memories/add", "text_len": len(req.text)})

    e = MR.add_memory(req.text, tags=req.tags)

    return {"ok": True, "entry": e.to_dict()}



@app.get("/memories/list")

async def memories_list(limit: int = 50):

    log_action("api_request", {"endpoint": "/memories/list"})

    return {"count": len(MR.list_memories()), "memories": MR.list_memories(limit=limit)}



@app.post("/memories/delete")

async def memories_delete(id: str):

    log_action("api_request", {"endpoint": "/memories/delete", "id": id})

    ok = MR.delete_memory(id)

    return {"deleted": ok}

@app.get("/mood")

async def mood_get():

    log_action("api_request", {"endpoint": "/mood"})

    return {"mood": mood_engine.current_state(), "summary": mood_engine.current_summary()}



@app.post("/mood/adjust")

async def mood_adjust(curiosity: float = 0.0, affection: float = 0.0, energy: float = 0.0, focus: float = 0.0):

    log_action("api_request", {"endpoint": "/mood/adjust"})

    mood_engine.adjust(curiosity_delta=curiosity, affection_delta=affection, energy_delta=energy, focus_delta=focus)

    return {"mood": mood_engine.current_state()}





@app.get("/action")

async def action():

    log_action("api_request", {"endpoint": "/action"})

    return decide_action()





@app.post("/pmgr/request")

async def pmgr_request(req: ApprovalReq):

    log_action("api_request", {"endpoint": "/pmgr/request", "action": req.action})

    token = pmgr.request_approval(req.action, req.reason, ttl=req.ttl_seconds)

    ttl = pmgr.config.get("ephemeral_token_policy", {}).get("default_ttl_seconds", 600)

    return {"token": token, "expires_seconds": ttl}



@app.post("/pmgr/approve")

async def pmgr_approve(token: str):

    log_action("api_request", {"endpoint": "/pmgr/approve", "token": token})

    ok = pmgr.approve(token)

    return {"approved": ok}



@app.get("/pmgr/check")

async def pmgr_check(token: str):

    log_action("api_request", {"endpoint": "/pmgr/check", "token": token})

    ok = pmgr.check_approval(token)

    return {"approved": ok}



@app.get("/health")

async def health():

    log_action("api_request", {"endpoint": "/health"})

    return {"ok": True, "memory_count": len(MR.list_memories())}



def _daily_reflection():

    try:

        recent = MR.list_memories(limit=20)

        texts = [m["text"] for m in recent]

        summary = " | ".join([t[:120] for t in texts])

        mood_engine.reflect_and_log(f"Auto-reflection: {summary}")

    except Exception:

        pass



@app.post("/admin/reflection")

async def force_reflection(bg: BackgroundTasks):

    log_action("api_request", {"endpoint": "/admin/reflection"})

    bg.add_task(_daily_reflection)

    return {"queued": True}



