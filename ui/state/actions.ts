import { InsightData, UserSettings } from '@/types';
import { api } from '@/utils/api';

export const fetchInsights = async (startDate?: Date, endDate?: Date) => {
  try {
    const response = await api.get('/insights', {
      params: { startDate, endDate },
    });
    return response.data;
  } catch (error) {
    throw new Error('Failed to fetch insights');
  }
};

export const updateUserSettings = async (settings: Partial<UserSettings>) => {
  try {
    const response = await api.patch('/settings', settings);
    return response.data;
  } catch (error) {
    throw new Error('Failed to update settings');
  }
};

export const generateInsightReport = async (insightId: string) => {
  try {
    const response = await api.post(`/insights/${insightId}/report`);
    return response.data;
  } catch (error) {
    throw new Error('Failed to generate report');
  }
};

export const exportData = async (format: 'csv' | 'json', dateRange?: { start: Date; end: Date }) => {
  try {
    const response = await api.get('/export', {
      params: { format, ...dateRange },
      responseType: 'blob',
    });
    return response.data;
  } catch (error) {
    throw new Error('Failed to export data');
  }
};
