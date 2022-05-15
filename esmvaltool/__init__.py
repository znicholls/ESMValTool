"""ESMValTool diagnostics package."""
import logging
__version__ = '2.5.0'

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class ESMValToolDeprecationWarning(UserWarning):
    """Custom deprecation warning."""
