import React from "react";
import { Notification } from "../../types/notification";
import {
  UserPlusIcon,
  ArrowPathIcon,
  InformationCircleIcon,
} from "@heroicons/react/24/outline";
import clsx from "clsx";

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
        return <UserPlusIcon className="h-5 w-5 text-blue-400" />;
      case "task_updated":
        return <ArrowPathIcon className="h-5 w-5 text-green-400" />;
      default:
        return <InformationCircleIcon className="h-5 w-5 text-gray-400" />;
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
      className={clsx(
        "p-4 cursor-pointer transition-colors border-l-2",
        notification.is_read
          ? "bg-transparent border-transparent hover:bg-white/5 opacity-60 hover:opacity-100"
          : "bg-primary/5 border-primary hover:bg-primary/10"
      )}
    >
      <div className="flex items-start space-x-3">
        {/* Icon */}
        <div className="flex-shrink-0 mt-0.5 opacity-80">{getIcon(notification.type)}</div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <p
            className={clsx(
              "text-sm mb-1",
              notification.is_read ? "text-gray-400" : "text-white font-medium"
            )}
          >
            {notification.message}
          </p>

          {/* Metadata */}
          <div className="flex items-center space-x-2 text-xs text-gray-500">
            <span>{formatDate(notification.created_at)}</span>
            {!notification.is_read && (
              <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default NotificationItem;
