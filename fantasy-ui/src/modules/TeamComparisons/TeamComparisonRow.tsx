import React from 'react';
import { TeamComparison } from '../../services/teamComparisonsApi';

export type TeamStatTone = 'strength' | 'best' | 'worst';
export type TeamStatTones = Partial<Record<string, TeamStatTone>>;

export default function TeamComparisonRow({
  team,
  rank,
  tones
}: {
  team: TeamComparison;
  rank: number;
  tones: TeamStatTones;
}) {
  const statClass = (key: string) =>
    tones[key] ? `team-comparison-value ${tones[key]}` : 'team-comparison-value';

  return (
    <div className="team-comparison-row" role="row">
      <div className="team-comparison-identity" role="cell">
        <span className="team-comparison-rank">{rank}</span>
        <span>
          <strong>{team.teamName}</strong>
          <small>
            {team.managerName} · {team.corePlayerCount} core players
          </small>
        </span>
      </div>
      <span className={statClass('minutes')} role="cell">{team.minutes.toFixed(1)}</span>
      <span className={statClass('fieldGoalsMade')} role="cell">
        {team.fieldGoalsMade.toFixed(1)} / {team.fieldGoalsAttempted.toFixed(1)}
      </span>
      <span className={statClass('freeThrowsMade')} role="cell">
        {team.freeThrowsMade.toFixed(1)} / {team.freeThrowsAttempted.toFixed(1)}
      </span>
      <span className={statClass('points')} role="cell">{team.points.toFixed(1)}</span>
      <span className={statClass('rebounds')} role="cell">{team.rebounds.toFixed(1)}</span>
      <span className={statClass('assists')} role="cell">{team.assists.toFixed(1)}</span>
      <span className={statClass('steals')} role="cell">{team.steals.toFixed(1)}</span>
      <span className={statClass('blocks')} role="cell">{team.blocks.toFixed(1)}</span>
      <span className={statClass('turnovers')} role="cell">{team.turnovers.toFixed(1)}</span>
      <span className={statClass('threePointersMade')} role="cell">{team.threePointersMade.toFixed(1)}</span>
      <strong className={statClass('fantasyPoints')} role="cell">{team.fantasyPoints.toFixed(1)}</strong>
    </div>
  );
}
