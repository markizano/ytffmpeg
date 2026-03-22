'''
Unit tests for the mkzforge web server module.
Tests module imports, configuration, and component structure.
'''

import os
import sys
import unittest

from kizano import getLogger
log = getLogger(__name__)


class TestWebServerImports(unittest.TestCase):
    '''Test that web server components can be imported'''

    def test_action_serve_exists(self):
        '''Verify SERVE action is defined in Action enum'''
        from mkzforge.types import Action
        # Check that SERVE attribute exists and has correct value
        self.assertTrue(hasattr(Action, 'SERVE'))
        self.assertEqual(Action.SERVE, 'serve')
        # Check it's in the enum values
        self.assertIn('serve', [action.value for action in Action])

    def test_webserv_module_imports(self):
        '''Verify webserv module and its classes can be imported'''
        from mkzforge import webserv

        self.assertTrue(hasattr(webserv, 'serve'))
        self.assertTrue(hasattr(webserv, 'PageHandlers'))
        self.assertTrue(hasattr(webserv, 'ApiHandlers'))
        self.assertTrue(hasattr(webserv, 'process_video_pipeline'))

    def test_serve_registered_in_cli(self):
        '''Verify SERVE action is registered in CLI actions'''
        from mkzforge.cli import Cli
        from mkzforge.types import Action

        self.assertIn(Action.SERVE, Cli.ACTIONS)
        self.assertTrue(callable(Cli.ACTIONS[Action.SERVE]))

    def test_webserv_imported_in_cli(self):
        '''Verify webserv module is imported in CLI __init__'''
        from mkzforge.cli import webserv as imported_webserv
        self.assertIsNotNone(imported_webserv)


class TestWebAssets(unittest.TestCase):
    '''Test that web assets exist and are accessible'''

    def setUp(self):
        '''Set up test fixtures'''
        self.web_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'web')
        self.required_files = [
            'index.html',
            'projects.html',
            'project-detail.html',
            'style.css',
            'app.js'
        ]

    def test_web_directory_exists(self):
        '''Verify web directory exists'''
        self.assertTrue(os.path.exists(self.web_dir))
        self.assertTrue(os.path.isdir(self.web_dir))

    def test_all_web_assets_exist(self):
        '''Verify all required web assets exist'''
        for filename in self.required_files:
            filepath = os.path.join(self.web_dir, filename)
            with self.subTest(filename=filename):
                self.assertTrue(os.path.exists(filepath), f"{filename} should exist")
                self.assertTrue(os.path.isfile(filepath), f"{filename} should be a file")

    def test_index_html_content(self):
        '''Verify index.html has expected content'''
        index_path = os.path.join(self.web_dir, 'index.html')
        with open(index_path, 'r') as f:
            content = f.read()

        # Check for key elements
        self.assertIn('mkzforge', content.lower())
        self.assertIn('<form', content.lower())
        self.assertIn('upload', content.lower())

    def test_css_file_not_empty(self):
        '''Verify CSS file has content'''
        css_path = os.path.join(self.web_dir, 'style.css')
        self.assertGreater(os.path.getsize(css_path), 0)

    def test_js_file_not_empty(self):
        '''Verify JavaScript file has content'''
        js_path = os.path.join(self.web_dir, 'app.js')
        self.assertGreater(os.path.getsize(js_path), 0)


class TestWebServerClasses(unittest.TestCase):
    '''Test web server class structure'''

    def test_page_handlers_initialization(self):
        '''Verify PageHandlers can be instantiated'''
        from mkzforge.webserv import PageHandlers

        config = {'mkzforge': {'workspace': '/tmp/workspace', 'webroot': '/tmp/webroot'}}
        handler = PageHandlers(config)

        self.assertEqual(handler.workspace, '/tmp/workspace')
        self.assertEqual(handler.config, config)
        self.assertEqual(handler.webroot, '/tmp/webroot')

    def test_api_handlers_initialization(self):
        '''Verify ApiHandlers can be instantiated'''
        from mkzforge.webserv import ApiHandlers

        config = {'mkzforge': {'workspace': '/tmp/workspace'}}
        handler = ApiHandlers(config)

        self.assertEqual(handler.workspace, '/tmp/workspace')
        self.assertEqual(handler.config, config)
        self.assertTrue(hasattr(handler, 'processing_jobs'))

    def test_page_handlers_methods(self):
        '''Verify PageHandlers has required methods'''
        from mkzforge.webserv import PageHandlers

        self.assertTrue(hasattr(PageHandlers, 'index'))
        self.assertTrue(hasattr(PageHandlers, 'videos'))
        self.assertTrue(hasattr(PageHandlers, 'video'))

    def test_api_handlers_methods(self):
        '''Verify ApiHandlers has required methods'''
        from mkzforge.webserv import ApiHandlers

        self.assertTrue(hasattr(ApiHandlers, 'projects'))
        self.assertTrue(hasattr(ApiHandlers, 'project'))
        self.assertTrue(hasattr(ApiHandlers, 'process'))


class TestConfiguration(unittest.TestCase):
    '''Test configuration handling'''

    def test_serve_function_signature(self):
        '''Verify serve function accepts config dict'''
        from mkzforge import webserv
        import inspect

        sig = inspect.signature(webserv.serve)
        params = list(sig.parameters.keys())

        self.assertIn('config', params)

    def test_process_video_pipeline_signature(self):
        '''Verify background processing function signature'''
        from mkzforge.webserv import process_video_pipeline
        import inspect

        sig = inspect.signature(process_video_pipeline)
        params = list(sig.parameters.keys())

        expected_params = ['workspace', 'project_name', 'project_config',
                          'metadata', 'file_paths', 'config']

        for param in expected_params:
            with self.subTest(param=param):
                self.assertIn(param, params)


class TestPackageConfiguration(unittest.TestCase):
    '''Test package configuration in pyproject.toml'''

    def setUp(self):
        '''Set up test fixtures'''
        self.pyproject_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'pyproject.toml'
        )

    def test_pyproject_exists(self):
        '''Verify pyproject.toml exists'''
        self.assertTrue(os.path.exists(self.pyproject_path))

    def test_package_data_configured(self):
        '''Verify package-data section exists'''
        with open(self.pyproject_path, 'r') as f:
            content = f.read()

        self.assertIn('[tool.setuptools.package-data]', content)

    def test_data_files_configured(self):
        '''Verify data-files section exists'''
        with open(self.pyproject_path, 'r') as f:
            content = f.read()

        self.assertIn('[tool.setuptools.data-files]', content)

    def test_web_assets_in_data_files(self):
        '''Verify web assets are listed in data-files'''
        with open(self.pyproject_path, 'r') as f:
            content = f.read()

        self.assertIn('web/*.html', content)
        self.assertIn('web/*.css', content)
        self.assertIn('web/*.js', content)


class TestDocumentation(unittest.TestCase):
    '''Test that documentation exists'''

    def test_webserver_doc_exists(self):
        '''Verify WEBSERVER.md documentation exists'''
        doc_path = os.path.join(os.path.dirname(__file__), '..', '..', 'doc', 'WEBSERVER.md')
        self.assertTrue(os.path.exists(doc_path))

    def test_claude_md_updated(self):
        '''Verify CLAUDE.md mentions the serve command'''
        claude_path = os.path.join(os.path.dirname(__file__), '..', '..', 'CLAUDE.md')
        with open(claude_path, 'r') as f:
            content = f.read()

        self.assertIn('serve', content.lower())
        self.assertIn('web interface', content.lower())
