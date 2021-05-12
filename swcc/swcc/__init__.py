from importlib.metadata import PackageNotFoundError, version
import logging
from typing import Optional

from rich.logging import RichHandler

SWCC_CONFIG_PATH = __name__
SWCC_CONFIG_FILE = 'config'
FORMAT = '%(message)s'
logging.basicConfig(format=FORMAT, datefmt='[%X]', handlers=[RichHandler()])

__version__: Optional[str] = None
try:
    __version__ = version('swcc')
except PackageNotFoundError:
    # package is not installed
    pass
