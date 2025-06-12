# Backwards compatibility imports
# These allow existing code to continue importing from utils.* while we migrate

# Core utilities
# Re-export modules for compatibility
from . import core, database, domain
from .core.datetime import *
from .core.debug import *
from .core.localization import *
from .core.logger import *
from .core.singleton import *

# Database utilities
from .database.db_utils import *

# Domain utilities
from .domain.constants import *
