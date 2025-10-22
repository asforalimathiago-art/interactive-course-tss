from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import json, csv, yaml, os, random, hashlib, logging
from pathlib import Path

from tss_crypto import tss_create, tss_reconstruct

LOG = logging.getLogger("course_tss")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Course+TSS", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
if Path("index.html").exists():
    app.mount("/", StaticFiles(directory=".", html=True), name="static")

RULES = yaml.safe_load(open("adaptive_rules.yaml", "r", encoding="utf-8"))
BANK: Dict[int, dict] = {}

# Load question bank
with open("question_bank.csv", "r", encoding="utf-8") as f:
    r = csv.DictReader(f)
    for row in r:
        BANK[int(row["id"])] = {
            "id": int(row["id"]),
            "module": int(row["module"]),
            "topic": row["topic"],
            "difficulty": int(row["difficulty"]),
            "type": row["type"],
            "stem": row["stem"],
            "choices": json.loads(row["choices"]),
            "answer_key": row["answer_key"],
            "rationale": row["rationale"],
            "tags": row["tags"].split("|") if row["tags"] else [],
        }

# Simple optional persistence for STATE
STATE_FILE = Path("state.json")
try:
    if STATE_FILE.exists():
        STATE = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    else:
        STATE = {}
except Exception:
    LOG.exception("Failed to load state.json, starting with empty state")
    STATE = {}

class NextReq(BaseModel):
    session_id: str
    context: Dict[str, Any] = {}

class SubmitReq(BaseModel):
    session_id: str
    question_id: int
    selected: str

def _save_state():
    try:
        STATE_FILE.write_text(json.dumps(STATE, indent=2), encoding="utf-8")
    except Exception:
        LOG.exception("Failed to persist state.json")


def _match_role_rules(role: str) -> List[int]:
    """Safely evaluate role-based branching from RULES. Only supports simple equality checks of the form: role == 'support'"""
    prefer_modules: List[int] = []
    for rule in RULES.get("branches", {}).get("role", []):
        when = rule.get("when", "")
        if isinstance(when, str) and "==" in when:
            parts = when.split("==", 1)
            lhs = parts[0].strip()
            rhs = parts[1].strip().strip('"')
            if lhs == "role" and rhs == role:
                prefer_modules.extend(rule.get("prefer_modules", []))
    return prefer_modules


def pick(st: Dict[str, Any]):
    role = st.get("role", "support")
    preferred = _match_role_rules(role)
    candidates = [q for q in BANK.values() if (not preferred or q["module"] in preferred)]
    random.shuffle(candidates)
    attempted = set(st.get("attempted", []))
    for q in candidates:
        if q["id"] not in attempted:
            return q
    return candidates[0] if candidates else list(BANK.values())[0]

@app.post("/questionnaire/next")
def nxt(req: NextReq):
    st = STATE.setdefault(req.session_id, {"attempted": [], "correct": 0, "total": 0, **req.context})
    q = pick(st)
    q_out = {k: v for k, v in q.items() if k != "answer_key"}
    LOG.info("Next question for %s -> %s", req.session_id, q["id"])
    _save_state()
    return {"question": q_out}

@app.post("/questionnaire/submit")
def sub(req: SubmitReq):
    st = STATE.setdefault(req.session_id, {"attempted": [], "correct": 0, "total": 0})
    q = BANK.get(req.question_id)
    if not q:
        raise HTTPException(404, "Question not found")
    if q["id"] not in st.get("attempted", []):
        st["attempted"].append(q["id"])
    st["total"] = st.get("total", 0) + 1
    ok = (str(req.selected) == str(q["answer_key"]))
    if ok:
        st["correct"] = st.get("correct", 0) + 1
    fb = RULES["feedback"]["correct" if ok else "incorrect"]
    _save_state()
    return {"correct": ok, "score": round(st["correct"]/st["total"], 3), "feedback": fb, "rationale": q["rationale"]}

# TSS demo endpoints (in-memory)
PAYLOADS = {}
SHARES = {}

class TSSEventIn(BaseModel):
    org_id: str
    event_type: str
    payload: Dict[str, Any]

class TSSReconIn(BaseModel):
    payload_id: str
    provided_roles: Dict[str, str]
    reason: str

@app.post("/tss/event")
def tss_event(e: TSSEventIn):
    art = tss_create({"org_id": e.org_id, "event_type": e.event_type, "payload": e.payload}, threshold=2)
    pid = hashlib.sha256(art["cipher"]["ciphertext_b64"].encode()).hexdigest()[:16]
    PAYLOADS[pid] = {"cipher": art["cipher"], "hash": art.get("payload_hash")}
    SHARES[pid] = {s["owner_role"]: s["wrapped_share"] for s in art["shares"]}
    return {"payload_id": pid, "shares_demo": SHARES[pid]}

@app.post("/tss/reconstruct")
def tss_recon(r: TSSReconIn):
    rec = PAYLOADS.get(r.payload_id)
    if not rec:
        raise HTTPException(404, "payload not found")
    if len(r.provided_roles) < 2:
        raise HTTPException(403, "need at least 2 shares")
    data = tss_reconstruct(rec["cipher"], r.provided_roles)
    return {"ok": True, "payload_hash": rec["hash"], "data": data}
