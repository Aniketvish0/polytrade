import { AgentStatusBar } from './AgentStatusBar';
import { MessageList } from './MessageList';
import { CommandInput } from './CommandInput';

export function Terminal() {
  return (
    <div className="flex flex-col h-full bg-base">
      <AgentStatusBar />
      <MessageList />
      <CommandInput />
    </div>
  );
}
