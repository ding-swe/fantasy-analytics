import React from 'react';
import './StatTrend.css';

export default function StatTrend({
  current,
  previous,
  inverse = false,
  label,
  minimumChange = 0.2
}: {
  current: number | null | undefined;
  previous: number | null | undefined;
  inverse?: boolean;
  label: string;
  minimumChange?: number;
}) {
  if (
    current === null ||
    current === undefined ||
    previous === null ||
    previous === undefined ||
    !Number.isFinite(current) ||
    !Number.isFinite(previous)
  ) {
    return <span className="stat-trend-slot" aria-hidden="true" />;
  }

  let favorableChange: number;
  if (previous === 0) {
    if (current === 0) return <span className="stat-trend-slot" aria-hidden="true" />;
    favorableChange = inverse ? -current : current;
  } else {
    const change = (current - previous) / Math.abs(previous);
    favorableChange = inverse ? -change : change;
  }
  if (
    (minimumChange === 0 && favorableChange === 0) ||
    (minimumChange > 0 &&
      favorableChange > -minimumChange &&
      favorableChange < minimumChange)
  ) {
    return <span className="stat-trend-slot" aria-hidden="true" />;
  }

  const isUp = minimumChange === 0
    ? favorableChange > 0
    : favorableChange >= minimumChange;
  const amount = Math.round(minimumChange * 100);
  const description = minimumChange === 0
    ? (isUp ? 'up' : 'down')
    : (isUp ? `up at least ${amount}%` : `down at least ${amount}%`);

  return (
    <span
      className={`stat-trend-slot stat-trend ${isUp ? 'up' : 'down'}`}
      role="img"
      aria-label={`${label} ${description} compared with last week`}
      title={`${label} ${description} compared with last week's full-week average`}
    >
      <svg viewBox="0 0 12 12" aria-hidden="true" focusable="false">
        <path
          d={isUp ? 'M2 8.5 6 4.5 10 8.5' : 'M2 3.5 6 7.5 10 3.5'}
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </span>
  );
}
