import ctypes
import weakref
from functools import lru_cache

from aikido_zen.helpers.get_lib_path import get_binary_path


class IpMatcherByteSlice(ctypes.Structure):
    _fields_ = [("ptr", ctypes.c_char_p), ("len", ctypes.c_size_t)]


@lru_cache(maxsize=1)
def _load_library():
    library = ctypes.CDLL(get_binary_path())
    library.ip_matcher_create.argtypes = [
        ctypes.POINTER(IpMatcherByteSlice),
        ctypes.c_size_t,
    ]
    library.ip_matcher_create.restype = ctypes.c_void_p
    library.ip_matcher_has.argtypes = [
        ctypes.c_void_p,
        ctypes.c_char_p,
        ctypes.c_size_t,
    ]
    library.ip_matcher_has.restype = ctypes.c_int
    library.ip_matcher_free.argtypes = [ctypes.c_void_p]
    library.ip_matcher_free.restype = None
    return library


def _release_handle(library, handle):
    try:
        library.ip_matcher_free(handle)
    except Exception:
        pass


class NativeIPMatcher:
    def __init__(self, networks):
        library = _load_library()
        encoded_networks = []
        for network in networks:
            try:
                encoded_networks.append(network.encode("utf-8"))
            except UnicodeError:
                continue

        descriptors = (IpMatcherByteSlice * len(encoded_networks))(
            *(IpMatcherByteSlice(network, len(network)) for network in encoded_networks)
        )

        handle = library.ip_matcher_create(
            descriptors if descriptors else None, len(encoded_networks)
        )
        if not handle:
            raise RuntimeError("Native IP matcher creation failed")

        self._library = library
        self._handle = handle
        self._finalizer = weakref.finalize(
            self, _release_handle, self._library, self._handle
        )

    def has(self, network):
        encoded_network = network.encode("utf-8")
        return (
            self._library.ip_matcher_has(
                self._handle, encoded_network, len(encoded_network)
            )
            == 1
        )


def create_ip_matcher(networks):
    try:
        return NativeIPMatcher(networks)
    except Exception:
        return None
