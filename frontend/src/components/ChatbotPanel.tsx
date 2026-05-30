import { FormEvent, useState } from 'react';

import { chatWithAI } from '../api/ai';

interface ChatMessage {
  role: 'assistant' | 'user';
  text: string;
}

export function ChatbotPanel() {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [mode, setMode] = useState<'ai' | 'fallback' | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: 'assistant', text: 'Xin chào. Bạn có thể hỏi tôi về KPI, công việc quá hạn hoặc hiệu suất của nhóm.' },
  ]);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const message = input.trim();
    if (!message || sending) return;
    setInput('');
    setMessages((current) => [...current, { role: 'user', text: message }]);
    setSending(true);
    try {
      const history = messages.slice(-8).map((item) => ({ role: item.role, content: item.text }));
      const result = await chatWithAI(message, history);
      setMode(result.used_fallback ? 'fallback' : 'ai');
      setMessages((current) => [...current, { role: 'assistant', text: result.reply }]);
    } catch (error) {
      setMessages((current) => [...current, { role: 'assistant', text: 'Không thể kết nối trợ lý lúc này. Vui lòng thử lại.' }]);
    } finally {
      setSending(false);
    }
  };

  return (
    <>
      <button type="button" className="chatbot-fab" onClick={() => setIsOpen((current) => !current)}>
        {isOpen ? 'Đóng' : 'Trợ lý KPI'}
      </button>
      {isOpen ? (
        <section className="glass-panel chatbot-panel">
          <header>
            <div>
              <strong>Trợ lý KPI</strong>
              <p>Phản hồi theo dữ liệu bạn được phép xem</p>
              {mode ? <span className={`chatbot-panel__mode chatbot-panel__mode--${mode}`}>{mode === 'ai' ? 'OpenAI' : 'Dự phòng nội bộ'}</span> : null}
            </div>
          </header>
          <div className="chatbot-panel__messages">
            {messages.map((message, index) => (
              <p className={`chat-message chat-message--${message.role}`} key={`${message.role}-${index}`}>
                {message.text}
              </p>
            ))}
          </div>
          <form onSubmit={(event) => void handleSubmit(event)}>
            <input value={input} onChange={(event) => setInput(event.target.value)} placeholder="Hỏi về KPI hoặc công việc..." />
            <button type="submit" disabled={sending}>{sending ? 'Đang gửi' : 'Gửi'}</button>
          </form>
        </section>
      ) : null}
    </>
  );
}
