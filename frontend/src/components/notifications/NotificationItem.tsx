import React from "react";
import { Notification } from "../../types/notification";
import {
  UserPlusIcon,
  ArrowPathIcon,
  InformationCircleIcon,
} from "@heroicons/react/24/outline";

interface NotificationItemProps {
  notification: Notification;
  onMarkAsRead: (id: number) => void;
}

const NotificationItem: React.FC<NotificationItemProps> = ({
  notification,
  onMarkAsRead,
}) => {
  const getIcon = (type: string) => {
    switch (type) {
      case "task_assigned":
        return <UserPlusIcon className="h-5 w-5 text-blue-500" />;
      case "task_updated":
        return <ArrowPathIcon className="h-5 w-5 text-green-500" />;
      default:
        return <InformationCircleIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInMinutes = Math.floor(
      (now.getTime() - date.getTime()) / (1000 * 60)
    );

    if (diffInMinutes < 1) {
      return "Just now";
    } else if (diffInMinutes < 60) {
      return `${diffInMinutes}m ago`;
    } else if (diffInMinutes < 1440) {
      const hours = Math.floor(diffInMinutes / 60);
      return `${hours}h ago`;
    } else {
      const days = Math.floor(diffInMinutes / 1440);
      return `${days}d ago`;
    }
  };

  const handleClick = () => {
    if (!notification.is_read) {
      onMarkAsRead(notification.id);
    }
  };

  return (
    <div
      onClick={handleClick}
      className={`p-3 rounded-lg cursor-pointer transition-colors ${
        notification.is_read
          ? "bg-gray-50 hover:bg-gray-100"
          : "bg-blue-50 hover:bg-blue-100 border-l-4 border-blue-500"
      }`}
    >
      <div className="flex items-start space-x-3">
        {/* Icon */}
        <div className="flex-shrink-0 mt-0.5">{getIcon(notification.type)}</div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <p
            className={`text-sm ${
              notification.is_read
                ? "text-gray-600"
                : "text-gray-900 font-medium"
            }`}
          >
            {notification.message}
          </p>

          {/* Metadata */}
          <div className="mt-1 flex items-center space-x-2 text-xs text-gray-500">
            <span>{formatDate(notification.created_at)}</span>
            {!notification.is_read && (
              <span className="inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                New
              </span>
            )}
          </div>
        </div>

        {/* Unread Indicator */}
        {!notification.is_read && (
          <div className="flex-shrink-0">
            <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
          </div>
        )}
      </div>
    </div>
  );
};

export default NotificationItem;
