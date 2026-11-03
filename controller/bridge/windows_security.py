"""Current-user-only Windows directories for local IPC and runtime material.

Use a protected DACL, not chmod (which only toggles read-only on Windows).
Reparse points and directories with unexpected owners/ACEs fail closed.
"""
import ctypes
from ctypes import wintypes
from pathlib import Path
import stat


def _api():
    adv = ctypes.WinDLL('advapi32', use_last_error=True)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    adv.OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)]
    adv.GetTokenInformation.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    adv.ConvertSidToStringSidW.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.LPWSTR)]
    adv.ConvertStringSecurityDescriptorToSecurityDescriptorW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p]
    adv.SetFileSecurityW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.c_void_p]
    adv.GetFileSecurityW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    adv.ConvertSecurityDescriptorToStringSecurityDescriptorW.argtypes = [ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(wintypes.LPWSTR), ctypes.c_void_p]
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    return adv, kernel


def _check(result):
    if not result:
        raise ctypes.WinError(ctypes.get_last_error())


def current_sid():
    adv, kernel = _api()
    token = wintypes.HANDLE()
    _check(adv.OpenProcessToken(kernel.GetCurrentProcess(), 8, ctypes.byref(token)))
    try:
        size = wintypes.DWORD()
        adv.GetTokenInformation(token, 1, None, 0, ctypes.byref(size))
        data = ctypes.create_string_buffer(size.value)
        _check(adv.GetTokenInformation(token, 1, data, size, ctypes.byref(size)))
        sid = ctypes.cast(data, ctypes.POINTER(ctypes.c_void_p))[0]
        value = wintypes.LPWSTR()
        _check(adv.ConvertSidToStringSidW(sid, ctypes.byref(value)))
        try:
            return value.value
        finally:
            kernel.LocalFree(value)
    finally:
        kernel.CloseHandle(token)


def _no_reparse(path, directory=True):
    info = Path(path).lstat()
    if (bool(stat.S_ISDIR(info.st_mode)) != directory or
            info.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT):
        raise PermissionError('Unsafe Windows private path: wrong type or reparse point')


def secure_directory(path, create=False, restrict_existing=False):
    path = Path(path)
    sid = current_sid()
    adv, kernel = _api()
    if create:
        try:
            path.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            pass  # Existing directories must already satisfy the policy.
        else:
            _no_reparse(path)
            descriptor = ctypes.c_void_p()
            _check(adv.ConvertStringSecurityDescriptorToSecurityDescriptorW(
                'D:P(A;OICI;FA;;;' + sid + ')', 1, ctypes.byref(descriptor), None))
            try:
                _check(adv.SetFileSecurityW(str(path), 0x80000004, descriptor))
            finally:
                kernel.LocalFree(descriptor)
    _no_reparse(path)
    size = wintypes.DWORD()
    adv.GetFileSecurityW(str(path), 5, None, 0, ctypes.byref(size))
    data = ctypes.create_string_buffer(size.value)
    _check(adv.GetFileSecurityW(str(path), 5, data, size, ctypes.byref(size)))
    value = wintypes.LPWSTR()
    _check(adv.ConvertSecurityDescriptorToStringSecurityDescriptorW(data, 1, 5, ctypes.byref(value), None))
    try:
        # Only our explicit, protected full-control ACE is supported. Unknown
        # ACL shapes are rejected rather than interpreted permissively.
        expected = 'O:' + sid + 'D:P(A;OICI;FA;;;' + sid + ')'
        if value.value != expected:
            if restrict_existing and value.value.startswith('O:' + sid + 'D:'):
                descriptor = ctypes.c_void_p()
                _check(adv.ConvertStringSecurityDescriptorToSecurityDescriptorW(
                    'D:P(A;OICI;FA;;;' + sid + ')', 1, ctypes.byref(descriptor), None))
                try:_check(adv.SetFileSecurityW(str(path), 0x80000004, descriptor))
                finally:kernel.LocalFree(descriptor)
                return secure_directory(path)
            raise PermissionError('Unsafe Windows private directory owner/DACL; expected current-user-only access')
    finally:
        kernel.LocalFree(value)
    return path


def _security_text(path):
    adv, kernel = _api()
    size = wintypes.DWORD()
    adv.GetFileSecurityW(str(path), 5, None, 0, ctypes.byref(size))
    data = ctypes.create_string_buffer(size.value)
    _check(adv.GetFileSecurityW(str(path), 5, data, size, ctypes.byref(size)))
    value = wintypes.LPWSTR()
    _check(adv.ConvertSecurityDescriptorToStringSecurityDescriptorW(data, 1, 5, ctypes.byref(value), None))
    try:return value.value
    finally:kernel.LocalFree(value)


def protect_file(path):
    path = Path(path)
    _no_reparse(path, directory=False)
    sid = current_sid()
    if not _security_text(path).startswith('O:' + sid + 'D:'):
        raise PermissionError('Refusing to change a private file owned by another user')
    adv, kernel = _api()
    descriptor = ctypes.c_void_p()
    _check(adv.ConvertStringSecurityDescriptorToSecurityDescriptorW(
        'D:P(A;;FA;;;' + sid + ')', 1, ctypes.byref(descriptor), None))
    try:_check(adv.SetFileSecurityW(str(path), 0x80000004, descriptor))
    finally:kernel.LocalFree(descriptor)
    return private_file(path)


def private_file(path):
    _no_reparse(path, directory=False)
    sid = current_sid()
    acl = _security_text(path)
    if acl not in ('O:' + sid + 'D:P(A;;FA;;;' + sid + ')',
                   'O:' + sid + 'D:(A;;FA;;;' + sid + ')',
                   'O:' + sid + 'D:AI(A;ID;FA;;;' + sid + ')'):
        raise PermissionError('Unsafe Windows private file owner/DACL')
    return Path(path)
