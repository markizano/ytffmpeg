"""
AWS SNS Notification Module for ytffmpeg

This module provides a singleton Notifier class that integrates with AWS SNS
to send notifications at different levels (INFO, WARNING, ERROR).

Usage:
    from ytffmpeg.notify import Notifier

    notifier = Notifier.getInstance()
    notifier.send('INFO', 'Video Processing Started', 'Processing video123.mp4')
    notifier.send('ERROR', 'Processing Failed', 'Error: File not found')
"""

import boto3
import kizano
from typing import Dict, Optional

log = kizano.getLogger(__name__)


class Notifier:
    """
    Singleton class for sending AWS SNS notifications.

    Notification Levels:
        - INFO: Status updates like video received and processing complete
        - WARNING: Currently unused
        - ERROR: Errors or exceptions during video processing
    """

    _instance: Optional['Notifier'] = None
    _topics: Dict[str, str] = {}
    _sns_client = None

    def __init__(self):
        """
        Initialize the Notifier and fetch SNS topics.

        Note: Use getInstance() instead of calling this directly.
        """
        if Notifier._instance is not None:
            raise RuntimeError("Use Notifier.getInstance() instead of direct instantiation")

        # Initialize boto3 SNS client (uses env vars or ~/.aws/ configuration)
        try:
            self._sns_client = boto3.client('sns')
            self._load_topics()
            log.info(f"Notifier initialized with topics: {list(self._topics.keys())}")
        except Exception as e:
            log.error(f"Failed to initialize SNS client: {e}")
            raise

    def _load_topics(self):
        """
        Load SNS topics from AWS and store them by notification level.

        Topics are identified by checking if the level name (INFO, WARN, ERROR)
        appears in the topic ARN.
        """
        try:
            response = self._sns_client.list_topics()
            topics = response.get('Topics', [])

            # Map topics by notification level
            for topic in topics:
                topic_arn = topic['TopicArn']

                if 'INFO' in topic_arn:
                    self._topics['INFO'] = topic_arn
                    log.debug(f"Found INFO topic: {topic_arn}")
                elif 'WARN' in topic_arn or 'WARNING' in topic_arn:
                    self._topics['WARNING'] = topic_arn
                    log.debug(f"Found WARNING topic: {topic_arn}")
                elif 'ERROR' in topic_arn:
                    self._topics['ERROR'] = topic_arn
                    log.debug(f"Found ERROR topic: {topic_arn}")

            if not self._topics:
                log.warning("No SNS topics found matching INFO, WARNING, or ERROR patterns")

        except Exception as e:
            log.error(f"Failed to load SNS topics: {e}")
            raise

    @staticmethod
    def getInstance() -> 'Notifier':
        """
        Get the singleton instance of Notifier.

        Returns:
            Notifier: The singleton Notifier instance
        """
        if Notifier._instance is None:
            Notifier._instance = Notifier()
        return Notifier._instance

    def send(self, notif_lvl: str, subject: str, message: str) -> bool:
        """
        Send a notification to the appropriate SNS topic.

        Args:
            notif_lvl: Notification level ('INFO', 'WARNING', or 'ERROR')
            subject: Email subject line (max 100 characters for SNS)
            message: Notification message body

        Returns:
            bool: True if notification was sent successfully, False otherwise

        Example:
            notifier.send('INFO', 'Video Processing Complete',
                         'Successfully processed video123.mp4')
        """
        # Normalize notification level
        notif_lvl = notif_lvl.upper()

        # Check if topic exists for this level
        if notif_lvl not in self._topics:
            log.error(f"No SNS topic found for notification level: {notif_lvl}")
            log.error(f"Available topics: {list(self._topics.keys())}")
            return False

        topic_arn = self._topics[notif_lvl]

        try:
            # Truncate subject if too long (SNS has 100 char limit)
            if len(subject) > 100:
                log.warning(f"Subject truncated from {len(subject)} to 100 characters")
                subject = subject[:97] + "..."

            # Send notification
            response = self._sns_client.publish(
                TopicArn=topic_arn,
                Subject=subject,
                Message=message
            )

            message_id = response.get('MessageId')
            log.info(f"Sent {notif_lvl} notification: {subject} (MessageId: {message_id})")
            return True

        except Exception as e:
            log.error(f"Failed to send {notif_lvl} notification: {e}")
            return False

    def get_available_levels(self) -> list:
        """
        Get list of available notification levels.

        Returns:
            list: List of available notification level names
        """
        return list(self._topics.keys())

    @classmethod
    def reset_instance(cls):
        """
        Reset the singleton instance (primarily for testing purposes).
        """
        cls._instance = None
        cls._topics = {}
        cls._sns_client = None


# Convenience function for quick access
def send_notification(notif_lvl: str, subject: str, message: str) -> bool:
    """
    Convenience function to send a notification without manually getting the instance.

    Args:
        notif_lvl: Notification level ('INFO', 'WARNING', or 'ERROR')
        subject: Email subject line
        message: Notification message body

    Returns:
        bool: True if notification was sent successfully, False otherwise

    Example:
        from ytffmpeg.notify import send_notification
        send_notification('INFO', 'Processing Complete', 'Video processed successfully')
    """
    notifier = Notifier.getInstance()
    return notifier.send(notif_lvl, subject, message)
