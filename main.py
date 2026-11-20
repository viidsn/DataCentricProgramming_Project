"""Check the connection to the local XAMPP database server."""

import os

import pymysql


def main() -> int:
    """Run a read-only query to confirm the connection works."""
    try:
        with pymysql.connect(
            host="127.0.0.1",
            port=3306,
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", ""),
            connect_timeout=5,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT VERSION()")
                (version,) = cursor.fetchone()
    except pymysql.MySQLError as error:
        print(f"Database connection failed: {error}")
        return 1

    print(f"Connected to the database server (version {version}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
