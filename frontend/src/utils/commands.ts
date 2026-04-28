export interface SlashCommand {
  name: string;
  description: string;
  usage: string;
  handler?: (args: string) => string | null;
}

export const SLASH_COMMANDS: SlashCommand[] = [
  {
    name: '/help',
    description: 'Show available commands',
    usage: '/help',
  },
  {
    name: '/policy',
    description: 'View or modify trading policies',
    usage: '/policy [list|enable|disable] [policy_name]',
  },
  {
    name: '/strategy',
    description: 'View or modify trading strategies',
    usage: '/strategy [list|enable|disable] [strategy_name]',
  },
  {
    name: '/pause',
    description: 'Pause the trading agent',
    usage: '/pause',
  },
  {
    name: '/resume',
    description: 'Resume the trading agent',
    usage: '/resume',
  },
  {
    name: '/status',
    description: 'Show agent status and connection info',
    usage: '/status',
  },
  {
    name: '/portfolio',
    description: 'Show portfolio summary',
    usage: '/portfolio',
  },
  {
    name: '/clear',
    description: 'Clear the terminal',
    usage: '/clear',
  },
];

export function matchCommands(input: string): SlashCommand[] {
  if (!input.startsWith('/')) return [];
  const lower = input.toLowerCase();
  return SLASH_COMMANDS.filter((cmd) =>
    cmd.name.toLowerCase().startsWith(lower)
  );
}

export function isSlashCommand(input: string): boolean {
  return input.startsWith('/');
}

export function parseCommand(input: string): { name: string; args: string } {
  const trimmed = input.trim();
  const spaceIndex = trimmed.indexOf(' ');
  if (spaceIndex === -1) {
    return { name: trimmed.toLowerCase(), args: '' };
  }
  return {
    name: trimmed.slice(0, spaceIndex).toLowerCase(),
    args: trimmed.slice(spaceIndex + 1).trim(),
  };
}
