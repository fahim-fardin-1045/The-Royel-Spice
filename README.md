# Version 2: redesigned website + promotional offers

See **`UPGRADE_GUIDE_MAC.md`** for safe steps to upgrade your existing Mac/XAMPP install. The admin now supports offer/coupon management and the public pages have a redesigned layout. Run `flask --app app init-db` to add **two new tables without deleting your data**, then `flask --app app seed` for two optional demo offers. MySQL remains on **3307**, Flask recommended on **5055** on macOS.

---

# The Royal Spice — Dynamic Restaurant Website + Admin Panel

A **Flask / SQLAlchemy** restaurant-management starter connected to **XAMPP MySQL / MariaDB**. The customer website adapts the supplied **Spice Haven** HTML/CSS/photos. The staff area adapts the supplied **TailwindAdmin** compiled CSS and imagery. Both interfaces use the same database.

**Demo business:** The Royal Spice, REST-001, Dhanmondi, Dhaka. The document's 10 foods, 5 staff members, 20 tables (4 seats each), 80 seats, opening hours (10:00–23:00), and BDT currency are used. This data is **fictional**.

## Mac / XAMPP setup (MySQL on port 3307)

This project is configured for the XAMPP MySQL server on **port 3307**. Its `app.py` automatically updates **local MySQL URLs** using port `3306` (including those already saved in `.env`) to port `3307`; it does **not** change the XAMPP MySQL service or rewrite `.env`. Other database URLs (such as SQLite used by tests) are left unchanged. MySQL must be running, the database `royal_spice` must exist, and the username/password must be correct.

From the extracted `royal_spice` folder:

```sh
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` to insert your actual MySQL password, if any, and a randomly generated `SECRET_KEY`. Create the database using phpMyAdmin or run `db_setup.sql`. Then execute:

```sh
python -m flask --app app init-db
python -m flask --app app seed
python -m flask --app app create-admin
python -m flask --app app run --debug
```

If replacing an earlier `app.py` with this version, **keep your existing `.env` file**. A local MySQL URL that says port 3306 will be directed to 3307 automatically. If you see `Access denied`, check the existing `.env` username/password; the port fix does not change credentials.

## Step-by-step installation on Windows with XAMPP

1. Install **Python 3.11+** and **XAMPP**, if not installed already.
2. Extract this ZIP to a folder such as `C:\projects\royal_spice`.
3. Open the **XAMPP Control Panel**. Start **MySQL**. Also start **Apache** if you want to use phpMyAdmin.
4. In a browser, open **http://localhost/phpmyadmin**, choose the **SQL** tab and paste `db_setup.sql`:

   ```sql
   CREATE DATABASE IF NOT EXISTS royal_spice
   CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

   Press **Go**. (You only need to do this once.)
5. Open **PowerShell** in the extracted project directory and run:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   Copy-Item .env.example .env
   ```

   If PowerShell blocks activation, use Command Prompt: `.venv\Scripts\activate.bat`, or run `.\.venv\Scripts\python.exe` instead of `python` below.
6. Open `.env` in Notepad/VS Code. Set `DATABASE_URL` for **your MySQL password**. By default, an untouched XAMPP installation often uses MySQL user `root` with a blank password:

   ```dotenv
   DATABASE_URL=mysql+pymysql://root:@127.0.0.1:3307/royal_spice?charset=utf8mb4
   ```

   If you configured a password (or a separate database user), insert its real credentials instead. If your password contains special characters, URL-encode them (e.g., `@` → `%40`). **Using root without a password is only acceptable for isolated local development; create a limited MySQL account for deployments.**
7. Generate a permanent random Flask session secret:

   ```powershell
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

   Paste the generated value after `SECRET_KEY=` in `.env`.
8. Initialise the database, seed the sample menu/staff/tables and make an admin account:

   ```powershell
   flask --app app init-db
   flask --app app seed
   flask --app app create-admin
   ```

   `create-admin` will prompt for a username and password (at least 10 characters); no admin account or default password is shipped in the source.
9. Start the website:

   ```powershell
   flask --app app run --debug
   ```

10. Visit:

   - **Customer website:** http://127.0.0.1:5000/
   - **Menu and ordering:** http://127.0.0.1:5000/menu
   - **Reservation requests:** http://127.0.0.1:5000/reserve
   - **Admin login:** http://127.0.0.1:5000/admin/login
   - **POS billing:** http://127.0.0.1:5000/admin/pos
   - **phpMyAdmin:** http://localhost/phpmyadmin

> **XAMPP is the MySQL server, not the Python web host.** The `flask` command serves the site on port 5000, and phpMyAdmin lets you inspect the database through Apache (typically port 80).

## Main features

| Customer website | Admin interface |
| --- | --- |
| Original responsive landing page and About page | Protected login and dashboard |
| Dynamic database-driven food menu and BDT prices | Food menu create/edit/delete/unpublish |
| Add food to cart and edit quantities | View and update order statuses |
| Delivery, takeaway, dine-in checkout | Manual POS sale and bill generation |
| Order receipt with opaque, hard-to-guess link | Manually mark payments as paid/unpaid |
| Reservation form with server-side capacity checks | Confirm/cancel reservations |
| CSRF-protected order and reservation forms | Manage seating tables, staff, and inventory |
| | Customer list, expenses, simple sales reports |
| | Edit restaurant profile, address, opening hours |

### Typical flow

1. Sign into the admin panel. Check the 10 preloaded foods on **Food Menu**.
2. Open the public menu, add items, go to cart and checkout. Submit a **Cash** order.
3. Return to **Admin → Orders & Billing**, mark the order **Completed** and the payment **Paid**.
4. On **Dashboard**, today's completed sales will update. **Reports** will include the completed order.
5. Visit **Book a Table**, enter a future time inside operating hours, and submit. In **Admin → Reservations**, set its status to **Confirmed**.
6. Use **New POS Sale** for a staff-entered dine-in bill. Its completed/paid checkboxes affect dashboard totals.

## Project structure

```text
royal_spice/
├── app.py                    # Flask routes, models and commands
├── requirements.txt          # Python dependencies
├── db_setup.sql              # Create database in XAMPP MySQL
├── .env.example              # Environment variable example
├── templates/
│   ├── home.html             # Adapted Spice Haven homepage
│   ├── menu.html             # Live menu from database
│   ├── about.html
│   ├── reserve.html           # Reservation POST form
│   ├── cart.html
│   ├── checkout.html
│   ├── receipt.html
│   └── admin/                # TailwindAdmin-derived dashboard pages
├── static/
│   ├── site/                 # Spice Haven CSS, JS, photos and video
│   └── admin/                # TailwindAdmin compiled CSS, logo and images
└── tests/                    # Pytest integration tests (optional)
```

## Quick test instructions

After following setup, open the browser and try a food order and reservation. To run automated SQLite-backed integration tests without changing your MySQL database:

```powershell
python -m pip install pytest
python -m pytest -q
```

Tests override the database URL with a temporary SQLite database and disable CSRF **only for test requests**. Normal operation uses the XAMPP MySQL URL from `.env`.

## Important starter-project limitations

- This is a **development MVP, not production-ready software**. Before public deployment, add rate limiting, staff roles/permissions, tests against real MySQL, database migrations, monitoring, backups, TLS, proper secrets management and a production WSGI server.
- Payment dropdowns for **Cash / Card / bKash / Nagad** record preferences. **No payment gateway, automatic verification, or charge is performed.** Staff mark received payments manually.
- Reservations check aggregate 2-hour seating capacity and may be pending or confirmed. They **do not reserve a specific table**, combine tables for large groups, or sync external booking platforms. Admin must check actual seating assignment.
- Inventory is **manual**; it does not deduct ingredients from recipes. Staff salaries are records, not automated payroll. Simple sales-minus-expenses reporting is not full accounting profit.
- The POS records dine-in or takeaway orders. Delivery requires the public checkout to enter an address.
- A customer receipt URL contains a random access token; share it privately. The demonstration does not include customer accounts, email, or SMS alerts.
- Demo phone, email and website fields are **placeholders**, not real business contact details. Replace them in **Admin → Settings** before any public use.
- The original template's imagery is **illustrative**; the food images are not individually mapped to the 10 sample menu items.
- All times are interpreted as the **machine's local time**. For restaurant use, set the computer/server timezone to **Asia/Dhaka**.

## Credits and licenses

- **Spice Haven** (provided template): design and code by Rabina Vishwakarma, distributed by ThemeWagon. Credits retained in the adapted public footer. Refer to the supplied template's own license and attribution terms for any public deployment.
- **TailwindAdmin** (provided template): MIT license copyright © 2023 Codescandy, copied into `TAILWINDADMIN_LICENSE.txt`.

---
To stop the dev server, press `Ctrl+C` in the terminal. Stop MySQL from the XAMPP Control Panel when you no longer need it.
