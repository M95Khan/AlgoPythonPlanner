from ._core import JsProxy
from importlib.abc import MetaPathFinder, Loader
from importlib.util import spec_from_loader
import sys


class JsFinder(MetaPathFinder):
    def __init__(self):
        self.jsproxies = {}

    def find_spec(self, fullname, path, target=None):
        [parent, _, child] = fullname.rpartition(".")
        if parent:
            parent_module = sys.modules[parent]
            if not isinstance(parent_module, JsProxy):
                # Not one of us.
                return None
            try:
                jsproxy = getattr(parent_module, child)
            except AttributeError:
                raise ModuleNotFoundError(
                    f"No module named {fullname!r}", name=fullname
                ) from None
            if not isinstance(jsproxy, JsProxy):
                raise ModuleNotFoundError(
                    f"No module named {fullname!r}", name=fullname
                )
        else:
            try:
                jsproxy = self.jsproxies[fullname]
            except KeyError:
                return None
        loader = JsLoader(jsproxy)
        return spec_from_loader(fullname, loader, origin="javascript")

    def register_js_module(self, name: str, jsproxy: JsProxy):
        """
        Registers ``jsproxy`` as a Javascript module named ``name``. The module
        can then be imported from Python using the standard Python import
        system. If another module by the same name has already been imported,
        this won't have much effect unless you also delete the imported module
        from ``sys.modules``. This is called by the javascript API
        :any:`pyodide.registerJsModule`.

        Parameters
        ----------
        name : str
            Name of js module

        jsproxy : JsProxy
            Javascript object backing the module
        """
        if not isinstance(name, str):
            raise TypeError(
                f"Argument 'name' must be a str, not {type(name).__name__!r}"
            )
        if not isinstance(jsproxy, JsProxy):
            raise TypeError(
                f"Argument 'jsproxy' must be a JsProxy, not {type(jsproxy).__name__!r}"
            )
        self.jsproxies[name] = jsproxy

    def unregister_js_module(self, name: str):
        """
        Unregisters a Javascript module with given name that has been previously
        registered with :any:`pyodide.registerJsModule` or
        :any:`pyodide.register_js_module`. If a Javascript module with that name
        does not already exist, will raise an error. If the module has already
        been imported, this won't have much effect unless you also delete the
        imported module from ``sys.modules``. This is called by the Javascript
        API :any:`pyodide.unregisterJsModule`.

        Parameters
        ----------
        name : str
            Name of js module
        """
        try:
            del self.jsproxies[name]
        except KeyError:
            raise ValueError(
                f"Cannot unregister {name!r}: no Javascript module with that name is registered"
            ) from None


class JsLoader(Loader):
    def __init__(self, jsproxy):
        self.jsproxy = jsproxy

    def create_module(self, spec):
        return self.jsproxy

    def exec_module(self, module):
        pass

    # used by importlib.util.spec_from_loader
    def is_package(self, fullname):
        return True


jsfinder = JsFinder()
