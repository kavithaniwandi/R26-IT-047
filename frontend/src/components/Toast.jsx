import React from 'react';
import { CheckCircle2, AlertCircle, Info, AlertTriangle, X } from 'lucide-react';

export function ToastContainer({ toasts, onDismiss }) {
  if (!toasts || toasts.length === 0) return null;

  return (
    <div className="toast-container" aria-live="polite">
      {toasts.map((t) => {
        const getIcon = () => {
          switch (t.type) {
            case 'success': return <CheckCircle2 size={18} className="toast-icon success" />;
            case 'error': return <AlertCircle size={18} className="toast-icon error" />;
            case 'warning': return <AlertTriangle size={18} className="toast-icon warning" />;
            default: return <Info size={18} className="toast-icon info" />;
          }
        };

        return (
          <div key={t.id} className={`toast-item toast-${t.type || 'info'}`}>
            <div className="toast-content-wrapper">
              {getIcon()}
              <div className="toast-text-area">
                {t.title && <div className="toast-title">{t.title}</div>}
                <div className="toast-message">{t.message}</div>
              </div>
            </div>
            <button
              className="toast-close-btn"
              onClick={() => onDismiss(t.id)}
              aria-label="Dismiss notification"
            >
              <X size={14} />
            </button>
          </div>
        );
      })}
    </div>
  );
}
