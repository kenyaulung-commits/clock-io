import sqlite3
import sys


def print_table(cursor, table_name):
  print(f"\n--- Table: {table_name} ---")

  cursor.execute(f"PRAGMA table_info('{table_name}')")
  columns = [info[1] for info in cursor.fetchall()]

  cursor.execute(f"SELECT * FROM '{table_name}'")
  rows = cursor.fetchall()

  if not rows:
    print("(Table is empty)")
    return

  col_widths = [len(col) for col in columns]
  for row in rows:
    for i, val in enumerate(row):
      col_widths[i] = max(col_widths[i], len(str(val)))

  header = " | ".join(
      f"{col.ljust(col_widths[i])}" for i, col in enumerate(columns)
  )
  separator = "-+-".join("-" * width for width in col_widths)

  print(header)
  print(separator)

  for row in rows:
    row_str = " | ".join(
        f"{str(val).ljust(col_widths[i])}" for i, val in enumerate(row)
    )
    print(row_str)
  print(f"Total rows: {len(rows)}")


def inspect_sqlite_db(db_path):
  try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE"
        " 'sqlite_%';"
    )
    tables = cursor.fetchall()

    if not tables:
      print(f"No tables found in database: {db_path}")
      return

    print(f"Database: {db_path}")
    print(f"Found {len(tables)} table(s).")

    for (table_name,) in tables:
      print_table(cursor, table_name)

    conn.close()
  except Exception as e:
    print(f"Error reading database: {e}")


if __name__ == "__main__":
  db = sys.argv[1] if len(sys.argv) > 1 else "hr_attendance.db"
  inspect_sqlite_db(db)