import React from 'react';
import StatTrend from '../StatTrend';
import './PlayerStats.css';

export default function WeeklyFantasyCard({
  current,
  previous,
  loading
}: {
  current: number;
  previous: number;
  loading: boolean;
}) {
  const formatTotal = (value: number) =>
    Math.round(value).toLocaleString('en-US');

  return (
    <article className="weekly-fantasy-card" aria-label="Roster fantasy average this week">
      <span className="weekly-fantasy-card-label">Roster fantasy average this week</span>
      <div className="weekly-fantasy-card-total">
        <strong>{loading ? '…' : formatTotal(current)}</strong>
        {!loading && (
          <StatTrend
            current={current}
            previous={previous}
            minimumChange={0}
            label="Roster fantasy average this week"
          />
        )}
      </div>
      <span className="weekly-fantasy-card-comparison">
        compared to {loading ? '…' : formatTotal(previous)} last week
      </span>
    </article>
  );
}
