"""
Climbing route database and tools.

Winging it.
"""

from tiddlyweb.util import merge_config
from tiddlywebplugins.utils import replace_handler, do_html
from tiddlywebplugins.nitor.config import config as plugin_config
from tiddlywebplugins.nitor.template import send_template


__version__ = '0.0.1'


@do_html()
def home(environ, start_response):
    return send_template(environ, 'home.html', { 'title': 'Welcome'})


def establish_handlers(config):
    selector = config['selector']
    replace_handler(selector, '/', dict(GET=home))


def init(config):
    merge_config(config, plugin_config)
    if 'selector' in config:
        establish_handlers(config)

