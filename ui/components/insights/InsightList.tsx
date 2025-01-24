import React from 'react';
import { InsightCard } from './InsightCard';
import { InsightData } from '@/types';

interface InsightListProps {
  insights: InsightData[];
}

const InsightList: React.FC<InsightListProps> = ({ insights }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {insights.map((insight) => (
        <InsightCard key={insight.id} insight={insight} />
      ))}
    </div>
  );
};

export default InsightList;
