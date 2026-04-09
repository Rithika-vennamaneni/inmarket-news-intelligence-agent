import { FormEvent, useRef, useState } from "react";

type ChatMessage = {
  id: string;
  role: "user" | "agent";
  text: string;
  usedTools?: string[];
  sources?: SourceAttribution[];
};

type ChatSuccess = {
  conversation_id: string;
  response: string;
  used_tools: string[];
  sources: SourceAttribution[];
};

type ChatError = {
  error?: string;
};

type SourceAttribution = {
  title: string;
  source_name: string;
};

const SUGGESTIONS = [
  "What's happening with Tesla today",
  "Top business headlines right now",
  "What are consumers saying about Apple",
];

const ENDPOINT = import.meta.env.VITE_API_URL || "http://localhost:8001/chat";

function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const canSend = input.trim().length > 0 && !isLoading;

  async function handleSubmit(event?: FormEvent<HTMLFormElement>, preset?: string): Promise<void> {
    event?.preventDefault();
    const message = (preset ?? input).trim();
    if (!message || isLoading) {
      return;
    }
    setShowSuggestions(false);
    setInput("");
    setIsLoading(true);
    setMessages((current) => [...current, buildMessage("user", message)]);
    try {
      const payload = await sendMessage(message, conversationId);
      setConversationId(payload.conversation_id);
      setMessages((current) => [...current, buildAgentMessage(payload)]);
    } catch (error) {
      setMessages((current) => [...current, buildMessage("agent", getErrorMessage(error))]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  }

  return (
    <main className="min-h-screen px-4 py-8 text-slate-100 sm:px-6 lg:px-8">
      <div className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-5xl flex-col rounded-[2rem] border border-white/10 bg-ink/90 shadow-panel backdrop-blur">
        <section className="flex-1 space-y-4 overflow-y-auto px-4 py-6 sm:px-6">
          {messages.length === 0 && showSuggestions ? (
            <EmptyState onSelect={(value) => void handleSubmit(undefined, value)} />
          ) : null}
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
          {isLoading ? <LoadingBubble /> : null}
        </section>

        <form className="border-t border-white/10 px-4 py-4 sm:px-6" onSubmit={(event) => void handleSubmit(event)}>
          <div className="flex items-end gap-3 rounded-3xl border border-white/10 bg-bubble p-3">
            <input
              ref={inputRef}
              type="text"
              value={input}
              disabled={isLoading}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Ask what is happening with a brand, category, or market trend..."
              className="h-12 flex-1 bg-transparent px-3 text-sm text-white outline-none placeholder:text-muted"
            />
            <button
              type="submit"
              disabled={!canSend}
              className="inline-flex h-12 items-center justify-center rounded-full bg-accent px-5 text-sm font-medium text-white transition hover:bg-[#1f5dff] disabled:cursor-not-allowed disabled:bg-[#2a2a4a]"
            >
              {isLoading ? "Working..." : "Send"}
            </button>
          </div>
        </form>
      </div>
    </main>
  );
}

function EmptyState({ onSelect }: { onSelect: (value: string) => void }) {
  return (
    <div className="flex min-h-full flex-col items-center justify-center py-10 text-center">
      <h2 className="text-2xl font-semibold text-white">News Intelligence Chat</h2>
      <div className="mt-8 flex flex-wrap justify-center gap-3">
        {SUGGESTIONS.map((suggestion) => (
          <button
            key={suggestion}
            type="button"
            onClick={() => onSelect(suggestion)}
            className="rounded-full bg-accent px-4 py-2 text-sm text-white transition hover:bg-[#1f5dff]"
          >
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  const alignment = isUser ? "items-end" : "items-start";
  const bubble = isUser ? "bg-accent text-white" : "bg-bubble text-slate-100";
  const radius = isUser ? "rounded-[1.6rem] rounded-br-md" : "rounded-[1.6rem] rounded-bl-md";
  return (
    <div className={`flex flex-col ${alignment}`}>
      <div className={`max-w-[85%] whitespace-pre-wrap px-5 py-4 text-sm leading-6 shadow-lg ${bubble} ${radius}`}>
        {message.text}
      </div>
      {!isUser && message.usedTools && message.usedTools.length > 0 ? (
        <p className="mt-2 px-2 text-xs text-muted">used: {message.usedTools.join(", ")}</p>
      ) : null}
      {!isUser && message.sources && message.sources.length > 0 ? (
        <div className="mt-3 px-2 text-xs text-muted">
          <p className="mb-1">Sources:</p>
          <ul className="list-disc space-y-1 pl-4">
            {message.sources.map((item) => (
              <li key={`${item.title}-${item.source_name}`}>
                {item.title} ({item.source_name})
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

function LoadingBubble() {
  return (
    <div className="flex items-start">
      <div className="flex items-center gap-2 rounded-[1.6rem] rounded-bl-md bg-bubble px-5 py-4 text-sm text-muted">
        <span className="h-2.5 w-2.5 animate-bounce rounded-full bg-muted [animation-delay:-0.2s]" />
        <span className="h-2.5 w-2.5 animate-bounce rounded-full bg-muted [animation-delay:-0.1s]" />
        <span className="h-2.5 w-2.5 animate-bounce rounded-full bg-muted" />
      </div>
    </div>
  );
}

function buildAgentMessage(payload: ChatSuccess): ChatMessage {
  return {
    id: crypto.randomUUID(),
    role: "agent",
    text: payload.response,
    usedTools: payload.used_tools,
    sources: payload.sources,
  };
}

function buildMessage(role: ChatMessage["role"], text: string): ChatMessage {
  return { id: crypto.randomUUID(), role, text };
}

async function sendMessage(message: string, conversationId: string | null): Promise<ChatSuccess> {
  const response = await fetch(ENDPOINT, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      conversation_id: conversationId,
    }),
  });
  const payload = await parseResponse(response);
  if (!response.ok) {
    throw new Error(payload.error ?? "Request failed.");
  }
  return payload as ChatSuccess;
}

async function parseResponse(response: Response): Promise<ChatSuccess | ChatError> {
  try {
    return (await response.json()) as ChatSuccess | ChatError;
  } catch {
    return { error: "Unable to process the server response right now." };
  }
}

function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return "Unable to reach the agent service right now.";
}

export default App;
