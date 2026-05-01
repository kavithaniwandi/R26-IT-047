import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Pill, Sparkles, Calendar, Clock3, DollarSign, MapPin, ArrowRight, Heart, Zap, Shield, CheckCircle2 } from 'lucide-react';
import donorProfile from '../data/mockDonorProfile';
import mockDonations from '../data/mockDonations';
import ReEngagementBanner from '../components/ReEngagementBanner';
import FeedFilterBar from '../components/FeedFilterBar';
import DonationRequestCard from '../components/DonationRequestCard';

const urgencyOrder = {
  'CRITICAL': 0,
  'HIGH PRIORITY': 1,
  'REGULAR': 2
};

const MedicineDonations = () => {
  const [showPersonalizedFeed, setShowPersonalizedFeed] = useState(false);
  const [bannerVisible, setBannerVisible] = useState(true);
  const [sortBy, setSortBy] = useState('best-match');
  const [activeCategory, setActiveCategory] = useState('All');

  const donor = donorProfile;

  const medicineDonations = mockDonations.filter(
    (request) => request.category !== 'General OTC'
  );

  const visibleRequests = medicineDonations
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
    <div className="min-h-screen bg-gradient-to-br from-donation-50 via-green-50 to-emerald-50">
      {/* Hero Section with Enhanced Styling */}
      <section className="relative overflow-hidden bg-gradient-to-br from-donation-600 via-donation-500 to-emerald-500 text-white py-24">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-20 right-20 w-96 h-96 bg-white rounded-full blur-3xl" />
          <div className="absolute bottom-0 left-10 w-80 h-80 bg-white rounded-full blur-3xl" />
        </div>

        <div className="relative max-w-6xl mx-auto px-4 text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <motion.div
              animate={{ y: [0, -10, 0] }}
              transition={{ duration: 4, repeat: Infinity }}
              className="w-24 h-24 bg-white/20 rounded-full flex items-center justify-center mx-auto mb-8 backdrop-blur-sm border-2 border-white/30"
            >
              <Pill className="w-14 h-14 text-white" />
            </motion.div>

            <h1 className="text-5xl md:text-6xl font-bold mb-6 leading-tight">
              Medicine Donations
            </h1>
            <p className="text-xl md:text-2xl text-white/90 max-w-3xl mx-auto leading-relaxed font-light">
              Help patients get the medicines they need. Contribute to chronic illness support,
              pediatric care, and specialized medical treatments across Sri Lanka.
            </p>

            <div className="mt-10 flex flex-wrap justify-center gap-4">
              <motion.div
                whileHover={{ scale: 1.05 }}
                className="px-6 py-3 bg-white/20 rounded-full backdrop-blur-sm border border-white/30 text-white font-medium"
              >
                🏥 Verified Hospitals
              </motion.div>
              <motion.div
                whileHover={{ scale: 1.05 }}
                className="px-6 py-3 bg-white/20 rounded-full backdrop-blur-sm border border-white/30 text-white font-medium"
              >
                📍 Local Impact
              </motion.div>
              <motion.div
                whileHover={{ scale: 1.05 }}
                className="px-6 py-3 bg-white/20 rounded-full backdrop-blur-sm border border-white/30 text-white font-medium"
              >
                💚 Direct Help
              </motion.div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-12 bg-white border-b border-donation-100">
        <div className="max-w-6xl mx-auto px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {[
              { value: '2,847', label: 'Lives Saved', icon: Heart, color: 'text-red-500' },
              { value: '15,000+', label: 'Medicines Donated', icon: Pill, color: 'text-donation-600' },
              { value: '150+', label: 'Partner Hospitals', icon: Shield, color: 'text-blue-500' },
              { value: '892', label: 'Active Donors', icon: Sparkles, color: 'text-yellow-500' }
            ].map((stat, index) => {
              const Icon = stat.icon;
              return (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  className="rounded-2xl bg-gradient-to-br from-donation-50 to-green-50 p-6 border border-donation-100 hover:shadow-lg transition-all"
                >
                  <Icon className={`w-8 h-8 ${stat.color} mx-auto mb-4`} />
                  <div className="text-3xl font-bold text-donation-900">{stat.value}</div>
                  <div className="text-sm text-donation-700 mt-1">{stat.label}</div>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Personalized Feed Button Section */}
      <section className="py-12 bg-gradient-to-b from-white to-donation-50">
        <div className="max-w-6xl mx-auto px-4">
          <motion.button
            whileHover={{ scale: 1.02 }}
            onClick={() => setShowPersonalizedFeed((current) => !current)}
            className="w-full group relative overflow-hidden rounded-3xl bg-gradient-to-r from-donation-50 to-emerald-50 p-8 border-2 border-donation-300 transition-all hover:border-donation-500 hover:shadow-2xl"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-donation-600 to-emerald-500 opacity-0 group-hover:opacity-5 transition-opacity" />
            <div className="relative flex flex-col md:flex-row md:items-center md:justify-between gap-6">
              <div className="flex items-center gap-4 text-left">
                <motion.div
                  animate={{ scale: [1, 1.1, 1] }}
                  transition={{ duration: 2, repeat: Infinity }}
                  className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-donation-600 to-emerald-500 text-white shadow-lg"
                >
                  <Sparkles className="h-8 w-8" />
                </motion.div>
                <div>
                  <h2 className="text-2xl font-bold text-donation-900">Your Personalized Donation Feed</h2>
                  <p className="text-sm text-donation-700 mt-1">
                    {showPersonalizedFeed
                      ? '✓ Showing matched medicine requests for your profile'
                      : 'View medicine requests matched to your location and preferences'}
                  </p>
                </div>
              </div>
              <div className="inline-flex items-center gap-3 rounded-full bg-gradient-to-r from-donation-600 to-emerald-500 text-white font-semibold px-6 py-3 shadow-lg group-hover:shadow-xl transition-all">
                {showPersonalizedFeed ? 'Hide Feed' : 'View Feed'}
                <ArrowRight className="h-5 w-5 group-hover:translate-x-1 transition-transform" />
              </div>
            </div>
          </motion.button>

          {/* Personalized Feed Content */}
          <AnimatePresence>
            {showPersonalizedFeed && (
              <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="mt-8 space-y-6"
              >
                {/* Donor Profile Header */}
                <div className="rounded-3xl border-2 border-donation-200 bg-gradient-to-br from-white to-donation-50 p-8 shadow-lg">
                  <div className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
                    <div className="max-w-2xl">
                      <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-donation-100 px-4 py-2 text-sm font-bold text-donation-700">
                        <Sparkles className="h-4 w-4" />
                        Your Impact Feed
                      </div>
                      <h2 className="text-4xl font-bold tracking-tight text-donation-900">Your Impact Feed</h2>
                      <p className="mt-4 text-lg text-donation-700">
                        Personalized medicine donation requests based on your history and location in Sri Lanka.
                      </p>
                    </div>

                    <div className="grid gap-4 text-sm md:grid-cols-3">
                      <motion.div
                        whileHover={{ scale: 1.05 }}
                        className="inline-flex items-center gap-3 rounded-2xl bg-gradient-to-br from-donation-100 to-green-100 px-5 py-4 font-semibold text-donation-700 border border-donation-200"
                      >
                        <MapPin className="h-5 w-5" />
                        <div>
                          <div className="text-xs opacity-75">Location</div>
                          <div>Colombo</div>
                        </div>
                      </motion.div>
                      <motion.div
                        whileHover={{ scale: 1.05 }}
                        className="inline-flex items-center gap-3 rounded-2xl bg-gradient-to-br from-green-100 to-emerald-100 px-5 py-4 font-semibold text-green-700 border border-green-200"
                      >
                        <DollarSign className="h-5 w-5" />
                        <div>
                          <div className="text-xs opacity-75">Capacity</div>
                          <div>LKR 10K/mo</div>
                        </div>
                      </motion.div>
                      <motion.div
                        whileHover={{ scale: 1.05 }}
                        className="inline-flex items-center gap-3 rounded-2xl bg-gradient-to-br from-emerald-100 to-teal-100 px-5 py-4 font-semibold text-emerald-700 border border-emerald-200"
                      >
                        <Heart className="h-5 w-5" />
                        <div>
                          <div className="text-xs opacity-75">Preferences</div>
                          <div>Chronic, Pediatric</div>
                        </div>
                      </motion.div>
                    </div>
                  </div>

                  <div className="mt-6 flex flex-wrap gap-4 border-t-2 border-donation-100 pt-6 text-sm">
                    <motion.div
                      whileHover={{ scale: 1.05 }}
                      className="inline-flex items-center gap-2 rounded-full bg-donation-100 px-4 py-2 text-donation-700 font-medium"
                    >
                      <Calendar className="h-4 w-4" />
                      Last donation: 90 days ago
                    </motion.div>
                    <motion.div
                      whileHover={{ scale: 1.05 }}
                      className="inline-flex items-center gap-2 rounded-full bg-green-100 px-4 py-2 text-green-700 font-medium"
                    >
                      <Clock3 className="h-4 w-4" />
                      Monthly capacity tracked
                    </motion.div>
                  </div>
                </div>

                {/* Re-engagement Banner */}
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

                {/* Filter Bar */}
                <FeedFilterBar
                  sortBy={sortBy}
                  onSortChange={setSortBy}
                  activeCategory={activeCategory}
                  onCategoryChange={setActiveCategory}
                  visibleCount={visibleRequests.length}
                />

                {/* Donation Cards */}
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
                  <div className="rounded-3xl border border-dashed border-donation-300 bg-white p-10 text-center shadow-sm">
                    <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-donation-50 text-3xl">
                      ▢
                    </div>
                    <h3 className="mt-5 text-xl font-semibold text-slate-900">No matches for this filter.</h3>
                    <p className="mt-2 text-sm text-slate-600">
                      Try adjusting your category preferences in your profile.
                    </p>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </section>

      {/* Featured Medicine Categories */}
      <section className="py-16 bg-gradient-to-b from-donation-50 to-emerald-50">
        <div className="max-w-6xl mx-auto px-4">
          <div className="mb-12 text-center">
            <h2 className="text-4xl font-bold text-donation-900 mb-4">Featured Medicine Categories</h2>
            <p className="text-lg text-donation-700">Popular medicine donation needs across Sri Lanka</p>
            <div className="mt-4 h-1 w-16 bg-gradient-to-r from-donation-600 to-emerald-500 rounded-full mx-auto" />
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                name: 'Chronic Illness',
                icon: '💊',
                color: 'from-donation-500 to-donation-400',
                lightColor: 'from-donation-100 to-donation-50',
                borderColor: 'border-donation-300',
                textColor: 'text-donation-700',
                desc: 'Diabetes, hypertension, and ongoing treatments'
              },
              {
                name: 'Pediatric Care',
                icon: '👶',
                color: 'from-emerald-500 to-green-400',
                lightColor: 'from-emerald-100 to-emerald-50',
                borderColor: 'border-emerald-300',
                textColor: 'text-emerald-700',
                desc: 'Vitamins, growth support, and child health'
              },
              {
                name: 'Cancer Support',
                icon: '🏥',
                color: 'from-teal-500 to-cyan-400',
                lightColor: 'from-teal-100 to-teal-50',
                borderColor: 'border-teal-300',
                textColor: 'text-teal-700',
                desc: 'Chemotherapy support and palliative care'
              }
            ].map((category, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                whileHover={{ y: -8, boxShadow: '0 20px 40px rgba(0,0,0,0.1)' }}
                className={`group rounded-3xl border-2 ${category.borderColor} bg-gradient-to-br ${category.lightColor} p-8 shadow-lg hover:shadow-2xl transition-all`}
              >
                <div className={`text-6xl mb-6 group-hover:scale-110 transition-transform`}>{category.icon}</div>
                <h3 className={`text-2xl font-bold ${category.textColor} mb-3`}>{category.name}</h3>
                <p className={`${category.textColor} opacity-80 mb-6`}>
                  {category.desc}
                </p>
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  className={`w-full rounded-xl bg-gradient-to-r ${category.color} px-4 py-3 text-sm font-bold text-white transition-all shadow-lg hover:shadow-xl`}
                >
                  View Requests
                </motion.button>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-16 bg-white border-t-2 border-donation-100">
        <div className="max-w-6xl mx-auto px-4">
          <div className="mb-12 text-center">
            <h2 className="text-4xl font-bold text-donation-900 mb-4">How Medicine Donations Work</h2>
            <p className="text-lg text-donation-700">Simple steps to make a meaningful impact</p>
            <div className="mt-4 h-1 w-16 bg-gradient-to-r from-donation-600 to-emerald-500 rounded-full mx-auto" />
          </div>

          <div className="grid md:grid-cols-4 gap-6">
            {[
              {
                step: '1',
                title: 'Browse',
                desc: 'View verified medicine requests from patients in your area',
                icon: Pill,
                color: 'bg-donation-100 text-donation-600'
              },
              {
                step: '2',
                title: 'Select',
                desc: 'Choose medicines that match your donation capacity',
                icon: CheckCircle2,
                color: 'bg-emerald-100 text-emerald-600'
              },
              {
                step: '3',
                title: 'Deliver',
                desc: 'Drop off at nearby verified collection centers',
                icon: MapPin,
                color: 'bg-cyan-100 text-cyan-600'
              },
              {
                step: '4',
                title: 'Impact',
                desc: 'Your donation reaches patients directly and on time',
                icon: Heart,
                color: 'bg-red-100 text-red-600'
              }
            ].map((item, index) => {
              const Icon = item.icon;
              return (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  whileHover={{ scale: 1.05 }}
                  className="rounded-3xl border-2 border-donation-200 bg-gradient-to-br from-white to-donation-50 p-8 shadow-lg hover:shadow-xl transition-all"
                >
                  <div className="flex items-start justify-between mb-6">
                    <div className={`flex h-14 w-14 items-center justify-center rounded-2xl ${item.color} text-2xl font-bold`}>
                      {item.step}
                    </div>
                    <Icon className="h-8 w-8 text-donation-400 opacity-50" />
                  </div>
                  <h3 className="text-xl font-bold text-donation-900 mb-2">{item.title}</h3>
                  <p className="text-donation-700">{item.desc}</p>
                </motion.div>
              );
            })}
          </div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-12 rounded-3xl border-2 border-donation-200 bg-gradient-to-r from-donation-50 to-green-50 p-8 text-center"
          >
            <Shield className="h-12 w-12 text-donation-600 mx-auto mb-4" />
            <h3 className="text-xl font-bold text-donation-900 mb-2">100% Verified & Secure</h3>
            <p className="text-donation-700 max-w-2xl mx-auto">
              All requests are verified by our medical partners. Your donations are tracked from collection to delivery to ensure they reach the right patients.
            </p>
          </motion.div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-br from-donation-600 via-emerald-500 to-teal-500 text-white relative overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 right-0 w-96 h-96 bg-white rounded-full blur-3xl" />
          <div className="absolute bottom-0 left-0 w-80 h-80 bg-white rounded-full blur-3xl" />
        </div>

        <div className="relative max-w-4xl mx-auto px-4 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-5xl font-bold mb-6">Ready to Save Lives?</h2>
            <p className="text-xl text-white/90 mb-10 leading-relaxed">
              Your medicine donation can transform the life of a patient in need. Start by viewing personalized requests matched to your location and preferences.
            </p>
            <motion.button
              whileHover={{ scale: 1.1, boxShadow: '0 20px 40px rgba(0,0,0,0.3)' }}
              onClick={() => setShowPersonalizedFeed(true)}
              className="inline-flex items-center gap-3 rounded-2xl bg-white px-8 py-4 font-bold text-donation-600 transition-all shadow-xl hover:shadow-2xl text-lg"
            >
              <Sparkles className="h-6 w-6" />
              View Your Matches
              <ArrowRight className="h-6 w-6" />
            </motion.button>
          </motion.div>
        </div>
      </section>
    </div>
  );
};

export default MedicineDonations;
