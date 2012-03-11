"""
Base configuration for nitor.

This provides the basics which may be changed in tidlywebconfig.py.
"""

from tiddlywebplugins.instancer.util import get_tiddler_locations

from tiddlywebplugins.nitor.instance import store_contents

try:
    from pkg_resources import resource_filename
except ImportError:
    from tiddlywebplugins.utils import resource_filename


PACKAGE_NAME = 'tiddlywebplugins.nitor'

config = {
    'instance_tiddlers': get_tiddler_locations(store_contents, PACKAGE_NAME),
    'beanstalk.listeners': ['tiddlywebplugins.dispatcher.listener'],
    'bag_create_policy': 'ANY',
    'recipe_create_policy': 'ANY',
    'css_uri': '/bags/common/tiddlers/base.css',
    'socialusers.reserved_names': ['www', 'about', 'help', 'announcements',
        'dev', 'info', 'api', 'status', 'login'],
    'cookie_age': '2592000',  # 1 month
    'server_store': ['tiddlywebplugins.mysql3', {
        'db_config': 'mysql:///nitor?charset=utf8&use_unicode=0'}],
    'indexer': 'tiddlywebplugins.mysql3'}
