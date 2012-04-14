"""
structure and contents of a default nitor instance
"""

from tiddlywebplugins.instancer.util import get_tiddler_locations

ADMIN_POLICY = {
    'read': [],
    'write': ['R:ADMIN'],
    'create': ['R:ADMIN'],
    'delete': ['R:ADMIN'],
    'manage': ['R:ADMIN'],
    'accept': ['R:ADMIN'],
    'owner': 'administrator'}

NONE_POLICY = {
    'read': ['NONE'],
    'write': ['NONE'],
    'create': ['ANY'],
    'delete': ['NONE'],
    'manage': ['NONE'],
    'accept': ['NONE'],
    'owner': 'administrator'}


instance_config = {
        'system_plugins': ['tiddlywebplugins.nitor'],
        'twanager_plugins': ['tiddlywebplugins.nitor']}

store_contents = {
        'testgym_climbs': ['src/testdata.recipe'],
        'common': ['src/common.recipe'],
        'gyms': ['src/gyms.recipe'],
        'climbtypes': ['src/climbtypes.recipe']}

store_structure = {
        'bags': {
            'common': {
                'desc': 'Common tiddlers for various functions',
                'policy': ADMIN_POLICY},
            'gyms': {
                'desc': 'List of gyms',
                'policy': ADMIN_POLICY},
            'climbtypes': {
                'desc': 'List of types of climbs',
                'policy': ADMIN_POLICY},
            'MAPUSER': {
                'desc': 'maps extracted user credentials',
                'policy': NONE_POLICY},
            'MAGICUSER': {
                'desc': 'store user details',
                'policy': NONE_POLICY},
            'testgym_climbs': {
                'desc': 'debugging test gym'},
            'testgym_archive': {
                'desc': 'debugging test gym archvie'},
            'testgym_news': {
                'desc': 'debugging test gym news'},
            'GUEST': { # XXX remove after prototyping
                'desc': 'test bag for guest user'},
            }
        }
