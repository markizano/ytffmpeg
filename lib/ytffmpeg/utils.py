'''
Ancilary utility functions to help processing.
'''
import os
import time
import subprocess
import fcntl
import random
from contextlib import contextmanager
from kizano.utils import read_yaml, write_yaml

from ytffmpeg import getLogger, notify
log = getLogger(__name__)

_gpu_vram_mb = None

def filename(path: str) -> str:
    '''
    Gets the filename without the extension or leading path.
    '''
    return os.path.splitext(os.path.basename(path))[0]

def hasVideo(videos: list[dict], vid: str) -> bool:
    '''
    Check the list of videos. If any of the input videos match the resource using filename() then return True.
    '''
    for video in videos:
        for inputVid in video['input']:
            if inputVid['i'] == vid:
                return True
    return False

def load() -> dict:
    '''
    Read `ytffmpeg.yml` config into memory.
    '''
    log.info('Reading ytffmpeg.yml config...')
    return read_yaml('ytffmpeg.yml')

def save(videos: list[dict]) -> None:
    '''
    Write ytffmpeg.yml updates to disk.
    '''
    log.info('Writing out ytffmpeg.yml configuration...')
    write_yaml('ytffmpeg.yml', { 'videos': videos })
    log.info('Done writing out ytffmpeg.yml configuration!')

def get_gpu_vram_mb() -> int:
    '''
    Detect available GPU VRAM in megabytes.
    Returns 0 if no GPU detected or on error.
    '''
    global _gpu_vram_mb
    if _gpu_vram_mb is not None:
        return _gpu_vram_mb

    # Try nvidia-smi first
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=memory.total', '--format=csv,noheader,nounits'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            # Get first GPU's VRAM (in MB)
            vram_mb = int(result.stdout.strip().split('\n')[0])
            _gpu_vram_mb = vram_mb
            log.info(f'Detected GPU with {vram_mb} MB VRAM via nvidia-smi')
            return vram_mb
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError, IndexError) as e:
        log.debug(f'nvidia-smi detection failed: {e}')

    # Try torch if available
    try:
        import torch
        if torch.cuda.is_available():
            vram_bytes = torch.cuda.get_device_properties(0).total_memory
            vram_mb = int(vram_bytes / (1024 * 1024))
            _gpu_vram_mb = vram_mb
            log.info(f'Detected GPU with {vram_mb} MB VRAM via torch')
            return vram_mb
    except (ImportError, RuntimeError) as e:
        log.debug(f'torch detection failed: {e}')

    # No GPU detected
    log.warning('No GPU detected, will use CPU or smaller models')
    _gpu_vram_mb = 0
    return 0

@contextmanager
def video_processing_lock(self, operation: str):
    '''
    Context manager for acquiring an exclusive lock for video processing operations.

    Prevents multiple refresh or build processes from running simultaneously.
    Uses POSIX file locking (fcntl.flock) with retry logic and random delays to avoid race conditions.

    Args:
        operation: The operation name (e.g., 'refresh', 'build') for logging purposes

    Usage:
        with self.video_processing_lock('refresh'):
            # Run refresh operation
            self.process_videos()
    '''
    lock_file = None
    lock_acquired = False
    start_time = time.time()

    try:
        # Create lock file if it doesn't exist
        lock_dir = os.path.dirname(self.lockfile)
        if lock_dir and not os.path.exists(lock_dir):
            try:
                os.makedirs(lock_dir, mode=0o755, exist_ok=True)
            except (OSError, PermissionError) as e:
                log.error(f'Failed to create lockfile directory {lock_dir}: {e}')
                raise

        # Open/create lock file
        lock_file = open(self.lockfile, 'w')

        # Try to acquire lock with retry logic
        while True:
            try:
                # Try non-blocking lock first
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                lock_acquired = True

                # Write current PID to lockfile
                lock_file.write(str(os.getpid()))
                lock_file.flush()

                log.info(f'Acquired video processing lock for {operation}: {self.lockfile} (PID: {os.getpid()})')
                break
            except IOError:
                # Lock is held by another process
                elapsed = time.time() - start_time
                if elapsed >= self.lockfile_timeout:
                    error_msg = (
                        f'Failed to acquire video processing lock for {operation} after {elapsed:.1f}s '
                        f'(timeout: {self.lockfile_timeout}s). '
                        f'Another ytffmpeg process may be stuck or still running. '
                        f'Check lockfile: {self.lockfile}'
                    )
                    log.error(error_msg)

                    # Send ERROR notification
                    try:
                        notify.send_notification(
                            'ERROR',
                            f'ytffmpeg {operation} lock timeout',
                            error_msg
                        )
                    except Exception as notify_error:
                        log.warning(f'Failed to send notification: {notify_error}')

                    raise RuntimeError(error_msg)

                # Wait 1 second + random 0.1-1.0s to mitigate race conditions
                wait_time = 1.0 + random.uniform(0.1, 1.0)
                log.warning(
                    f'Video processing lock for {operation} is held by another process. '
                    f'Waiting {wait_time:.2f}s... (elapsed: {elapsed:.1f}s/{self.lockfile_timeout}s)'
                )
                time.sleep(wait_time)

        # Yield control to caller (lock is held)
        yield

    finally:
        # Always release lock and close file
        if lock_file:
            if lock_acquired:
                try:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                    log.info(f'Released video processing lock for {operation}: {self.lockfile}')
                except Exception as e:
                    log.warning(f'Error releasing video processing lock: {e}')

            try:
                lock_file.truncate(0)
                lock_file.close()
            except Exception as e:
                log.warning(f'Error closing lock file: {e}')
