import { useState } from 'react';
import { motion } from 'framer-motion';
import { X, CreditCard } from 'lucide-react';

const PaymentSandboxModal = ({ open, onClose, payload, onSuccess }) => {
  const [processing, setProcessing] = useState(false);

  if (!open) return null;

  const handlePay = async () => {
    setProcessing(true);
    // simulate network/payment processing delay
    await new Promise((r) => setTimeout(r, 1500));
    const txId = `sandbox_tx_${Math.random().toString(36).slice(2, 10)}`;
    setProcessing(false);
    onSuccess({ ...payload, transactionId: txId });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <motion.div
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.98 }}
        className="relative z-10 max-w-md w-full rounded-3xl bg-white p-6 shadow-xl"
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="rounded-full bg-slate-100 p-2">
              <CreditCard className="h-5 w-5 text-slate-600" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900">Sandbox Payment</h3>
              <p className="mt-1 text-sm text-slate-600">This is a simulated payment flow for testing (no real charges).</p>
            </div>
          </div>
          <button onClick={onClose} className="rounded-full p-2 text-slate-600 hover:bg-slate-100">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="mt-4">
          <div className="text-sm text-slate-700">Donation target</div>
          <div className="mt-1 text-lg font-semibold text-slate-900">{payload?.requestId ? `Request ${payload.requestId}` : 'General'}</div>
          <div className="text-sm text-slate-500">Amount: LKR {payload?.amount ?? '—'}</div>
        </div>

        <div className="mt-6 space-y-3">
          <div className="text-sm text-slate-700">Card (sandbox)</div>
          <input className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm" placeholder="4242 4242 4242 4242" />
          <div className="flex gap-2">
            <input className="w-1/2 rounded-lg border border-slate-200 px-3 py-2 text-sm" placeholder="MM/YY" />
            <input className="w-1/2 rounded-lg border border-slate-200 px-3 py-2 text-sm" placeholder="CVC" />
          </div>
        </div>

        <div className="mt-6 flex items-center justify-end gap-3">
          <button onClick={onClose} className="rounded-full px-4 py-2 text-sm font-semibold border border-slate-200 text-slate-700 hover:bg-slate-50">Cancel</button>
          <button onClick={handlePay} disabled={processing} className="rounded-full bg-[#2D9E6B] px-4 py-2 text-sm font-semibold text-white hover:bg-[#23845c] disabled:opacity-60">
            {processing ? 'Processing...' : `Pay LKR ${payload?.amount ?? ''}`}
          </button>
        </div>
      </motion.div>
    </div>
  );
};

export default PaymentSandboxModal;
