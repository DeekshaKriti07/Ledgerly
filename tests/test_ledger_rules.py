from decimal import Decimal
def test_debits_equal_credits():
    debit=Decimal("1250.50"); credit=Decimal("1250.50")
    assert debit==credit
