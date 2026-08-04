from datetime import timedelta

from django.utils import timezone

from tests import test_order_migrations as migration_helpers

database_connection = migration_helpers.database_connection
disposable_postgres_database = migration_helpers.disposable_postgres_database
run_manage = migration_helpers.run_manage


def applied_account_migrations(database_name, config):
    with database_connection(database_name, config) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT name FROM django_migrations "
                "WHERE app = 'accounts' ORDER BY name"
            )
            return [row[0] for row in cursor.fetchall()]


def test_auth_hardening_migration_preserves_users_and_invalidates_plaintext_otp(
    disposable_postgres_database,
):
    database_name, config = disposable_postgres_database
    run_manage(
        database_name,
        config,
        "migrate",
        "accounts",
        "0001_initial",
        "--noinput",
        "--verbosity=0",
    )
    now = timezone.now()
    with database_connection(database_name, config) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO accounts_user "
                "(password, last_login, is_superuser, phone_number, first_name, "
                "last_name, email, is_phone_verified, is_active, is_staff, "
                "date_joined) VALUES (%s, NULL, FALSE, %s, %s, %s, %s, TRUE, "
                "TRUE, FALSE, %s) RETURNING id",
                (
                    "existing-password-hash",
                    "09120000000",
                    "Existing",
                    "User",
                    "existing@example.com",
                    now,
                ),
            )
            user_id = cursor.fetchone()[0]
            cursor.execute(
                "INSERT INTO accounts_phoneotp "
                "(phone_number, code, purpose, is_used, expires_at, created_at, "
                "verified_at) VALUES (%s, %s, 'register', FALSE, %s, %s, NULL)",
                ("09120000000", "123456", now, now),
            )

    run_manage(
        database_name,
        config,
        "migrate",
        "accounts",
        "--noinput",
        "--verbosity=0",
    )

    assert applied_account_migrations(database_name, config)[-1] == (
        "0002_auth_session_hardening"
    )
    with database_connection(database_name, config) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT password, is_active, is_phone_verified FROM accounts_user "
                "WHERE id = %s",
                (user_id,),
            )
            assert cursor.fetchone() == ("existing-password-hash", True, True)
            cursor.execute(
                "SELECT code_hash, delivery_status, invalidated_at "
                "FROM accounts_phoneotp"
            )
            code_hash, delivery_status, invalidated_at = cursor.fetchone()
            assert code_hash.startswith("!")
            assert delivery_status == "failed"
            assert invalidated_at is not None
            cursor.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'accounts_phoneotp'"
            )
            columns = {row[0] for row in cursor.fetchall()}
            assert "code" not in columns
            assert "code_hash" in columns


def test_fresh_auth_migration_graph_applies_from_zero(disposable_postgres_database):
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
    assert applied_account_migrations(database_name, config)[-1] == (
        "0002_auth_session_hardening"
    )


def test_auth_hardening_migration_rolls_back_without_reviving_otp(
    disposable_postgres_database,
):
    database_name, config = disposable_postgres_database
    run_manage(
        database_name,
        config,
        "migrate",
        "accounts",
        "0001_initial",
        "--noinput",
        "--verbosity=0",
    )
    now = timezone.now()
    with database_connection(database_name, config) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO accounts_user "
                "(password, last_login, is_superuser, phone_number, first_name, "
                "last_name, email, is_phone_verified, is_active, is_staff, "
                "date_joined) VALUES (%s, NULL, FALSE, %s, %s, %s, %s, TRUE, "
                "TRUE, FALSE, %s) RETURNING id",
                (
                    "existing-password-hash",
                    "09120000001",
                    "Rollback",
                    "User",
                    "rollback@example.com",
                    now,
                ),
            )
            user_id = cursor.fetchone()[0]
            cursor.execute(
                "INSERT INTO accounts_phoneotp "
                "(phone_number, code, purpose, is_used, expires_at, created_at, "
                "verified_at) VALUES (%s, %s, 'register', FALSE, %s, %s, NULL)",
                ("09120000001", "654321", now + timedelta(minutes=5), now),
            )

    run_manage(
        database_name,
        config,
        "migrate",
        "accounts",
        "0002_auth_session_hardening",
        "--noinput",
        "--verbosity=0",
    )
    run_manage(
        database_name,
        config,
        "migrate",
        "accounts",
        "0001_initial",
        "--noinput",
        "--verbosity=0",
    )

    with database_connection(database_name, config) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT password, is_active, is_phone_verified FROM accounts_user "
                "WHERE id = %s",
                (user_id,),
            )
            assert cursor.fetchone() == ("existing-password-hash", True, True)
            cursor.execute("SELECT code, is_used, expires_at FROM accounts_phoneotp")
            code, is_used, expires_at = cursor.fetchone()
            assert code == "000000"
            assert is_used is True
            assert expires_at < timezone.now()
