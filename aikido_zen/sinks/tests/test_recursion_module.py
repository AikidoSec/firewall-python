import importlib
import sys
import types

import aikido_zen
class HashableNamespace(types.SimpleNamespace):
    def __hash__(self):
        return hash(tuple(vars(self)))
zipfile = HashableNamespace(**vars(importlib.import_module('zipfile')))
zipfile._path = aikido_zen
sys.modules[__name__ + '.zipfile'] = zipfile  # type: ignore[assignment]
