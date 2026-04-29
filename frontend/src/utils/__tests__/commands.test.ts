import { describe, it, expect } from 'vitest';
import {
  SLASH_COMMANDS,
  matchCommands,
  isSlashCommand,
  parseCommand,
} from '../commands';

describe('SLASH_COMMANDS', () => {
  it('contains all expected commands', () => {
    const names = SLASH_COMMANDS.map((c) => c.name);
    expect(names).toContain('/help');
    expect(names).toContain('/policy');
    expect(names).toContain('/strategy');
    expect(names).toContain('/start');
    expect(names).toContain('/pause');
    expect(names).toContain('/resume');
    expect(names).toContain('/status');
    expect(names).toContain('/portfolio');
    expect(names).toContain('/clear');
  });
});

describe('matchCommands', () => {
  it('matches /he to /help', () => {
    const results = matchCommands('/he');
    const names = results.map((c) => c.name);
    expect(names).toEqual(['/help']);
  });

  it('matches /p to /policy, /pause, /portfolio', () => {
    const results = matchCommands('/p');
    const names = results.map((c) => c.name);
    expect(names).toContain('/policy');
    expect(names).toContain('/pause');
    expect(names).toContain('/portfolio');
    expect(names).toHaveLength(3);
  });

  it('returns empty for unknown command', () => {
    expect(matchCommands('/xyz')).toEqual([]);
  });

  it('returns empty when input has no slash', () => {
    expect(matchCommands('hello')).toEqual([]);
  });
});

describe('isSlashCommand', () => {
  it('returns true for a slash-prefixed string', () => {
    expect(isSlashCommand('/help')).toBe(true);
  });

  it('returns false for a plain string', () => {
    expect(isSlashCommand('hello')).toBe(false);
  });
});

describe('parseCommand', () => {
  it('parses a command with no args', () => {
    expect(parseCommand('/help')).toEqual({ name: '/help', args: '' });
  });

  it('parses a command with one arg', () => {
    expect(parseCommand('/policy list')).toEqual({
      name: '/policy',
      args: 'list',
    });
  });

  it('parses a command with multiple args', () => {
    expect(parseCommand('/strategy create My Strategy')).toEqual({
      name: '/strategy',
      args: 'create My Strategy',
    });
  });
});
