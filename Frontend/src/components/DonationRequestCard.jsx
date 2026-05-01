import { motion } from 'framer-motion';
import { BadgeCheck, MapPin, Package, Store, ChevronRight, ShieldCheck } from 'lucide-react';
import { useState } from 'react';
import DonationDetailsModal from './DonationDetailsModal';
import DonateItemModal from './DonateItemModal';

const urgencyStyles = {
  'CRITICAL': 'bg-[#E53E3E]/10 text-[#E53E3E]',
  'HIGH PRIORITY': 'bg-orange-100 text-orange-700',
  'REGULAR': 'bg-blue-100 text-blue-700'
};

const matchStyles = (score) => {
  if (score >= 90) {
    return 'border-green-200 bg-green-50 text-green-800';
  }

  if (score >= 70) {
    return 'border-teal-200 bg-teal-50 text-teal-800';
  }

  return 'border-slate-200 bg-slate-50 text-slate-700';
};

const DonationRequestCard = ({ request, donorDistrict }) => {
  const isNearYou = request.district === donorDistrict;
  const locationLabel = isNearYou ? 'Near you' : `${request.distanceKm.toFixed(1)} km away`;
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [donateOpen, setDonateOpen] = useState(false);

  return (
    <motion.article
      whileHover={{ y: -4 }}
      transition={{ duration: 0.2 }}
      className="rounded-3xl border border-white/80 bg-white p-6 shadow-sm transition-shadow hover:shadow-xl"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${urgencyStyles[request.urgencyLevel]}`}>
            {request.urgencyLevel}
          </span>
        </div>

        <div className={`rounded-full border px-3 py-1 text-xs font-semibold ${matchStyles(request.matchScore)}`}>
          {request.matchScore}% Match
        </div>
      </div>

      <div className="mt-4 flex items-start justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-xl font-bold text-slate-900">{request.medicineName}</h3>
            {request.isVerified ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2.5 py-1 text-xs font-semibold text-green-700">
                <BadgeCheck className="h-3.5 w-3.5" />
                Verified
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-600">
                <ShieldCheck className="h-3.5 w-3.5" />
                Pending verification
              </span>
            )}
          </div>
          <p className="mt-2 text-sm leading-6 text-slate-600">{request.patientDescription}</p>
        </div>
      </div>

      <div className="mt-5 space-y-3 text-sm text-slate-700">
        <div className="flex items-center gap-3">
          <MapPin className="h-4 w-4 text-[#2D9E6B]" />
          <span>
            {request.district} District <span className="font-semibold text-slate-500">• {locationLabel}</span>
          </span>
        </div>
        <div className="flex items-center gap-3">
          <span className="inline-flex h-7 min-w-7 items-center justify-center rounded-full bg-[#319795]/10 text-xs font-bold text-[#319795]">
            💊
          </span>
          <span>
            <span className="font-medium text-slate-900">{request.category}</span> medicine category
          </span>
        </div>
        <div className="flex items-center gap-3">
          <Package className="h-4 w-4 text-[#2D9E6B]" />
          <span>{request.quantityNeeded}</span>
        </div>
      </div>

      <div className="mt-5 flex items-start gap-3 rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-600">
        <Store className="mt-0.5 h-4 w-4 flex-shrink-0 text-slate-400" />
        <span>{request.nearestPickupPoint}</span>
      </div>

      <div className="mt-6 flex flex-col gap-3 sm:flex-row">
        <button
          type="button"
          onClick={() => setDetailsOpen(true)}
          className="inline-flex flex-1 items-center justify-center gap-2 rounded-xl border border-slate-200 px-4 py-3 text-sm font-semibold text-slate-700 transition-colors hover:border-[#2D9E6B] hover:text-[#2D9E6B]"
        >
          View Donation Details
          <ChevronRight className="h-4 w-4" />
        </button>
        <button
          type="button"
          onClick={() => setDonateOpen(true)}
          className="inline-flex flex-1 items-center justify-center rounded-xl bg-[#2D9E6B] px-4 py-3 text-sm font-semibold text-white transition-colors hover:bg-[#23845c]"
        >
          Donate This Item
        </button>
      </div>

      <DonationDetailsModal open={detailsOpen} onClose={() => setDetailsOpen(false)} request={request} />
      <DonateItemModal
        open={donateOpen}
        onClose={() => setDonateOpen(false)}
        request={request}
        onConfirm={(payload) => {
          // placeholder: show simple confirmation (replace with API call later)
          alert(`Thanks! Donation queued for request ${payload.requestId} (qty: ${payload.quantity})`);
        }}
      />
    </motion.article>
  );
};

export default DonationRequestCard;