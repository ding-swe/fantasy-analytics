import React from 'react';
import { ComparisonColumn, ComparisonTeam } from '../../services/teamComparisonsApi';

export type TeamStatTone = 'strength' | 'best' | 'worst';
export type TeamStatTones = Partial<Record<string, TeamStatTone>>;

export default function TeamComparisonRow({ team, rank, columns, tones }: {
  team: ComparisonTeam;
  rank: number;
  columns: ComparisonColumn[];
  tones: TeamStatTones;
}) {
  const detail = [team.managerName, team.opponentName && 'vs. ' + team.opponentName]
    .filter(Boolean).join(' · ');

  return (
    <div className="team-comparison-row" role="row">
      <div className="team-comparison-identity" role="cell">
        <span className="team-comparison-rank">{rank}</span>
        <span>
          <strong>{team.teamName}</strong>
          {detail && <small>{detail}</small>}
        </span>
      </div>
      {columns.map(({ key }) => {
        const className = 'team-comparison-value' + (tones[key] ? ' ' + tones[key] : '');
        const value = team.values[key]?.display ?? '—';
        return key === 'result'
          ? <strong key={key} className={className} role="cell">{value}</strong>
          : <span key={key} className={className} role="cell">{value}</span>;
      })}
    </div>
  );
}
