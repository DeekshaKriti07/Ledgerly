
"""Ledgerly UI kit: theme injection and small HTML components (neo-brutalist bento).

All user-supplied text is escaped before it is placed in HTML.
"""
from __future__ import annotations

import html
from functools import lru_cache
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
PALETTE = ["#ffb4d2", "#ffdd7a", "#55d6a0", "#a9d9fb", "#8ea3f6", "#ff7a63", "#5ed3c8"]
INK = "#1b1a17"

PAGES = {
    "Overview": "pink",
    "General Ledger": "yellow",
    "Journal Entries": "mint",
    "Invoices": "sky",
    "Banking": "blue",
    "Expenses": "coral",
    "Vendors & Customers": "teal",
    "Financial Statements": "yellow",
    "Administration": "pink",
}

BRAND_SVG = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="#1b1a17" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M5 20V13M12 20V6M19 20V10"/></svg>'
)


def esc(value) -> str:
    return html.escape(str(value if value is not None else ""))


def _h(markup: str) -> str:
    """Collapse indentation/blank lines so Markdown never treats HTML as a code block."""
    return "".join(line.strip() for line in markup.splitlines())


def html_block(markup: str) -> None:
    st.markdown(_h(markup), unsafe_allow_html=True)


@lru_cache(maxsize=1)
def _css() -> str:
    return (ROOT / "assets" / "theme.css").read_text(encoding="utf-8")


def inject_theme() -> None:
    st.markdown(f"<style>{_css()}</style>", unsafe_allow_html=True)


def money(value) -> str:
    try:
        return f"₹{float(value):,.2f}"
    except (TypeError, ValueError):
        return "₹0.00"


def brand(sub: str = "FINANCE INTELLIGENCE") -> str:
    return (
        f'<div class="brand"><div class="brand-mark">{BRAND_SVG}</div>'
        f'<div><div class="brand-word">Ledgerly</div><div class="brand-sub">{esc(sub)}</div></div></div>'
    )


def pill(text: str, kind: str = "") -> str:
    return f'<span class="pill {kind}">{esc(text)}</span>'


def status_kind(status: str) -> str:
    return {"Matched": "ok", "Posted": "ok", "Paid": "ok", "Approved": "ok",
            "Unmatched": "warn", "Pending": "warn", "Rejected": "bad", "Overdue": "bad"}.get(status, "info")


def page_header(page: str, subtitle: str) -> None:
    names = list(PAGES)
    color = PAGES.get(page, "pink")
    number = f"{names.index(page) + 1:02d}" if page in names else ""
    html_block(f"""
    <div class="page-head"><div>
      <div class="eyebrow">Finance operations / control room</div>
      <h1>{esc(page)}</h1><p>{esc(subtitle)}</p></div>
      <div class="page-badge t-{color}">{number}</div></div>""")


def section(title: str, hint: str = "") -> None:
    hint_html = f"<span>{esc(hint)}</span>" if hint else ""
    html_block(f'<div class="section-title"><h3>{esc(title)}</h3>{hint_html}</div>')


def kpi(label: str, value, color: str = "white", hint: str = "",
        compact: bool = False, index: int = 0, extra_class: str = "") -> str:
    hint_html = f'<div class="kpi-hint">{esc(hint)}</div>' if hint else ""
    cls = "compact" if compact else ""
    return (
        f'<div class="tile kpi t-{color} {cls} {extra_class}" style="--i:{index}">'
        f'<div class="kpi-top"><div class="kpi-label">{esc(label)}</div></div>'
        f'<div><div class="kpi-value">{esc(value)}</div>{hint_html}</div></div>'
    )


def kpi_grid(items: list[dict], cols: int = 4) -> None:
    cards = "".join(kpi(index=i, **item) for i, item in enumerate(items))
    html_block(f'<div class="bento cols-{cols}">{cards}</div>')


def empty_state(title: str, text: str) -> None:
    html_block(f'<div class="empty"><div><b>{esc(title)}</b><span>{esc(text)}</span></div></div>')


def style_figure(fig, height: int = 320):
    """Apply the Ledgerly look to a Plotly figure."""
    fig.update_layout(
        height=height, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif", color=INK, size=13),
        margin=dict(l=4, r=4, t=10, b=4), colorway=PALETTE, bargap=.28,
        legend=dict(orientation="h", y=1.14, x=0, title=None, font=dict(size=12)),
        hoverlabel=dict(bgcolor="#fffdf8", font_color=INK, bordercolor=INK),
    )
    fig.update_xaxes(showgrid=False, linecolor=INK, linewidth=2, tickfont=dict(size=11), title=None)
    fig.update_yaxes(gridcolor="rgba(27,26,23,.12)", zeroline=False, tickfont=dict(size=11), title=None)
    fig.update_traces(marker_line_color=INK, marker_line_width=2, selector=dict(type="bar"))
    return fig


# --------------------------- Login artwork (inline SVG) ---------------------------
SCENE_SVG = """
<svg viewBox="0 0 440 300" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Rising chart, coin and receipt">
<g stroke="#1b1a17" stroke-width="3.5" stroke-linejoin="round" stroke-linecap="round">
 <ellipse cx="70" cy="236" rx="46" ry="14" fill="#fffdf8" opacity=".55" stroke="none"/>
 <g class="float"><rect x="58" y="44" width="250" height="176" rx="16" fill="#fffdf8"/>
  <path d="M58 76h250" /><circle cx="78" cy="60" r="5" fill="#ff7a63"/><circle cx="96" cy="60" r="5" fill="#ffdd7a"/><circle cx="114" cy="60" r="5" fill="#55d6a0"/>
  <rect x="86" y="150" width="34" height="50" rx="5" fill="#ffb4d2"/><rect x="134" y="128" width="34" height="72" rx="5" fill="#ffdd7a"/>
  <rect x="182" y="110" width="34" height="90" rx="5" fill="#55d6a0"/><rect x="230" y="92" width="34" height="108" rx="5" fill="#8ea3f6"/>
  <path d="M84 140l56-26 40-8 70-36" fill="none" stroke="#ff7a63" stroke-width="4.5"/><path d="M236 62l16 4-6 15" fill="none" stroke="#ff7a63" stroke-width="4.5"/></g>
 <g class="float b"><circle cx="350" cy="86" r="42" fill="#ffdd7a"/><circle cx="350" cy="86" r="29" fill="none"/>
  <text x="350" y="100" text-anchor="middle" font-family="Archivo, Arial Black, sans-serif" font-weight="900" font-size="42" fill="#1b1a17" stroke="none">₹</text></g>
 <g class="float c"><path d="M318 160h84v108l-14-9-14 9-14-9-14 9-14-9-14 9z" fill="#fcf8de"/>
  <path d="M334 184h52M334 202h52M334 220h30" stroke-width="3.5"/><path d="M372 238h14" stroke="#ff7a63"/></g>
 <path d="M30 100l7 -18 7 18 18 7 -18 7 -7 18 -7 -18 -18 -7z" transform="translate(-10 120) scale(.7)" fill="#ffb4d2"/>
</g></svg>
"""


def splash_html() -> str:
    return _h(f"""
    <div class="splash"><div class="splash-inner">
      <div class="splash-mark">{BRAND_SVG}</div><div class="splash-word">Ledgerly</div>
      <div class="splash-tag">CLARITY IN EVERY NUMBER</div><div class="splash-bar"><i></i></div></div></div>""")


def login_art_html() -> str:
    features = "".join(
        f'<div class="tile feature t-{c}" style="--i:{i + 2}"><span class="eyebrow">{i + 1:02d}</span><b>{esc(t)}</b></div>'
        for i, (c, t) in enumerate([
            ("sky", "Insightful reports"), ("mint", "Smooth workflows"),
            ("yellow", "Balanced books"), ("pink", "Locked periods")]))
    return _h(f"""
    <div class="tile t-cream login-hero" style="--i:0">
      {brand("FINANCE INTELLIGENCE PLATFORM")}
      <h1>Clarity in every <em>number.</em></h1>
      <p>A calmer way to run your finance operations: journals, invoices, banking and statements in one connected workspace.</p>
      <div class="sticker s2">₹</div>
    </div>
    <div class="feature-row">{features}</div>
    <div class="scene-row">
      <div class="tile t-sky scene" style="--i:6">{SCENE_SVG}</div>
      <div class="tile t-yellow fact" style="--i:7">
        <div class="eyebrow">Built for India</div><b>INR + GSTIN ready</b>
        <span>Vendor and customer GSTIN fields, rupee formatting and role-based controls out of the box.</span></div>
    </div>""")
