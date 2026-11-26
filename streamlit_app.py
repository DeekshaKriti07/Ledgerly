import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime
from sqlalchemy import func
from app.database import init_db,SessionLocal
from app.bootstrap import seed
from app.models import User,Invoice,Vendor,Customer,JournalEntry,JournalLine,BankTransaction,Expense,PeriodLock,Account
from app.security import authenticate,can_post,can_lock,can_admin,hash_password
from app.ledger import post_entry,balances

st.set_page_config(page_title="Ledgerly — Finance Intelligence",page_icon="assets/favicon.png",layout="wide",initial_sidebar_state="expanded")
seed()
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
:root{--ink:#20201e;--paper:#f6f0e9;--card:#fffaf2;--pink:#f4b3ca;--yellow:#f4d86f;--mint:#83d6b1;--blue:#aab9ef;--muted:#77736e}
html,body,[class*="css"]{font-family:'Manrope',sans-serif;color:var(--ink)}
.stApp{background:var(--paper)}
[data-testid="stHeader"]{background:rgba(246,240,233,.94)}
[data-testid="stToolbar"]{visibility:hidden;height:0}
[data-testid="stDecoration"]{display:none}
.block-container{max-width:1500px;padding-top:2.2rem;padding-bottom:4rem}
h1,h2,h3,h4,p,span,label,div{color:inherit}
h1{font-weight:800;letter-spacing:-.055em;font-size:2.45rem!important}
h2,h3{font-weight:800;letter-spacing:-.035em}
section[data-testid="stSidebar"]{background:#fffaf2;border-right:1px solid #252522}
section[data-testid="stSidebar"] *{color:#252522!important}
.stButton>button,.stDownloadButton>button{border:1.5px solid #242421;border-radius:10px;background:#f4b3ca;color:#20201e;font-weight:800;min-height:42px;box-shadow:3px 3px 0 #20201e}
.stButton>button:hover,.stDownloadButton>button:hover{background:#f4d86f;color:#20201e;border-color:#20201e}
div[data-testid="stMetric"]{background:#fffaf2;border:1.5px solid #242421;border-radius:14px;padding:17px 18px;box-shadow:3px 3px 0 #242421}
[data-testid="stMetricLabel"]{color:#66615b!important;font-size:.75rem;font-weight:800;text-transform:uppercase;letter-spacing:.08em}
[data-testid="stMetricValue"]{color:#20201e!important;font-size:1.85rem;font-weight:800}
[data-testid="stMetricDelta"]{font-weight:700}
[data-testid="stDataFrame"]{border:1px solid #ded5cb;border-radius:12px;overflow:hidden}
[data-testid="stTabs"] button{font-weight:800;color:#56514c}
[data-testid="stTabs"] button[aria-selected="true"]{color:#20201e;border-bottom:3px solid #e68daf}
input,textarea,[data-baseweb="select"]>div{border-radius:9px!important}
.hero{background:#fffaf2;border:1.5px solid #20201e;border-radius:18px;padding:30px 34px;box-shadow:5px 5px 0 #20201e;margin:18px 0 24px;animation:rise .7s ease both}
.eyebrow{font:700 11px 'DM Mono',monospace;letter-spacing:.16em;text-transform:uppercase;color:#756f68}
.hero h2{font-size:2.1rem;margin:12px 0 8px;color:#20201e}
.hero p{color:#66615b;margin:0}
.brand{font-size:24px;font-weight:900;letter-spacing:-1.5px}
.brandmark{display:inline-grid;place-items:center;width:35px;height:35px;background:#f4b3ca;border:1.5px solid #20201e;border-radius:10px;margin-right:9px}
.panel{background:#fffaf2;border:1.5px solid #242421;border-radius:15px;padding:20px;box-shadow:3px 3px 0 #242421}
@keyframes rise{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}
@media(max-width:700px){h1{font-size:1.8rem!important}.hero h2{font-size:1.45rem}}
</style>""",unsafe_allow_html=True)

def money(v): return f"₹{float(v):,.2f}"
def login_screen(db):
    st.markdown("<div style='height:5vh'></div>",unsafe_allow_html=True)
    left,right=st.columns([1.1,1],gap="large")
    with left:
        st.markdown("<div class='eyebrow'>FINANCE INTELLIGENCE PLATFORM</div><h1 style='font-size:3.4rem!important;margin-top:20px'>Clarity in every<br>number.</h1><p style='font-size:1.1rem;color:#68625c'>A calmer way to close the books, understand the business and stay in control.</p>",unsafe_allow_html=True)
        st.video("assets/ledgerly_intro.mp4",autoplay=True,muted=True)
        st.caption("LEDGERLY · FINANCE OPERATIONS")
    with right:
        st.markdown("<div class='panel'>",unsafe_allow_html=True)
        st.subheader("Welcome back")
        st.caption("Sign in to your secure finance workspace.")
        with st.form("login"):
            email=st.text_input("Work email",placeholder="name@company.com")
            password=st.text_input("Password",type="password")
            go=st.form_submit_button("Sign in",use_container_width=True)
        st.markdown("</div>",unsafe_allow_html=True)
        if go:
            user=authenticate(db,email,password)
            if user: st.session_state.user_id=user.id; st.rerun()
            else: st.error("Email or password is incorrect, or the account is inactive.")
        st.info("First launch? Create the initial CFO account from Terminal using the setup command in README.md.")
    st.stop()

db=SessionLocal()
if "user_id" not in st.session_state or not db.get(User,st.session_state.get("user_id")):
    login_screen(db)
user=db.get(User,st.session_state.user_id)
if not user.is_active:
    st.session_state.pop("user_id",None); st.rerun()

with st.sidebar:
    st.markdown("<div class='brand'><span class='brandmark'>◈</span>LEDGERLY</div><div class='eyebrow' style='margin:8px 0 22px'>FINANCE INTELLIGENCE</div>",unsafe_allow_html=True)
    st.write(f"**{user.full_name}**")
    st.caption(f"{user.role} · {user.email}")
    st.divider()
    page=st.radio("WORKSPACE",["Overview","General Ledger","Journal Entries","Invoices","Banking","Expenses","Vendors & Customers","Financial Statements","Administration"],label_visibility="collapsed")
    st.divider()
    st.caption("WORKSPACE STATUS")
    st.markdown("● Database connected")
    if st.button("Sign out",use_container_width=True):
        st.session_state.pop("user_id",None); st.rerun()
    st.caption("Ledgerly v2.0 · Demo environment")

st.markdown("<div class='eyebrow'>FINANCE OPERATIONS / CONTROL ROOM</div>",unsafe_allow_html=True)
st.title(page)
if page=="Overview":
    journals=db.query(JournalEntry).count()
    invoices=db.query(Invoice).count()
    pending=db.query(Invoice).filter(Invoice.status=="Pending").count()
    vendors=db.query(Vendor).count()
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Posted journals",journals)
    c2.metric("Invoices recorded",invoices)
    c3.metric("Pending invoices",pending)
    c4.metric("Active vendors",vendors)
    st.markdown("<div class='hero'><div class='eyebrow'>LEDGERLY INTELLIGENCE</div><h2>Close the books. Not your momentum.</h2><p>Your finance operations, journal controls and reporting in one connected workspace.</p></div>",unsafe_allow_html=True)
    left,right=st.columns([1.55,1])
    with left:
        st.subheader("Transaction activity")
        q=db.query(JournalEntry).order_by(JournalEntry.entry_date).all()
        if q:
            df=pd.DataFrame([{"Date":x.entry_date,"Journal":x.entry_no,"Description":x.description} for x in q])
            st.dataframe(df,use_container_width=True,hide_index=True)
        else:
            st.info("No journals posted yet. Start by creating a balanced journal entry.")
    with right:
        st.subheader("Close checklist")
        for label,done in [("Chart of accounts configured",db.query(Account).count()>0),("User authenticated",True),("Journal activity recorded",journals>0),("Invoices reviewed",invoices>0),("Bank reconciliation reviewed",db.query(BankTransaction).filter_by(status="Matched").count()>0)]:
            st.write(("✓ " if done else "○ ")+label)
        st.progress(sum([db.query(Account).count()>0,True,journals>0,invoices>0,db.query(BankTransaction).filter_by(status="Matched").count()>0])/5)
    st.subheader("Operational signals")
    a,b,c=st.columns(3)
    a.metric("Bank lines awaiting review",db.query(BankTransaction).filter_by(status="Unmatched").count())
    b.metric("Employee expenses",db.query(Expense).count())
    c.metric("Chart of accounts",db.query(Account).count())
elif page=="General Ledger":
    st.subheader("General ledger")
    rows=[]
    for e in db.query(JournalEntry).order_by(JournalEntry.entry_date.desc()).all():
        for l in e.lines:
            a=db.get(Account,l.account_code)
            rows.append({"Date":e.entry_date,"Journal":e.entry_no,"Description":e.description,"Account":a.name if a else "Unknown","Debit":l.debit,"Credit":l.credit,"Created by":db.get(User,e.created_by).full_name})
    if rows: st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
    else: st.info("The general ledger is empty. Post a journal entry to populate it.")
elif page=="Journal Entries":
    st.subheader("Create a journal entry")
    if not can_post(user): st.warning("Your Auditor role has read-only access.")
    else:
        accounts=db.query(Account).order_by(Account.code).all()
        with st.form("new_journal"):
            dt=st.date_input("Posting date",value=date.today())
            desc=st.text_input("Description",placeholder="Monthly cloud hosting expense")
            cols=st.columns(2)
            debit=cols[0].selectbox("Debit account",accounts,format_func=lambda x:f"{x.code} · {x.name}")
            credit=cols[1].selectbox("Credit account",accounts,format_func=lambda x:f"{x.code} · {x.name}",index=min(12,len(accounts)-1))
            amount=st.number_input("Amount (INR)",min_value=0.01,value=10000.0,step=100.0)
            submit=st.form_submit_button("Validate & post journal")
        if submit:
            try:
                entry=post_entry(db,user,dt,desc,[{"account_code":debit.code,"debit":amount},{"account_code":credit.code,"credit":amount}])
                st.success(f"Posted {entry.entry_no}. Debits equal credits.")
            except Exception as ex: st.error(str(ex))
    recent=db.query(JournalEntry).order_by(JournalEntry.created_at.desc()).limit(20).all()
    st.subheader("Recent journal entries")
    st.dataframe(pd.DataFrame([{"Journal":e.entry_no,"Date":e.entry_date,"Description":e.description,"Status":e.status} for e in recent]),use_container_width=True,hide_index=True)
elif page=="Invoices":
    st.subheader("Invoice register")
    vendors=db.query(Vendor).order_by(Vendor.name).all()
    if can_post(user):
        with st.expander("Add invoice",expanded=False):
            with st.form("invoice_form"):
                no=st.text_input("Invoice number")
                vendor=st.selectbox("Vendor",vendors,format_func=lambda x:x.name) if vendors else None
                dt=st.date_input("Invoice date",value=date.today())
                due=st.date_input("Due date",value=date.today())
                subtotal=st.number_input("Subtotal",min_value=0.0,value=10000.0)
                tax=st.number_input("Tax",min_value=0.0,value=1800.0)
                save=st.form_submit_button("Save invoice")
            if save:
                if not no.strip(): st.error("Invoice number is required.")
                elif db.query(Invoice).filter_by(invoice_no=no.strip()).first(): st.error("Invoice number already exists.")
                else:
                    db.add(Invoice(invoice_no=no.strip(),vendor_id=vendor.id if vendor else None,invoice_date=dt,due_date=due,subtotal=subtotal,tax=tax,total=subtotal+tax)); db.commit(); st.success("Invoice saved to database."); st.rerun()
    data=db.query(Invoice).order_by(Invoice.invoice_date.desc()).all()
    st.dataframe(pd.DataFrame([{"Invoice":i.invoice_no,"Vendor":i.vendor.name if i.vendor else "—","Date":i.invoice_date,"Due":i.due_date,"Subtotal":i.subtotal,"Tax":i.tax,"Total":i.total,"Status":i.status} for i in data]),use_container_width=True,hide_index=True)
elif page=="Banking":
    st.subheader("Bank transactions")
    tx=db.query(BankTransaction).order_by(BankTransaction.txn_date.desc()).all()
    st.caption("Review transaction rows and mark matched only after checking the supporting ledger entry.")
    for t in tx[:30]:
        c1,c2,c3,c4=st.columns([2.5,1.3,1,1])
        c1.write(f"{t.txn_date} · {t.description}")
        c2.write(money(t.debit or t.credit))
        c3.write(t.status)
        if c4.button("Match" if t.status=="Unmatched" else "Matched",key=f"match{t.id}",disabled=t.status=="Matched" or not can_post(user)):
            t.status="Matched"; db.commit(); st.rerun()
    st.download_button("Export bank CSV",pd.DataFrame([{"Date":t.txn_date,"Description":t.description,"Debit":t.debit,"Credit":t.credit,"Status":t.status} for t in tx]).to_csv(index=False),"bank_transactions.csv","text/csv")
elif page=="Expenses":
    st.subheader("Employee expense register")
    if can_post(user):
        with st.expander("Record expense"):
            with st.form("expense_form"):
                employee=st.text_input("Employee")
                cat=st.selectbox("Category",["Travel","Meals","Software","Office supplies","Utilities","Other"])
                amt=st.number_input("Amount",min_value=1.0,value=1200.0)
                dt=st.date_input("Expense date",value=date.today())
                save=st.form_submit_button("Save expense")
            if save:
                db.add(Expense(employee=employee,category=cat,amount=amt,expense_date=dt)); db.commit(); st.success("Expense saved."); st.rerun()
    exp=db.query(Expense).order_by(Expense.expense_date.desc()).all()
    st.dataframe(pd.DataFrame([{"Date":e.expense_date,"Employee":e.employee,"Category":e.category,"Amount":e.amount,"Status":e.status} for e in exp]),use_container_width=True,hide_index=True)
elif page=="Vendors & Customers":
    t1,t2=st.tabs(["Vendors","Customers"])
    with t1:
        if can_post(user):
            with st.form("vendor_form"):
                name=st.text_input("Vendor name"); gst=st.text_input("GSTIN"); email=st.text_input("Email")
                add=st.form_submit_button("Add vendor")
            if add:
                if name.strip(): db.add(Vendor(name=name.strip(),gstin=gst or None,email=email or None)); db.commit(); st.success("Vendor saved."); st.rerun()
        v=db.query(Vendor).all(); st.dataframe(pd.DataFrame([{"Name":x.name,"GSTIN":x.gstin,"Email":x.email,"Terms":x.payment_terms} for x in v]),use_container_width=True,hide_index=True)
    with t2:
        if can_post(user):
            with st.form("customer_form"):
                name=st.text_input("Customer name"); gst=st.text_input("Customer GSTIN"); email=st.text_input("Customer email")
                add=st.form_submit_button("Add customer")
            if add:
                if name.strip(): db.add(Customer(name=name.strip(),gstin=gst or None,email=email or None)); db.commit(); st.success("Customer saved."); st.rerun()
        c=db.query(Customer).all(); st.dataframe(pd.DataFrame([{"Name":x.name,"GSTIN":x.gstin,"Email":x.email} for x in c]),use_container_width=True,hide_index=True)
elif page=="Financial Statements":
    st.subheader("Financial statements")
    b=balances(db)
    if not b: st.info("Statements will populate when journal entries are posted.")
    else:
        df=pd.DataFrame(b)
        df["debit_balance"]=df.balance.clip(lower=0); df["credit_balance"]=(-df.balance).clip(lower=0)
        st.markdown("**Trial balance**"); st.dataframe(df,use_container_width=True,hide_index=True)
        revenue=sum(x["credit"]-x["debit"] for x in b if x["category"]=="Revenue")
        expenses=sum(x["debit"]-x["credit"] for x in b if x["category"]=="Expense")
        assets=sum(x["debit"]-x["credit"] for x in b if x["category"]=="Asset")
        liabilities=sum(x["credit"]-x["debit"] for x in b if x["category"]=="Liability")
        equity=sum(x["credit"]-x["debit"] for x in b if x["category"]=="Equity")+revenue-expenses
        x,y,z=st.columns(3); x.metric("Revenue",money(revenue)); y.metric("Expenses",money(expenses)); z.metric("Net income",money(revenue-expenses))
        st.markdown("**Balance sheet snapshot**")
        a,c,e=st.columns(3); a.metric("Assets",money(assets)); c.metric("Liabilities",money(liabilities)); e.metric("Equity incl. current earnings",money(equity))
        st.caption(f"Accounting equation variance: {money(assets-liabilities-equity)}")
        st.download_button("Export trial balance",df.to_csv(index=False),"trial_balance.csv","text/csv")
elif page=="Administration":
    st.subheader("Workspace administration")
    if can_admin(user):
        st.markdown("**Create user account**")
        with st.form("user_create"):
            name=st.text_input("Full name"); email=st.text_input("Work email"); pw=st.text_input("Temporary password",type="password"); role=st.selectbox("Role",["Controller","Accountant","Auditor","CFO"])
            add=st.form_submit_button("Create account")
        if add:
            try:
                if db.query(User).filter_by(email=email.lower().strip()).first(): st.error("Email already exists.")
                else: db.add(User(full_name=name,email=email.lower().strip(),password_hash=hash_password(pw),role=role)); db.commit(); st.success("Account created.")
            except Exception as ex: st.error(str(ex))
        st.markdown("**User directory**")
        us=db.query(User).all(); st.dataframe(pd.DataFrame([{"Name":u.full_name,"Email":u.email,"Role":u.role,"Active":u.is_active} for u in us]),use_container_width=True,hide_index=True)
    else: st.warning("Only CFO users can administer accounts.")
    st.markdown("**Accounting period controls**")
    if can_lock(user):
        period=st.text_input("Period (YYYY-MM)",value=date.today().strftime("%Y-%m"))
        if st.button("Lock accounting period"):
            if len(period)==7 and period[4]=="-":
                if not db.query(PeriodLock).filter_by(period=period).first(): db.add(PeriodLock(period=period,locked_by=user.id)); db.commit()
                st.success(f"{period} is locked.")
            else: st.error("Use YYYY-MM.")
    locks=db.query(PeriodLock).all()
    st.dataframe(pd.DataFrame([{"Period":x.period,"Locked at":x.locked_at,"Locked by":db.get(User,x.locked_by).full_name} for x in locks]),use_container_width=True,hide_index=True)

db.close()
