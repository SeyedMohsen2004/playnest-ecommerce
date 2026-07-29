# PlayNest Product Import Data

This directory is a local staging area for the guarded product import command.
The public repository retains only this guide and `.gitkeep`; imported
workbooks, archives, images, and generated media are gitignored.

Expected local structure:

```text
backend/import_data/
  products.xlsx
  product_images/
    example-product/
```

Customer datasets and commercial product media are not included in the public
repository.

## Import

From the backend directory:

```bash
python manage.py import_real_products
```

Or provide explicit paths:

```bash
python manage.py import_real_products \
  --excel import_data/products.xlsx \
  --images-dir import_data/product_images
```

The importer validates expected workbook columns, imports rows in individual
transactions, and reports skipped records and image warnings for operator
review.

## Destructive Options

Remove existing products before import:

```bash
python manage.py import_real_products --clear-existing
```

`--clear-existing` deletes products only. If order items still reference
products, the command stops rather than deleting orders or payments.

For disposable local development data only, dependent ecommerce data can be
removed explicitly:

```bash
python manage.py import_real_products \
  --clear-existing \
  --clear-dependent-demo-data
```

This mode deletes payments, orders, carts, wishlist items, reviews, product
images, and products before importing. Do not use it against production or
valuable data without explicit approval.

Production imports require:

1. A verified database and media backup created before the import.
2. Operator review of the workbook, image set, and command options.
3. A rollback plan and an approved maintenance window.
4. Confirmation that destructive modes are not selected unless deletion is
   explicitly intended and approved.
