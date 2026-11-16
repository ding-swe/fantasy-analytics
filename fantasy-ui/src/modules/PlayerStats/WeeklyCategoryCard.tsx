import React from 'react';
import StatTrend from '../StatTrend';

export interface WeeklyCategoryIncrease {
  label: string;
  percentIncrease: number;
}

export default function WeeklyCategoryCard({
  increase,
  loading
}: {
  increase: WeeklyCategoryIncrease | null;
  loading: boolean;
}) {
  return (
    <article className="weekly-fantasy-card weekly-category-card" aria-label="Biggest category increase this week">
      <span className="weekly-fantasy-card-label">Biggest category increase</span>
      <div className="weekly-fantasy-card-total">
        <strong>{loading ? '…' : increase?.label || '—'}</strong>
        {!loading && increase && (
          <StatTrend
            current={1}
            previous={0}
            minimumChange={0}
            label={`${increase.label} category`}
          />
        )}
      </div>
      <span className="weekly-fantasy-card-comparison">
        {loading
          ? 'Comparing weekly stats…'
          : increase
          ? `up ${(increase.percentIncrease * 100).toFixed(0)}% from last week`
          : 'No category increased this week'}
      </span>
    </article>
  );
}
