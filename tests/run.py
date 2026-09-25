"""Run the GuitarRig tests inside Blender, from the add-on folder:

    blender -b --factory-startup --python-exit-code 1 --python tests/run.py [-- [-v] [-k PATTERN]...]

The add-on is imported from this checkout (not installed) and registered for the run.
"""

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ADDON_DIR = os.path.dirname(HERE)


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    patterns = [f"*{args[i + 1]}*" for i, arg in enumerate(args[:-1]) if arg == "-k"]

    for path in (os.path.dirname(ADDON_DIR), HERE):
        if path not in sys.path:
            sys.path.insert(0, path)
    import guitar_rig

    guitar_rig.register()
    try:
        loader = unittest.TestLoader()
        if patterns:
            loader.testNamePatterns = patterns
        suite = loader.discover(HERE, pattern="test_*.py", top_level_dir=HERE)
        result = unittest.TextTestRunner(verbosity=2 if "-v" in args else 1).run(suite)
    finally:
        guitar_rig.unregister()
    sys.exit(0 if result.wasSuccessful() else 1)


main()
