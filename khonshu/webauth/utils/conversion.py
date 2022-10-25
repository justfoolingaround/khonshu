from datetime import datetime

CHROMIUM_EPOCH = 11644473600000

def webkit_timestamp_to_utc(webkit_timestamp, *, chrome_epoch=CHROMIUM_EPOCH):
    unix_time = (webkit_timestamp / 1000 - chrome_epoch) / 1000

    try:
        return datetime.utcfromtimestamp(unix_time)
    except OSError:
        return datetime.utcfromtimestamp(0)


def datetime_to_webkit_timestamp(utc: datetime, *, chrome_epoch=CHROMIUM_EPOCH):

    webkit_time = (
        (utc - datetime(1970, 1, 1)).total_seconds() * 1000 + chrome_epoch
    ) * 1000

    return int(webkit_time)
