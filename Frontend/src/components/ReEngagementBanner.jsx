import { X, ArrowRight } from 'lucide-react';

const ReEngagementBanner = ({ message, onDismiss, onViewMatch }) => {
  return (
    <div className="rounded-2xl border border-amber-200 bg-[#D69E2E]/15 px-4 py-4 shadow-sm">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 flex h-10 w-10 items-center justify-center rounded-full bg-white/80 text-xl">
            💊
          </div>
          <div>
            <p className="font-medium text-amber-950">{message}</p>
            <p className="mt-1 text-sm text-amber-900/80">
              We surfaced a relevant request based on your recent donation history and location.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 self-end md:self-auto">
          <button
            type="button"
            onClick={onViewMatch}
            className="inline-flex items-center gap-2 rounded-full bg-[#2D9E6B] px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-[#23845c]"
          >
            View Match
            <ArrowRight className="h-4 w-4" />
          </button>
          <button
            type="button"
            onClick={onDismiss}
            aria-label="Dismiss banner"
            className="rounded-full p-2 text-amber-950/70 transition-colors hover:bg-white/70 hover:text-amber-950"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ReEngagementBanner;