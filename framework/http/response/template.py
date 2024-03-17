import os
import re


class Http(object):
    __slots__ = ('_request', '_response')

    def __init__(self):
        from .. import request, response

        self._request, self._response = request, response

    def url_file(self, name: str):
        return self._response.url_file(name.strip(r'\'"'))

    def url_for(self, args_kwargs: str):
        args, kwargs = list(), dict()

        for item in args_kwargs.split(','):
            if '=' in item:
                k, v = item.lstrip().split('=')

                kwargs.update({k: v.strip(r'\'"')})

            else:
                args.append(item.strip(r'\'"'))

        url = self._response.url_for(*args, **kwargs)

        return str(url) if url is None else url

    def form(self, name: str):
        value = self._request.form(name.strip(r'\'"'))

        return '' if value is None else value


def context_replace(context: dict[str, str] | None, body: str):
    keys, http = tuple() if context is None else context.keys(), Http()

    for key in re.findall(r'{{ ([A-Za-z0-9_]+\(?[\sA-Za-z0-9_,=\'."]*\)?) }}', body):
        if key in keys:
            body = body.replace('{{ %s }}' % key, context[key])

        elif '(' in key:
            if r := re.findall(r'([A-Za-z0-9_]+)\(\s*([A-Za-z0-9 _,=\'."]+[\'"])', key):
                name, args = r[-1]

                if name not in http.__slots__ and hasattr(http, name):
                    body = body.replace('{{ %s }}' % key, getattr(http, name)(args))

    return body.rstrip()


class Template(object):
    __slots__ = ('templates', 'body')

    templates: str
    body: str | None

    def __init__(self, filename: str | os.PathLike):
        filepath = os.path.abspath(os.path.join(self.templates, filename))

        if os.path.isfile(filepath):
            self.raw_body(filepath)

            if not hasattr(self, 'body'):
                self.body = 'Error reading file.'

        else:
            self.body = None

    def raw_body(self, filepath: str):
        try:
            f = open(filepath, 'r')
            body = f.read()
            f.close()

            self.body = body

        except OSError:
            pass

    def render(self, context: dict[str, str] | None):
        if self.body is None:
            return b'Template file not found.'

        else:
            return context_replace(context, self.body)
