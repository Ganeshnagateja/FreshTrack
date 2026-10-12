# FreshTrack architecture

## Request flow

1. The user visits a Django URL in a browser.
2. Django's URL dispatcher routes the request to an inventory view.
3. The view checks authentication and the user's business workspace.
4. Django ORM reads or writes workspace-scoped records in PostgreSQL.
5. Django templates render the page and display the updated inventory or expiry state.

## Core data models

- **Organization**: a business workspace.
- **User**: an authenticated user associated with a workspace.
- **FoodCategory**: a shared food category with a perishability profile and default expiry alert window.
- **InventoryItem**: an organization's item record, including quantity, unit, received date, expiry date and optional alert-window override.
- **ExpiryAlert**: records an item that was included in a successfully sent daily email digest, avoiding repeat sends for the same item/date/type.

## Expiry-state rules

For an active item with an expiry date:

- **Expired**: the expiry date is earlier than the current local date.
- **Expiring**: the expiry date is today or within the effective alert window.
- **Fresh**: the expiry date is later than the alert window.
- **No date**: no expiry date has been recorded.

An item's effective alert window is its own override when set, otherwise the default for its food category. The dashboard computes status at request time, so it does not depend on the email digest command.

## CSV workflow

1. The user downloads the CSV template or prepares a UTF-8 CSV file.
2. Django checks the upload extension and file size.
3. The importer checks required headers, category names, quantities, units, dates and duplicate identifiers.
4. Valid rows are saved to PostgreSQL; invalid rows appear in a report with CSV line numbers.
5. The user reviews the imported records in the inventory page.

## Boundaries

The current application is intentionally limited to inventory entry, CSV import, and expiry tracking. It does not include forecasting models, donation listings, recipient matching, POS integration endpoints, barcode camera scanning, or pickup logistics.
