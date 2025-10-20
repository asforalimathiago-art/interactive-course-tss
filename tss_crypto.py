import os, base64, json, hashlib
from typing import Dict, Any, List
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
try:
    from secretsharing import PlaintextToHexSecretSharer as SSS
except Exception:
    SSS=None
def b64e(b): return base64.b64encode(b).decode()
def b64d(s): return base64.b64decode(s.encode())
def encrypt_payload(payload: bytes):
    key=AESGCM.generate_key(bit_length=256); aes=AESGCM(key); nonce=os.urandom(12)
    ct=aes.encrypt(nonce,payload,None); meta={"alg":"AES-GCM","nonce":b64e(nonce),"aad":None,"v":"1"}
    return {"ciphertext_b64":b64e(ct),"meta":meta}, key
def decrypt_payload(art,key):
    aes=AESGCM(key); nonce=b64d(art["meta"]["nonce"]); ct=b64d(art["ciphertext_b64"]); return aes.decrypt(nonce,ct,None)
def split_key_shamir(key, threshold=2, parts=3):
    if SSS is None: raise RuntimeError("secretsharing not installed")
    return SSS.split_secret(key.hex(), threshold, parts)
def combine_shares_shamir(shares):
    if SSS is None: raise RuntimeError("secretsharing not installed")
    return bytes.fromhex(SSS.recover_secret(shares))
def wrap_share(s, k): return b64e(s.encode())
def unwrap_share(w,k): return b64d(w).decode()
def tss_create(payload: Dict[str,Any], threshold: int=2)->Dict[str,Any]:
    raw=json.dumps(payload).encode(); art,key=encrypt_payload(raw); shares=split_key_shamir(key,threshold,3)
    roles=["user","operator","regulator"]; env=[{"owner_role":r,"wrapped_share":wrap_share(s,f"kfp::{r}")} for r,s in zip(roles,shares)]
    ph=hashlib.sha256(raw).hexdigest(); return {"cipher":art,"shares":env,"payload_hash":ph}
def tss_reconstruct(cipher: Dict[str,Any], provided: Dict[str,str])->Dict[str,Any]:
    plains=[unwrap_share(w,f"kfp::{r}") for r,w in provided.items()]; key=combine_shares_shamir(plains)
    return json.loads(decrypt_payload(cipher,key).decode())