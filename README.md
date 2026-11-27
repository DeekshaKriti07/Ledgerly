# Ledgerly — Finance Intelligence

A Python + Streamlit finance workspace with a persistent SQL database, password-hash authentication, role-aware access, journal controls, invoice/vendor/customer registers, bank transactions, expenses and statements.

## 1. Requirements
- Python 3.10+
- macOS, Windows or Linux
- No Homebrew required for the database or core application

## 2. Install
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m app.bootstrap
```

## 3. Create the first administrator
```bash
python -m app.create_admin --name "Workspace Admin" --email admin@yourcompany.com --password "ChangeThisPassword123" --role CFO
```
Use a unique password of at least 10 characters. Do not commit credentials or `.env`.

## 4. Start
```bash
streamlit run streamlit_app.py
```
Open http://localhost:8501.

## Database
SQLite is the default persistent relational database (`data/ledgerly.db`). SQLAlchemy models cover users, chart of accounts, vendors, customers, invoices, journal headers and lines, bank transactions, expenses and period locks. To use PostgreSQL, set `DATABASE_URL` in `.env` and install `psycopg[binary]`.

## Security notes
- Passwords are stored as bcrypt hashes, never plaintext.
- User records and roles are stored in the database.
- CFO-only user administration; CFO/Controller period locking; Auditor read-only posting controls.
- Journal posting uses Decimal validation and enforces balanced debit/credit totals.
- Streamlit session state is used for the logged-in session. For internet-facing production deployment, place the app behind HTTPS, use a managed identity provider / hardened server-side session handling, CSRF protections, secrets management, backups and a security review. This is a local prototype, not a certified accounting system.

## UI
Neo-brutalist bento design system: thick ink outlines, hard offset shadows, flat pastel tiles (pink, butter yellow, mint, sky, coral) on warm cream, heavy Archivo headlines, tiles that pop in on load. Responsive down to phone width and respects `prefers-reduced-motion`.

- `assets/theme.css` is the single stylesheet (design tokens at the top).
- `app/ui.py` holds the reusable components (page header, KPI tiles, empty states, chart styling, login artwork).
- `streamlit_app.py` contains page logic only.

## Demo data
The bootstrap command seeds the chart of accounts, vendors, customers, bank transactions and employee expenses with synthetic examples. It does not seed real invoices or journal postings.
