import create from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { InsightData, UserSettings, NotificationType } from '@/types';

interface AppState {
  insights: InsightData[];
  settings: UserSettings;
  notifications: NotificationType[];
  loading: boolean;
  error: string | null;
  
  // Actions
  setInsights: (insights: InsightData[]) => void;
  updateSettings: (settings: Partial<UserSettings>) => void;
  addNotification: (notification: NotificationType) => void;
  removeNotification: (id: string) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

const useStore = create<AppState>()(
  devtools(
    persist(
      (set) => ({
        insights: [],
        settings: {
          theme: 'light',
          notifications: true,
          dataCollection: true,
        },
        notifications: [],
        loading: false,
        error: null,

        setInsights: (insights) => set({ insights }),
        updateSettings: (settings) => 
          set((state) => ({ 
            settings: { ...state.settings, ...settings } 
          })),
        addNotification: (notification) =>
          set((state) => ({
            notifications: [...state.notifications, notification],
          })),
        removeNotification: (id) =>
          set((state) => ({
            notifications: state.notifications.filter((n) => n.id !== id),
          })),
        setLoading: (loading) => set({ loading }),
        setError: (error) => set({ error }),
      }),
      {
        name: 'clarity-storage',
      }
    )
  )
);

export default useStore;
