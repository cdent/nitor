.PHONY: test remotes dev clean

clean:
	find . -name "*.pyc" | xargs rm || true
	rm -rf dist || true
	rm -rf build || true
	rm -rf *.egg-info || true
	rm -rf tiddlywebplugins/nitor/resources || true
	rm -f src/externals/* || true
	rm -r test_instance || true


dev: remotes dev_local

dev_local:
	@mysqladmin -f drop nitor || true
	@mysqladmin create nitor
	@PYTHONPATH="." ./nitor dev_instance
	( cd dev_instance && \
		ln -s ../devconfig.py && \
		ln -s ../mangler.py && \
		ln -s ../tiddlywebplugins && \
		ln -s ../tiddlywebplugins/templates )
	@echo "from devconfig import update_config; update_config(config)" \
		>> dev_instance/tiddlywebconfig.py
	@echo "INFO development instance created in dev_instance"

remotes:
	curl -Lo src/externals/jquery.js.js https://ajax.googleapis.com/ajax/libs/jquery/1/jquery.min.js
	./cacher

test:
	py.test -x test
