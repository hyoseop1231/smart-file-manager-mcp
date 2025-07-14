import React, { createContext, useContext, useState, useEffect } from 'react';
import { useQuery } from 'react-query';
import axios from 'axios';

interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  timestamp: Date;
  read: boolean;
}

interface NotificationContextType {
  notifications: Notification[];
  unreadCount: number;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  clearNotifications: () => void;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export const useNotifications = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
};

interface NotificationProviderProps {
  children: React.ReactNode;
}

export const NotificationProvider: React.FC<NotificationProviderProps> = ({ children }) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);

  // Monitor background tasks
  const { data: healthData } = useQuery(
    'health-notifications',
    () => axios.get('/health').then(res => res.data),
    { 
      refetchInterval: 30000,
      onSuccess: (data) => {
        // Check for system warnings
        if (data.status === 'warning' || data.status === 'error') {
          addNotification({
            title: 'System Alert',
            message: `System is in ${data.status} state`,
            type: 'warning',
          });
        }

        // Check for high resource usage
        if (data.performance?.system_metrics) {
          const { cpu_percent, memory_percent, disk_percent } = data.performance.system_metrics;
          
          if (cpu_percent > 80) {
            addNotification({
              title: 'High CPU Usage',
              message: `CPU usage is at ${cpu_percent}%`,
              type: 'warning',
            });
          }
          
          if (memory_percent > 85) {
            addNotification({
              title: 'High Memory Usage',
              message: `Memory usage is at ${memory_percent}%`,
              type: 'warning',
            });
          }
          
          if (disk_percent > 90) {
            addNotification({
              title: 'Low Disk Space',
              message: `Disk usage is at ${disk_percent}%`,
              type: 'error',
            });
          }
        }
      }
    }
  );

  const addNotification = (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => {
    const newNotification: Notification = {
      ...notification,
      id: Date.now().toString(),
      timestamp: new Date(),
      read: false,
    };

    setNotifications(prev => {
      // Avoid duplicate notifications
      const exists = prev.some(n => 
        n.title === notification.title && 
        n.message === notification.message &&
        new Date().getTime() - n.timestamp.getTime() < 60000 // Within 1 minute
      );
      
      if (exists) return prev;
      
      // Keep only last 50 notifications
      return [newNotification, ...prev].slice(0, 50);
    });
  };

  const markAsRead = (id: string) => {
    setNotifications(prev =>
      prev.map(notification =>
        notification.id === id ? { ...notification, read: true } : notification
      )
    );
  };

  const markAllAsRead = () => {
    setNotifications(prev =>
      prev.map(notification => ({ ...notification, read: true }))
    );
  };

  const clearNotifications = () => {
    setNotifications([]);
  };

  const unreadCount = notifications.filter(n => !n.read).length;

  // Load notifications from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('notifications');
    if (saved) {
      const parsed = JSON.parse(saved);
      setNotifications(parsed.map((n: any) => ({
        ...n,
        timestamp: new Date(n.timestamp),
      })));
    }
  }, []);

  // Save notifications to localStorage
  useEffect(() => {
    localStorage.setItem('notifications', JSON.stringify(notifications));
  }, [notifications]);

  return (
    <NotificationContext.Provider value={{
      notifications,
      unreadCount,
      markAsRead,
      markAllAsRead,
      clearNotifications,
    }}>
      {children}
    </NotificationContext.Provider>
  );
};