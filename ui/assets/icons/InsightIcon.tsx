import React from 'react';

const InsightIcon = ({ className = '', size = 24 }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="M2 22h20" />
    <path d="M12 2v6l4.5-4.5" />
    <path d="M12 2v6l-4.5-4.5" />
    <path d="M12 8v14" />
    <path d="M5 10v12" />
    <path d="M19 10v12" />
  </svg>
);

export default InsightIcon;
