import { useEffect, useRef, useState } from "react";
import { api, errorMessage } from "../api/client";

const WELCOME = {
  role: "assistant",
  content:
    "Hi! Ask me about products, budgets, specs or comparisons. I only use the demo product data, so prices are sample prices.",
  source: "welcome",
};

export default function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([WELCOME]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const endRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView?.({ behavior: "smooth", block: "end" });
  }, [messages, loading, open]);

  useEffect(() => {
    if (open) inputRef.current?.focus();
  }, [open]);

  // Other pages can dispatch `window.dispatchEvent(new CustomEvent("ask-ai", { detail: "..." }))`
  // to open the chat with a prefilled question (used by the "Ask AI" button).
  useEffect(() => {
    const handler = (e) => {
      setOpen(true);
      if (typeof e.detail === "string") setInput(e.detail.slice(0, 1000));
    };
    window.addEventListener("ask-ai", handler);
    return () => window.removeEventListener("ask-ai", handler);
  }, []);

  const send = async (e) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;
    if (text.length > 1000) {
      setError("Please keep your message under 1000 characters.");
      return;
    }
    setError("");
    const history = messages
      .filter((m) => m.source !== "welcome" && !m.isError)
      .map((m) => ({ role: m.role, content: m.content }));
    setMessages((m) => [...m, { role: "user", content: text }]);
    setInput("");
    setLoading(true);
    try {
      const data = await api.chat(text, history);
      setMessages((m) => [
        ...m,
        { role: "assistant", content: data.reply, source: data.source, ai: data.ai_generated },
      ]);
    } catch (err) {
      setMessages((m) => [
        ...m,
        { role: "assistant", content: errorMessage(err), isError: true, source: "error" },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const clear = () => {
    setMessages([WELCOME]);
    setError("");
  };

  return (
    <>
      <button
        className="chat-fab"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-controls="chat-panel"
      >
        {open ? "✕ Close" : "💬 Ask AI"}
      </button>

      {open ? (
        <section id="chat-panel" className="chat-panel" aria-label="Shopping assistant chat">
          <div className="chat-head">
            <strong>Shopping assistant</strong>
            <button className="btn btn-sm btn-ghost-light" onClick={clear}>Clear chat</button>
          </div>

          <div className="chat-messages" role="log" aria-live="polite">
            {messages.map((m, i) => (
              <div key={i} className={`msg ${m.role} ${m.isError ? "err" : ""}`}>
                <div className="bubble">{m.content}</div>
                {m.role === "assistant" && m.source && m.source !== "welcome" && m.source !== "error" ? (
                  <div className="msg-meta">
                    {m.ai ? "✨ Gemini" : "⚙️ Rule-based fallback (AI unavailable)"}
                  </div>
                ) : null}
              </div>
            ))}
            {loading ? (
              <div className="msg assistant"><div className="bubble typing" aria-label="Assistant is typing">…</div></div>
            ) : null}
            <div ref={endRef} />
          </div>

          <form className="chat-input" onSubmit={send}>
            <label htmlFor="chat-text" className="sr-only">Message</label>
            <input
              id="chat-text"
              ref={inputRef}
              value={input}
              maxLength={1000}
              onChange={(e) => setInput(e.target.value)}
              placeholder="e.g. Which laptop is best under ₹60,000?"
              disabled={loading}
            />
            <button className="btn btn-primary" type="submit" disabled={loading || !input.trim()}>
              Send
            </button>
          </form>
          {error ? <p className="form-error pad" role="alert">{error}</p> : null}
        </section>
      ) : null}
    </>
  );
}
