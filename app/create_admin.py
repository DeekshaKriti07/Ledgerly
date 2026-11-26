import argparse
from app.database import init_db,SessionLocal
from app.models import User
from app.security import hash_password,ROLES
def main():
    p=argparse.ArgumentParser(); p.add_argument("--name",required=True); p.add_argument("--email",required=True); p.add_argument("--password",required=True); p.add_argument("--role",choices=ROLES,default="CFO")
    a=p.parse_args(); init_db(); db=SessionLocal()
    email=a.email.lower().strip()
    if db.query(User).filter_by(email=email).first(): raise SystemExit("An account with this email already exists.")
    db.add(User(full_name=a.name,email=email,password_hash=hash_password(a.password),role=a.role)); db.commit(); db.close()
    print(f"Created {a.role} account: {email}")
if __name__=="__main__": main()
