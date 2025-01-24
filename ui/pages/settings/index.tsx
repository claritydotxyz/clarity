import React from 'react';
import { Header } from '@/components/shared';
import { useStore } from '@/state/store';
import { updateUserSettings } from '@/state/actions';

const SettingsPage: React.FC = () => {
  const { settings, loading } = useStore();

  const handleSettingChange = async (key: string, value: any) => {
    try {
      await updateUserSettings({ [key]: value });
    } catch (error) {
      console.error('Failed to update settings:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <Header />
      <main className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-8">Settings</h1>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">General Settings</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Theme
              </label>
              <select
                className="mt-1 block w-full rounded-md border-gray-300"
                value={settings.theme}
                onChange={(e) => handleSettingChange('theme', e.target.value)}
              >
                <option value="light">Light</option>
                <option value="dark">Dark</option>
                <option value="system">System</option>
              </select>
            </div>

            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  className="rounded border-gray-300"
                  checked={settings.notifications}
                  onChange={(e) => handleSettingChange('notifications', e.target.checked)}
                />
                <span className="ml-2">Enable notifications</span>
              </label>
            </div>

            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  className="rounded border-gray-300"
                  checked={settings.dataCollection}
                  onChange={(e) => handleSettingChange('dataCollection', e.target.checked)}
                />
                <span className="ml-2">Enable data collection</span>
              </label>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6 mt-6">
          <h2 className="text-xl font-semibold mb-4">Integrations</h2>
          <div className="space-y-4">
            {/* Integration settings */}
            {Object.entries(settings.integrations || {}).map(([name, enabled]) => (
              <div key={name}>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    className="rounded border-gray-300"
                    checked={enabled}
                    onChange={(e) => 
                      handleSettingChange(`integrations.${name}`, e.target.checked)
                    }
                  />
                  <span className="ml-2">Enable {name}</span>
                </label>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
};

export default SettingsPage;
