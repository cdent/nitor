"""
develpment instance configuration
"""

import mangler


def update_config(config, set_host=True):
    config['log_level'] = 'DEBUG'
    if set_host:
        config['server_host'] = {
            'scheme': 'http',
            'host': 'nitor.org',
            'port': '8080'
        }

    config['server_store'] = ['tiddlywebplugins.devstore2', {
        'devstore_root': './src'}]
    config['wrapped_devstore'] = ['tiddlywebplugins.mysql3', {
        'db_config': 'mysql:///nitor?charset=utf8&use_unicode=0'}]
