from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Any
import json, csv, yaml, os, random, hashlib
from tss_crypto import tss_create, tss_reconstruct

app=FastAPI(title="Course+TSS",version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
if os.path.exists("index.html"): app.mount("/", StaticFiles(directory=".", html=True), name="static")

RULES=yaml.safe_load(open("adaptive_rules.yaml","r",encoding="utf-8"))
BANK={}
with open("question_bank.csv","r",encoding="utf-8") as f:
    r=csv.DictReader(f)
    for row in r:
        BANK[int(row["id"])]={
            "id":int(row["id"]),"module":int(row["module"]),"topic":row["topic"],"difficulty":int(row["difficulty"]),
            "type":row["type"],"stem":row["stem"],"choices":json.loads(row["choices"]),"answer_key":row["answer_key"],
            "rationale":row["rationale"],"tags":row["tags"].split("|") if row["tags"] else []
        }

STATE: Dict[str, Dict[str, Any]] = {}
class NextReq(BaseModel): session_id:str; context:Dict[str,Any]={}
class SubmitReq(BaseModel): session_id:str; question_id:int; selected:str

def pick(st): 
    role=st.get("role","support"); preferred=[]
    for rule in RULES.get("branches",{}).get("role",[]): 
        try:
            if eval(rule["when"],{"__builtins__":{}},{"role":role}): preferred+=rule["prefer_modules"]
        except: pass
    c=[q for q in BANK.values() if (not preferred or q["module"] in preferred)]
    random.shuffle(c); 
    for q in c:
        if q["id"] not in st.get("attempted",set()): return q
    return c[0] if c else list(BANK.values())[0]

@app.post("/questionnaire/next")
def nxt(req:NextReq):
    st=STATE.setdefault(req.session_id, {"attempted":set(),"correct":0,"total":0,**req.context})
    q=pick(st); return {"question": {k:v for k,v in q.items() if k!="answer_key"}}

@app.post("/questionnaire/submit")
def sub(req:SubmitReq):
    st=STATE.setdefault(req.session_id, {"attempted":set(),"correct":0,"total":0})
    q=BANK.get(req.question_id); 
    if not q: raise HTTPException(404,"Question not found")
    st["attempted"].add(q["id"]); st["total"]+=1; ok=(str(req.selected)==q["answer_key"]); 
    if ok: st["correct"]+=1
    fb=RULES["feedback"]["correct" if ok else "incorrect"]
    return {"correct":ok,"score":round(st["correct"]/st["total"],3),"feedback":fb,"rationale":q["rationale"]}

# TSS demo endpoints (in-memory)
PAYLOADS={}; SHARES={}
class TSSEventIn(BaseModel): org_id:str; event_type:str; payload:Dict[str,Any]
class TSSReconIn(BaseModel): payload_id:str; provided_roles:Dict[str,str]; reason:str

@app.post("/tss/event")
def tss_event(e:TSSEventIn):
    art=tss_create({"org_id":e.org_id,"event_type":e.event_type,"payload":e.payload},threshold=2)
    pid=hashlib.sha256(art["cipher"]["ciphertext_b64"].encode()).hexdigest()[:16]
    PAYLOADS[pid]={"cipher":art["cipher"],"hash":art["payload_hash"]}
    SHARES[pid]={s["owner_role"]:s["wrapped_share"] for s in art["shares"]}
    return {"payload_id":pid,"shares_demo":SHARES[pid]}

@app.post("/tss/reconstruct")
def tss_recon(r:TSSReconIn):
    rec=PAYLOADS.get(r.payload_id)
    if not rec: raise HTTPException(404,"payload not found")
    if len(r.provided_roles)<2: raise HTTPException(403,"need at least 2 shares")
    data=tss_reconstruct(rec["cipher"], r.provided_roles)
    return {"ok":True,"payload_hash":rec["hash"],"data":data}