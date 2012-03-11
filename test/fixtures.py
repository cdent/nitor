import os
import sys
import shutil

from tiddlyweb.config import config

from tiddlywebplugins.utils import get_store
from tiddlywebplugins.instancer.util import spawn
from tiddlywebplugins.nitor import instance as instance_module
from tiddlywebplugins.nitor.config import config as init_config


SESSION_COUNT = 1


def make_test_env(module):
    global SESSION_COUNT
    try:
        shutil.rmtree('test_instance')
    except:
        pass

    os.system('mysqladmin -f drop nitortest create nitortest')
    if SESSION_COUNT > 1:
        del sys.modules['tiddlywebplugins.mysql3']
        del sys.modules['tiddlywebplugins.sqlalchemy3']
        import tiddlywebplugins.mysql3
        import tiddlywebplugins.sqlalchemy3
        clear_hooks(HOOKS)
    SESSION_COUNT += 1
    db_config = init_config['server_store'][1]['db_config']
    db_config = db_config.replace('///nitor?', '///nitortest?')
    init_config['server_store'][1]['db_config'] = db_config
    init_config['log_level'] = 'DEBUG'

    if sys.path[0] != os.getcwd():
        sys.path.insert(0, os.getcwd())
    spawn('test_instance', init_config, instance_module)
    os.symlink('../tiddlywebplugins/templates', 'templates')

    from tiddlyweb.web import serve
    module.store = get_store(config)

    app = serve.load_app()

    def app_fn():
        return app
    module.app_fn = app_fn
