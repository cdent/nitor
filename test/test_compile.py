


def test_compile():
    try:
        import tiddlywebplugins.nitor
        assert True
    except ImportError, exc:
        assert False, exc
