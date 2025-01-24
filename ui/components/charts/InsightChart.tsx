import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import { InsightData } from '@/types';

interface InsightChartProps {
  data: InsightData[];
  width?: number;
  height?: number;
}

const InsightChart: React.FC<InsightChartProps> = ({ 
  data,
  width = 800,
  height = 400
}) => {
  return (
    <div className="p-4 bg-white rounded-lg shadow">
      <LineChart width={width} height={height} data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="timestamp" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Line 
          type="monotone" 
          dataKey="productivity" 
          stroke="#8884d8" 
          activeDot={{ r: 8 }}
        />
        <Line 
          type="monotone" 
          dataKey="focus" 
          stroke="#82ca9d" 
        />
      </LineChart>
    </div>
  );
};

export default InsightChart;
