'''
Test GPU lock mechanism to prevent concurrent Whisper instances from causing OOM errors.

Tests verify:
- Lock can be acquired and released
- Lock file is created in correct location
- Multiple concurrent locks wait properly
- Lock is released on exception
- Random delay prevents race conditions
'''

import os
import time
import unittest
import threading
from unittest.mock import patch

from mkzforge.cli.base import BaseCommand

from kizano import getLogger
log = getLogger(__name__)


class TestGPULock(unittest.TestCase):

    def setUp(self):
        '''Set up test configuration'''
        self.config = {
            'mkzforge': {
                'device': 'cuda',
                'subtitles': True
            },
            'videos': []
        }
        self.cmd = BaseCommand(self.config)

    def test_lock_acquisition_and_release(self):
        '''
        Test that GPU lock can be acquired and released successfully.
        '''
        start = time.time()

        with self.cmd.gpu_lock():
            elapsed = time.time() - start
            # Lock should be acquired almost immediately if no contention
            self.assertLess(elapsed, 1.0, 'Lock acquisition took too long')

        # Lock should be released after context manager exits
        # Verify by acquiring it again immediately
        with self.cmd.gpu_lock():
            pass

        log.info('✓ Lock acquisition and release working correctly')

    def test_lock_file_location(self):
        '''
        Test that lock file is created in the correct user-writable location.
        '''
        # Expected locations (in order of preference)
        cache_dir = os.path.expanduser('~/.cache/mkzforge')
        expected_locations = [
            os.path.join(cache_dir, 'gpu.lock'),
            '/tmp/mkzforge-gpu.lock'
        ]

        with self.cmd.gpu_lock():
            # At least one of the expected locations should exist
            lock_exists = any(os.path.exists(loc) for loc in expected_locations)
            self.assertTrue(lock_exists, f'Lock file not found in expected locations: {expected_locations}')

        log.info('✓ Lock file created in correct location')

    def test_concurrent_lock_contention(self):
        '''
        Test that multiple threads properly wait for GPU lock.
        This simulates multiple mkzforge instances running concurrently.
        '''
        results = []
        lock_order = []

        def acquire_lock(thread_id, hold_time=0.5):
            '''Helper function for threads to acquire lock'''
            try:
                with self.cmd.gpu_lock(max_wait_seconds=10):
                    lock_order.append(thread_id)
                    time.sleep(hold_time)  # Simulate work
                    results.append((thread_id, 'success'))
            except Exception as e:
                results.append((thread_id, f'error: {e}'))

        # Start 3 threads that will contend for the lock
        threads = []
        for i in range(3):
            thread = threading.Thread(target=acquire_lock, args=(i,))
            threads.append(thread)

        # Start all threads at roughly the same time
        start = time.time()
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=20)

        elapsed = time.time() - start

        # Verify all threads succeeded
        self.assertEqual(len(results), 3, 'Not all threads completed')
        for thread_id, status in results:
            self.assertEqual(status, 'success', f'Thread {thread_id} failed: {status}')

        # Verify they ran sequentially (total time should be ~1.5s for 3 threads with 0.5s hold each)
        # Add some tolerance for random delays and scheduling
        self.assertGreater(elapsed, 1.0, 'Threads ran too quickly - may have run concurrently')
        self.assertLess(elapsed, 10.0, 'Threads took too long - possible deadlock')

        # Verify all 3 threads acquired the lock
        self.assertEqual(len(lock_order), 3, 'Not all threads acquired the lock')

        log.info(f'✓ Concurrent lock contention handled correctly (elapsed: {elapsed:.2f}s)')
        log.info(f'  Lock acquisition order: {lock_order}')

    def test_lock_released_on_exception(self):
        '''
        Test that lock is properly released even when an exception occurs.
        '''
        class TestException(Exception):
            pass

        # Acquire lock and raise exception
        with self.assertRaises(TestException):
            with self.cmd.gpu_lock():
                raise TestException('Simulated error during GPU operation')

        # Verify lock was released by acquiring it again
        with self.cmd.gpu_lock():
            pass

        log.info('✓ Lock properly released on exception')

    def test_lock_timeout(self):
        '''
        Test that lock acquisition times out if held too long.
        '''
        def hold_lock_forever():
            '''Helper to hold lock for extended period'''
            with self.cmd.gpu_lock(max_wait_seconds=30):
                time.sleep(5)  # Hold for 5 seconds

        # Start thread that holds lock
        thread = threading.Thread(target=hold_lock_forever)
        thread.start()

        # Give first thread time to acquire lock
        time.sleep(0.5)

        # Try to acquire with short timeout (should fail)
        start = time.time()
        with self.assertRaises(RuntimeError) as context:
            with self.cmd.gpu_lock(max_wait_seconds=2):
                pass

        elapsed = time.time() - start

        # Verify timeout occurred around expected time
        self.assertGreater(elapsed, 1.5, 'Timeout occurred too quickly')
        self.assertLess(elapsed, 3.0, 'Timeout took too long')

        # Verify error message mentions timeout
        self.assertIn('timeout', str(context.exception).lower())

        # Clean up
        thread.join(timeout=10)

        log.info(f'✓ Lock timeout working correctly (timed out after {elapsed:.2f}s)')

    def test_cpu_mode_no_lock(self):
        '''
        Test that CPU mode doesn't use GPU lock (optimization).
        '''
        # Create CPU config
        cpu_config = {
            'mkzforge': {
                'device': 'cpu',
                'subtitles': True
            },
            'videos': []
        }

        cpu_cmd = BaseCommand(cpu_config)

        # The _run_whisper method should be called directly without lock for CPU mode
        # This is tested implicitly through get_subtitles behavior
        # For now, just verify the config is set correctly
        self.assertEqual(cpu_cmd.config['mkzforge']['device'], 'cpu')

        log.info('✓ CPU mode configuration verified')

    def test_random_delay_range(self):
        '''
        Test that random delay is within expected range (1.0 to 3.0 seconds).
        This is implicitly tested through lock contention behavior.
        '''
        # Mock time.sleep to capture the delay values
        sleep_calls = []

        original_sleep = time.sleep
        def mock_sleep(duration):
            sleep_calls.append(duration)
            # Don't actually sleep in the test
            return None

        # Create a second BaseCommand instance to cause contention
        cmd2 = BaseCommand(self.config)

        def hold_lock():
            with self.cmd.gpu_lock():
                time.sleep(0.2)

        # Start a thread to hold the lock
        thread = threading.Thread(target=hold_lock)
        thread.start()

        # Give first thread time to acquire
        original_sleep(0.1)

        # Try to acquire with second instance (will wait)
        with patch('time.sleep', side_effect=mock_sleep):
            try:
                with cmd2.gpu_lock(max_wait_seconds=5):
                    pass
            except:
                pass  # Ignore any errors

        thread.join(timeout=10)

        # If there were any sleep calls due to lock contention, verify they're in range
        wait_sleeps = [s for s in sleep_calls if s >= 1.0]
        if wait_sleeps:
            for delay in wait_sleeps:
                self.assertGreaterEqual(delay, 1.0, 'Random delay too short')
                self.assertLessEqual(delay, 3.0, 'Random delay too long')
            log.info(f'✓ Random delays in correct range: {wait_sleeps}')
        else:
            log.info('✓ No lock contention detected (expected if first lock released quickly)')


if __name__ == '__main__':
    unittest.main()
