"""
Notification Repository

This module provides data access layer for notification operations,
implementing the repository pattern for database interactions.
"""

import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, update, and_
from sqlalchemy.exc import SQLAlchemyError
from .models import Notification

logger = logging.getLogger(__name__)


class NotificationRepository:
    """Repository class for notification database operations."""
    
    def __init__(self, session: Session):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy session
        """
        self.session = session
    def create_notification(self, notification: Notification) -> Notification:
        """
        Create a new notification in the database.
        
        Args:
            notification: Notification instance to create
            
        Returns:
            Notification: Created notification with assigned ID
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            self.session.add(notification)
            self.session.commit()
            logger.info(f"Created notification {notification.id} for user {notification.user_id}")
            return notification
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error creating notification: {e}")
            raise
    def get_notification_by_id(self, notification_id: int) -> Optional[Notification]:
        """
        Get a notification by its ID.
        
        Args:
            notification_id: ID of the notification to retrieve
            
        Returns:
            Optional[Notification]: Notification if found, None otherwise
        """
        try:
            logger.debug(f"Searching for notification with ID: {notification_id}")
            result = self.session.execute(
                select(Notification).where(Notification.id == notification_id)
            )
            notification = result.scalar_one_or_none()
            if notification:
                logger.debug(f"Retrieved notification {notification_id}")
            else:
                logger.debug(f"No notification found with ID {notification_id}")
            return notification
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving notification {notification_id}: {e}")
            raise
    def get_user_notifications(
        self, 
        user_id: int, 
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Notification]:
        """
        Get notifications for a specific user.
        
        Args:
            user_id: ID of the user
            unread_only: If True, only return unread notifications
            limit: Maximum number of notifications to return
            
        Returns:
            List[Notification]: List of user's notifications
        """
        try:
            query = select(Notification).where(Notification.user_id == user_id)
            
            if unread_only:
                query = query.where(Notification.is_read == False)
            
            query = query.order_by(Notification.created_at.desc()).limit(limit)
            
            result = self.session.execute(query)
            notifications = result.scalars().all()
            
            logger.debug(f"Retrieved {len(notifications)} notifications for user {user_id}")
            return list(notifications)
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving notifications for user {user_id}: {e}")
            raise
    def mark_notification_as_read(self, notification_id: int) -> bool:
        """
        Mark a notification as read.
        
        Args:
            notification_id: ID of the notification to mark as read
            
        Returns:
            bool: True if notification was updated, False if not found
        """
        try:
            result = self.session.execute(
                update(Notification)
                .where(Notification.id == notification_id)
                .values(is_read=True)
            )
            self.session.commit()
            
            updated = result.rowcount > 0
            if updated:
                logger.info(f"Marked notification {notification_id} as read")
            else:
                logger.warning(f"Notification {notification_id} not found for marking as read")
            
            return updated
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error marking notification {notification_id} as read: {e}")
            raise
    def mark_user_notifications_as_read(self, user_id: int) -> int:
        """
        Mark all unread notifications for a user as read.
        
        Args:
            user_id: ID of the user
            
        Returns:
            int: Number of notifications marked as read
        """
        try:
            result = self.session.execute(
                update(Notification)
                .where(and_(Notification.user_id == user_id, Notification.is_read == False))
                .values(is_read=True)
            )
            self.session.commit()
            
            count = result.rowcount
            logger.info(f"Marked {count} notifications as read for user {user_id}")
            return count
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error marking notifications as read for user {user_id}: {e}")
            raise
    def delete_notification(self, notification_id: int) -> bool:
        """
        Delete a notification by ID.
        
        Args:
            notification_id: ID of the notification to delete
            
        Returns:
            bool: True if notification was deleted, False if not found
        """
        try:
            notification = self.get_notification_by_id(notification_id)
            if notification:
                self.session.delete(notification)
                self.session.commit()
                logger.info(f"Deleted notification {notification_id}")
                return True
            else:
                logger.warning(f"Notification {notification_id} not found for deletion")
                return False
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error deleting notification {notification_id}: {e}")
            raise
    def get_notifications_by_task(self, task_id: str) -> List[Notification]:
        """
        Get all notifications related to a specific task.
        
        Args:
            task_id: ID of the task
            
        Returns:
            List[Notification]: List of notifications for the task
        """
        try:
            result = self.session.execute(
                select(Notification)
                .where(Notification.task_id == task_id)
                .order_by(Notification.created_at.desc())
            )
            notifications = result.scalars().all()
            
            logger.debug(f"Retrieved {len(notifications)} notifications for task {task_id}")
            return list(notifications)
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving notifications for task {task_id}: {e}")
            raise
