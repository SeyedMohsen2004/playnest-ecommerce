import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from django.db import connections
from psycopg import sql

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def database_connection(database_name, config, *, autocommit=False):
    return psycopg.connect(
        dbname=database_name,
        user=config["USER"],
        password=config["PASSWORD"],
        host=config["HOST"],
        port=config["PORT"],
        autocommit=autocommit,
    )


def run_manage(database_name, config, *arguments):
    environment = os.environ.copy()
    environment.update(
        {
            "POSTGRES_DB": database_name,
            "POSTGRES_USER": str(config["USER"]),
            "POSTGRES_PASSWORD": str(config["PASSWORD"]),
            "POSTGRES_HOST": str(config["HOST"]),
            "POSTGRES_PORT": str(config["PORT"]),
        }
    )
    return subprocess.run(
        [sys.executable, "manage.py", *arguments],
        cwd=BACKEND_ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.fixture
def disposable_postgres_database():
    database_name = f"playnest_migration_{uuid4().hex}"
    default_config = deepcopy(connections.databases["default"])
    admin_connection = database_connection(
        "postgres",
        default_config,
        autocommit=True,
    )
    with admin_connection.cursor() as cursor:
        cursor.execute(
            sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name))
        )

    try:
        yield database_name, default_config
    finally:
        with admin_connection.cursor() as cursor:
            cursor.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = %s AND pid <> pg_backend_pid()",
                (database_name,),
            )
            cursor.execute(
                sql.SQL("DROP DATABASE {}").format(sql.Identifier(database_name))
            )
        admin_connection.close()


def applied_order_migrations(database_name, config):
    with database_connection(database_name, config) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT name FROM django_migrations "
                "WHERE app = 'orders' ORDER BY name"
            )
            return [row[0] for row in cursor.fetchall()]


def test_consolidated_order_migration_applies_from_0011(
    disposable_postgres_database,
):
    database_name, config = disposable_postgres_database
    run_manage(
        database_name,
        config,
        "migrate",
        "orders",
        "0011_order_shipping_zone_shippingsettings",
        "--noinput",
        "--verbosity=0",
    )
    assert applied_order_migrations(database_name, config)[-1] == (
        "0011_order_shipping_zone_shippingsettings"
    )

    run_manage(
        database_name,
        config,
        "migrate",
        "orders",
        "--noinput",
        "--verbosity=0",
    )

    migrations = applied_order_migrations(database_name, config)
    assert migrations[-1] == "0012_couponredemption_and_more"
    assert not any(name.startswith("0013") for name in migrations)
    with database_connection(database_name, config) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'orders_orderitem'"
            )
            order_item_columns = {row[0] for row in cursor.fetchall()}
            cursor.execute(
                "SELECT conname FROM pg_constraint "
                "WHERE conname = 'coupon_used_count_within_limit'"
            )
            coupon_constraint = cursor.fetchone()
            cursor.execute(
                "SELECT indexname FROM pg_indexes "
                "WHERE indexname = 'coupon_redemption_state_idx'"
            )
            redemption_index = cursor.fetchone()
    assert "cart_item_id_snapshot" in order_item_columns
    assert coupon_constraint == ("coupon_used_count_within_limit",)
    assert redemption_index == ("coupon_redemption_state_idx",)


def test_fresh_migration_graph_applies_from_zero(disposable_postgres_database):
    database_name, config = disposable_postgres_database
    run_manage(
        database_name,
        config,
        "migrate",
        "--noinput",
        "--verbosity=0",
    )
    check = run_manage(
        database_name,
        config,
        "migrate",
        "--check",
        "--noinput",
        "--verbosity=0",
    )

    assert check.returncode == 0
    migrations = applied_order_migrations(database_name, config)
    assert migrations[-1] == "0012_couponredemption_and_more"
    assert not any(name.startswith("0013") for name in migrations)
