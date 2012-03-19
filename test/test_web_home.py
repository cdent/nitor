
from fixtures import make_test_env

from wsgi_intercept import httplib2_intercept
import wsgi_intercept
import httplib2

def setup_module(module):
    make_test_env(module)
    httplib2_intercept.install()
    wsgi_intercept.add_wsgi_intercept('nitor.org', 8080, app_fn)
    module.http = httplib2.Http()

def teardown_module(module):
    import os
    os.chdir('..')

def test_home_handler():
    response, content = http.request('http://nitor.org:8080/')

    assert response['status'] == '200', content
    assert 'Welcome to Nitor' in content
    assert '/bags/common/tiddlers/base.css' in content

def test_admin_handler():
    response, content = http.request('http://nitor.org:8080/admin')

    assert response['status'] == '200', content
    assert 'href="admin/testgym"' in content
    assert 'A debugging test gym' in content
