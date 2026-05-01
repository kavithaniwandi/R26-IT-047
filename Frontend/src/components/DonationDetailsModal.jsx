import { motion } from 'framer-motion';
import { X, MapPin, Package, Store } from 'lucide-react';

const DonationDetailsModal = ({ open, onClose, request }) => {
  if (!open || !request) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <motion.div
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.98 }}
        className="relative z-10 max-w-2xl w-full rounded-3xl bg-white p-6 shadow-xl"
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <h3 className="text-2xl font-bold text-slate-900">{request.medicineName}</h3>
            <p className="mt-1 text-sm text-slate-600">{request.patientDescription}</p>
          </div>
          <button onClick={onClose} className="rounded-full p-2 text-slate-600 hover:bg-slate-100">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="mt-6 grid gap-4 text-sm text-slate-700">
          <div className="flex items-center gap-3">
            <MapPin className="h-4 w-4 text-[#2D9E6B]" />
            <div>
              <div className="font-medium text-slate-900">{request.district} District</div>
              <div className="text-xs text-slate-500">{request.distanceKm.toFixed(1)} km away</div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Package className="h-4 w-4 text-[#2D9E6B]" />
            <div>
              <div className="font-medium text-slate-900">Quantity Needed</div>
              <div className="text-xs text-slate-500">{request.quantityNeeded}</div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Store className="h-4 w-4 text-slate-400" />
            <div>
              <div className="font-medium text-slate-900">Pickup Point</div>
              <div className="text-xs text-slate-500">{request.nearestPickupPoint}</div>
            </div>
          </div>

          <div className="pt-4 border-t">
            <h4 className="text-sm font-semibold text-slate-900">Patient Notes</h4>
            <p className="mt-2 text-sm text-slate-600">{request.patientDescription}</p>
          </div>
        </div>

        <div className="mt-6 flex justify-end">
          <button
            onClick={onClose}
            className="rounded-full px-5 py-2 text-sm font-semibold border border-slate-200 text-slate-700 hover:bg-slate-50"
          >
            Close
          </button>
        </div>
      </motion.div>
    </div>
  );
};

export default DonationDetailsModal;
