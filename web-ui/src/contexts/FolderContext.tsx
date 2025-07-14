import React, { createContext, useContext, useState, useEffect } from 'react';

interface WatchedFolder {
  id: string;
  path: string;
  name: string;
  enabled: boolean;
}

interface FolderContextType {
  watchedFolders: WatchedFolder[];
  setWatchedFolders: React.Dispatch<React.SetStateAction<WatchedFolder[]>>;
  getEnabledFolders: () => WatchedFolder[];
  toggleFolder: (folderId: string) => void;
  addFolder: (folder: Omit<WatchedFolder, 'id'>) => void;
  removeFolder: (folderId: string) => void;
}

const FolderContext = createContext<FolderContextType | undefined>(undefined);

export const useFolders = () => {
  const context = useContext(FolderContext);
  if (!context) {
    throw new Error('useFolders must be used within a FolderProvider');
  }
  return context;
};

interface FolderProviderProps {
  children: React.ReactNode;
}

const defaultFolders: WatchedFolder[] = [
  { id: '1', path: '/watch_directories/Desktop', name: 'Desktop', enabled: true },
  { id: '2', path: '/watch_directories/Documents', name: 'Documents', enabled: true },
  { id: '3', path: '/watch_directories/Downloads', name: 'Downloads', enabled: true },
  { id: '4', path: '/watch_directories/Pictures', name: 'Pictures', enabled: true },
  { id: '5', path: '/watch_directories/Movies', name: 'Movies', enabled: false },
  { id: '6', path: '/watch_directories/Music', name: 'Music', enabled: false },
];

export const FolderProvider: React.FC<FolderProviderProps> = ({ children }) => {
  const [watchedFolders, setWatchedFolders] = useState<WatchedFolder[]>(() => {
    const saved = localStorage.getItem('watchedFolders');
    return saved ? JSON.parse(saved) : defaultFolders;
  });

  useEffect(() => {
    localStorage.setItem('watchedFolders', JSON.stringify(watchedFolders));
  }, [watchedFolders]);

  const getEnabledFolders = () => {
    return watchedFolders.filter(folder => folder.enabled);
  };

  const toggleFolder = (folderId: string) => {
    setWatchedFolders(prev =>
      prev.map(folder =>
        folder.id === folderId ? { ...folder, enabled: !folder.enabled } : folder
      )
    );
  };

  const addFolder = (folder: Omit<WatchedFolder, 'id'>) => {
    const newFolder: WatchedFolder = {
      ...folder,
      id: Date.now().toString(),
    };
    setWatchedFolders(prev => [...prev, newFolder]);
  };

  const removeFolder = (folderId: string) => {
    setWatchedFolders(prev => prev.filter(folder => folder.id !== folderId));
  };

  return (
    <FolderContext.Provider value={{
      watchedFolders,
      setWatchedFolders,
      getEnabledFolders,
      toggleFolder,
      addFolder,
      removeFolder,
    }}>
      {children}
    </FolderContext.Provider>
  );
};