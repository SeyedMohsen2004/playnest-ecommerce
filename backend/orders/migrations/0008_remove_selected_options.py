from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0007_option_value_stock_snapshots"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="cartitem",
            name="selected_option_value_ids",
        ),
        migrations.RemoveField(
            model_name="cartitem",
            name="selected_options",
        ),
        migrations.RemoveField(
            model_name="orderitem",
            name="selected_option_value_ids_snapshot",
        ),
        migrations.RemoveField(
            model_name="orderitem",
            name="selected_options_snapshot",
        ),
        migrations.RunSQL(
            sql="""
            WITH duplicate_totals AS (
                SELECT
                    cart_id,
                    product_id,
                    MIN(id) AS keep_id,
                    SUM(quantity) AS total_quantity
                FROM orders_cartitem
                GROUP BY cart_id, product_id
                HAVING COUNT(*) > 1
            )
            UPDATE orders_cartitem AS item
            SET quantity = duplicate_totals.total_quantity
            FROM duplicate_totals
            WHERE item.id = duplicate_totals.keep_id;

            WITH duplicate_totals AS (
                SELECT
                    cart_id,
                    product_id,
                    MIN(id) AS keep_id
                FROM orders_cartitem
                GROUP BY cart_id, product_id
                HAVING COUNT(*) > 1
            )
            DELETE FROM orders_cartitem AS item
            USING duplicate_totals
            WHERE item.cart_id = duplicate_totals.cart_id
              AND item.product_id = duplicate_totals.product_id
              AND item.id <> duplicate_totals.keep_id;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.AddConstraint(
            model_name="cartitem",
            constraint=models.UniqueConstraint(
                fields=("cart", "product"),
                name="unique_product_per_cart",
            ),
        ),
    ]
