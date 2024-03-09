import unittest

from framework.http.request import Path
from framework.http.response import (
    url_file, url_for,
    set_header, get_header, has_header, delete_header,
    set_cookie, delete_cookie,
    redirect_page,
    render_template
)
from framework.main import Main
from framework.routing import Rule, Endpoint, Map

from .. import dummy_environ, dummy, DummyStartResponse

environ, start_response = dummy_environ.copy(), DummyStartResponse()


def dummy_section():
    return 'section'


def dummy_subsection(path: Path):
    return path['subsection']


def dummy_header():
    set_header('header', 'header')
    set_header('delete', 'delete')
    true = has_header('delete')
    value = get_header('delete')
    delete_header('delete')
    set_cookie('one', 'one')
    set_cookie('two', 'two')
    set_cookie('delete', 'delete')
    delete_cookie('delete')
    return f"{true} {value} {has_header('delete')}"


def dummy_redirect(path: Path):
    args = [url_for(path['urlpath'])]

    if 0 != path['code']:
        args.append(path['code'])

    return redirect_page(*args)


def dummy_template(path: Path):
    context = {'title': (filename := path['filename']).split('.')[0].title()}

    return render_template(filename, context)


class TestModule(unittest.TestCase):
    def test_init(self):
        Main(__name__, Map(()))

        self.assertEqual('/static/test.file', url_file('test.file'))
        self.assertIsNone(url_for('index'))

        Main(__name__, Map(()), static_urlpath='/')

        self.assertEqual('/test.file', url_file('test.file'))

        Main(__name__, Map(()), static_urlpath='/files/')

        self.assertEqual('/files/path/to/test.file', url_file('path/to/test.file'))

        app = Main(__name__, Map((
            Rule('/', 'index'),
            Endpoint('index', dummy),
            Rule('/section', 'section'),
            Endpoint('section', dummy_section),
            Rule('/section/<subsection>', 'subsection'),
            Endpoint('subsection', dummy_subsection),
        )))

        environ['PATH_INFO'] = url_for('index')

        self.assertEqual(b'', b''.join(app(environ, start_response)))

        environ['PATH_INFO'] = url_for('section')

        self.assertEqual(b'section', b''.join(app(environ, start_response)))

        environ['PATH_INFO'] = url_for('subsection', subsection='subsection')

        self.assertEqual(b'subsection', b''.join(app(environ, start_response)))

    def test_header(self):
        app = Main(__name__, Map((
            Rule('/', 'index'),
            Endpoint('index', dummy),
            Rule('/header', 'header'),
            Endpoint('header', dummy_header),
            Rule('/redirect/<urlpath>/<int:code>', 'redirect'),
            Endpoint('redirect', dummy_redirect),
        )))

        environ['PATH_INFO'], header, delete, cookie = '/header', None, None, dict()

        self.assertEqual(b'True delete False', b''.join(app(environ, start_response)))

        for key, value in start_response.headers:
            if 'header' == key:
                header = value

            if 'delete' == key:
                delete = value

            if 'set-cookie' == key:
                cookie[value.split('=', 1)[0]] = value

        self.assertEqual('header', header)
        self.assertIsNone(delete)

        self.assertEqual('one=one; Path=/', cookie['one'])
        self.assertEqual('two=two; Path=/', cookie['two'])
        self.assertEqual('delete=; expires=Thu, 01 Jan 1970 00:00:00 GMT; Path=/', cookie['delete'])

        environ['PATH_INFO'], value = url_for('redirect', urlpath='index', code='0'), None

        self.assertEqual(b'', b''.join(app(environ, start_response)))
        self.assertEqual('307 Temporary Redirect', start_response.status)

        for key, value in start_response.headers:
            if 'location' == key:
                break

        self.assertEqual(url_for('index'), value)

        environ['PATH_INFO'], value = url_for('redirect', urlpath='header', code='308'), None

        self.assertEqual(b'', b''.join(app(environ, start_response)))
        self.assertEqual('308 Permanent Redirect', start_response.status)

        for key, value in start_response.headers:
            if 'location' == key:
                break

        self.assertEqual(url_for('header'), value)

    def test_template(self):
        app = Main(__name__, Map((
            Rule('/', 'index'),
            Endpoint('index', dummy),
            Rule('/<filename>', 'template', {'filename': r'[a-z.]+'}),
            Endpoint('template', dummy_template),
        )))

        environ['PATH_INFO'] = url_for('template', filename='index.html')

        self.assertEqual(
            b'<!DOCTYPE html>\n'
            b'<html lang="en">\n'
            b'<head>\n'
            b'    <meta charset="UTF-8">\n'
            b'    <title>Index</title>\n'
            b'    <link rel="stylesheet" href="' + url_file('style.css').encode('ascii') +
            b'">\n'
            b'</head>\n'
            b'<body>\n'
            b'<ul>\n'
            b'    <li><a href="' + url_for('index').encode('ascii') +
            b'">Homepage</a></li>\n'
            b'    <li><a href="' + url_for('template', filename='index.html').encode('ascii') +
            b'">Template</a></li>\n'
            b'</ul>\n'
            b'</body>\n'
            b'</html>', b''.join(app(environ, start_response))
        )


def response_tests():
    suite = unittest.TestSuite()

    for test in (
            'test_init',
            'test_header',
            'test_template',
    ):
        suite.addTest(TestModule(test))

    return suite
