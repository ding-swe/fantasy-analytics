export interface RosterPlayer {
  playerId: number;
  name: string;
}

export const coreRoster: RosterPlayer[] = [
  { playerId: 1630581, name: 'Josh Giddey' },
  { playerId: 1628384, name: 'OG Anunoby' },
  { playerId: 1631095, name: 'Jabari Smith Jr.' },
  { playerId: 1641705, name: 'Victor Wembanyama' },
  { playerId: 203497, name: 'Rudy Gobert' },
  { playerId: 1642847, name: 'Jeremiah Fears' },
  { playerId: 202331, name: 'Paul George' },
  { playerId: 1629027, name: 'Trae Young' },
  { playerId: 1626164, name: 'Devin Booker' },
  { playerId: 1628401, name: 'Derrick White' },
  { playerId: 1630188, name: 'Jalen Smith' }
];

export const streamSlotCandidates: RosterPlayer[] = [
  { playerId: 201950, name: 'Jrue Holiday' },
  { playerId: 1642258, name: 'Zaccharie Risacher' }
];
