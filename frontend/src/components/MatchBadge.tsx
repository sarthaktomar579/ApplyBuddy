import React from 'react';

interface MatchBadgeProps {
  score: number;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

export const MatchBadge: React.FC<MatchBadgeProps> = ({ score, size = 'md', showLabel = true }) => {
  let colorClasses = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
  let badgeText = 'High Match';

  if (score < 60) {
    colorClasses = 'bg-amber-500/10 text-amber-400 border-amber-500/30';
    badgeText = 'Low Match';
  } else if (score < 75) {
    colorClasses = 'bg-blue-500/10 text-blue-400 border-blue-500/30';
    badgeText = 'Good Match';
  }

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-2.5 py-1',
    lg: 'text-base px-3.5 py-1.5 font-semibold',
  }[size];

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border font-medium ${colorClasses} ${sizeClasses}`}
    >
      <span className="font-bold">{score}%</span>
      {showLabel && <span className="opacity-80 text-[11px] font-normal tracking-wide uppercase">{badgeText}</span>}
    </span>
  );
};
