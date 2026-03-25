import { useState, useRef, useEffect } from 'react';
import { MessageCircle, X, Send, Loader2 } from 'lucide-react';
import { useDiagnoseChat } from '../lib/api';
import type { ChatMessage } from '../lib/types';

function generateId(): string {
  return Math.random().toString(36).substring(2, 10);
}

export function DiagnosisChat() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState<string | undefined>();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const diagnoseChat = useDiagnoseChat();

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input when panel opens
  useEffect(() => {
    if (isOpen) {
      inputRef.current?.focus();
    }
  }, [isOpen]);

  // Initialize session when first opened
  useEffect(() => {
    if (isOpen && messages.length === 0) {
      sendMessage('');
    }
  }, [isOpen]);

  function sendMessage(text: string) {
    if (diagnoseChat.isPending) return;

    if (text.trim()) {
      const userMsg: ChatMessage = {
        id: generateId(),
        role: 'user',
        content: text,
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, userMsg]);
    }
    setInput('');

    diagnoseChat.mutate(
      { message: text, session_id: sessionId },
      {
        onSuccess: (data) => {
          setSessionId(data.session_id);
          const assistantMsg: ChatMessage = {
            id: generateId(),
            role: 'assistant',
            content: data.response,
            timestamp: Date.now(),
            metadata: {
              actions: data.actions,
            },
          };
          setMessages((prev) => [...prev, assistantMsg]);
        },
        onError: (err) => {
          const errorMsg: ChatMessage = {
            id: generateId(),
            role: 'assistant',
            content: `Error: ${err instanceof Error ? err.message : 'Failed to connect'}`,
            timestamp: Date.now(),
          };
          setMessages((prev) => [...prev, errorMsg]);
        },
      }
    );
  }

  function handleActionClick(action: string) {
    sendMessage(action);
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim()) return;
    sendMessage(input);
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (input.trim()) {
        sendMessage(input);
      }
    }
  }

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-gray-900 text-white shadow-lg transition hover:bg-gray-800 hover:shadow-xl"
        aria-label="Open diagnosis chat"
      >
        <MessageCircle className="h-6 w-6" />
      </button>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 z-50 flex h-[500px] w-[380px] flex-col overflow-hidden rounded-xl border border-gray-200 bg-white shadow-2xl">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-200 bg-gray-900 px-4 py-3">
        <div>
          <h3 className="text-sm font-semibold text-white">AutoAgent Diagnosis</h3>
          <p className="text-xs text-gray-400">Interactive failure analysis</p>
        </div>
        <button
          onClick={() => setIsOpen(false)}
          className="rounded-lg p-1 text-gray-400 transition hover:bg-gray-800 hover:text-white"
          aria-label="Close chat"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                msg.role === 'user'
                  ? 'bg-gray-900 text-white'
                  : 'bg-gray-100 text-gray-800'
              }`}
            >
              <pre className="whitespace-pre-wrap font-sans">{msg.content}</pre>
              {/* Action buttons */}
              {msg.metadata?.actions && msg.metadata.actions.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {msg.metadata.actions.map((action, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleActionClick(action.action)}
                      className="rounded-md border border-gray-300 bg-white px-2 py-1 text-xs font-medium text-gray-700 transition hover:bg-gray-50"
                    >
                      {action.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {diagnoseChat.isPending && (
          <div className="flex justify-start">
            <div className="rounded-lg bg-gray-100 px-3 py-2">
              <Loader2 className="h-4 w-4 animate-spin text-gray-400" />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="border-t border-gray-200 p-3">
        <div className="flex gap-2">
          <input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about failures..."
            className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none"
            disabled={diagnoseChat.isPending}
          />
          <button
            type="submit"
            disabled={diagnoseChat.isPending || !input.trim()}
            className="rounded-lg bg-gray-900 px-3 py-2 text-white transition hover:bg-gray-800 disabled:opacity-50"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </form>
    </div>
  );
}
