import React from 'react';
import { InsightData } from '@/types';
import { Chart } from '@/components/charts';
import { formatDate } from '@/utils/helpers/formatting';

interface InsightCardProps {
  insight: InsightData;
}

const InsightCard: React.FC<InsightCardProps> = ({ insight }) => {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-lg font-semibold">{insight.title}</h3>
        <span className="text-sm text-gray-500">
          {formatDate(insight.timestamp)}
        </span>
      </div>

      <p className="text-gray-600 mb-4">{insight.description}</p>

      {insight.data && (
        <div className="mb-4">
          <Chart data={insight.data} />
        </div>
      )}

      <div className="flex justify-between items-center">
        <span className={`text-sm ${getScoreColor(insight.score)}`}>
          Score: {insight.score}
        </span>
        <button className="text-blue-500 hover:text-blue-600">
          View Details
        </button>
      </div>
    </div>
  );
};

const getScoreColor = (score: number): string => {
  if (score >= 0.8) return 'text-green-500';
  if (score >= 0.6) return 'text-yellow-500';
  return 'text-red-500';
};

export default InsightCard;
