"""
Test get_sidebar, which provides tiddlers that
match some criteria. Figuring out those criteria
is the job of this test.
"""

from fixtures import make_test_env

from tiddlyweb.model.tiddler import Tiddler
from tiddlyweb.model.bag import Bag

from uuid import uuid4

from tiddlywebplugins.nitor import get_sidebar

def setup_module(module):
    make_test_env(module)
    module.environ = module.store.environ
    module.environ['tiddlyweb.store'] = module.store
    module.environ['tiddlyweb.usersign'] = {'name': 'GUEST', 'roles': []}

def teardown_module(module):
    import os
    os.chdir('..')

def test_sidebar_global():
    store.put(Bag('cdent'))
    tiddler = Tiddler('%s' % uuid4(), 'cdent')
    tiddler.tags = ['climb']
    tiddler.text = 'sweet'
    store.put(tiddler)

    tiddlers = list(get_sidebar(environ))

    assert len(tiddlers) == 5
