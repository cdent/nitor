"""
Send a template.
"""

from tiddlywebplugins.templates import get_template


def send_template(environ, template_name, template_data=None):
    if template_data == None:
        template_data = {}
    template = get_template(environ, template_name)
    template_defaults = {
            'title': '',
            }
    template_defaults.update(template_data)
    return template.generate(template_defaults)
