
import os

if os.environ.get('MODE') is not None:
    from .settings_local import *

else:
    from .settings_local import *
