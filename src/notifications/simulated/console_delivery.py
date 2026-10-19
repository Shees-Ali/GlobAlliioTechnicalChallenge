import logging

from notifications.core.notification import Notification

logger = logging.getLogger("uvicorn.error")


class ConsoleDelivery:
    """Placeholder delivery that logs each notification. Feature 003 replaces it with the real simulated delivery."""

    def deliver(self, notification: Notification, token: str | None) -> None:
        logger.info(
            "deliver to player %s (token=%s) [%s] %s",
            notification.recipient_id,
            token,
            notification.category.value,
            notification.message,
        )
