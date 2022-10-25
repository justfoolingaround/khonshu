import base64
import pathlib

import orjson
import win32crypt
from Cryptodome.Cipher import AES


def fetch_decryption_key(localstate_path: pathlib.Path) -> bytes:

    with open(localstate_path, "rb") as localstate_file:
        localstate_json = orjson.loads(localstate_file.read())

    master_key = localstate_json.get("os_crypt", {}).get("encrypted_key", None)

    if master_key is None:
        return None

    return win32crypt.CryptUnprotectData(
        base64.b64decode(master_key)[5:], None, None, None, 0
    )[1]


def buffer_decrypt(buffer, decryption_key, *, processor=None):

    if processor is not None:
        buffer = processor(buffer)

    if buffer[:3] not in (b"v10", b"v11"):
        return buffer

    return (
        AES.new(decryption_key, AES.MODE_GCM, buffer[3:15])
        .decrypt(buffer[15:])[:-16]
        .decode()
    )
