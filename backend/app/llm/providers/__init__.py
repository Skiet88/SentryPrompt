"""Concrete providers. Every module in this package is imported automatically,
so a new provider only needs a new module that registers itself."""

import importlib
import pkgutil

for _module in pkgutil.iter_modules(__path__):
    importlib.import_module(f"{__name__}.{_module.name}")
