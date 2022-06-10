import os
import pathlib
import sqlite3
import shutil

from .utils import buffer_decrypt, fetch_decryption_key


def iter_raw_cookies(
    *, strict_searching=False, user_local_appdata=None, user_roaming_appdata=None
):
    local_appdata = user_local_appdata or pathlib.Path(os.getenv("LOCALAPPDATA"))
    roaming_appdata = user_roaming_appdata or pathlib.Path(os.getenv("APPDATA"))

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
            for row in db.execute(
                "SELECT host_key, name, encrypted_value FROM cookies"
            ):
                host, user, value, *_ = row

                yield path, (host, user, buffer_decrypt(value, decryption_key), *_)

    for path in roaming_appdata.glob("*/Profiles/*.sqlite"):

        with sqlite3.connect(path) as db:
            for row in db.execute("SELECT * FROM moz_cookies"):
                yield path, *row


def iter_raw_login_credentials(
    *, strict_searching=False, user_local_appdata=None, user_roaming_appdata=None
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
            for (
                origin_url,
                action_url,
                username_element,
                username_value,
                password_element,
                password_value,
                submit_element,
                signon_realm,
                date_created,
                blacklisted_by_user,
                scheme,
                password_type,
                times_used,
                form_data,
                display_name,
                icon_url,
                federation_url,
                skip_zero_click,
                generation_upload_status,
                possible_username_pairs,
                _id,
                date_last_used,
                moving_blocked_for,
                date_password_modified,
            ) in db.execute("select * from logins"):
                if password_value[:3] in (b"v10", b"v11"):
                    password_value = buffer_decrypt(password_value, decryption_key)

                yield path, {
                    "origin_url": origin_url,
                    "action_url": action_url,
                    "username_element": username_element,
                    "username": username_value,
                    "password_element": password_element,
                    "password": password_value,
                    "submit_element": submit_element,
                    "signon_realm": signon_realm,
                    "date_created": date_created,
                    "blacklisted_by_user": blacklisted_by_user,
                    "scheme": scheme,
                    "password_type": password_type,
                    "times_used": times_used,
                    "form_data": form_data,
                    "display_name": display_name,
                    "icon_url": icon_url,
                    "federation_url": federation_url,
                    "skip_zero_click": skip_zero_click,
                    "generation_upload_status": generation_upload_status,
                    "possible_username_pairs": possible_username_pairs,
                    "id": _id,
                    "date_last_used": date_last_used,
                    "moving_blocked_for": moving_blocked_for,
                    "date_password_modified": date_password_modified,
                }

        try:
            tempfile.unlink(missing_ok=True)
        except PermissionError:
            pass
