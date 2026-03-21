'''
CLI entrypoint module for the web service.
'''
import os
import cherrypy
import signal

from importlib import resources
from ytffmpeg import getLogger, webserv

log = getLogger(__name__)


def serveTheWeb(cfg: dict):
    '''
    Main entry point for 'ytffmpeg serve' command.
    Starts the CherryPy web server.
    '''
    # Get configuration
    workspace = os.path.abspath(cfg.get('workspace', os.getcwd()))
    http_port = cfg.get('http_port', int(os.getenv('HTTP_PORT', '9091')))
    os.chdir(workspace)

    # Ensure workspace exists
    os.makedirs(workspace, exist_ok=True)
    log.info(f'Workspace directory: {workspace}')

    # Determine webroot
    # Try importlib.resources first (for installed package)
    try:
        # For Python 3.9+, resources.files returns a Traversable
        webroot_resource = resources.files('ytffmpeg').joinpath('../../web')
        default_webroot = str(webroot_resource)
    except (AttributeError, TypeError):
        # Fallback for development or older Python
        default_webroot = os.path.join(os.path.dirname(__file__), '../../web')

    webroot = cfg.get('webroot', default_webroot)
    webroot = os.path.abspath(webroot)
    cfg['webroot'] = webroot

    if not os.path.exists(webroot):
        log.error(f'Webroot directory not found: {webroot}')
        log.error('Please ensure web assets are installed or specify webroot in config')
        return 1

    log.info(f'Serving static files from: {webroot}')

    # Create handlers
    page_handler = webserv.PageHandlers(cfg)
    api_handler = webserv.ApiHandlers(cfg)

    # Mount handlers
    cherrypy.tree.mount(page_handler, '/', config={
        '/': {
            'tools.staticdir.on': False
        },
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': webroot
        }
    })

    cherrypy.tree.mount(api_handler, '/api', config={
        '/': {
            'error_page.default': webserv.jsonify_error,
        },
    })

    # Server configuration
    cherrypy.config.update({
        'tools.sessions.on': False,
        'error_page.default': webserv.jsonify_error,
        'request.show_tracebacks': False,
        'server.socket_host': '0.0.0.0',
        'server.socket_port': http_port,
        'server.thread_pool': 50,
        'server.max_request_body_size': 5 * 1024 * 1024 * 1024,  # 5GB
        'server.socket_timeout': 600,
        'log.screen': True,
        'log.access_file': '',
        'log.error_file': ''
    })

    log.info(f'Starting ytffmpeg web server on http://0.0.0.0:{http_port}')
    log.info('Press Ctrl+C to stop')
    signal.signal(signal.SIGCHLD, signal.SIG_IGN)

    try:
        cherrypy.engine.start()
        cherrypy.engine.block()
    except KeyboardInterrupt:
        log.info('Shutting down server...')
        cherrypy.engine.stop()

    return 0

