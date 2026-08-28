"""patch_db.py - Update database.py to support MySQL alongside SQLite"""
import re

with open("app/database.py", encoding="utf-8") as f:
    content = f.read()

old_block = (
    "engine = create_engine(\n"
    '    settings.DATABASE_URL,\n'
    '    connect_args={"check_same_thread": False},\n'
    "    echo=False,\n"
    ")"
)

new_block = (
    "# Detect database type (SQLite for local dev, MySQL for Docker)\n"
    '_is_sqlite = settings.DATABASE_URL.startswith("sqlite")\n'
    '_connect_args = {"check_same_thread": False} if _is_sqlite else {}\n'
    "_pool_kwargs = {} if _is_sqlite else {\n"
    '    "pool_size": 10,\n'
    '    "max_overflow": 20,\n'
    '    "pool_recycle": 3600,\n'
    '    "pool_pre_ping": True,\n'
    "}\n\n"
    "engine = create_engine(\n"
    "    settings.DATABASE_URL,\n"
    "    connect_args=_connect_args,\n"
    "    echo=False,\n"
    "    **_pool_kwargs,\n"
    ")"
)

if old_block in content:
    content = content.replace(old_block, new_block)
    with open("app/database.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("SUCCESS: database.py patched for MySQL/SQLite dual support")
else:
    print("ERROR: old pattern not found. Check manually.")
