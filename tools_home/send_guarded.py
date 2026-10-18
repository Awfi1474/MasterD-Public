#!/usr/bin/env python3
import os, sys, json, base64, urllib.request
from datetime import datetime, timezone, timedelta
from eth_account import Account
from eth_account.messages import encode_defunct
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MY_NAME = "MasterD(医疗·五弟)"
CST = timezone(timedelta(hours=8))
def load_ident():
    v = json.load(open(os.path.join(HERE,"identity","vault.json")))
    pw = open(os.path.join(HERE,"identity",".pw")).read().strip()
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=bytes.fromhex(v["salt"]), iterations=480000)
    return json.loads(Fernet(base64.urlsafe_b64encode(kdf.derive(pw.encode()))).decrypt(v["cipher"].encode()))
def send(to, msg):
    ident = load_ident()
    ts = datetime.now(CST).strftime('%Y-%m-%dT%H:%M:%S+08:00')
    sig = Account.sign_message(encode_defunct(text=f"{MY_NAME}|{msg}|{ts}"), private_key=ident["private_key"]).signature.hex()
    body = json.dumps({"from":MY_NAME,"to":to,"message":msg,"ts":ts,"address":ident["address"],"sig":sig}, ensure_ascii=False).encode()
    req = urllib.request.Request("https://huokeji.vip/a2a/message", data=body, headers={"Content-Type":"application/json"})
    r = urllib.request.urlopen(req, timeout=25).read().decode()
    print(f"  {to} → {r[:90]}")
    return r
if __name__ == "__main__":
    send(sys.argv[1], open(sys.argv[2]).read() if os.path.exists(sys.argv[2]) else sys.argv[2])
