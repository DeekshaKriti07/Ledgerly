from app.ui import esc, kpi, money, status_kind


def test_money_formats_rupees():
    assert money(1234.5) == "₹1,234.50"
    assert money(None) == "₹0.00"


def test_user_text_is_escaped():
    assert "<script>" not in esc("<script>alert(1)</script>")
    assert "<script>" not in kpi("<script>", "<b>x</b>")


def test_status_kind():
    assert status_kind("Matched") == "ok"
    assert status_kind("Unmatched") == "warn"
