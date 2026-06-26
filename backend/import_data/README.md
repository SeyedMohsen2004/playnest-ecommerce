# IpakToys Product Import Data

Place real client import files here before running the product import command.

Expected local structure:

```text
backend/import_data/
  products.xlsx
  raw/
    محصولات.rar
  product_images/
    هوش چین/
    لگو بتمن/
    ...
```

The repository ignores the actual Excel workbook, archive, and extracted images
because they are client data. Keep this README so developers know where to place
the files.

Default import command:

```bash
python manage.py import_real_products
```

Explicit paths:

```bash
python manage.py import_real_products \
  --excel import_data/products.xlsx \
  --images-dir import_data/product_images
```

Clear existing products before import:

```bash
python manage.py import_real_products --clear-existing
```

`--clear-existing` deletes products only. If products are referenced by order
items, the command stops safely and explains that dependent data still exists.

For a disposable local/demo reset, explicitly allow dependent data cleanup:

```bash
python manage.py import_real_products \
  --clear-existing \
  --clear-dependent-demo-data
```

This destructive option deletes payments, orders, carts, wishlist items,
reviews, product images, and products before importing. Use it only for
development/demo data and take a database backup before any production import.
