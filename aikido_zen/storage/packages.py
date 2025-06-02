import sys
import importlib.metadata
import importlib.util

import aikido_zen.helpers.get_current_unixtime_ms as t


class Packages:
    def __init__(self):
        self.packages = dict()

    def add_package(self, name, version):
        if name in self.packages.keys():
            # In python only 1 version of a package can be installed
            return

        self.packages[name] = {
            "name": name,
            "version": version,
            "requiredAt": t.get_unixtime_ms(),
        }

    def populate(self):
        modules = list(sys.modules.keys())
        for module in modules:
            try:
                self.add_package_from_name(module)
            except Exception:
                pass

    def add_package_from_name(self, module):
        if module == "__main__":
            return

        # Make sure to remove all trailing dots
        module = module.split(".")[0]

        if module in self.packages.keys():
            # Do not re-attempt for a successful module
            return

        origin = importlib.util.find_spec(module).origin
        if origin == "built-in":
            return  # Built-in packages cannot be reported
        if origin == "frozen":
            return  # Frozen packages means it did not come from an installed package, cannot get version.

        self.add_package(module, importlib.metadata.version(module))

    def clear(self):
        self.packages.clear()

    def as_array(self):
        return list(self.packages.values())

    def import_from_array(self, imported_packages):
        for package in imported_packages:
            if package["name"] in self.packages.keys():
                continue
            self.packages[package["name"]] = package
