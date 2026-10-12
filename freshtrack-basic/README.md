# FreshTrack — Inventory & Expiry Management

FreshTrack is a Django web application for recording food inventory, importing items from CSV files, and identifying items that are expired or approaching their expiry dates. It uses PostgreSQL as its database and provides a responsive dashboard for day-to-day stock checks.

## Features

- Account registration, login, and separate business workspaces.
- Dashboard showing tracked items, items expiring soon, expired items, and low stock.
- Add and edit inventory items with food category, quantity, unit, SKU/barcode, storage location, received date, expiry date, and notes.
- Expiry watchlist driven by the recorded expiry date and the category alert window. Individual items can override the alert window.
- Search and filter inventory by name, category, expiry status, and stock level.
- CSV bulk import with a downloadable template and row-level validation report. Valid rows can be imported even when another row contains an error.
- Django admin for managing food categories and inventory records.
- Optional daily email digest using a Django management command. By default, emails print to the application terminal for local development.

## Technology stack

- Python 3.13
- Django 5.2 LTS
- PostgreSQL 16
- Psycopg 3 PostgreSQL driver
- Django templates, HTML, CSS, and vanilla JavaScript
- Docker Compose for running the application and database together

## Run with Docker Desktop

Prerequisites: Docker Desktop installed and running, with its engine started.

1. Extract this ZIP file and open the `freshtrack` folder in VS Code.
2. Copy `.env.example` to `.env` if you want to edit local settings. The Compose file uses development-only defaults.
3. In the project root, run:

   ```powershell
   docker compose up --build
   ```

   Compose starts PostgreSQL, waits for the database health check, applies migrations, and then starts Django.

4. Create an account and workspace at <http://127.0.0.1:8000/accounts/register/>.
5. Open the dashboard at <http://127.0.0.1:8000/>.

To stop the app, press `Ctrl+C` and run `docker compose down`. To remove the local database volume and all data, run `docker compose down -v`.

## Run with local Python and PostgreSQL

Prerequisites: Python 3.12 or later, PostgreSQL, and a PostgreSQL database/user.

Create a database and user (using a PostgreSQL administrator account):

```sql
CREATE USER freshtrack WITH PASSWORD 'choose-a-local-password';
CREATE DATABASE freshtrack OWNER freshtrack;
```

From the project folder, in PowerShell:

```powershell
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and set `DATABASE_URL` to your local PostgreSQL credentials, for example:

```text
DATABASE_URL=postgresql://freshtrack:choose-a-local-password@localhost:5432/freshtrack
```

Then run:

```powershell
python manage.py migrate
python manage.py check
python manage.py test
python manage.py runserver
```

Open <http://127.0.0.1:8000/> and register an account.

## Main pages

| URL | Purpose |
|---|---|
| `/` | Overview dashboard and expiry summary |
| `/inventory/` | Searchable inventory list |
| `/inventory/new/` | Add an inventory item |
| `/inventory/<id>/edit/` | Edit an existing item |
| `/inventory/import/` | Upload a CSV file |
| `/inventory/template.csv` | Download a CSV template |
| `/alerts/` | Expiry watchlist and sent-digest history |
| `/admin/` | Django administration |

## CSV import format

Required columns:

- `name`
- `category` — use a seeded category name such as `Vegetables & Fruits` or `Dairy & Eggs`
- `quantity`

Optional columns:

- `unit` — `kg`, `g`, `L`, `ml`, `pcs`, `box`, or `pack`
- `expiry_date` and `received_date` — `YYYY-MM-DD`
- `sku`, `barcode`, `reorder_level`, `storage_location`, `alert_days`, `notes`

CSV files must be UTF-8 and 5 MB or smaller. SKU and barcode values must be unique within a workspace when provided. Import is row-oriented: errors are shown with CSV line numbers, while valid rows may still be saved.

## Expiry alerts

The dashboard and `/alerts/` calculate expiry status on each page request. To generate an email digest manually, run:

```powershell
docker compose exec web python manage.py send_expiry_alerts
```

The development email backend writes the message to the `web` container's terminal logs rather than delivering it to an inbox. For real delivery, configure SMTP environment variables and schedule the same management command once per day. Digest entries are recorded so that successfully handled item/date/type combinations are not repeatedly emailed on the same day.

## Notes for local development

- Food categories are seeded through database migrations.
- Inventory records are scoped to the signed-in user's workspace.
- Generic storage notes are informational only. Follow the food label and applicable food-safety procedures.
- Compose credentials, debug mode, and Django's development server are for local development only. Configure secrets, HTTPS, backups, monitoring, real email delivery, and a production server before deployment.

## Official references

See [`REFERENCES.md`](REFERENCES.md) for documentation links used while assembling this project.
