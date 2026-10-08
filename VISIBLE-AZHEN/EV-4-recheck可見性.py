#!/usr/bin/env python3
"""阿診 · 複查器（★ 把「說法」變成「機制」）
★ CASE-018「可見性假綠」的機制化：
   判「未見」前 → 先自動檢查「我有沒有讀取權限」
"""
import os, json, urllib.request

def can_read_repo(slug, token=None):
    hdr = {"Authorization": f"token {token}"} if token else {}
    try:
        req = urllib.request.Request(f"https://api.github.com/repos/{slug}", headers=hdr)
        d = json.loads(urllib.request.urlopen(req, timeout=12).read())
        if d.get("full_name"):
            return True, f"可見（private={d.get('private')}）"
        return False, f"不可讀（{d.get('message')}）"
    except Exception as e:
        return False, f"不可讀（{str(e)[:50]}）"

def main():
    tokp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".gh_token")
    TOK = open(tokp).read().strip() if os.path.exists(tokp) else None
    targets = [("老四","7336awfi/masterd-lobby"), ("三哥","7336awfi/masterd-lab-lobby"),
               ("大哥","awfi4374/ai-meeting-room"), ("自己","Awfi1474/masterd-medical")]
    print("★ 複查前「可見性」檢查（CASE-018 機制化）")
    for who, slug in targets:
        ok, msg = can_read_repo(slug, TOK)
        icon = "✅" if ok else "⏸️"
        print(f"  {icon} {who}: {msg}（{'可判' if ok else '★ 先要證據位置，不能判「未見」'}）")

if __name__ == "__main__":
    main()
