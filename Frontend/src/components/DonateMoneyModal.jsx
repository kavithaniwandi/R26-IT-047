import { useState } from 'react';
import { motion } from 'framer-motion';
import { X, DollarSign } from 'lucide-react';

const DonateMoneyModal = ({ open, onClose, request, onConfirm }) => {
  const [amount, setAmount] = useState('500');
  const [notes, setNotes] = useState('');

  if (!open) return null;

  const handleConfirm = () => {
    const numeric = Number(amount);
    if (!numeric || numeric <= 0) return;
    onConfirm({ requestId: request?.id, amount: numeric, notes });
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
          <div>
            <h3 className="text-lg font-bold text-slate-900">Monetary Donation</h3>
            <p className="mt-1 text-sm text-slate-600">Support this request with a monetary contribution.</p>
          </div>
          <button onClick={onClose} className="rounded-full p-2 text-slate-600 hover:bg-slate-100">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="mt-4 space-y-4">
          <label className="block text-sm font-medium text-slate-700">Amount (LKR)</label>
          <div className="flex items-center gap-2">
            <DollarSign className="h-5 w-5 text-slate-500" />
            <input
              type="number"
              value={amount}
              min={1}
              onChange={(e) => setAmount(e.target.value)}
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
            />
          </div>

          <label className="block text-sm font-medium text-slate-700">Notes (optional)</label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={3}
            className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
          />
        </div>

        <div className="mt-6 flex items-center justify-end gap-3">
          <button onClick={onClose} className="rounded-full px-4 py-2 text-sm font-semibold border border-slate-200 text-slate-700 hover:bg-slate-50">Cancel</button>
          <button onClick={handleConfirm} className="rounded-full bg-[#2D9E6B] px-4 py-2 text-sm font-semibold text-white hover:bg-[#23845c]">Donate LKR</button>
        </div>
      </motion.div>
    </div>
  );
};

export default DonateMoneyModal;
