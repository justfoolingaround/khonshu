import ctypes
import shlex
import sys
from ctypes import POINTER, c_char_p, c_int, c_ulong, c_void_p, windll
from ctypes.wintypes import BOOL, DWORD, HANDLE, HINSTANCE, HKEY, HWND

SEE_MASK_NOCLOSEPROCESS = 0x00000040
SEE_MASK_NO_CONSOLE = 0x00008000


class ShellExecuteInfo(ctypes.Structure):
    _fields_ = [
        ("cbSize", DWORD),
        ("fMask", c_ulong),
        ("hwnd", HWND),
        ("lpVerb", c_char_p),
        ("lpFile", c_char_p),
        ("lpParameters", c_char_p),
        ("lpDirectory", c_char_p),
        ("nShow", c_int),
        ("hInstApp", HINSTANCE),
        ("lpIDList", c_void_p),
        ("lpClass", c_char_p),
        ("hKeyClass", HKEY),
        ("dwHotKey", DWORD),
        ("hIcon", HANDLE),
        ("hProcess", HANDLE),
    ]

    def __init__(self, **kw):
        super(ShellExecuteInfo, self).__init__()
        self.cbSize = ctypes.sizeof(self)
        for field_name, field_value in kw.items():
            setattr(self, field_name, field_value)


PShellExecuteInfo = POINTER(ShellExecuteInfo)

ShellExecuteEx = windll.shell32.ShellExecuteExA
ShellExecuteEx.argtypes = (PShellExecuteInfo,)
ShellExecuteEx.restype = BOOL

WaitForSingleObject = windll.kernel32.WaitForSingleObject
WaitForSingleObject.argtypes = (HANDLE, DWORD)
WaitForSingleObject.restype = DWORD

CloseHandle = windll.kernel32.CloseHandle
CloseHandle.argtypes = (HANDLE,)
CloseHandle.restype = BOOL


def is_elevated():
    return bool(windll.shell32.IsUserAnAdmin())


def elevate(show_console=False):
    if is_elevated():
        return

    params = ShellExecuteInfo(
        fMask=SEE_MASK_NOCLOSEPROCESS | SEE_MASK_NO_CONSOLE,
        hwnd=None,
        lpVerb=b"runas",
        lpFile=sys.executable.encode("cp1252"),
        lpParameters=shlex.join(sys.argv).encode("cp1252"),
        nShow=int(show_console),
    )

    if not ShellExecuteEx(ctypes.byref(params)):
        raise ctypes.WinError()

    handle = params.hProcess
    ret = DWORD()
    WaitForSingleObject(handle, -1)

    if windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(ret)) == 0:
        raise ctypes.WinError()

    CloseHandle(handle)
    sys.exit(ret.value)
