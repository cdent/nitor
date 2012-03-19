
# this is required for testing
import mangler
config = {
        'server_store': ['tiddlywebplugins.devstore2', {
            'devstore_root': './src'}],
    'wrapped_devstore': ['tiddlywebplugins.mysql3', {
        'db_config': 'mysql:///nitor?charset=utf8&use_unicode=0'}],
        'log_level': 'DEBUG',
        'system_plugins': ['tiddlywebplugins.nitor'],
        'twanager_plugins': ['tiddlywebplugins.nitor'],
        }
