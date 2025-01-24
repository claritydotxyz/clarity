import React from 'react';
import { DashboardLayout } from '@/components/layouts';
import { InsightPanel, ActivityFeed, ProductivityChart } from '@/components/dashboard';
import { useStore } from '@/state/store';
import { fetchInsights } from '@/state/actions';

const DashboardPage: React.FC = () => {
    const { insights, loading } = useStore();

    React.useEffect(() => {
        fetchInsights();
    }, []);

    if (loading) return <div>Loading...</div>;

    return (
        <DashboardLayout>
            <div className="grid grid-cols-12 gap-6">
                <div className="col-span-8">
                    <ProductivityChart data={insights} />
                    <InsightPanel insights={insights} />
                </div>
                <div className="col-span-4">
                    <ActivityFeed />
                </div>
            </div>
        </DashboardLayout>
    );
};

export default DashboardPage;
