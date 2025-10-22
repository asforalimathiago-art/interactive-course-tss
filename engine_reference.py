"""
Refactored engine with safe rule parsing, JSON-serializable state, and logging.
"""

import csv
import hashlib
import json
import logging
import os
import random
from typing import Any, Dict, List

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from tss_crypto import tss_create, tss_reconstruct

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Course+TSS", version="1.0.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

# Mount static files after API routes are defined (at the end of file)
# if os.path.exists("index.html"):
#     app.mount("/", StaticFiles(directory=".", html=True), name="static")


def load_rules(filepath: str = "adaptive_rules.yaml") -> Dict[str, Any]:
    """Load rules from YAML file safely."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            rules = yaml.safe_load(f)
            logger.info(f"Loaded rules from {filepath}")
            return rules
    except Exception as e:
        logger.error(f"Failed to load rules: {e}")
        return {}


def load_question_bank(
    filepath: str = "question_bank.csv",
) -> Dict[int, Dict[str, Any]]:
    """Load question bank from CSV file."""
    bank = {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                qid = int(row["id"])
                bank[qid] = {
                    "id": qid,
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
        logger.info(f"Loaded {len(bank)} questions from {filepath}")
    except Exception as e:
        logger.error(f"Failed to load question bank: {e}")
    return bank


RULES = load_rules()
BANK = load_question_bank()
STATE: Dict[str, Dict[str, Any]] = {}


class NextReq(BaseModel):
    """Request model for next question endpoint."""

    session_id: str
    context: Dict[str, Any] = {}


class SubmitReq(BaseModel):
    """Request model for submit answer endpoint."""

    session_id: str
    question_id: int
    selected: str


def safe_eval_rule(rule_condition: str, variables: Dict[str, Any]) -> bool:
    """
    Safely evaluate rule conditions without using eval().
    Only supports simple equality checks for now.
    """
    try:
        # Parse simple conditions like "role == 'instructor'"
        if "==" in rule_condition:
            left, right = rule_condition.split("==")
            left = left.strip()
            right = right.strip().strip("'\"")
            return variables.get(left) == right
        logger.warning(f"Unsupported rule condition: {rule_condition}")
        return False
    except Exception as e:
        logger.error(f"Error evaluating rule: {e}")
        return False


def pick_question(state: Dict[str, Any]) -> Dict[str, Any]:
    """Pick next question based on state and rules."""
    role = state.get("role", "support")
    preferred_modules: List[int] = []

    # Safe rule evaluation
    for rule in RULES.get("branches", {}).get("role", []):
        try:
            if safe_eval_rule(rule.get("when", ""), {"role": role}):
                preferred_modules.extend(rule.get("prefer_modules", []))
        except Exception as e:
            logger.warning(f"Error processing rule: {e}")

    # Filter questions
    candidates = [
        q
        for q in BANK.values()
        if not preferred_modules or q["module"] in preferred_modules
    ]

    if not candidates:
        candidates = list(BANK.values())

    random.shuffle(candidates)

    # Find unattempted question
    attempted = state.get("attempted", [])
    for question in candidates:
        if question["id"] not in attempted:
            return question

    # Return first candidate if all attempted
    return candidates[0] if candidates else list(BANK.values())[0]


@app.post("/questionnaire/next")
def next_question(req: NextReq):
    """Get next question for session."""
    # Initialize state with JSON-serializable attempted list
    state = STATE.setdefault(
        req.session_id, {"attempted": [], "correct": 0, "total": 0, **req.context}
    )
    question = pick_question(state)
    logger.info(f"Session {req.session_id}: next question {question['id']}")

    # Return question without answer key
    return {"question": {k: v for k, v in question.items() if k != "answer_key"}}


@app.post("/questionnaire/submit")
def submit_answer(req: SubmitReq):
    """Submit answer and get feedback."""
    state = STATE.setdefault(
        req.session_id, {"attempted": [], "correct": 0, "total": 0}
    )

    question = BANK.get(req.question_id)
    if not question:
        logger.warning(f"Question {req.question_id} not found")
        raise HTTPException(404, "Question not found")

    # Update state (use list instead of set for JSON serialization)
    if question["id"] not in state["attempted"]:
        state["attempted"].append(question["id"])

    state["total"] += 1
    is_correct = str(req.selected) == question["answer_key"]

    if is_correct:
        state["correct"] += 1

    feedback = RULES.get("feedback", {}).get(
        "correct" if is_correct else "incorrect", "No feedback available"
    )

    score = round(state["correct"] / state["total"], 3) if state["total"] > 0 else 0

    logger.info(
        f"Session {req.session_id}: answered Q{req.question_id} "
        f"{'correctly' if is_correct else 'incorrectly'}"
    )

    return {
        "correct": is_correct,
        "score": score,
        "feedback": feedback,
        "rationale": question["rationale"],
    }


# TSS demo endpoints (in-memory)
PAYLOADS: Dict[str, Dict[str, Any]] = {}
SHARES: Dict[str, Dict[str, str]] = {}


class TSSEventIn(BaseModel):
    """Request model for TSS event creation."""

    org_id: str
    event_type: str
    payload: Dict[str, Any]


class TSSReconIn(BaseModel):
    """Request model for TSS reconstruction."""

    payload_id: str
    provided_roles: Dict[str, str]
    reason: str


@app.post("/tss/event")
def create_tss_event(event: TSSEventIn):
    """Create TSS-protected event."""
    try:
        artifact = tss_create(
            {
                "org_id": event.org_id,
                "event_type": event.event_type,
                "payload": event.payload,
            },
            threshold=2,
        )

        payload_id = hashlib.sha256(
            artifact["cipher"]["ciphertext_b64"].encode()
        ).hexdigest()[:16]

        PAYLOADS[payload_id] = {
            "cipher": artifact["cipher"],
            "hash": artifact["payload_hash"],
        }
        SHARES[payload_id] = {
            s["owner_role"]: s["wrapped_share"] for s in artifact["shares"]
        }

        logger.info(f"Created TSS event with ID {payload_id}")
        return {"payload_id": payload_id, "shares_demo": SHARES[payload_id]}
    except Exception as e:
        logger.error(f"Failed to create TSS event: {e}")
        raise HTTPException(500, f"Failed to create TSS event: {str(e)}")


@app.post("/tss/reconstruct")
def reconstruct_tss_event(request: TSSReconIn):
    """Reconstruct TSS-protected event."""
    record = PAYLOADS.get(request.payload_id)
    if not record:
        logger.warning(f"Payload {request.payload_id} not found")
        raise HTTPException(404, "Payload not found")

    if len(request.provided_roles) < 2:
        logger.warning("Insufficient shares provided")
        raise HTTPException(403, "Need at least 2 shares")

    try:
        data = tss_reconstruct(record["cipher"], request.provided_roles)
        logger.info(f"Reconstructed payload {request.payload_id}")
        return {"ok": True, "payload_hash": record["hash"], "data": data}
    except Exception as e:
        logger.error(f"Failed to reconstruct payload: {e}")
        raise HTTPException(500, f"Failed to reconstruct payload: {str(e)}")


# Mount static files last so API routes take precedence
if os.path.exists("index.html"):
    app.mount("/static", StaticFiles(directory=".", html=True), name="static")
