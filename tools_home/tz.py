from datetime import datetime, timezone, timedelta
CST = timezone(timedelta(hours=8), name="CST")
def now(): return datetime.now(CST)
def now_iso(): return now().isoformat()
def stamp(): return now().strftime('%Y%m%d-%H%M%S')
