import bcrypt, re
from app.models import User

ROLES=("CFO","Controller","Accountant","Auditor")
def hash_password(password:str)->str:
    if len(password)<10: raise ValueError("Use at least 10 characters for your password.")
    return bcrypt.hashpw(password.encode(),bcrypt.gensalt(rounds=12)).decode()
def verify_password(password:str, password_hash:str)->bool:
    try: return bcrypt.checkpw(password.encode(),password_hash.encode())
    except Exception: return False
def authenticate(db,email,password):
    user=db.query(User).filter(User.email==email.strip().lower(),User.is_active==True).first()
    return user if user and verify_password(password,user.password_hash) else None
def can_post(user): return user.role in ("CFO","Controller","Accountant")
def can_lock(user): return user.role in ("CFO","Controller")
def can_admin(user): return user.role=="CFO"
