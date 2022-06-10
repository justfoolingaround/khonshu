import io
import re

from typing import Union

KV_PAIR_REGEX = re.compile(rb"(?P<key>.+?)\s+:\s+(?P<value>.*)")
UNIT_PAIR = re.compile(r"(?P<value>[0-9.]+)\s+(?P<unit>[\w%]+)")


def signature_value_processor(
    value: Union[str, bytes], *, encoding: str = "utf-8", pythonic: bool = True
):

    if isinstance(value, bytes):
        value = value.decode(encoding=encoding)

    if value.strip().isdigit():
        return int(value.strip())

    unit_match = UNIT_PAIR.match(value)

    if unit_match:
        val, unit = unit_match.groups()
        return float(val), unit

    value = value.strip()

    if value.lower() in ("none",):
        return None

    if pythonic:
        return re.sub(r"\s+", "_", value.lower())

    return value


def get_dict_from_indented_stream(
    stream: io.BufferedReader,
    *,
    key_processor=signature_value_processor,
    value_processor=lambda v: signature_value_processor(v, pythonic=False)
):

    kv_pair = {}
    indent_level = None

    for line in stream:

        if not line.strip():
            continue

        if indent_level is None:
            indent_level = max(len(line) - len(line.lstrip(b" ")), 0)

        match = KV_PAIR_REGEX.match(line)
        if match:
            key, value = match.groups()
            kv_pair[key_processor(key)] = value_processor(value)
        else:
            kv_pair[key_processor(line)] = get_dict_from_indented_stream(stream)

        if indent_level and (
            (stream.peek(indent_level)[:indent_level]) != b" " * indent_level
        ):
            return kv_pair

    return kv_pair
