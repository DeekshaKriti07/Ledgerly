
from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from app.bootstrap import seed
from app.database import SessionLocal
from app.ledger import balances, post_entry
from app.models import (Account, BankTransaction, Customer, Expense, Invoice, JournalEntry,
                        PeriodLock, User, Vendor)
from app.security import authenticate, can_admin, can_lock, can_post, hash_password
from app.ui import (PAGES, brand, empty_state, esc, html_block, inject_theme, kpi_grid, login_art_html,
                    money, page_header, pill, section, splash_html, status_kind, style_figure)

st.set_page_config(page_title="Ledgerly — Finance Intelligence", page_icon="assets/favicon.png",
                   layout="wide", initial_sidebar_state="expanded")
seed()
inject_theme()


def table(df: pd.DataFrame, money_cols=(), empty=("Nothing here yet", "Records will show up here once added."), height=None):
    """Render a dataframe with rupee formatting, or a friendly empty state."""
    if df.empty:
        empty_state(*empty)
        return
    cfg = {c: st.column_config.NumberColumn(c, format="₹%.2f") for c in money_cols if c in df.columns}
    extra = {"height": height} if height else {}
    st.dataframe(df, hide_index=True, width="stretch", column_config=cfg, **extra)


# ------------------------------------------------------------------ Login
def login_screen(db):
    if not st.session_state.get("ledgerly_intro_seen", False):
        st.session_state["ledgerly_intro_seen"] = True
        html_block(splash_html())

    left, right = st.columns([1.3, 1], gap="large")
    with left:
        html_block(login_art_html())
    with right:
        html_block("""<div class="signin-head"><div class="eyebrow">Your workspace awaits</div>
            <h2>Welcome back<em>.</em></h2><p>Sign in to open your finance workspace.</p></div>""")
        with st.form("login"):
            email = st.text_input("Work email", placeholder="name@company.com")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            go = st.form_submit_button("Sign in", width="stretch")
        if go:
            user = authenticate(db, email, password)
            if user:
                st.session_state.user_id = user.id
                st.rerun()
            else:
                st.error("Email or password is incorrect, or the account is inactive.")
        html_block("""<div class="tile t-mint setup" style="--i:4"><div>
            <b>Demo login</b><span>Email: demo@ledgerly.com<br>Password: LedgerlyDemo2026</span></div></div>
            <div class="legal">SECURE FINANCE WORKSPACE · LEDGERLY 2.0</div>""")
    st.stop()


db = SessionLocal()
if "user_id" not in st.session_state or not db.get(User, st.session_state.get("user_id")):
    login_screen(db)
user = db.get(User, st.session_state.user_id)
if not user.is_active:
    st.session_state.pop("user_id", None)
    st.rerun()

# ------------------------------------------------------------------ Sidebar
with st.sidebar:
    html_block(brand())
    html_block(f"""<div class="user-card"><b>{esc(user.full_name)}</b><span>{esc(user.email)}</span>
        {pill(user.role, '')}</div><div class="side-label">Workspace</div>""")
    page = st.radio("Workspace", list(PAGES), label_visibility="collapsed")
    html_block('<div class="side-label">Status</div><div class="side-status"><span class="status-dot"></span>Database connected</div>')
    if st.button("Sign out", width="stretch"):
        st.session_state.pop("user_id", None)
        st.rerun()
    st.caption("Ledgerly v2.0 · Demo environment")

SUBTITLES = {
    "Overview": f"Welcome back, {user.full_name.split()[0] if user.full_name.strip() else 'there'}. Here is where the books stand today.",
    "General Ledger": "Every posted debit and credit, line by line.",
    "Journal Entries": "Post balanced entries. Debits must equal credits, always.",
    "Invoices": "Track vendor invoices from received to settled.",
    "Banking": "Review statement lines and match them to your ledger.",
    "Expenses": "Employee spend, categorised and on record.",
    "Vendors & Customers": "The people and companies you do business with.",
    "Financial Statements": "Trial balance, income and balance-sheet snapshot.",
    "Administration": "Users, roles and accounting period controls.",
}
page_header(page, SUBTITLES[page])

# ------------------------------------------------------------------ Pages
if page == "Overview":
    journals = db.query(JournalEntry).count()
    invoices = db.query(Invoice).count()
    pending = db.query(Invoice).filter(Invoice.status == "Pending").count()
    vendors = db.query(Vendor).count()
    accounts_n = db.query(Account).count()
    matched = db.query(BankTransaction).filter_by(status="Matched").count()
    unmatched = db.query(BankTransaction).filter_by(status="Unmatched").count()

    html_block(f"""<div class="bento cols-4">
      <div class="tile t-cream hero span-2 row-2" style="--i:0"><div class="eyebrow">Ledgerly intelligence</div>
        <h2>Close the books. Not your momentum.</h2>
        <p>Your finance operations, journal controls and reporting in one connected workspace.</p>
        <div class="hero-chips">{pill(f'{unmatched} bank lines to review', 'warn')}{pill(f'{pending} pending invoices', 'pink')}</div>
        </div>
      {''.join([
        f'<div class="tile kpi t-{c}" style="--i:{i + 1}"><div class="kpi-top"><div class="kpi-label">{l}</div></div><div class="kpi-value">{v}</div></div>'
        for i, (l, v, c) in enumerate([("Posted journals", journals, "pink"), ("Invoices recorded", invoices, "yellow"),
                                       ("Pending invoices", pending, "coral"), ("Active vendors", vendors, "mint")])])}
    </div>""")

    c_left, c_right = st.columns([1.55, 1], gap="large")
    with c_left:
        section("Cash movement", "last 30 days")
        with st.container(border=True, key="tile-1"):
            since = date.today() - timedelta(days=29)
            tx = db.query(BankTransaction).filter(BankTransaction.txn_date >= since).all()
            if tx:
                df = pd.DataFrame([{"Date": t.txn_date, "Money in": t.credit, "Money out": t.debit} for t in tx])
                df = df.groupby("Date", as_index=False).sum().sort_values("Date")
                fig = px.bar(df, x="Date", y=["Money in", "Money out"], barmode="group",
                             color_discrete_map={"Money in": "#55d6a0", "Money out": "#ff7a63"})
                st.plotly_chart(style_figure(fig, 300), width="stretch", config={"displayModeBar": False})
            else:
                empty_state("No bank activity", "Imported bank lines will chart here.")
    with c_right:
        section("Close checklist")
        steps = [("Chart of accounts configured", accounts_n > 0), ("User authenticated", True),
                 ("Journal activity recorded", journals > 0), ("Invoices reviewed", invoices > 0),
                 ("Bank reconciliation started", matched > 0)]
        done = sum(1 for _, d in steps if d)
        rows = "".join(f'<div class="check {"done" if d else ""}"><div class="box">{""}</div><span class="txt">{esc(l)}</span></div>' for l, d in steps)
        html_block(f'<div class="tile t-white" style="--i:2">{rows}<div class="bar"><i style="width:{done / len(steps) * 100:.0f}%"></i></div>'
                   f'<div class="eyebrow" style="margin-top:10px">{done} of {len(steps)} complete</div></div>')

    e_left, e_right = st.columns([1, 1.55], gap="large")
    with e_left:
        section("Spend by category")
        with st.container(border=True, key="tile-2"):
            ex = db.query(Expense).all()
            if ex:
                edf = pd.DataFrame([{"Category": e.category, "Amount": e.amount} for e in ex]).groupby("Category", as_index=False).sum()
                fig = px.pie(edf, names="Category", values="Amount", hole=.55)
                fig.update_traces(marker=dict(line=dict(color="#1b1a17", width=2.5)), textinfo="percent")
                st.plotly_chart(style_figure(fig, 290), width="stretch", config={"displayModeBar": False})
            else:
                empty_state("No expenses", "Record an expense to see the mix.")
    with e_right:
        section("Recent journal activity")
        q = db.query(JournalEntry).order_by(JournalEntry.entry_date.desc()).limit(8).all()
        table(pd.DataFrame([{"Date": x.entry_date, "Journal": x.entry_no, "Description": x.description} for x in q]),
              empty=("No journals posted yet", "Start by creating a balanced journal entry."))
    section("Operational signals")
    kpi_grid([dict(label="Bank lines awaiting review", value=unmatched, color="sky", compact=True),
              dict(label="Employee expenses", value=db.query(Expense).count(), color="pink", compact=True),
              dict(label="Chart of accounts", value=accounts_n, color="yellow", compact=True)], cols=3)

elif page == "General Ledger":
    rows = []
    names = {a.code: a.name for a in db.query(Account).all()}
    people = {u.id: u.full_name for u in db.query(User).all()}
    for e in db.query(JournalEntry).order_by(JournalEntry.entry_date.desc()).all():
        for l in e.lines:
            rows.append({"Date": e.entry_date, "Journal": e.entry_no, "Description": e.description,
                         "Account": names.get(l.account_code, "Unknown"), "Debit": l.debit, "Credit": l.credit,
                         "Created by": people.get(e.created_by, "Unknown")})
    df = pd.DataFrame(rows)
    if not df.empty:
        kpi_grid([dict(label="Journal lines", value=len(df), color="yellow", compact=True),
                  dict(label="Total debits", value=money(df.Debit.sum()), color="mint", compact=True),
                  dict(label="Total credits", value=money(df.Credit.sum()), color="pink", compact=True)], cols=3)
    table(df, ("Debit", "Credit"), ("The ledger is empty", "Post a journal entry to populate it."))

elif page == "Journal Entries":
    f_col, r_col = st.columns([1, 1.25], gap="large")
    with f_col:
        section("New entry")
        if not can_post(user):
            st.warning("Your Auditor role has read-only access.")
        else:
            accounts = db.query(Account).order_by(Account.code).all()
            with st.form("new_journal"):
                dt = st.date_input("Posting date", value=date.today())
                desc = st.text_input("Description", placeholder="Monthly cloud hosting expense")
                debit = st.selectbox("Debit account", accounts, format_func=lambda x: f"{x.code} · {x.name}")
                credit = st.selectbox("Credit account", accounts, format_func=lambda x: f"{x.code} · {x.name}", index=min(12, len(accounts) - 1))
                amount = st.number_input("Amount (INR)", min_value=0.01, value=10000.0, step=100.0)
                submit = st.form_submit_button("Validate & post journal", width="stretch")
            if submit:
                try:
                    entry = post_entry(db, user, dt, desc, [{"account_code": debit.code, "debit": amount}, {"account_code": credit.code, "credit": amount}])
                    st.success(f"Posted {entry.entry_no}. Debits equal credits.")
                except Exception as ex:
                    st.error(str(ex))
    with r_col:
        section("Recent entries", "latest 20")
        recent = db.query(JournalEntry).order_by(JournalEntry.created_at.desc()).limit(20).all()
        table(pd.DataFrame([{"Journal": e.entry_no, "Date": e.entry_date, "Description": e.description, "Status": e.status} for e in recent]),
              empty=("No entries yet", "Your first posted journal will appear here."))

elif page == "Invoices":
    vendors = db.query(Vendor).order_by(Vendor.name).all()
    data = db.query(Invoice).order_by(Invoice.invoice_date.desc()).all()
    kpi_grid([dict(label="Invoices", value=len(data), color="sky", compact=True),
              dict(label="Pending", value=sum(1 for i in data if i.status == "Pending"), color="yellow", compact=True),
              dict(label="Total value", value=money(sum(i.total for i in data)), color="mint", compact=True)], cols=3)
    if can_post(user):
        with st.expander("Add invoice"):
            with st.form("invoice_form"):
                c1, c2 = st.columns(2)
                no = c1.text_input("Invoice number")
                vendor = c2.selectbox("Vendor", vendors, format_func=lambda x: x.name) if vendors else None
                dt = c1.date_input("Invoice date", value=date.today())
                due = c2.date_input("Due date", value=date.today())
                subtotal = c1.number_input("Subtotal", min_value=0.0, value=10000.0)
                tax = c2.number_input("Tax", min_value=0.0, value=1800.0)
                save = st.form_submit_button("Save invoice")
            if save:
                if not no.strip():
                    st.error("Invoice number is required.")
                elif db.query(Invoice).filter_by(invoice_no=no.strip()).first():
                    st.error("Invoice number already exists.")
                else:
                    db.add(Invoice(invoice_no=no.strip(), vendor_id=vendor.id if vendor else None, invoice_date=dt, due_date=due,
                                   subtotal=subtotal, tax=tax, total=subtotal + tax))
                    db.commit()
                    st.success("Invoice saved to database.")
                    st.rerun()
    section("Invoice register")
    table(pd.DataFrame([{"Invoice": i.invoice_no, "Vendor": i.vendor.name if i.vendor else "—", "Date": i.invoice_date, "Due": i.due_date,
                         "Subtotal": i.subtotal, "Tax": i.tax, "Total": i.total, "Status": i.status} for i in data]),
          ("Subtotal", "Tax", "Total"), ("No invoices yet", "Add your first invoice above."))

elif page == "Banking":
    tx_all = db.query(BankTransaction).order_by(BankTransaction.txn_date.desc(), BankTransaction.id.desc()).all()
    kpi_grid([dict(label="Awaiting review", value=sum(t.status == "Unmatched" for t in tx_all), color="yellow", compact=True),
              dict(label="Matched", value=sum(t.status == "Matched" for t in tx_all), color="mint", compact=True),
              dict(label="Money in", value=money(sum(t.credit for t in tx_all)), color="sky", compact=True),
              dict(label="Money out", value=money(sum(t.debit for t in tx_all)), color="pink", compact=True)], cols=4)
    f1, f2 = st.columns([2, 1])
    flt = f1.segmented_control("Show", ["All", "Unmatched", "Matched"], default="All", label_visibility="collapsed") or "All"
    limit = f2.selectbox("Rows", [15, 30, 60], index=1, label_visibility="collapsed", format_func=lambda n: f"Latest {n} rows")
    tx = [t for t in tx_all if flt == "All" or t.status == flt][:limit]
    st.caption("Mark a line as matched only after checking the supporting ledger entry.")
    if not tx:
        empty_state("Nothing to show", "No bank lines match this filter.")
    with st.container(border=True, key="tile-3"):
        if tx:
            h = st.columns([1.2, 3, 1.4, 1.2, 1.1])
            for col, label in zip(h, ["Date", "Description", "Amount", "Status", ""]):
                col.markdown(f'<div class="txn-head">{label}</div>', unsafe_allow_html=True)
        for t in tx:
            c1, c2, c3, c4, c5 = st.columns([1.2, 3, 1.4, 1.2, 1.1], vertical_alignment="center")
            c1.markdown(f'<div class="txn-row-text mono">{t.txn_date:%d %b %Y}</div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="txn-row-text">{esc(t.description)}</div>', unsafe_allow_html=True)
            is_in = bool(t.credit) and not t.debit
            c3.markdown(f'<div class="txn-row-text {"amt-in" if is_in else "amt-out"}">{"+" if is_in else "−"}{money(t.credit or t.debit)}</div>', unsafe_allow_html=True)
            c4.markdown(pill(t.status, status_kind(t.status)), unsafe_allow_html=True)
            if t.status == "Unmatched" and c5.button("Match", key=f"match{t.id}", disabled=not can_post(user)):
                t.status = "Matched"
                db.commit()
                st.rerun()
    st.download_button("Export bank CSV", pd.DataFrame([{"Date": t.txn_date, "Description": t.description, "Debit": t.debit, "Credit": t.credit, "Status": t.status} for t in tx_all]).to_csv(index=False),
                       "bank_transactions.csv", "text/csv")

elif page == "Expenses":
    exp = db.query(Expense).order_by(Expense.expense_date.desc()).all()
    kpi_grid([dict(label="Expense claims", value=len(exp), color="coral", compact=True),
              dict(label="Total spend", value=money(sum(e.amount for e in exp)), color="yellow", compact=True),
              dict(label="Pending approval", value=sum(e.status == "Pending" for e in exp), color="sky", compact=True)], cols=3)
    if can_post(user):
        with st.expander("Record expense"):
            with st.form("expense_form"):
                c1, c2 = st.columns(2)
                employee = c1.text_input("Employee")
                cat = c2.selectbox("Category", ["Travel", "Meals", "Software", "Office supplies", "Utilities", "Other"])
                amt = c1.number_input("Amount", min_value=1.0, value=1200.0)
                dt = c2.date_input("Expense date", value=date.today())
                save = st.form_submit_button("Save expense")
            if save:
                db.add(Expense(employee=employee, category=cat, amount=amt, expense_date=dt))
                db.commit()
                st.success("Expense saved.")
                st.rerun()
    section("Employee expense register")
    table(pd.DataFrame([{"Date": e.expense_date, "Employee": e.employee, "Category": e.category, "Amount": e.amount, "Status": e.status} for e in exp]),
          ("Amount",), ("No expenses yet", "Record the first employee expense above."))

elif page == "Vendors & Customers":
    t1, t2 = st.tabs(["Vendors", "Customers"])
    with t1:
        if can_post(user):
            with st.form("vendor_form"):
                c1, c2, c3 = st.columns(3)
                name = c1.text_input("Vendor name")
                gst = c2.text_input("GSTIN")
                email = c3.text_input("Email")
                add = st.form_submit_button("Add vendor")
            if add and name.strip():
                db.add(Vendor(name=name.strip(), gstin=gst or None, email=email or None))
                db.commit()
                st.success("Vendor saved.")
                st.rerun()
        section("Vendor directory")
        table(pd.DataFrame([{"Name": x.name, "GSTIN": x.gstin, "Email": x.email, "Terms": x.payment_terms} for x in db.query(Vendor).all()]),
              empty=("No vendors yet", "Add your first vendor above."))
    with t2:
        if can_post(user):
            with st.form("customer_form"):
                c1, c2, c3 = st.columns(3)
                name = c1.text_input("Customer name")
                gst = c2.text_input("Customer GSTIN")
                email = c3.text_input("Customer email")
                add = st.form_submit_button("Add customer")
            if add and name.strip():
                db.add(Customer(name=name.strip(), gstin=gst or None, email=email or None))
                db.commit()
                st.success("Customer saved.")
                st.rerun()
        section("Customer directory")
        table(pd.DataFrame([{"Name": x.name, "GSTIN": x.gstin, "Email": x.email} for x in db.query(Customer).all()]),
              empty=("No customers yet", "Add your first customer above."))

elif page == "Financial Statements":
    b = balances(db)
    if not b:
        empty_state("Statements are waiting", "They will populate as soon as journal entries are posted.")
    else:
        df = pd.DataFrame(b)
        df["debit_balance"] = df.balance.clip(lower=0)
        df["credit_balance"] = (-df.balance).clip(lower=0)
        revenue = sum(x["credit"] - x["debit"] for x in b if x["category"] == "Revenue")
        expenses = sum(x["debit"] - x["credit"] for x in b if x["category"] == "Expense")
        assets = sum(x["debit"] - x["credit"] for x in b if x["category"] == "Asset")
        liabilities = sum(x["credit"] - x["debit"] for x in b if x["category"] == "Liability")
        equity = sum(x["credit"] - x["debit"] for x in b if x["category"] == "Equity") + revenue - expenses
        section("Income snapshot")
        kpi_grid([dict(label="Revenue", value=money(revenue), color="mint"),
                  dict(label="Expenses", value=money(expenses), color="coral"),
                  dict(label="Net income", value=money(revenue - expenses), color="yellow")], cols=3)
        section("Balance sheet snapshot")
        kpi_grid([dict(label="Assets", value=money(assets), color="sky"),
                  dict(label="Liabilities", value=money(liabilities), color="pink"),
                  dict(label="Equity incl. current earnings", value=money(equity), color="blue")], cols=3)
        variance = round(assets - liabilities - equity, 2)
        html_block(f'<div style="margin:-8px 0 8px">{pill("Balanced" if variance == 0 else "Out of balance", "ok" if variance == 0 else "bad")} '
                   f'<span class="eyebrow" style="margin-left:8px">Accounting equation variance: {money(variance)}</span></div>')
        section("Trial balance")
        tb = df.rename(columns={"code": "Code", "account": "Account", "category": "Category", "debit": "Debit", "credit": "Credit",
                                "balance": "Net balance", "debit_balance": "Debit balance", "credit_balance": "Credit balance"})
        table(tb, ("Debit", "Credit", "Net balance", "Debit balance", "Credit balance"))
        st.download_button("Export trial balance", tb.to_csv(index=False), "trial_balance.csv", "text/csv")

elif page == "Administration":
    if can_admin(user):
        section("Create user account")
        with st.form("user_create"):
            c1, c2 = st.columns(2)
            name = c1.text_input("Full name")
            email = c2.text_input("Work email")
            pw = c1.text_input("Temporary password", type="password")
            role = c2.selectbox("Role", ["Controller", "Accountant", "Auditor", "CFO"])
            add = st.form_submit_button("Create account")
        if add:
            try:
                if db.query(User).filter_by(email=email.lower().strip()).first():
                    st.error("Email already exists.")
                else:
                    db.add(User(full_name=name, email=email.lower().strip(), password_hash=hash_password(pw), role=role))
                    db.commit()
                    st.success("Account created.")
            except Exception as ex:
                st.error(str(ex))
        section("User directory")
        table(pd.DataFrame([{"Name": u.full_name, "Email": u.email, "Role": u.role, "Active": u.is_active} for u in db.query(User).all()]))
    else:
        st.warning("Only CFO users can administer accounts.")
    section("Accounting period controls", "locked periods reject new postings")
    if can_lock(user):
        c1, c2 = st.columns([2, 1], vertical_alignment="bottom")
        period = c1.text_input("Period (YYYY-MM)", value=date.today().strftime("%Y-%m"))
        if c2.button("Lock accounting period", width="stretch"):
            if len(period) == 7 and period[4] == "-":
                if not db.query(PeriodLock).filter_by(period=period).first():
                    db.add(PeriodLock(period=period, locked_by=user.id))
                    db.commit()
                st.success(f"{period} is locked.")
            else:
                st.error("Use YYYY-MM.")
    people = {u.id: u.full_name for u in db.query(User).all()}
    table(pd.DataFrame([{"Period": x.period, "Locked at": x.locked_at, "Locked by": people.get(x.locked_by, "Unknown")} for x in db.query(PeriodLock).all()]),
          empty=("No locked periods", "Locked periods will be listed here."))

db.close()
