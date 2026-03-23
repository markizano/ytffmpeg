'''
Google Drive integration for mkzforge.
Handles OAuth2 authentication and file operations using the Drive v3 API.
'''

import os
import json
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from mkzforge import getLogger

log = getLogger(__name__)

TOKEN_PATH = os.path.expanduser('~/.config/mkzforge/grive_token.json')
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']


def _load_token() -> dict:
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'r') as f:
            return json.load(f)
    return {}


def _save_token(data: dict) -> None:
    os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
    with open(TOKEN_PATH, 'w') as f:
        json.dump(data, f)
    os.chmod(TOKEN_PATH, 0o600)


def _get_credentials():
    token_data = _load_token()
    if not token_data.get('token'):
        return None
    return Credentials(
        token=token_data.get('token'),
        refresh_token=token_data.get('refresh_token'),
        token_uri=token_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
        client_id=token_data.get('client_id'),
        client_secret=token_data.get('client_secret'),
        scopes=token_data.get('scopes', SCOPES),
    )


def is_authenticated() -> bool:
    '''Returns True if a valid, non-expired token exists at TOKEN_PATH.'''
    log.info('Checking Google Drive authentication status.')
    if not os.path.exists(TOKEN_PATH):
        log.info('No token file found — not authenticated.')
        return False
    creds = _get_credentials()
    if creds is None:
        log.info('Token data missing — not authenticated.')
        return False
    if creds.valid:
        log.info('Token is valid.')
        return True
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            token_data = _load_token()
            token_data['token'] = creds.token
            _save_token(token_data)
            log.info('Token refreshed successfully.')
            return True
        except Exception as e:
            log.warning(f'Token refresh failed: {e}')
            return False
    log.info('Token is invalid and cannot be refreshed.')
    return False


def get_auth_url(cfg: dict, redirect_uri: str) -> str:
    '''Starts the OAuth2 flow and returns the authorization URL.

    google-auth-oauthlib 1.3+ defaults autogenerate_code_verifier=True, so a
    PKCE code_challenge is included in the authorization URL.  The matching
    code_verifier is persisted in the token file under _pending_code_verifier
    so that handle_oauth_callback can supply the same one when exchanging the
    code — failing to do so causes Google to return invalid_grant.
    '''
    log.info(f'Building OAuth2 authorization URL with redirect_uri={redirect_uri}')
    client_config = {
        'web': {
            'client_id': cfg.get('google', {}).get('client_id', ''),
            'client_secret': cfg.get('google', {}).get('client_secret', ''),
            'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
            'token_uri': 'https://oauth2.googleapis.com/token',
            'redirect_uris': [redirect_uri],
        }
    }
    flow = Flow.from_client_config(client_config, scopes=SCOPES)
    flow.redirect_uri = redirect_uri
    auth_url, _state = flow.authorization_url(access_type='offline', prompt='consent')

    # Persist the PKCE code_verifier so the callback can present the same one.
    token_data = _load_token()
    token_data['_pending_code_verifier'] = flow.code_verifier
    _save_token(token_data)

    log.info('OAuth2 authorization URL generated.')
    return auth_url


def handle_oauth_callback(cfg: dict, authorization_response: str, redirect_uri: str) -> None:
    '''Exchanges the full OAuth2 authorization response URL for credentials and stores the token.

    `authorization_response` must be the complete redirect URL including all query
    parameters (state, code, scope, iss, etc.) that Google appended.

    The PKCE code_verifier stored by get_auth_url is read back and passed to
    Flow.from_client_config so fetch_token sends the matching verifier — without
    it Google returns (invalid_grant) Missing code verifier.
    '''
    log.info(f'Exchanging OAuth2 authorization response for credentials, redirect_uri={redirect_uri}')
    # oauthlib requires HTTPS by default; allow HTTP for private LAN deployments.
    if redirect_uri.startswith('http://'):
        os.environ.setdefault('OAUTHLIB_INSECURE_TRANSPORT', '1')
    client_config = {
        'web': {
            'client_id': cfg.get('google', {}).get('client_id', ''),
            'client_secret': cfg.get('google', {}).get('client_secret', ''),
            'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
            'token_uri': 'https://oauth2.googleapis.com/token',
            'redirect_uris': [redirect_uri],
        }
    }
    # Restore the PKCE code_verifier saved during get_auth_url.
    token_data = _load_token()
    code_verifier = token_data.pop('_pending_code_verifier', None)
    log.info(f'PKCE code_verifier present: {code_verifier is not None}')

    flow = Flow.from_client_config(
        client_config, scopes=SCOPES, code_verifier=code_verifier
    )
    flow.redirect_uri = redirect_uri
    flow.fetch_token(authorization_response=authorization_response)
    creds = flow.credentials
    token_data.update({
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': list(creds.scopes) if creds.scopes else SCOPES,
    })
    _save_token(token_data)
    log.info('OAuth2 credentials saved to token file.')


def list_folder(cfg: dict) -> list:
    '''Lists video files in the configured Google Drive folder.

    Uses cfg['google']['folder'] as the logical path, caches the resolved
    folder_id in the token file to avoid repeated API lookups.
    Returns [{id, name, size, mimeType, modifiedTime}] for video/* files only.
    '''

    folder_path = cfg.get('google', {}).get('folder', 'mkzforge/input')
    log.info(f'Listing Google Drive folder: {folder_path}')

    creds = _get_credentials()
    if creds is None:
        raise RuntimeError('Not authenticated with Google Drive.')

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_data = _load_token()
        token_data['token'] = creds.token
        _save_token(token_data)

    service = build('drive', 'v3', credentials=creds)

    token_data = _load_token()
    folder_id = token_data.get('folder_id')
    cached_path = token_data.get('folder_path')

    if not folder_id or cached_path != folder_path:
        log.info(f'Resolving folder path to Drive ID: {folder_path}')
        folder_id = _resolve_folder_path(service, folder_path)
        token_data['folder_id'] = folder_id
        token_data['folder_path'] = folder_path
        _save_token(token_data)
        log.info(f'Resolved folder ID: {folder_id}')

    results = service.files().list(
        q=f"'{folder_id}' in parents and mimeType contains 'video/' and trashed=false",
        fields='files(id, name, size, mimeType, modifiedTime)',
        pageSize=100,
    ).execute()

    files = results.get('files', [])
    log.info(f'Found {len(files)} video file(s) in Drive folder.')
    return files


def _resolve_folder_path(service, folder_path: str) -> str:
    '''Resolves a slash-separated path string to a Google Drive folder ID.'''
    parts = [p for p in folder_path.strip('/').split('/') if p]
    parent_id = 'root'
    for part in parts:
        query = (
            f"name='{part}' and '{parent_id}' in parents"
            " and mimeType='application/vnd.google-apps.folder' and trashed=false"
        )
        results = service.files().list(q=query, fields='files(id, name)').execute()
        folders = results.get('files', [])
        if not folders:
            raise RuntimeError(f"Folder segment not found: '{part}' in path '{folder_path}'")
        parent_id = folders[0]['id']
    return parent_id


def download_file(file_id: str, destination: str) -> str:
    '''Streams a file from Google Drive to destination using MediaIoBaseDownload.

    Returns the destination path on success. Logs progress and a final
    "Saved from GDrive: {path} ({size} bytes)" line on completion.
    '''
    log.info(f'Downloading GDrive file_id={file_id} to {destination}')
    creds = _get_credentials()
    if creds is None:
        raise RuntimeError('Not authenticated with Google Drive.')

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_data = _load_token()
        token_data['token'] = creds.token
        _save_token(token_data)

    service = build('drive', 'v3', credentials=creds)
    request = service.files().get_media(fileId=file_id)

    dest_dir = os.path.dirname(destination)
    if dest_dir:
        os.makedirs(dest_dir, exist_ok=True)

    with open(destination, 'wb') as fd:
        downloader = MediaIoBaseDownload(fd, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                log.info(f'GDrive download {file_id}: {int(status.progress() * 100)}%')

    size = os.path.getsize(destination)
    log.info(f'Saved from GDrive: {destination} ({size} bytes)')
    return destination
