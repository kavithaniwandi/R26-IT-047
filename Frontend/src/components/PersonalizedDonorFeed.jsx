import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Calendar, Heart, Clock3, DollarSign, MapPin, Sparkles } from 'lucide-react';
import donorProfile from '../data/mockDonorProfile';
import mockDonations from '../data/mockDonations';
import ReEngagementBanner from './ReEngagementBanner';
import FeedFilterBar from './FeedFilterBar';
import DonationRequestCard from './DonationRequestCard';

const urgencyOrder = {
  'CRITICAL': 0,
  'HIGH PRIORITY': 1,
  'REGULAR': 2
};

const PersonalizedDonorFeed = () => {
  const donor = donorProfile;
  const [bannerVisible, setBannerVisible] = useState(true);
  const [sortBy, setSortBy] = useState('best-match');
  const [activeCategory, setActiveCategory] = useState('All');

  const visibleRequests = mockDonations
    .filter((request) => activeCategory === 'All' || request.category === activeCategory)
    .sort((left, right) => {
      if (sortBy === 'urgency') {
        const urgencyDifference = urgencyOrder[left.urgencyLevel] - urgencyOrder[right.urgencyLevel];
        return urgencyDifference !== 0 ? urgencyDifference : right.matchScore - left.matchScore;
      }

      if (sortBy === 'nearest-location') {
        const distanceDifference = left.distanceKm - right.distanceKm;
        return distanceDifference !== 0 ? distanceDifference : right.matchScore - left.matchScore;
      }

      return right.matchScore - left.matchScore;
    });

  const shouldShowBanner = bannerVisible && donor.lastDonationDaysAgo > 60;

  return (
    <section className="space-y-6">
      <div className="rounded-[2rem] border border-white/80 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div className="max-w-2xl">
            <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-[#2D9E6B]/10 px-3 py-1 text-sm font-semibold text-[#2D9E6B]">
              <Sparkles className="h-4 w-4" />
              Your Impact Feed
            </div>
            <h2 className="text-3xl font-bold tracking-tight text-slate-900">Your Impact Feed</h2>
            <p className="mt-3 text-slate-600">
              Personalized donation requests based on your history and location in Sri Lanka.
            </p>
          </div>

          <div className="grid gap-3 text-sm text-slate-700 md:grid-cols-3">
            <div className="inline-flex items-center gap-2 rounded-2xl bg-[#F0FFF4] px-4 py-3 font-medium">
              <MapPin className="h-4 w-4 text-[#2D9E6B]" />
              Colombo District
            </div>
            <div className="inline-flex items-center gap-2 rounded-2xl bg-[#F0FFF4] px-4 py-3 font-medium">
              <DollarSign className="h-4 w-4 text-[#2D9E6B]" />
              Capacity: LKR 10,000/month
            </div>
            <div className="inline-flex items-center gap-2 rounded-2xl bg-[#F0FFF4] px-4 py-3 font-medium">
              <Heart className="h-4 w-4 text-[#2D9E6B]" />
              Preferred: Chronic Illness, Pediatric
            </div>
          </div>
        </div>

        <div className="mt-5 flex flex-wrap gap-4 border-t border-slate-100 pt-5 text-sm text-slate-600">
          <div className="inline-flex items-center gap-2 rounded-full bg-slate-50 px-3 py-2">
            <Calendar className="h-4 w-4 text-[#2D9E6B]" />
            Last donation: 90 days ago
          </div>
          <div className="inline-flex items-center gap-2 rounded-full bg-slate-50 px-3 py-2">
            <Clock3 className="h-4 w-4 text-[#2D9E6B]" />
            Monthly capacity tracked
          </div>
        </div>
      </div>

      <AnimatePresence>
        {shouldShowBanner && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
          >
            <ReEngagementBanner
              message={`It's been a while, ${donor.name}! Here's an urgent request 0.8km from you that matches your profile.`}
              onDismiss={() => setBannerVisible(false)}
              onViewMatch={() => setActiveCategory('Chronic Illness')}
            />
          </motion.div>
        )}
      </AnimatePresence>

      <FeedFilterBar
        sortBy={sortBy}
        onSortChange={setSortBy}
        activeCategory={activeCategory}
        onCategoryChange={setActiveCategory}
        visibleCount={visibleRequests.length}
      />

      {visibleRequests.length > 0 ? (
        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
          {visibleRequests.map((request) => (
            <DonationRequestCard
              key={request.id}
              request={request}
              donorDistrict={donor.district}
            />
          ))}
        </div>
      ) : (
        <div className="rounded-3xl border border-dashed border-slate-300 bg-white p-10 text-center shadow-sm">
          <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-[#F0FFF4] text-3xl">
            ▢
          </div>
          <h3 className="mt-5 text-xl font-semibold text-slate-900">No matches for this filter.</h3>
          <p className="mt-2 text-sm text-slate-600">
            Try adjusting your category preferences in your profile.
          </p>
        </div>
      )}
    </section>
  );
};

export default PersonalizedDonorFeed;