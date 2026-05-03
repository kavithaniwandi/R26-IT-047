import { motion } from 'framer-motion';
import { X } from 'lucide-react';

const DonateChoiceModal = ({ open, onClose, onChooseMedicine, onChooseMoney, request }) => {
  if (!open) return null;

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
            <h3 className="text-lg font-bold text-slate-900">Donate for: {request?.medicineName}</h3>
            <p className="mt-1 text-sm text-slate-600">Choose whether you'd like to donate medicine or make a monetary contribution.</p>
          </div>
          <button onClick={onClose} className="rounded-full p-2 text-slate-600 hover:bg-slate-100">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="mt-6 grid grid-cols-1 gap-3">
          <button
            onClick={() => { onChooseMedicine(); onClose(); }}
            className="w-full rounded-xl bg-[#2D9E6B] px-4 py-3 text-sm font-semibold text-white hover:bg-[#23845c]"
          >
            Donate Medicine
          </button>
          <button
            onClick={() => { onChooseMoney(); onClose(); }}
            className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50"
          >
            Donate Money
          </button>
        </div>

      </motion.div>
    </div>
  );
};

export default DonateChoiceModal;
