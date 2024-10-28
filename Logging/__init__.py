import sys

# must have custom repo at https://github.com/tkeith1106/Custom-Logging.git pulled. then put the path to that repo below
logging_class_path = r"/Volumes/Data/Documents/Python/Custom-Logging"

sys.path.insert(0, logging_class_path)

from Logger import logger

__all__ = ["logger"]

del sys