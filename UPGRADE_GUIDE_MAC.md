# The Royal Spice — Upgrade to v2 (Offers + New Website Design)

This update keeps the **existing** XAMPP/MySQL server on **port 3307**. Do **not** change MySQL's port. Your previously created database, orders, administrator, products, reservations and tables remain in place.

## Upgrade an existing working installation on your Mac

1. **Back up your database first** in phpMyAdmin: select `royal_spice` → **Export** → SQL. Keep your `.env` file private and unchanged.
2. Stop your Flask server in Terminal with **Ctrl+C**.
3. Extract `Royal_Spice_v2_Upgrade_Only.zip`. It contains the new `app.py`, updated `templates`, and new `static/site/css/royal-v2.css` / `static/site/js/royal-v2.js`.
4. Copy the **contents of the ZIP's `royal_spice/` directory into your existing directory** `/Applications/XAMPP/xamppfiles/htdocs/royal_spice/`, allowing replacement of matching files. Do **not** replace/delete `.env`, and do **not** replace the database or delete your `venv` directory. Existing static images are reused, so keep `static/site/images/` intact.
5. In Terminal:

   ```bash
   cd /Applications/XAMPP/xamppfiles/htdocs/royal_spice
   source venv/bin/activate
   python -m flask --app app init-db
   python -m flask --app app seed
   python -m flask --app app run --host 127.0.0.1 --port 5055 --debug
   ```

6. Open **http://127.0.0.1:5055/**, then **http://127.0.0.1:5055/offers** and **http://127.0.0.1:5055/admin/offers** (admin login required). `init-db` uses SQLAlchemy `create_all()` to **create the new tables** `offers` and `order_discounts` without dropping or modifying existing tables. You should not need to re-create your admin login or re-install packages.

**Important:** `seed` creates two demonstration codes (only if absent): `WELCOME10` (10% off) and `SPICE50` (৳50 off orders of at least ৳500). These are for testing; edit or disable in Admin → Offers before using the site commercially.

## What's new

- Redesigned customer homepage, sticky responsive navigation, menu cards, menu search and category filters, offer landing page, cart, checkout, receipt, About and reservations pages.
- Admin → **Offers & Promotions**: create or edit promotions, activate/deactivate, feature on homepage, set percentage/fixed discount, order minimum, optional percentage cap, date/time window, and maximum redemptions.
- Cart applies promo code; checkout checks eligibility again in the server against the trusted menu subtotal. Receipt and MySQL retain an **order discount snapshot**.
- Existing customer and POS order totals include discounts when a valid code is used. Staff can enter a promo code on the POS form too.
- No external payment processing is enabled: Cash/Card/bKash/Nagad selections are recorded for manual collection, not charged.

### File locations

- `app.py`: Flask models, discounts, checkout, admin offer routes and seed data.
- `templates/admin/offers.html`: admin promotion form.
- `templates/offers.html`: customer-facing offer page.
- `static/site/css/royal-v2.css`: new public-site design.
- `static/site/js/royal-v2.js`: responsive navigation and menu filtering.
- `tests/test_app.py`: extra automated SQLite tests (`python -m pip install pytest && python -m pytest -q`).

### Notes

- Offer expiry/starts are interpreted in the local timezone of the server process, intended to be **Asia/Dhaka** when deployed for Bangladesh.
- One promo code per customer order. Use counts include completed orders and any other submitted orders, including cancelled orders, to prevent over-redemption. If you want cancellations to restore a use, that requires a separate policy and implementation.
- Existing order totals remain unchanged. Old receipts simply do not have a discount record.
- Requires an active MySQL server and existing `royal_spice` database; setting up MySQL on port 3307 is already handled in Python.
- Use a secure login and HTTPS before public deployment; the Flask debug server must not be exposed to the Internet.
