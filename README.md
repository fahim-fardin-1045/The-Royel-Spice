# The Royal Spice

### Restaurant Website & Management System · Version 2.0

A database-driven restaurant website and management dashboard built with **Python, Flask, SQLAlchemy, and MySQL/MariaDB via XAMPP**. The customer-facing experience is adapted from the provided **Spice Haven** template; the administration interface uses the supplied **TailwindAdmin** assets.

> **Project status:** Development MVP for local use, demonstration, and further development. This release is **not production-ready**. All restaurant identities, addresses, menu entries, staff, and promotions supplied as seed data are fictional.

**Stack:** Python 3.11+ · Flask 3.1+ · Flask-SQLAlchemy · Flask-Login · Flask-WTF · PyMySQL · MySQL/MariaDB · HTML/CSS/JavaScript

**Local development:** Flask on `127.0.0.1:5055` · XAMPP MySQL on `127.0.0.1:3307` · Database `royal_spice`

---

## Table of Contents

1. [Overview](#1-overview)
2. [Features](#2-features)
3. [System Architecture](#3-system-architecture)
4. [Prerequisites](#4-prerequisites)
5. [Installation — macOS with XAMPP](#5-installation--macos-with-xampp)
6. [Installation — Windows with XAMPP](#6-installation--windows-with-xampp)
7. [Upgrading an Existing Version 1 Installation](#7-upgrading-an-existing-version-1-installation)
8. [Configuration](#8-configuration)
9. [Using the Application](#9-using-the-application)
10. [Offers & Promotions](#10-offers--promotions)
11. [Project Structure](#11-project-structure)
12. [Database and Data Management](#12-database-and-data-management)
13. [Testing](#13-testing)
14. [Troubleshooting](#14-troubleshooting)
15. [Security and Known Limitations](#15-security-and-known-limitations)
16. [Credits and Licences](#16-credits-and-licences)

---

## 1. Overview

**The Royal Spice** brings together a public food-ordering website, a point-of-sale workflow, restaurant administration, and an integrated promotional-offers system. The frontend and admin panel read and write data through a single Flask application and relational database.

The sample configuration represents a restaurant in Dhanmondi, Dhaka, Bangladesh:

| Property | Seeded value |
| --- | --- |
| Restaurant | The Royal Spice — Restaurant & Café |
| Restaurant ID | `REST-001` |
| Location | Dhanmondi, Dhaka-1209, Bangladesh |
| Opening hours | 10:00 AM–11:00 PM |
| Currency | Bangladeshi Taka (BDT / ৳) |
| Dining tables | 20 tables, initially 4 seats each |
| Seating capacity | 80 guests |
| Seeded menu | 10 food and drink items |
| Seeded staff | 5 employees |
| Services | Dine-in, takeaway, delivery |
| Recorded payment options | Cash, Card, bKash, Nagad |

The details above are sample data. Update the restaurant profile in **Admin → Settings** before using the project for an actual restaurant.

## 2. Features

### Customer website

- Redesigned, responsive homepage with food highlights and featured promotions.
- Database-driven food menu with category filters and client-side search.
- Shopping cart with quantity adjustments and live order totals.
- Checkout for **dine-in**, **takeaway**, and **delivery**.
- Optional coupon code applied to eligible orders.
- Order confirmation and a private-token receipt link.
- Online reservation-request form with server-side aggregate capacity checks.
- About page and dedicated **Special Offers** page.

### Administration dashboard

- Administrator sign-in and sign-out.
- Overview dashboard with daily orders, completed sales, pending reservations, and stock alerts.
- Menu management: create, edit, unpublish, and delete eligible entries.
- Order management: progress statuses and manually recorded payment statuses.
- Staff-entered POS for dine-in or takeaway orders, including discount codes.
- **Offers & Promotions:** create, edit, enable, disable, feature, and schedule offers.
- Reservation management, dining-table management, and customer records.
- Employee records, basic inventory, expenses, and summary reports.
- Restaurant profile and operating-hours settings.

## 3. System Architecture

```text
Customer browser                      Staff / admin browser
        |                                      |
        +----------------+---------------------+
                         |
                    Flask application
                  (routes + templates)
                         |
              Flask-SQLAlchemy / PyMySQL
                         |
                 XAMPP MySQL / MariaDB
                  database: royal_spice
```

Flask serves the website directly during development. **XAMPP supplies the database server**; Apache is only needed if you want to access phpMyAdmin. You do not need to run the Flask website through Apache or browse to an `htdocs` URL.

## 4. Prerequisites

- **Python 3.11 or newer** with `venv` and `pip` (the project has been used with Python 3.13 on macOS).
- **XAMPP** with MySQL/MariaDB running.
- A supported terminal: **macOS Terminal (zsh)**, PowerShell, or Command Prompt.
- A code editor such as VS Code (recommended).
- The extracted project files and a database user with permission to create tables.

> **Port configuration:** The supplied application is tailored to your local XAMPP MySQL service on **3307**. For local MySQL URLs specifying `3306` or no port, `app.py` redirects the application connection to `3307`. It **does not modify XAMPP or your `.env` file**. Use a different code configuration if your installation genuinely requires a different MySQL port.

## 5. Installation — macOS with XAMPP

These steps target your current local development setup.

### 5.1 Open the project directory

Extract the **Complete Project ZIP** (for a new installation) and open Terminal:

```bash
cd /Applications/XAMPP/xamppfiles/htdocs/royal_spice
```

If you extracted the project elsewhere, use that actual folder path instead.

### 5.2 Create and activate a virtual environment

```bash
python3 --version
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

You should see `(venv)` in the Terminal prompt. **Do not** use `--break-system-packages` or install these dependencies into Homebrew's system-managed Python installation.

### 5.3 Start and verify XAMPP MySQL

Open **XAMPP Manager → Manage Servers → MySQL Database → Start**. Then check the database port:

```bash
nc -vz 127.0.0.1 3307
```

If necessary, identify MySQL's listening port:

```bash
sudo lsof -nP -iTCP -sTCP:LISTEN | grep -Ei 'mysql|maria'
```

### 5.4 Create the database

In phpMyAdmin (`http://localhost/phpmyadmin`), open the **SQL** tab and run:

```sql
CREATE DATABASE IF NOT EXISTS royal_spice
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

The identical SQL is included in `db_setup.sql`. If phpMyAdmin is unavailable, start XAMPP Apache or use the MySQL command-line client.

### 5.5 Configure the Flask environment

For a **fresh installation only**, create your local `.env` file:

```bash
cp .env.example .env
nano .env
```

For a common local XAMPP setup **with a blank MySQL root password**, use:

```dotenv
DATABASE_URL=mysql+pymysql://root:@127.0.0.1:3307/royal_spice?charset=utf8mb4
APP_ENV=development
COOKIE_SECURE=0
SECRET_KEY=PASTE_YOUR_GENERATED_SECRET_HERE
```

If your database user has a password, insert the **actual** password into the URL instead. Generate a stable secret:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Paste the generated value after `SECRET_KEY=`. Do not commit `.env` to a repository or share real credentials.

### 5.6 Initialise, seed, and create an administrator

Run the commands **in order**:

```bash
python -m flask --app app init-db
python -m flask --app app seed
python -m flask --app app create-admin
```

`create-admin` asks for a username and a password of **at least 10 characters**. The project does not contain default admin credentials.

### 5.7 Start the development server

```bash
python -m flask --app app run --host 127.0.0.1 --port 5055 --debug
```

Open these URLs **on the same Mac that runs Flask**:

| Page | Address |
| --- | --- |
| Customer homepage | <http://127.0.0.1:5055/> |
| Dynamic menu | <http://127.0.0.1:5055/menu> |
| Promotions | <http://127.0.0.1:5055/offers> |
| Cart | <http://127.0.0.1:5055/cart> |
| Reservations | <http://127.0.0.1:5055/reserve> |
| Admin login | <http://127.0.0.1:5055/admin/login> |
| Admin offers | <http://127.0.0.1:5055/admin/offers> |

To stop Flask, press **Ctrl+C**. When returning later, reactivate the environment with `source venv/bin/activate`; you do not need to reinstall packages each time.

## 6. Installation — Windows with XAMPP

1. Extract the **Complete Project ZIP** into your preferred directory, for example `C:\projects\royal_spice`.
2. Start **MySQL** in the XAMPP Control Panel; start Apache if you intend to use phpMyAdmin.
3. Create the `royal_spice` database using the SQL in **Section 5.4**.
4. Open **PowerShell** in the `royal_spice` directory and run:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   Copy-Item .env.example .env
   ```

5. Edit `.env` for your **actual** MySQL port and credentials. **Note:** this provided build assumes local MySQL on `3307`, including when a `3306` URL is supplied. Windows XAMPP frequently uses `3306`; in that case you must adapt the port-normalisation logic in `app.py` rather than only changing `.env`.
6. Generate a `SECRET_KEY` and initialise the application without requiring PowerShell activation:

   ```powershell
   .\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
   .\.venv\Scripts\python.exe -m flask --app app init-db
   .\.venv\Scripts\python.exe -m flask --app app seed
   .\.venv\Scripts\python.exe -m flask --app app create-admin
   .\.venv\Scripts\python.exe -m flask --app app run --host 127.0.0.1 --port 5055 --debug
   ```

7. Open <http://127.0.0.1:5055/>. See **Section 8** for environment variables.

## 7. Upgrading an Existing Version 1 Installation

**Do not perform a clean installation over your working database.** If you already have Version 1 running on your Mac, use the **Upgrade Only ZIP**.

1. In phpMyAdmin, select the `royal_spice` database and **Export → SQL** to create a backup.
2. Stop the Flask server (`Ctrl+C`).
3. Keep your existing `.env`, `venv/`, database, and image assets.
4. From Terminal, back up `app.py` and extract the upgrade into the directory containing `royal_spice/`:

   ```bash
   cd /Applications/XAMPP/xamppfiles/htdocs/royal_spice
   cp app.py app_before_v2.py
   unzip -o ~/Downloads/The_Royal_Spice_v2_Upgrade_Only.zip \
     -d /Applications/XAMPP/xamppfiles/htdocs/
   ```

   If the archive has a different filename or Downloads location, substitute its actual path. The archive contains a top-level `royal_spice/` folder.

5. Re-enable your existing environment and add **missing** tables:

   ```bash
   source venv/bin/activate
   python -m flask --app app init-db
   python -m flask --app app seed
   python -m flask --app app run --host 127.0.0.1 --port 5055 --debug
   ```

6. Verify `/offers` and `/admin/offers`, then place a test order.

**Data preservation:** `init-db` calls SQLAlchemy `create_all()`. For this upgrade, it creates missing tables (`offers` and `order_discounts`) and **does not intentionally drop existing tables**. It is **not a database migration tool** and does not update the structure of existing tables. `seed` adds missing sample records and demo offers; it does not overwrite existing records with matching seeded identifiers. Back up before upgrading regardless.

The bundled `UPGRADE_GUIDE_MAC.md` provides a shorter upgrade checklist.

## 8. Configuration

Configure application settings in the local `.env` file:

| Variable | Purpose | Local example |
| --- | --- | --- |
| `DATABASE_URL` | SQLAlchemy MySQL connection URL | `mysql+pymysql://root:@127.0.0.1:3307/royal_spice?charset=utf8mb4` |
| `SECRET_KEY` | Signs session and CSRF data; keep stable and secret | Generated random 64-character hex value |
| `APP_ENV` | Environment marker; production requires an explicit secret | `development` |
| `COOKIE_SECURE` | Set to `1` only when using HTTPS | `0` for local HTTP |

If the MySQL password contains `@`, `#`, `/`, `:` or similar URL-reserved characters, **percent-encode** it in `DATABASE_URL`.

**Time zone:** Booking times, promotion validity, and daily reports use the application machine's local time. Use **Asia/Dhaka** on a restaurant server in Bangladesh. There is no timezone selector in the current application.

## 9. Using the Application

### First-run checklist

1. Sign in at `/admin/login` using the credentials you created.
2. Check the preloaded menu in **Admin → Food Menu**.
3. Edit the fictional address, telephone number, email, operating hours and capacity in **Admin → Settings**.
4. Open `/menu` and add items to the cart.
5. Apply an offer (optional), then complete checkout with a valid service type and contact details.
6. Open the receipt; use **Admin → Orders & Billing** to update the order's workflow and payment status.
7. Create a reservation request under `/reserve`, then confirm or cancel it in the admin dashboard.
8. For a staff-entered bill, open **Admin → New POS Sale**.

### Order and reservation statuses

- **Orders:** `new` → `confirmed` → `preparing` → `ready` → `completed`; orders can also be `cancelled`.
- **Payments:** `paid` or `unpaid`; this is updated manually by staff.
- **Reservations:** `pending`, `confirmed`, `completed`, or `cancelled`.

The admin dashboard and reports use **completed orders** for sales figures. They are not a substitute for a complete accounting system.

## 10. Offers & Promotions

Version 2 introduces promotion management at **Admin → Offers & Promotions**.

| Setting | Behaviour |
| --- | --- |
| Code | Unique coupon code such as `WELCOME10` |
| Discount type | Percentage or fixed BDT amount |
| Minimum order | Order subtotal required to redeem |
| Maximum discount | Optional cap for percentage discounts |
| Date window | Optional start and expiry date/time |
| Usage limit | Optional maximum redemptions across orders |
| Enabled | Allow/disallow redemption and public listing |
| Featured | Display a qualifying offer on the homepage |

### Demo offers created by `seed`

| Code | Benefit | Minimum subtotal |
| --- | --- | --- |
| `WELCOME10` | 10% off | No minimum |
| `SPICE50` | ৳50 off | ৳500 |

**Customer flow:** Browse `/offers` → add menu items to cart → enter the code in the cart → confirm the discounted total at checkout.

**Staff flow:** Open `/admin/pos` → enter order lines → enter the coupon code → save the POS order.

The backend checks offer eligibility using the **database-calculated subtotal**, rechecks at checkout, saves the discount against the order in `order_discounts`, and increments the offer's usage count. **Only one code can apply to an order.** Existing pre-upgrade order totals remain unchanged. Currently, cancelling an order does **not automatically return** its redeemed coupon use.

> Promo codes affect the bill total only. The application does not process actual card, bKash, or Nagad transactions.

## 11. Project Structure

```text
royal_spice/
├── app.py                       # Flask application, ORM models, routes and CLI commands
├── requirements.txt             # Python dependencies
├── db_setup.sql                 # Creates the MySQL database (not its tables)
├── .env.example                 # Example local environment variables
├── .gitignore                   # Excludes secrets and generated files
├── README.md                    # Main project documentation
├── UPGRADE_GUIDE_MAC.md         # Concise macOS v1 → v2 migration checklist
├── TAILWINDADMIN_LICENSE.txt    # Admin template licence
├── templates/
│   ├── site_base.html           # Shared public-site layout
│   ├── home.html                # Homepage
│   ├── menu.html                # Dynamic food menu
│   ├── offers.html              # Public promotions
│   ├── about.html               # Restaurant introduction
│   ├── cart.html                # Cart and coupon application
│   ├── checkout.html            # Order placement
│   ├── receipt.html             # Order receipt
│   ├── reserve.html             # Reservation request form
│   └── admin/                  # Dashboard, POS, orders, offers and management pages
├── static/
│   ├── site/                    # Restaurant CSS, JavaScript, images and videos
│   └── admin/                   # Admin CSS, imagery and template assets
└── tests/
    └── test_app.py              # Automated tests using temporary SQLite
```

## 12. Database and Data Management

The application's ORM models correspond to the following main tables:

| Area | Tables |
| --- | --- |
| Restaurant setup and access | `settings`, `admins` |
| Catalogue | `menu_items` |
| Sales and customers | `customers`, `orders`, `order_items` |
| Promotions | `offers`, `order_discounts` |
| Reservations | `restaurant_tables`, `reservations` |
| Operations | `employees`, `inventory_items`, `expenses` |

**Initialisation vs seeding**

```bash
python -m flask --app app init-db       # Create tables that do not yet exist
python -m flask --app app seed          # Add missing fictional sample records
python -m flask --app app create-admin  # Prompt for an admin account
```

To back up live or important test data, export the complete database from **phpMyAdmin → Export** before changing code or schemas. The application currently has **no Alembic/Flask-Migrate migration workflow**.

## 13. Testing

The repository contains integration tests that run against a temporary **SQLite** database rather than the XAMPP MySQL database.

```bash
python -m pip install pytest
python -m pytest -q
```

The tests cover key customer routes, sample data, ordering, reservation capacity, POS, offer redemption, and admin management. CSRF is disabled **only inside the test client**. A passing SQLite test suite does not by itself confirm MySQL connectivity or production readiness.

**Manual smoke test:** load the homepage and menu; log into admin; place one test order; redeem a demo coupon; view its receipt; update the order status; and submit a reservation request.

## 14. Troubleshooting

| Symptom | Cause / resolution |
| --- | --- |
| `zsh: command not found: python` | Before virtualenv activation, use `python3`. |
| `externally-managed-environment` | Install packages inside `venv`, not system/Homebrew Python. |
| `source: no such file or directory: venv/bin/activate` | Run `python3 -m venv venv` from the project folder, then activate it. |
| `No module named flask` | Activate the environment and run `python -m pip install -r requirements.txt`. |
| `Can't connect to MySQL server ... 3306` | This build uses port **3307**. Confirm the updated `app.py` is installed and XAMPP MySQL is running. |
| `Connection refused` on 3307 | Start MySQL in XAMPP and check the actual listening port with `lsof` or `nc`. |
| MySQL `Access denied for user` | Verify database credentials and permissions in `.env`. |
| `Unknown database 'royal_spice'` | Run `db_setup.sql` in phpMyAdmin; `init-db` only creates tables. |
| Browser shows **HTTP 403** at port 5000 | On some Macs another service (including AirPlay Receiver) uses port 5000. Use Flask port **5055**. |
| Browser opens an XAMPP page instead of Flask | Use **http://127.0.0.1:5055/**, not the bare `localhost` or an `htdocs` URL. |
| `Address already in use` on 5055 | Stop the conflicting service or choose another available Flask port. |
| `/admin/offers` redirects to login | Sign in with an administrator account created via `create-admin`. |
| Valid promotion does not apply | Check enablement, dates, minimum order, usage limit, and exact code. |

Useful diagnostics:

```bash
python3 --version
nc -vz 127.0.0.1 3307
lsof -nP -iTCP:5055 -sTCP:LISTEN
curl -i http://127.0.0.1:5055/
```

## 15. Security and Known Limitations

### Existing precautions

The starter includes administrator login with password hashing, CSRF protection on forms, server-calculated order totals, validation of discount rules, and private-token receipt URLs. These controls are not a complete security assessment.

### Not included in this release

- **Online payment processing:** Cash/Card/bKash/Nagad entries are selections only; no payment is collected or verified automatically.
- **Recipe-based stock consumption:** Inventory changes are manual, not calculated from orders.
- **Table-level reservation assignment:** Reservations check approximate aggregate capacity and require staff confirmation.
- **Automated salary or payroll:** Employee salary values are informational records.
- **Customer accounts and notifications:** No customer login, transactional email, or SMS alerts.
- **Full accounting or tax calculation:** Reports are simple sales and expenses summaries.
- **Fine-grained staff permissions:** The existing admin system does not offer separate cashier/manager role permissions.
- **Production deployment controls:** No integrated migrations, rate limiting, backup scheduler, background jobs, or production WSGI configuration.

**Before public deployment:** disable debug mode, use HTTPS with secure cookies, set a strong persistent `SECRET_KEY`, use a limited-privilege database account, review access controls, configure backups/monitoring, confirm template licences, and test thoroughly against production-like MySQL data.
