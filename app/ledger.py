from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from app.models import JournalEntry, JournalLine, PeriodLock, Account
from sqlalchemy.orm import joinedload

def post_entry(db, user, entry_date, description, lines):
    if user.role=="Auditor": raise PermissionError("Auditor access is read-only.")
    if len(lines)<2: raise ValueError("A journal needs at least two lines.")
    debit=sum((Decimal(str(x.get("debit",0))) for x in lines),Decimal("0"))
    credit=sum((Decimal(str(x.get("credit",0))) for x in lines),Decimal("0"))
    debit=debit.quantize(Decimal("0.01"),rounding=ROUND_HALF_UP)
    credit=credit.quantize(Decimal("0.01"),rounding=ROUND_HALF_UP)
    if debit<=0 or debit!=credit: raise ValueError(f"Entry is not balanced: debit ₹{debit} / credit ₹{credit}.")
    period=entry_date.strftime("%Y-%m")
    if db.query(PeriodLock).filter_by(period=period).first(): raise ValueError(f"{period} is locked.")
    codes={a.code for a in db.query(Account).all()}
    for line in lines:
        d=Decimal(str(line.get("debit",0))); c=Decimal(str(line.get("credit",0)))
        if line["account_code"] not in codes: raise ValueError("Unknown account code.")
        if d<0 or c<0 or (d and c): raise ValueError("Each line must have one non-negative debit or credit.")
    number=f"JE-{date.today():%y%m%d}-{db.query(JournalEntry).count()+1:04d}"
    entry=JournalEntry(entry_no=number,entry_date=entry_date,description=description,created_by=user.id)
    entry.lines=[JournalLine(account_code=x["account_code"],debit=float(x.get("debit",0)),credit=float(x.get("credit",0))) for x in lines]
    db.add(entry); db.commit(); db.refresh(entry)
    return entry
def balances(db):
    rows={}
    for e in db.query(JournalEntry).options(joinedload(JournalEntry.lines)).all():
        for l in e.lines:
            a=db.get(Account,l.account_code)
            if not a: continue
            r=rows.setdefault(a.code,{"code":a.code,"account":a.name,"category":a.category,"debit":0.0,"credit":0.0})
            r["debit"]+=l.debit; r["credit"]+=l.credit
    for r in rows.values(): r["balance"]=round(r["debit"]-r["credit"],2)
    return list(rows.values())
