"""
Climbing route database and tools.

Winging it.
"""

from __future__ import with_statement, absolute_import, division

from operator import attrgetter
from uuid import uuid4

from itertools import ifilter
from httpexceptor import HTTP303, HTTP400


from tiddlyweb.control import filter_tiddlers, readable_tiddlers_by_bag
from tiddlyweb.manage import make_command
from tiddlyweb.model.bag import Bag
from tiddlyweb.model.policy import PermissionsError
from tiddlyweb.model.tiddler import Tiddler, current_timestring
from tiddlyweb.store import StoreError
from tiddlyweb.util import merge_config
from tiddlyweb.web.util import get_route_value, server_base_url, encode_name
from tiddlyweb.wikitext import render_wikitext

from tiddlywebplugins.utils import (replace_handler, do_html, require_role,
        require_any_user)
from tiddlywebplugins.nitor.config import config as plugin_config
from tiddlywebplugins.nitor.template import send_template


__version__ = '0.0.1'


GYMS_BAG = 'gyms'
CLIMBTYPES = 'climbtypes'
CLEAN_CLIMB = ['onsight', 'flash', 'redpoint']
RESERVED_BAGS = [GYMS_BAG, 'common', CLIMBTYPES]
ROUTE_FIELDS = ['lineNumber', 'colorName', 'grade', 'routeSetter']
LEAD_FIELD = 'isLeadRoute'
TIDDLER_TYPE = 'text/x-markdown'
DEFAULT_SIDEBAR_TAGS = ['news', 'route', 'climb']


@do_html()
def home(environ, start_response):
    kept_bags, fullnames = get_gyms(environ, 'read')
    return send_template(environ, 'home.html', { 'gyms': kept_bags,
        'fullnames': fullnames, 'title': 'Welcome to Nitor',
        'sidebar_info': get_sidebar(environ)})


def get_sidebar(environ, tags=None, users=None, gyms=None):
    store = environ['tiddlyweb.store']
    usersign = environ['tiddlyweb.usersign']
    if not tags:
        tags =  DEFAULT_SIDEBAR_TAGS
    query = ' OR '.join(['tag:%s' % tag for tag in tags])
    return (store.get(tiddler) for tiddler in
            readable_tiddlers_by_bag(store, store.search(query), usersign))


#@require_role('ADMIN)
@do_html()
def admin(environ, start_response):
    """
    Present the admin interface.
    """
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
    """
    Present the admin editor for a single gym.
    """
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
    """
    Handle a POSTed gym edit, by an admin.
    """
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
    """
    Update the info about single gym.
    """
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
    bags = (store.get(climb_bag) for climb_bag in sorted(
        (bag for bag in store.list_bags() if bag.name.endswith('_climbs')),
        key=attrgetter('name')))
    kept_bags = []
    fullnames = {}
    for bag in bags:
        try:
            bag.policy.allows(usersign, constraint)
            bag_name = bag.name.replace('_climbs', '')
            kept_bags.append(bag_name)
            try:
                tiddler = store.get(Tiddler(bag_name, GYMS_BAG))
                fullnames[bag_name] = tiddler.fields['fullname']
            except StoreError:
                pass
        except PermissionsError:
            pass
    return kept_bags, fullnames


#@require_role('MANAGER')
@do_html()
def manager(environ, start_response):
    """
    Display all the gyms one manager can manage.
    """
    kept_bags, fullnames = get_gyms(environ, 'manage')
    return send_template(environ, 'manage_list.html', {'gyms': kept_bags,
        'title': 'Your Gyms', 'fullnames': fullnames})


#@require_role('MANAGER')
@do_html()
def manage_gym(environ, start_response):
    """
    Present a gym managers view upon a single gym.
    """
    store = environ['tiddlyweb.store']
    gym = get_route_value(environ, 'gym')
    routes_bag = store.get(Bag('%s_climbs' % gym))
    news_bag = Bag('%s_news' % gym)
    # Bail out if we are not allowed to manage. 
    routes_bag.policy.allows(environ['tiddlyweb.usersign'], 'manage')
    gym_tiddler = store.get(Tiddler(gym, GYMS_BAG))

    try:
        latest_news = [tiddler for tiddler in filter_tiddlers(
            store.list_bag_tiddlers(news_bag),
            'sort=-modified;limit=1', environ)][0]
        latest_news = store.get(latest_news)
        news_html = render_wikitext(latest_news, environ)
        latest_news.fields['html'] = news_html
    except IndexError:
        latest_news = Tiddler('tmp')
        latest_news.fields['html'] = '<p>No News</p>'

    routes = _get_gym_routes(environ, gym)

    return send_template(environ, 'manage_gym.html', {
        'title': 'Manage %s' % gym,
        'gym_tiddler': gym_tiddler,
        'latest_news': latest_news,
        'routes': routes})


def _get_gym_routes(environ, gym_name):
    """
    Get the current routes in a gym, order by the line number,
    which needs to be translated into an int (from a string).
    """
    store = environ['tiddlyweb.store']
    gym_bag = Bag('%s_climbs' % gym_name)

    def _get_and_mangle_tiddler(tiddler):
        tiddler = store.get(tiddler)
        try:
            tiddler.fields['lineNumber'] = int(tiddler.fields['lineNumber'])
        except ValueError:
            pass  # don't worry
        return tiddler

    return [_get_and_mangle_tiddler(tiddler) for tiddler
            in store.list_bag_tiddlers(gym_bag)]


#@require_role('MANAGER')
@do_html()
def manage_edit(environ, start_response):
    """
    Handle POSTed data from the gym manager's editor.
    """
    store = environ['tiddlyweb.store']
    gym = get_route_value(environ, 'gym')
    gym_bag = store.get(Bag('%s_climbs' % gym))
    # Bail out if we are not allowed to manage. 
    gym_bag.policy.allows(environ['tiddlyweb.usersign'], 'manage')

    submit = environ['tiddlyweb.query'].get('submit', [''])[0]

    if submit == 'Update Routes':
        return _manage_update_routes(environ, gym)
    elif submit == 'Create News':
        return _manage_create_news(environ, gym)
    else:
        return _manage_update_gym(environ, gym)

def _manage_create_news(environ, gym):
    """
    Store a newly created news item.
    """
    store = environ['tiddlyweb.store']
    news = environ['tiddlyweb.query'].get('news', [''])[0]
    tiddler = Tiddler(str(uuid4()), '%s_news' % gym)
    tiddler.text = news
    tiddler.type = TIDDLER_TYPE
    store.put(tiddler)
    raise HTTP303(server_base_url(environ) + '/manager/%s' % gym)

def _manage_update_routes(environ, gym):
    """
    Update routes with new information.
    """
    store = environ['tiddlyweb.store']
    query = environ['tiddlyweb.query']
    existing_titles = query.get('title', [])
    count = len(existing_titles)
    index = 0
    delete = query.get('delete', [])
    lead_route = query.get(LEAD_FIELD, [])
    while index < count:
        title = existing_titles[index]
        tiddler = Tiddler(title, '%s_climbs' % gym)
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
    tiddler = Tiddler(title, '%s_climbs' % gym)
    new_route = False
    if 'new_one' in lead_route:
        tiddler.fields[LEAD_FIELD] = '1'
    for key in ROUTE_FIELDS:
        value = query.get(key, [''])[index]
        if value == '':
            continue
        new_route = True
        tiddler.fields[key] = value
    if new_route:
        store.put(tiddler)
    raise HTTP303(server_base_url(environ) + '/manager/%s' % gym)

def _manage_update_gym(environ, gym):
    """
    Update the gym information.
    """
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
    news_tiddlers = []
    try:
        gym_tiddler = store.get(Tiddler(gym, GYMS_BAG))
        news_bag = Bag('%s_news' % gym)
        latest_news = [tiddler for tiddler in filter_tiddlers(
            store.list_bag_tiddlers(news_bag),
            'sort=-created;limit=10', environ)]
        for tiddler in latest_news:
            tiddler = store.get(tiddler)
            news_html = render_wikitext(tiddler, environ)
            tiddler.fields['html'] = news_html
            news_tiddlers.append(tiddler)

    except StoreError, exc:
        raise HTTP404('that gym does not exist: %s' % exc)
    return send_template(environ, 'gym.html', {
        'gym': gym_tiddler,
        'title': gym,
        'news_tiddlers': news_tiddlers})


@do_html()
def gym_routes(environ, start_response):
    """
    Display the routes from a single gym.
    """
    store = environ['tiddlyweb.store']
    current_user = environ['tiddlyweb.usersign']['name']
    gym = get_route_value(environ, 'gym')
    routes = _get_gym_routes(environ, gym)
    climbtypes = [tiddler.title for tiddler in
            store.list_bag_tiddlers(Bag(CLIMBTYPES))]
    if current_user:# != 'GUEST':
        search_query = 'bag:%s tag:climb gym:%s _limit:%s' % (current_user,
                gym, len(routes))
        recent_climbs = dict([(tiddler.title, store.get(tiddler))
            for tiddler in store.search(search_query)])
        search_query = 'bag:%s tag:tickwish gym:%s _limit:%s' % (current_user,
                gym, len(routes))
        wished_climbs = [tiddler.title for tiddler in store.search(search_query)]
        for route in routes:
            if route.title in recent_climbs:
                route.fields['climbtype'] = recent_climbs[
                        route.title].fields['climbtype']
            if route.title in wished_climbs:
                route.fields['do'] = True

    return send_template(environ, 'gym_routes.html', {
        'gym': gym,
        'climbtypes': [''] + climbtypes,
        'title': 'Routes @%s' % gym,
        'routes': routes})


#@require_any_user()
@do_html()
def ticklist(environ, start_response):
    """
    Display a user's own ticklist.
    """
    store = environ['tiddlyweb.store']
    current_user = environ['tiddlyweb.usersign']['name']
    gym = get_route_value(environ, 'gym')
    routes = _get_gym_routes(environ, gym)

    climbtypes = [tiddler.title for tiddler in
            store.list_bag_tiddlers(Bag(CLIMBTYPES))]

    search_query = 'bag:%s tag:tickwish gym:%s _limit:%s' % (current_user,
            gym, len(routes))
    wished_climbs = dict([(tiddler.title, store.get(tiddler))
        for tiddler in store.search(search_query)])
    for route in routes:
        if route.title in wished_climbs:
            wished_climbs[route.title].fields['do'] = True

    return send_template(environ, 'gym_routes.html', {
        'gym': gym,
        'climbtypes': [''] + climbtypes,
        'title': 'Ticklist for %s@%s' % (current_user, gym),
        'routes': wished_climbs.values()})

def record_climbs(environ, start_response):
    """
    Record a climb that has been accomplished.
    """
    query = environ['tiddlyweb.query']
    store = environ['tiddlyweb.store']
    current_user = environ['tiddlyweb.usersign']['name']
    gym = get_route_value(environ, 'gym')

    routes = query['route']
    dones = query['doneroute']
    
    for index, value in enumerate(dones):
        if value != '':
            route_title = routes[index]
            tiddler = Tiddler(route_title, current_user)
            try:
                tiddler = store.get(tiddler)
            except StoreError:
                pass
            if value in CLEAN_CLIMB:
                try:
                    tiddler.tags.remove('tickwish')
                except ValueError:
                    pass
            tiddler.fields['climbtype'] = value
            tiddler.fields['gym'] = gym
            tiddler.tags.append('climb')
            store.put(tiddler)

    raise HTTP303(server_base_url(environ) + environ['REQUEST_URI'])


#@require_any_user()
def make_ticklist(environ, start_response):
    """
    Record routes the user would like to climb.
    """
    store = environ['tiddlyweb.store']
    current_user = environ['tiddlyweb.usersign']['name']
    gym = get_route_value(environ, 'gym')
    tick_wishes = environ['tiddlyweb.query'].get('addroute', [])
    routes = _get_gym_routes(environ, gym)

    for route in routes:
        route.bag = current_user
        if route.title in tick_wishes:
            route.tags = ['tickwish']
            route.fields['gym'] = gym
            store.put(route)
        else:
            try:
                tiddler = store.get(route)
                tiddler.tags.remove('tickwish')
                store.put(tiddler)
            except (StoreError, ValueError):
                pass

    raise HTTP303(server_base_url(environ)
            + '/gyms/%s/ticklist' % encode_name(gym))


#@require_any_user()
@do_html()
def user_routes_update(environ, start_response):
    """
    Handle a user's POSTed ticks or routes.
    """
    submit = environ['tiddlyweb.query'].get('submit', [None])[0]
    if submit == 'Manage Ticklist':
        return make_ticklist(environ, start_response)
    elif submit == 'Manage Climbs':
        return record_climbs(environ, start_response)
    else:
        raise HTTP400('Bad request for route update')


def establish_handlers(config):
    selector = config['selector']
    replace_handler(selector, '/', dict(GET=home))
    selector.add('/admin', GET=admin)
    selector.add('/admin/{gym:segment}', GET=gym_editor, POST=gym_edit)
    selector.add('/manager', GET=manager)
    selector.add('/manager/{gym:segment}', GET=manage_gym, POST=manage_edit)
    selector.add('/gyms/{gym:segment}', GET=gym_info)
    selector.add('/gyms/{gym:segment}/routes', GET=gym_routes,
            POST=user_routes_update)
    selector.add('/gyms/{gym:segment}/ticklist', GET=ticklist,
            POST=user_routes_update)


def create_gym_bag(environ, bag_name):
    """
    Set up the bags used by a gym.
    """
    store = environ['tiddlyweb.store']
    news_bag = Bag('%s_news' % bag_name)
    climbs_bag = Bag('%s_climbs' % bag_name)
    archive_bag = Bag('%s_archive' % bag_name)
    # TODO Set policy appropriately
    #bag.policy.manage ....
    store.put(news_bag)
    store.put(climbs_bag)
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
