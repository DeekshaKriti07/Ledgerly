from app.database import init_db, SessionLocal
from app.models import Account, Vendor, Customer, BankTransaction, Expense
from datetime import date, timedelta
import random
def seed():
    init_db(); db=SessionLocal()
    if db.query(Account).count()==0:
        groups=[
        ("Asset","Debit",["Cash","Bank","Accounts Receivable","Inventory","Input CGST","Input SGST","Input IGST","Prepaid Expenses","Fixed Assets","Accumulated Depreciation","Security Deposit","Short-term Investments"]),
        ("Liability","Credit",["Accounts Payable","Output CGST","Output SGST","Output IGST","Employee Payable","Accrued Expenses","Short-term Loan","Long-term Loan","Unearned Revenue","TDS Payable"]),
        ("Equity","Credit",["Share Capital","Retained Earnings","Owner Drawings","Current Year Earnings"]),
        ("Revenue","Credit",["Product Sales","Service Revenue","Subscription Revenue","Interest Income","Other Income","Sales Returns"]),
        ("Expense","Debit",["Cost of Goods Sold","Salaries","Rent","Cloud & Software","Marketing","Travel","Meals","Utilities","Internet","Professional Fees","Office Supplies","Repairs","Insurance","Depreciation","Bank Charges","Freight","Training","Recruitment","Legal","Audit Fees","Telephone","Printing","Staff Welfare","Research","Miscellaneous"])]
        code=1001
        for cat,norm,names in groups:
            for name in names: db.add(Account(code=code,name=name,category=cat,normal_balance=norm)); code+=1
    if db.query(Vendor).count()==0:
        for i in range(1,31): db.add(Vendor(name=f"{['Aster','BluePeak','CloudNine','Delta','Evergreen'][i%5]} {['Technologies','Supplies','Services'][i%3]} Pvt Ltd",gstin=f"33ABCDE{i%10}F1Z{i%9}",email=f"finance{i}@vendor.example"))
    if db.query(Customer).count()==0:
        for i in range(1,21): db.add(Customer(name=f"Customer {i:02} Ltd",gstin=f"29ABCDE{i%10}F1Z{i%9}"))
    if db.query(BankTransaction).count()==0:
        random.seed(14)
        for i in range(60):
            db.add(BankTransaction(txn_date=date.today()-timedelta(days=i),description=["NEFT vendor settlement","UPI customer receipt","Cloud infrastructure charge","Bank transfer"][i%4],debit=round(random.uniform(1000,25000),2) if i%3 else 0,credit=round(random.uniform(5000,50000),2) if i%3==0 else 0,reference=f"REF-{i+1:04}"))
    if db.query(Expense).count()==0:
        for i in range(35): db.add(Expense(expense_date=date.today()-timedelta(days=i),category=["Travel","Meals","Software","Office supplies"][i%4],amount=round(random.uniform(400,12000),2),employee=f"Employee {i%12+1:02}"))
    db.commit(); db.close()
if __name__=="__main__": seed()
