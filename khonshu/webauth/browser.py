import os
import pathlib
import shutil
import sqlite3

from .utils import buffer_decrypt, fetch_decryption_key


def iter_sql_rows(sql_connection, *, table_name, where=None):

    columns = list(
        name
        for _, name, *_ in sql_connection.execute(f"PRAGMA table_info({table_name!r})")
    )

    for rows in sql_connection.execute(
        f"select * from {table_name!r} where {where or 1}"
    ):
        yield dict(zip(columns, rows))


def iter_raw_cookies_chromium(
    *,
    strict_searching=False,
    user_local_appdata=None,
    sql_where=None,
):
    local_appdata = user_local_appdata or pathlib.Path(os.getenv("LOCALAPPDATA"))

    for path in local_appdata.glob("*/User Data/*/Network/cookies"):
        storage_owner = path.parent.parent.parent
        localstate = storage_owner / "Local State"

        if not localstate.exists():
            if strict_searching:
                raise RuntimeError(
                    f"Found an encrypted cookie file at {path.as_posix()!r} but no localstate file at {localstate.as_posix()!r}"
                )
            continue

        decryption_key = fetch_decryption_key(localstate)

        with sqlite3.connect(path) as db:
            for row in iter_sql_rows(db, table_name="cookies", where=sql_where):

                encrypted_value = row.pop("encrypted_value", None)

                if encrypted_value is not None:
                    row.update(value=buffer_decrypt(encrypted_value, decryption_key))

                yield {
                    "database_path": path,
                    "data": row,
                    "from": {"browser": storage_owner.parent.name},
                }


def iter_raw_cookies_firefox(
    *,
    user_roaming_appdata=None,
    sql_where=None,
):
    roaming_appdata = user_roaming_appdata or pathlib.Path(os.getenv("APPDATA"))

    for path in roaming_appdata.glob(
        "Mozilla/Firefox/Profiles/*.default*/cookies.sqlite"
    ):
        with sqlite3.connect(path) as db:
            for row in iter_sql_rows(db, table_name="moz_cookies", where=sql_where):
                yield {
                    "database_path": path,
                    "data": row,
                    "from": {
                        "browser": "Mozilla Firefox",
                        "profile": path.parent.name,
                    },
                }


def iter_raw_login_credentials_chromium(
    *,
    strict_searching=False,
    user_local_appdata=None,
    sql_where=None,
):
    local_appdata = user_local_appdata or pathlib.Path(os.getenv("LOCALAPPDATA"))

    for path in local_appdata.glob("*/User Data/*/Login Data"):
        storage_owner = path.parent.parent
        localstate = storage_owner / "Local State"

        if not localstate.exists():
            if strict_searching:
                raise RuntimeError(
                    f"Found an encrypted login data file at {path.as_posix()!r} but no localstate file at {localstate.as_posix()!r}"
                )
            continue

        decryption_key = fetch_decryption_key(localstate)

        tempfile = pathlib.Path(os.getenv("TEMP")) / "login_data.db"
        shutil.copy(path, tempfile)

        with sqlite3.connect(tempfile) as db:
            for row in iter_sql_rows(db, table_name="logins", where=sql_where):
                password_value = row.pop("password_value", None)

                if password_value is not None:
                    row.update(
                        password_value=buffer_decrypt(password_value, decryption_key)
                    )

                yield {
                    "database_path": path,
                    "data": row,
                    "from": {"browser": storage_owner.parent.name},
                }

        try:
            tempfile.unlink(missing_ok=True)
        except PermissionError:
            pass


def iter_browser_history_chromium(*, user_local_appdata=None, sql_where=None):
    local_appdata = user_local_appdata or pathlib.Path(os.getenv("LOCALAPPDATA"))

    for path in local_appdata.glob("*/User Data/*/History"):

        storage_owner = path.parent.parent

        tempfile = pathlib.Path(os.getenv("TEMP")) / "login_data.db"
        shutil.copy(path, tempfile)

        with sqlite3.connect(tempfile) as db:
            for row in iter_sql_rows(db, table_name="urls", where=sql_where):
                yield {
                    "database_path": path,
                    "data": row,
                    "from": {"browser": storage_owner.parent.name},
                }

    try:
        tempfile.unlink(missing_ok=True)
    except PermissionError:
        pass


def iter_browser_history_firefox(*, user_roaming_appdata=None, sql_where=None):
    roaming_appdata = user_roaming_appdata or pathlib.Path(os.getenv("APPDATA"))

    for path in roaming_appdata.glob(
        "Mozilla/Firefox/Profiles/*.default*/places.sqlite"
    ):
        with sqlite3.connect(path) as db:
            for row in iter_sql_rows(db, table_name="moz_places", where=sql_where):
                yield {
                    "database_path": path,
                    "data": row,
                    "from": {
                        "browser": "Mozilla Firefox",
                        "profile": path.parent.name,
                    },
                }


def insert_to_chromium_history(
    url,
    title,
    last_visit_time,
    *,
    visit_count=1,
    hidden=0,
    typed_count=0,
    user_local_appdata=None,
):
    local_appdata = user_local_appdata or pathlib.Path(os.getenv("LOCALAPPDATA"))

    for path in local_appdata.glob("*/User Data/*/History"):

        tempfile = pathlib.Path(os.getenv("TEMP")) / "login_data.db"
        shutil.copy(path, tempfile)

        with sqlite3.connect(tempfile) as db:
            db.execute(
                "insert into urls (url, title, last_visit_time, visit_count, hidden, typed_count) values (?, ?, ?, ?, ?, ?)",
                (url, title, last_visit_time, visit_count, hidden, typed_count),
            )
            db.commit()
        db.close()

        path.unlink()
        shutil.move(tempfile, path)
