"""
Climbing route database and tools.

Winging it.
"""

from __future__ import with_statement, absolute_import, division

from operator import attrgetter
from uuid import uuid4


from tiddlyweb.control import filter_tiddlers
from tiddlyweb.manage import make_command
from tiddlyweb.model.bag import Bag
from tiddlyweb.model.policy import PermissionsError
from tiddlyweb.model.tiddler import Tiddler, current_timestring
from tiddlyweb.store import StoreError
from tiddlyweb.util import merge_config
from tiddlyweb.web.http import HTTP303, HTTP400
from tiddlyweb.web.util import get_route_value, server_base_url

from tiddlywebplugins.utils import replace_handler, do_html, require_role
from tiddlywebplugins.nitor.config import config as plugin_config
from tiddlywebplugins.nitor.template import send_template


__version__ = '0.0.1'


GYMS_BAG = 'gyms'
CLIMBTYPES = 'climbtypes'
RESERVED_BAGS = [GYMS_BAG, 'common', CLIMBTYPES]
ROUTE_FIELDS = ['lineNumber', 'colorName', 'grade', 'routeSetter']
LEAD_FIELD = 'isLeadRoute'


@do_html()
def home(environ, start_response):
    kept_bags, fullnames = get_gyms(environ, 'read')
    return send_template(environ, 'home.html', { 'gyms': kept_bags,
        'fullnames': fullnames, 'title': 'Welcome to Nitor'})


#@require_role('ADMIN)
@do_html()
def admin(environ, start_response):
    store = environ['tiddlyweb.store']
    gyms = (store.get(tiddler) for
            tiddler in filter_tiddlers(
                store.list_bag_tiddlers(Bag(GYMS_BAG)),
                'sort=title', environ))

    return send_template(environ, 'admin.html', { 'gyms': gyms,
        'title': 'Admin Page'})

#@require_role('ADMIN)
@do_html()
def gym_editor(environ, start_response):
    store = environ['tiddlyweb.store']
    gym = get_route_value(environ, 'gym')
    try:
        tiddler = Tiddler(gym, GYMS_BAG)
        tiddler = store.get(tiddler)
    except StoreError:
        pass  # new gym

    return send_template(environ, 'gym_editor.html', {'tiddler': tiddler,
        'title': 'Edit Gym %s' % gym})

#@require_role('ADMIN')
def gym_edit(environ, start_response):
    store = environ['tiddlyweb.store']
    gym = get_route_value(environ, 'gym')
    if gym in RESERVED_BAGS:
        raise HTTP400('Unable to create gym: name %s is reserved' % gym)
    tiddler = Tiddler(gym, GYMS_BAG)

    try:
        store.get(tiddler)
    except StoreError:  # is new
        create_gym_bag(environ, gym)

    _update_gym_info(environ, tiddler)

    raise HTTP303(server_base_url(environ) + '/admin')


def _update_gym_info(environ, tiddler):
    store = environ['tiddlyweb.store']
    query = environ['tiddlyweb.query']
    for key in ['fullname', 'tagline', 'geo.lat', 'geo.long']:
        value = query.get(key, [''])[0]
        tiddler.fields[key] = value
    tiddler.modifier = environ['tiddlyweb.usersign']['name']
    tiddler.modified = current_timestring()
    try:
        store.put(tiddler)
    except StoreError, exc:
        raise HTTP400('Unable to save gym: %s' % exc)

def get_gyms(environ, constraint):
    """
    Get the list of bags and fullnames that match
    the contraint for the provided usersign.
    """
    store = environ['tiddlyweb.store']
    usersign = environ['tiddlyweb.usersign']
    bags = (store.get(bag) for bag in store.list_bags())
    kept_bags = []
    fullnames = {}
    for bag in sorted(bags, key=attrgetter('name')):
        if bag.name in RESERVED_BAGS:
            continue
        try:
            bag.policy.allows(usersign, constraint)
            if not bag.name.endswith('_archive'):
                kept_bags.append(bag)
            try:
                tiddler = store.get(Tiddler(bag.name, GYMS_BAG))
                fullnames[bag.name] = tiddler.fields['fullname']
            except StoreError:
                pass
        except PermissionsError:
            pass
    return kept_bags, fullnames

#@require_role('MANAGER')
@do_html()
def manager(environ, start_response):
    kept_bags, fullnames = get_gyms(environ, 'manage')
    return send_template(environ, 'manage_list.html', {'gyms': kept_bags,
        'title': 'Your Gyms', 'fullnames': fullnames})


#@require_role('MANAGER')
@do_html()
def manage_gym(environ, start_response):
    store = environ['tiddlyweb.store']
    gym = get_route_value(environ, 'gym')
    gym_bag = store.get(Bag(gym))
    # Bail out if we are not allowed to manage. 
    gym_bag.policy.allows(environ['tiddlyweb.usersign'], 'manage')
    gym_tiddler = store.get(Tiddler(gym, GYMS_BAG))

    routes = _get_gym_routes(environ, gym)

    return send_template(environ, 'manage_gym.html', {
        'title': 'Manage %s' % gym,
        'gym_tiddler': gym_tiddler,
        'routes': routes})

def _get_gym_routes(environ, gym_name):
    store = environ['tiddlyweb.store']
    gym_bag = Bag(gym_name)

    def _get_and_mangle_tiddler(tiddler):
        store.get(tiddler)
        try:
            tiddler.fields['lineNumber'] = int(tiddler.fields['lineNumber'])
        except ValueError:
            pass  # don't worry
        return tiddler

    return [_get_and_mangle_tiddler(tiddler) for tiddler in filter_tiddlers(
        store.list_bag_tiddlers(gym_bag),
        'select=tag:route', environ)]


#@require_role('MANAGER')
@do_html()
def manage_edit(environ, start_response):
    store = environ['tiddlyweb.store']
    gym = get_route_value(environ, 'gym')
    gym_bag = store.get(Bag(gym))
    # Bail out if we are not allowed to manage. 
    gym_bag.policy.allows(environ['tiddlyweb.usersign'], 'manage')

    query = environ['tiddlyweb.query']

    if query.get('submit', [''])[0] == 'Update Routes':
        return _manage_update_routes(environ, gym)
    else:
        return _manage_update_gym(environ, gym)

def _manage_update_routes(environ, gym):
    store = environ['tiddlyweb.store']
    query = environ['tiddlyweb.query']
    existing_titles = query.get('title', [])
    count = len(existing_titles)
    index = 0
    delete = query.get('delete', [])
    lead_route = query.get(LEAD_FIELD, [])
    while index < count:
        title = existing_titles[index]
        tiddler = Tiddler(title, gym)
        try:
            tiddler = store.get(tiddler)
            if title in delete:
                original_bag = tiddler.bag
                tiddler.bag = '%s_archive' % gym
                store.put(tiddler)
                tiddler.bag = original_bag
                store.delete(tiddler)
                index += 1
                continue
        except StoreError:
            pass
        changed = False
        for key in ROUTE_FIELDS:
            value = query.get(key, [''])[index]
            if tiddler.fields[key] != value:
                tiddler.fields[key] = value
                changed = True
        if LEAD_FIELD in tiddler.fields and title not in lead_route:
            del tiddler.fields[LEAD_FIELD]
            changed = True
        elif title in lead_route and LEAD_FIELD not in tiddler.fields:
            tiddler.fields[LEAD_FIELD] = '1'
            changed = True
        if changed:
            store.put(tiddler)
        index += 1
    
    try:
        title = query.get('title', [])[index]
    except IndexError:
        title = str(uuid4())
    tiddler = Tiddler(title, gym)
    new_route = False
    if 'new_one' in lead_route:
        tiddler.fields[LEAD_FIELD] = '1'
    for key in ROUTE_FIELDS:
        value = query.get(key, [''])[index]
        if value == '':
            continue
        new_route = True
        tiddler.fields[key] = value
    tiddler.tags = ['route']
    if new_route:
        store.put(tiddler)
    raise HTTP303(server_base_url(environ) + '/manager/%s' % gym)

def _manage_update_gym(environ, gym):
    tiddler = Tiddler(gym, GYMS_BAG)
    _update_gym_info(environ, tiddler)

    raise HTTP303(server_base_url(environ) + '/manager/%s' % gym)

@do_html()
def gym_info(environ, start_response):
    """
    Display the info about a single gym for the public.
    """
    store = environ['tiddlyweb.store']
    gym = get_route_value(environ, 'gym')
    try:
        gym_tiddler = store.get(Tiddler(gym, GYMS_BAG))
    except StoreError, exc:
        raise HTTP404('that gym does not exist: %s' % exc)
    return send_template(environ, 'gym.html', { 'gym': gym_tiddler,
        'title': gym})


@do_html()
def gym_routes(environ, start_response):
    """
    Display the routes from a single gym.
    """
    gym = get_route_value(environ, 'gym')
    routes = _get_gym_routes(environ, gym)
    return send_template(environ, 'gym_routes.html', {
        'title': 'Routes @%s' % gym,
        'routes': routes})


def establish_handlers(config):
    selector = config['selector']
    replace_handler(selector, '/', dict(GET=home))
    selector.add('/admin', GET=admin)
    selector.add('/admin/{gym:segment}', GET=gym_editor, POST=gym_edit)
    selector.add('/manager', GET=manager)
    selector.add('/manager/{gym:segment}', GET=manage_gym, POST=manage_edit)
    selector.add('/gyms/{gym:segment}', GET=gym_info)
    selector.add('/gyms/{gym:segment}/routes', GET=gym_routes)


def create_gym_bag(environ, bag_name):
    store = environ['tiddlyweb.store']
    bag = Bag(bag_name)
    archive_bag = Bag('%s_archive' % bag_name)
    # TODO Set policy appropriately
    #bag.policy.manage ....
    store.put(bag)
    store.put(archive_bag)


def init(config):
    import tiddlywebplugins.instancer

    merge_config(config, plugin_config)
    if 'selector' in config:
        establish_handlers(config)

    # XXX Dupe from tiddlywebwiki, should probably be in instancer...
    @make_command()
    def update(args):
        """Update all instance_tiddlers in the current instance."""
        from tiddlywebplugins.instancer import Instance
        instance = Instance('.', config)
        instance.update_store()
