import re
import subprocess
import winreg

import psutil

from .utils import get_dict_from_indented_stream

CPU_KEY = r"Hardware\\Description\\System\\CentralProcessor\\0"

GPU_REGEX = re.compile(r"GPU (?P<index>\d+): (?P<name>.*) \(UUID: (?P<uuid>.*)\)")


def fetch_registry(key, *fields, hive=winreg.HKEY_LOCAL_MACHINE):
    """
    Fetch the registry value.
    """
    key = winreg.OpenKey(hive, key)

    for field in fields:
        value, _ = winreg.QueryValueEx(key, field)
        yield value

    return value


def get_device_information_full():
    """
    Get all information about the device.
    """

    processor_name, cpu_vendor, actual_hz, feature_set = fetch_registry(
        CPU_KEY, "ProcessorNameString", "VendorIdentifier", "~MHz", "FeatureSet"
    )

    architecture, *_ = fetch_registry(
        r"SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment",
        "PROCESSOR_ARCHITECTURE",
    )

    return {
        "ram": psutil.virtual_memory()._asdict(),
        "cpu": {
            "count": psutil.cpu_count(),
            "frequency": actual_hz,
            "percent": psutil.cpu_percent(1.0),
            "stats": psutil.cpu_stats()._asdict(),
            "per_cpu_detail": list(
                map(
                    lambda _: {**_[1]._asdict(), "index": _[0]},
                    enumerate(psutil.cpu_times(True)),
                )
            ),
            "information": {
                "architecture": architecture,
                "name": processor_name,
                "vendor": cpu_vendor,
                "feature_set": feature_set,
            },
        },
        "current_disk": psutil.disk_usage("/")._asdict(),
        "boot": (psutil.boot_time()),
    }


def iter_nvidia_gpu(executable="nvidia-smi"):

    process = subprocess.Popen(
        [executable, "-L"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    for line in process.stdout:
        match = GPU_REGEX.match(line.decode("utf-8"))

        if match:
            yield match.groupdict()

    return process.kill()


def get_full_nvidia_gpu_information(executable="nvidia-smi"):

    process = subprocess.Popen(
        [executable, "-q"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    stdout_stream = process.stdout

    while not re.match(rb"=+NVSMI LOG=+", next(stdout_stream), flags=re.IGNORECASE):
        pass

    return get_dict_from_indented_stream(stdout_stream)
