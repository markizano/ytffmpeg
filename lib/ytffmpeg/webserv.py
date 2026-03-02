'''
CherryPy Web Server for ytffmpeg

This module provides a web interface for uploading videos and managing ytffmpeg projects.
It includes:
- HTML page serving
- REST API endpoints for video processing
- Background processing workers
- Project management
'''

import os
import json
import shutil
import tempfile
import multiprocessing
from importlib import resources
from typing import Dict, List, Optional

import cherrypy
from kizano import getLogger
from kizano.utils import dictmerge, read_yaml, write_yaml

log = getLogger(__name__)

from ytffmpeg.notify import send_notification

class PageHandlers:
    '''
    Serves HTML pages from webroot directory.
    '''

    def __init__(self, config: dict):
        self.config = config
        self.workspace = config['ytffmpeg'].get('workspace', os.getcwd())
        self.webroot = config['ytffmpeg'].get('webroot', os.path.join(os.getcwd(), 'web'))

    @cherrypy.expose
    def index(self):
        '''Serve video submission form'''
        index_path = os.path.join(self.webroot, 'index.html')
        if not os.path.exists(index_path):
            raise cherrypy.HTTPError(404, 'index.html not found')
        return open(index_path, 'r').read()

    @cherrypy.expose
    def videos(self):
        '''Serve projects list page'''
        projects_path = os.path.join(self.webroot, 'projects.html')
        if not os.path.exists(projects_path):
            raise cherrypy.HTTPError(404, 'projects.html not found')
        return open(projects_path, 'r').read()

    @cherrypy.expose
    def video(self, project=None):
        '''Serve project detail page'''
        if not project:
            raise cherrypy.HTTPError(400, 'Project parameter required')
        detail_path = os.path.join(self.webroot, 'project-detail.html')
        if not os.path.exists(detail_path):
            raise cherrypy.HTTPError(404, 'project-detail.html not found')
        return open(detail_path, 'r').read()

class ApiHandlers:
    '''
    JSON API endpoints for video processing and project management.
    '''

    def __init__(self, config: dict):
        self.config = config
        self.workspace = config['ytffmpeg'].get('workspace', os.getcwd())
        self.processing_jobs: Dict[str, dict] = {}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def projects(self):
        '''
        GET /api/projects
        Returns list of all projects in workspace
        '''
        log.info(f'{cherrypy.request.method} /api/projects.')
        if cherrypy.request.method != 'GET':
            cherrypy.log.error(f'Method {cherrypy.request.method} not allowed. Use GET only.')
            raise cherrypy.HTTPError(405, 'Method not allowed')
        try:
            projects = []
            if not os.path.exists(self.workspace):
                return {'projects': projects}
            for project_name in os.listdir(self.workspace):
                project_path = os.path.join(self.workspace, project_name)
                if not os.path.isdir(project_path):
                    continue
                # Just check right quick if it's a `ytffmpeg.yml` configured folder.
                config_path = os.path.join(project_path, 'ytffmpeg.yml')
                if not os.path.exists(config_path): continue
                projects.append(project_name)
            return {'projects': projects}

        except Exception as e:
            log.error(f'Failed to list projects: {e}')
            raise cherrypy.HTTPError(500, str(e))

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def project(self, project_name):
        '''
        GET /api/project/<project_name>
        Returns detailed information about a specific project
        '''
        log.info(f'{cherrypy.request.method} /api/project/{project_name}.')
        if cherrypy.request.method != 'GET':
            raise cherrypy.HTTPError(405, 'Method not allowed')

        try:
            project_path = os.path.join(self.workspace, project_name)
            if not os.path.exists(project_path):
                raise cherrypy.HTTPError(404, f'Project {project_name} not found')

            # Read configuration
            config_path = os.path.join(project_path, 'ytffmpeg.yml')
            project_config = None
            if os.path.exists(config_path):
                project_config = read_yaml(config_path)
            return {
                'name': project_name,
                'config': project_config,
            }

        except Exception as e:
            log.error(f'Failed to get project details: {e}')
            raise cherrypy.HTTPError(500, str(e))

    @cherrypy.expose
    def resource(self, project_name: str, resource: str):
        '''
        GET /api/resource/<project_name>/(thumbnail|output)
        Returns a resource from the project.
        '''
        log.info(f'{cherrypy.request.method} /api/project/{project_name}/{resource}.')
        if cherrypy.request.method != 'GET':
            raise cherrypy.HTTPError(405, 'Method not allowed')

        try:
            project_path = os.path.join(self.workspace, project_name)
            if not os.path.exists(project_path):
                raise cherrypy.HTTPError(404, f'Project {project_name} not found')

            # Read configuration
            config_path = os.path.join(project_path, 'ytffmpeg.yml')
            project_config = None
            if os.path.exists(config_path):
                project_config = read_yaml(config_path)
            if resource == 'output':
                output_filename = os.path.join(self.workspace, project_name, project_config['videos'][0]['output'])
                attachment_filename = os.path.basename(output_filename)
                cherrypy.response.headers['Content-Type'] = 'video/mp4' if attachment_filename.endswith('mp4') else 'video/x-matroska'
            if resource == 'thumbnail':
                output_filename = os.path.join(self.workspace, project_name, 'thumbnail.png')
                attachment_filename = f'{project_name}.png'
                cherrypy.response.headers['Content-Type'] = 'image/png'
            if not os.path.exists(output_filename):
                raise cherrypy.HTTPError(404, f'Resource {resource} not found')
            cherrypy.response.headers['Content-Disposition'] = f'attachment; filename="{attachment_filename}"'
            return open(output_filename, 'rb').read()

        except Exception as e:
            log.error(f'Failed to get project details: {e}')
            raise cherrypy.HTTPError(500, str(e))

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def process(self):
        '''
        POST /api/process
        Upload videos and start processing pipeline
        '''
        cherrypy.log.info(f'{cherrypy.request.method} /api/process.')
        if cherrypy.request.method != 'POST':
            raise cherrypy.HTTPError(405, 'Method not allowed')

        try:
            # Parse multipart form data
            project_name = None
            project_config = None
            metadata = None
            video_files = []

            # Get form fields
            for key, value in cherrypy.request.params.items():
                if key == 'project_name':
                    project_name = value
                elif key == 'project_config':
                    project_config = json.loads(value)
                elif key == 'metadata':
                    metadata = json.loads(value)
                elif key == 'videos':
                    # Handle multiple video uploads
                    if not isinstance(value, list):
                        value = [value]
                    for video_file in value:
                        if hasattr(video_file, 'file'):
                            video_files.append(video_file)

            # Validation
            if not project_name:
                raise cherrypy.HTTPError(400, 'project_name is required')
            if not video_files:
                raise cherrypy.HTTPError(400, 'At least one video file is required')

            # Save uploaded files to temporary directory
            temp_dir = tempfile.mkdtemp(prefix='ytffmpeg_upload_')
            saved_files = []

            try:
                for video_file in video_files:
                    filename = video_file.filename
                    temp_path = os.path.join(temp_dir, filename)

                    # Save file
                    with open(temp_path, 'wb') as f:
                        while True:
                            chunk = video_file.file.read(8192)
                            if not chunk:
                                break
                            f.write(chunk)

                    saved_files.append((temp_path, filename))
                    log.info(f'Saved uploaded file: {filename} ({os.path.getsize(temp_path)} bytes)')

                # Start background processing
                process = multiprocessing.Process(
                    target=process_video_pipeline,
                    args=(self.workspace, project_name, project_config, metadata, saved_files, self.config),
                    daemon=True
                )
                process.start()

                log.info(f'Started background processing for project: {project_name}')

                return {
                    'status': 'success',
                    'message': 'Video upload successful. Processing started in background.',
                    'project': project_name
                }

            except Exception as e:
                # Cleanup on error
                shutil.rmtree(temp_dir, ignore_errors=True)
                raise

        except cherrypy.HTTPError:
            raise
        except Exception as e:
            log.error(f'Failed to process upload: {e}', exc_info=True)
            raise cherrypy.HTTPError(500, str(e))


def process_video_pipeline(workspace: str, project_name: str, project_config: dict,
                           metadata: Optional[dict], file_paths: List[tuple],
                           config: dict):
    '''
    Background worker for video processing.
    Uses built-in ytffmpeg interfaces instead of shell commands.
    '''
    from ytffmpeg.cli.new import gennew
    from ytffmpeg.cli.refresh import refresher
    from ytffmpeg.cli.build import builder

    log.info(f'Starting video pipeline for project: {project_name}')

    # Create a copy of config to avoid modifying the shared config
    worker_config = {
        'ytffmpeg': dict(config['ytffmpeg']),
        'videos': []
    }

    # Merge project-specific configuration
    if project_config and 'ytffmpeg' in project_config:
        worker_config['ytffmpeg'] = dictmerge(
            worker_config['ytffmpeg'],
            project_config['ytffmpeg']
        )

    temp_dir = None

    try:
        # Save current directory
        original_cwd = os.getcwd()

        # Create project directory
        project_path = os.path.join(workspace, project_name)
        if not os.path.exists(project_path):
            os.makedirs(project_path, exist_ok=True)

        # Change to workspace directory to run ytffmpeg commands
        os.chdir(workspace)

        # Run 'new' command to create project structure
        worker_config['ytffmpeg']['resource'] = project_name
        log.info(f'Creating project structure: {project_name}')
        result = gennew(worker_config)
        if result != 0:
            raise RuntimeError(f'Failed to create project structure (exit code: {result})')

        # Change to project directory
        os.chdir(project_path)

        # Move uploaded files to resources directory
        resources_dir = os.path.join(project_path, 'resources')
        for temp_path, save_name in file_paths:
            dest_path = os.path.join(resources_dir, save_name)
            log.info(f'Moving {save_name} to resources/')
            shutil.move(temp_path, dest_path)

        # Remember temp directory for cleanup
        if file_paths:
            temp_dir = os.path.dirname(file_paths[0][0])

        # If multiple videos, handle concatenation
        if len(file_paths) > 1:
            log.info(f'Multiple videos detected ({len(file_paths)}), concatenation mode')
            # The refresh command will handle this automatically

        # Run 'refresh' command to generate subtitles and create ytffmpeg.yml
        log.info('Running refresh to generate subtitles...')
        result = refresher(worker_config)
        if result != 0:
            log.warning(f'Refresh command returned non-zero exit code: {result}')

        # Merge metadata into generated configuration
        config_path = os.path.join(project_path, 'ytffmpeg.yml')
        if os.path.exists(config_path):
            generated_config = read_yaml(config_path)
            # Add metadata to first video if provided
            if metadata and generated_config.get('videos'):
                if 'metadata' not in generated_config['videos'][0]:
                    generated_config['videos'][0]['metadata'] = {}
                generated_config['videos'][0]['metadata'].update(metadata)

            # Merge project config
            if project_config and 'videos' in project_config:
                generated_config = dictmerge(generated_config, {'videos': project_config['videos']})

            # Save updated configuration
            write_yaml(config_path, generated_config)
            log.info('Configuration updated with metadata and project settings')

        # Run 'build' command to create final video
        log.info('Running build to create final video...')
        worker_config['ytffmpeg']['autoplay'] = False  # Disable autoplay on server
        result = builder(worker_config)
        if result != 0:
            log.warning(f'Build command returned non-zero exit code: {result}')

        # Send success notification
        try:
            send_notification(
                'INFO',
                f'ytffmpeg: {project_name} complete',
                f'Video processing completed successfully for project: {project_name}'
            )
        except Exception as notify_error:
            log.warning(f'Failed to send success notification: {notify_error}')

        log.info(f'Video pipeline completed successfully for: {project_name}')

    except Exception as e:
        log.error(f'Video pipeline failed for {project_name}: {e}', exc_info=True)

        # Send error notification
        try:
            send_notification(
                'ERROR',
                f'ytffmpeg: {project_name} failed',
                f'Video processing failed for project {project_name}: {str(e)}'
            )
        except Exception as notify_error:
            log.warning(f'Failed to send error notification: {notify_error}')

    finally:
        # Cleanup temporary directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                log.debug(f'Cleaned up temporary directory: {temp_dir}')
            except Exception as e:
                log.warning(f'Failed to cleanup temp directory {temp_dir}: {e}')

        # Restore original working directory
        try:
            os.chdir(original_cwd)
        except Exception as e:
            log.warning(f'Failed to restore original directory: {e}')


def serve(config: dict):
    '''
    Main entry point for 'ytffmpeg serve' command.
    Starts the CherryPy web server.
    '''
    # Get configuration
    workspace = config['ytffmpeg'].get('workspace', os.getcwd())
    http_port = config['ytffmpeg'].get('http_port', int(os.getenv('HTTP_PORT', '9091')))

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

    webroot = config['ytffmpeg'].get('webroot', default_webroot)
    webroot = os.path.abspath(webroot)
    config['ytffmpeg']['webroot'] = webroot

    if not os.path.exists(webroot):
        log.error(f'Webroot directory not found: {webroot}')
        log.error('Please ensure web assets are installed or specify webroot in config')
        return 1

    log.info(f'Serving static files from: {webroot}')

    # Create handlers
    page_handler = PageHandlers(config)
    api_handler = ApiHandlers(config)

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

    cherrypy.tree.mount(api_handler, '/api')

    # Server configuration
    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': http_port,
        'server.thread_pool': 10,
        'server.max_request_body_size': 5 * 1024 * 1024 * 1024,  # 5GB
        'server.socket_timeout': 600,
        'log.screen': True,
        'log.access_file': '',
        'log.error_file': ''
    })

    log.info(f'Starting ytffmpeg web server on http://0.0.0.0:{http_port}')
    log.info('Press Ctrl+C to stop')

    try:
        cherrypy.engine.start()
        cherrypy.engine.block()
    except KeyboardInterrupt:
        log.info('Shutting down server...')
        cherrypy.engine.stop()

    return 0


if __name__ == '__main__':
    # For testing
    config = {'ytffmpeg': {}}
    serve(config)
