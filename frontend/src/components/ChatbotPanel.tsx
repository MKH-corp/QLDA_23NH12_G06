import { FormEvent, PointerEvent, useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';

import { chatWithAI } from '../api/ai';
import { Icon } from './ui';

interface ChatMessage {
  role: 'assistant' | 'user';
  text: string;
}

interface PanelPosition {
  x: number;
  y: number;
}

export function ChatbotPanel() {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [mode, setMode] = useState<'ai' | 'fallback' | null>(null);
  const [position, setPosition] = useState<PanelPosition | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const panelRef = useRef<HTMLElement>(null);
  const dragRef = useRef<{ offsetX: number; offsetY: number; pointerId: number } | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: 'assistant', text: 'Xin chào. Bạn có thể hỏi tôi về KPI, công việc quá hạn hoặc hiệu suất của nhóm.' },
  ]);

  const clampPosition = (x: number, y: number): PanelPosition => {
    const rect = panelRef.current?.getBoundingClientRect();
    const width = rect?.width ?? 380;
    const height = rect?.height ?? 480;
    return {
      x: Math.min(Math.max(8, x), Math.max(8, window.innerWidth - width - 8)),
      y: Math.min(Math.max(8, y), Math.max(8, window.innerHeight - height - 8)),
    };
  };

  useEffect(() => {
    if (!isOpen || !position) return;
    const handleResize = () => setPosition(current => current ? clampPosition(current.x, current.y) : null);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [isOpen, position]);

  const handleDragStart = (event: PointerEvent<HTMLElement>) => {
    if (event.button !== 0 || !panelRef.current) return;
    const rect = panelRef.current.getBoundingClientRect();
    dragRef.current = {
      offsetX: event.clientX - rect.left,
      offsetY: event.clientY - rect.top,
      pointerId: event.pointerId,
    };
    event.currentTarget.setPointerCapture(event.pointerId);
    setIsDragging(true);
    event.preventDefault();
  };

  const handleDragMove = (event: PointerEvent<HTMLElement>) => {
    const drag = dragRef.current;
    if (!drag || drag.pointerId !== event.pointerId) return;
    setPosition(clampPosition(event.clientX - drag.offsetX, event.clientY - drag.offsetY));
  };

  const handleDragEnd = (event: PointerEvent<HTMLElement>) => {
    if (dragRef.current?.pointerId !== event.pointerId) return;
    dragRef.current = null;
    event.currentTarget.releasePointerCapture(event.pointerId);
    setIsDragging(false);
  };

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
      <button type="button" className="chatbot-fab" onClick={() => setIsOpen((current) => !current)} aria-label={isOpen ? 'Đóng trợ lý KPI' : 'Mở trợ lý KPI'}>
        <Icon name="bot" size={21} /> <span>{isOpen ? 'Đóng' : 'Trợ lý KPI'}</span>
      </button>
      {isOpen ? createPortal(
        <section
          className={`glass-panel chatbot-panel ${isDragging ? 'chatbot-panel--dragging' : ''}`}
          ref={panelRef}
          style={position ? { bottom: 'auto', left: position.x, right: 'auto', top: position.y } : undefined}
        >
          <header
            className="chatbot-panel__drag-handle"
            onPointerDown={handleDragStart}
            onPointerMove={handleDragMove}
            onPointerUp={handleDragEnd}
            onPointerCancel={handleDragEnd}
          >
            <span className="chatbot-panel__icon"><Icon name="bot" size={20} /></span>
            <div>
              <strong>Trợ lý KPI</strong>
              <p>Phản hồi theo dữ liệu bạn được phép xem</p>
              {mode ? <span className={`chatbot-panel__mode chatbot-panel__mode--${mode}`}>{mode === 'ai' ? 'OpenAI' : 'Dự phòng nội bộ'}</span> : null}
            </div>
            <span className="chatbot-panel__drag-grip" title="Giữ và kéo để di chuyển" aria-label="Kéo để di chuyển cửa sổ chat">
              <i /><i /><i /><i /><i /><i />
            </span>
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
        </section>,
        document.body,
      ) : null}
    </>
  );
}
