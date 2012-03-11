"""
Climbing route database and tools.

Winging it.
"""

from tiddlyweb.util import merge_config
from tiddlywebplugins.nitor.config import config as plugin_config


__version__ = '0.0.1'


def init(config):
    merge_config(config, plugin_config)

