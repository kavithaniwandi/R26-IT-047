import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { 
  Shield, 
  Plus, 
  Search, 
  Filter,
  Clock,
  MapPin,
  Users,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Activity,
  Home,
  Zap,
  Truck,
  Radio
} from 'lucide-react';

const DisasterDonations = () => {
  const [activeTab, setActiveTab] = useState('donate');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedDisaster, setSelectedDisaster] = useState('all');

  const donationCategories = [
    { id: 'all', name: 'All Categories', icon: Shield },
    { id: 'shelter', name: 'Shelter & Housing', icon: Home },
    { id: 'food', name: 'Food & Water', icon: Plus },
    { id: 'supplies', name: 'Emergency Supplies', icon: Truck },
    { id: 'communication', name: 'Communication', icon: Radio }
  ];

  const activeDisasters = [
    { id: 'all', name: 'All Disasters', severity: 'all' },
    { id: 'flood', name: 'Coastal Floods', severity: 'critical', affected: '50,000' },
    { id: 'earthquake', name: 'Earthquake Response', severity: 'high', affected: '25,000' },
    { id: 'fire', name: 'Wildfire Relief', severity: 'medium', affected: '15,000' },
    { id: 'hurricane', name: 'Hurricane Aftermath', severity: 'critical', affected: '75,000' }
  ];

  const reliefRequests = [
    {
      id: 1,
      title: 'Emergency Shelter Supplies Needed',
      disaster: 'Coastal Floods',
      location: 'East Coast Region',
      urgency: 'critical',
      amount: '500 families',
      timeLeft: '12 hours',
      description: 'Families displaced by flooding need immediate shelter supplies',
      category: 'shelter',
      severity: 'critical'
    },
    {
      id: 2,
      title: 'Clean Water Distribution',
      disaster: 'Earthquake Response',
      location: 'Mountain Valley',
      urgency: 'critical',
      amount: '10,000 gallons',
      timeLeft: '6 hours',
      description: 'Water systems damaged - urgent need for clean water',
      category: 'food',
      severity: 'critical'
    },
    {
      id: 3,
      title: 'Emergency Medical Kits',
      disaster: 'Wildfire Relief',
      location: 'Forest District',
      urgency: 'high',
      amount: '1,000 kits',
      timeLeft: '24 hours',
      description: 'Medical supplies for evacuation centers and first responders',
      category: 'supplies',
      severity: 'high'
    },
    {
      id: 4,
      title: 'Communication Equipment',
      disaster: 'Hurricane Aftermath',
      location: 'Coastal Cities',
      urgency: 'high',
      amount: '200 units',
      timeLeft: '2 days',
      description: 'Satellite phones and radios for emergency coordination',
      category: 'communication',
      severity: 'high'
    }
  ];

  const donationOpportunities = [
    {
      id: 1,
      title: 'Flood Relief Fund',
      organization: 'Emergency Response Network',
      location: 'Nationwide',
      date: 'Ongoing',
      time: '24/7',
      type: 'financial',
      impact: 'Provide immediate relief to flood victims',
      raised: 45000,
      goal: 100000
    },
    {
      id: 2,
      title: 'Supply Collection Drive',
      organization: 'Community Relief Coalition',
      location: 'City Center',
      date: 'This Weekend',
      time: '9:00 AM - 6:00 PM',
      type: 'supplies',
      impact: 'Collect essential supplies for disaster victims'
    },
    {
      id: 3,
      title: 'Volunteer Deployment',
      organization: 'Disaster Response Team',
      location: 'Multiple Locations',
      date: 'Immediate',
      time: 'Various Shifts',
      type: 'volunteer',
      impact: 'Join emergency response teams on the ground'
    }
  ];

  const filteredRequests = reliefRequests.filter(request => {
    const matchesSearch = request.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         request.location.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || request.category === selectedCategory;
    const matchesDisaster = selectedDisaster === 'all' || request.disaster.toLowerCase().includes(selectedDisaster.toLowerCase());
    return matchesSearch && matchesCategory && matchesDisaster;
  });

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'text-red-600 bg-red-50';
      case 'high': return 'text-orange-600 bg-orange-50';
      case 'medium': return 'text-yellow-600 bg-yellow-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getSeverityBadge = (severity) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-200';
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Hero Section */}
      <section className="bg-gradient-to-r from-disaster-600 to-red-600 text-white py-16">
        <div className="max-w-6xl mx-auto px-4 text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <div className="w-20 h-20 bg-white/20 rounded-full flex items-center justify-center mx-auto mb-6">
              <Shield className="w-12 h-12 text-white" />
            </div>
            <h1 className="text-4xl md:text-5xl font-bold mb-4">Disaster Relief Donations</h1>
            <p className="text-xl text-white/90 max-w-3xl mx-auto">
              Provide critical support during natural disasters and emergencies. 
              Your contribution brings hope to communities in crisis.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Active Disasters Alert */}
      <section className="py-8 bg-red-50 border-b border-red-200">
        <div className="max-w-6xl mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-red-100 rounded-lg p-6"
          >
            <div className="flex items-center space-x-3 mb-4">
              <AlertTriangle className="w-8 h-8 text-red-600" />
              <h2 className="text-2xl font-bold text-red-900">Active Disasters</h2>
            </div>
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
              {activeDisasters.slice(1).map((disaster) => (
                <div key={disaster.id} className={`bg-white rounded-lg p-4 border ${getSeverityBadge(disaster.severity)}`}>
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-semibold text-gray-800">{disaster.name}</h3>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(disaster.severity)}`}>
                      {disaster.severity}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">{disaster.affected} people affected</p>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-12 bg-white border-b">
        <div className="max-w-6xl mx-auto px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {[
              { value: '165,000', label: 'People Helped', icon: Users },
              { value: '$2.3M', label: 'Relief Funds', icon: TrendingUp },
              { value: '45', label: 'Active Missions', icon: Shield },
              { value: '12,000', label: 'Volunteers', icon: Zap }
            ].map((stat, index) => {
              const Icon = stat.icon;
              return (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  className="text-center"
                >
                  <Icon className="w-8 h-8 text-disaster-600 mx-auto mb-2" />
                  <div className="text-2xl font-bold text-gray-800">{stat.value}</div>
                  <div className="text-gray-600">{stat.label}</div>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Main Content */}
      <section className="py-12">
        <div className="max-w-6xl mx-auto px-4">
          {/* Tabs */}
          <div className="flex flex-col sm:flex-row gap-4 mb-8">
            <button
              onClick={() => setActiveTab('donate')}
              className={`px-6 py-3 rounded-lg font-medium transition-all ${
                activeTab === 'donate'
                  ? 'bg-disaster-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              Make a Donation
            </button>
            <button
              onClick={() => setActiveTab('requests')}
              className={`px-6 py-3 rounded-lg font-medium transition-all ${
                activeTab === 'requests'
                  ? 'bg-disaster-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              Relief Requests
            </button>
            <button
              onClick={() => setActiveTab('opportunities')}
              className={`px-6 py-3 rounded-lg font-medium transition-all ${
                activeTab === 'opportunities'
                  ? 'bg-disaster-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              Relief Opportunities
            </button>
          </div>

          {/* Donate Tab */}
          {activeTab === 'donate' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-8"
            >
              {/* Disaster Selection */}
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-xl font-bold text-gray-800 mb-4">Select Disaster to Support</h3>
                <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {activeDisasters.map((disaster) => (
                    <motion.div
                      key={disaster.id}
                      whileHover={{ scale: 1.05 }}
                      onClick={() => setSelectedDisaster(disaster.id)}
                      className={`p-4 rounded-lg border cursor-pointer transition-all ${
                        selectedDisaster === disaster.id
                          ? 'border-disaster-600 bg-disaster-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <h4 className="font-semibold text-gray-800">{disaster.name}</h4>
                      {disaster.affected && (
                        <p className="text-sm text-gray-600 mt-1">{disaster.affected} affected</p>
                      )}
                    </motion.div>
                  ))}
                </div>
              </div>

              {/* Donation Categories */}
              <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                {donationCategories.map((category) => {
                  const Icon = category.icon;
                  return (
                    <motion.div
                      key={category.id}
                      whileHover={{ scale: 1.05 }}
                      onClick={() => setSelectedCategory(category.id)}
                      className={`bg-white rounded-xl shadow-lg p-6 cursor-pointer transition-all ${
                        selectedCategory === category.id ? 'ring-2 ring-disaster-600' : ''
                      }`}
                    >
                      <Icon className="w-12 h-12 text-disaster-600 mb-4" />
                      <h3 className="font-semibold text-gray-800">{category.name}</h3>
                    </motion.div>
                  );
                })}
              </div>

              {/* Quick Donation Form */}
              <div className="bg-white rounded-xl shadow-lg p-8">
                <h3 className="text-2xl font-bold text-gray-800 mb-6">Emergency Relief Donation</h3>
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Donation Amount
                    </label>
                    <div className="grid grid-cols-4 gap-2 mb-4">
                      {['25', '50', '100', '500'].map((amount) => (
                        <button
                          key={amount}
                          className="py-2 border border-gray-300 rounded-lg hover:bg-disaster-50 hover:border-disaster-600 transition-colors"
                        >
                          ${amount}
                        </button>
                      ))}
                    </div>
                    <input
                      type="number"
                      placeholder="Custom amount"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-disaster-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Donation Type
                    </label>
                    <select className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-disaster-500 focus:border-transparent">
                      <option>One-time Donation</option>
                      <option>Monthly Recurring</option>
                      <option>Emergency Fund</option>
                    </select>
                  </div>
                </div>
                <button className="mt-6 bg-disaster-600 text-white px-8 py-3 rounded-lg hover:bg-disaster-700 transition-colors">
                  Donate Now
                </button>
              </div>
            </motion.div>
          )}

          {/* Requests Tab */}
          {activeTab === 'requests' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
            >
              {/* Search and Filter */}
              <div className="bg-white rounded-lg shadow p-4">
                <div className="flex flex-col md:flex-row gap-4">
                  <div className="flex-1 relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                    <input
                      type="text"
                      placeholder="Search relief requests..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-disaster-500 focus:border-transparent"
                    />
                  </div>
                  <div className="flex items-center space-x-2">
                    <Filter className="w-5 h-5 text-gray-400" />
                    <select
                      value={selectedCategory}
                      onChange={(e) => setSelectedCategory(e.target.value)}
                      className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-disaster-500 focus:border-transparent"
                    >
                      {donationCategories.map(category => (
                        <option key={category.id} value={category.id}>
                          {category.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>

              {/* Requests List */}
              <div className="grid gap-6">
                {filteredRequests.map((request) => (
                  <motion.div
                    key={request.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-all"
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <h3 className="text-xl font-semibold text-gray-800">{request.title}</h3>
                          <span className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(request.severity)}`}>
                            {request.severity}
                          </span>
                        </div>
                        <p className="text-gray-600 mb-4">{request.description}</p>
                        <div className="flex flex-wrap items-center gap-4 text-sm">
                          <div className="flex items-center text-gray-500">
                            <MapPin className="w-4 h-4 mr-1" />
                            {request.location}
                          </div>
                          <div className="flex items-center text-gray-500">
                            <AlertTriangle className="w-4 h-4 mr-1" />
                            {request.disaster}
                          </div>
                          <div className="flex items-center text-gray-500">
                            <Clock className="w-4 h-4 mr-1" />
                            {request.timeLeft}
                          </div>
                        </div>
                      </div>
                      <div className="flex flex-col items-end space-y-3">
                        <div className="text-right">
                          <div className="text-2xl font-bold text-disaster-600">{request.amount}</div>
                        </div>
                        <button className="bg-disaster-600 text-white px-4 py-2 rounded-lg hover:bg-disaster-700 transition-colors">
                          Help Now
                        </button>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}

          {/* Opportunities Tab */}
          {activeTab === 'opportunities' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
            >
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                {donationOpportunities.map((opportunity) => (
                  <motion.div
                    key={opportunity.id}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    whileHover={{ y: -5 }}
                    className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-all"
                  >
                    <div className="w-12 h-12 bg-disaster-100 rounded-lg flex items-center justify-center mb-4">
                      <Shield className="w-6 h-6 text-disaster-600" />
                    </div>
                    <h3 className="text-lg font-semibold text-gray-800 mb-2">{opportunity.title}</h3>
                    <p className="text-gray-600 mb-4">{opportunity.organization}</p>
                    <div className="space-y-2 text-sm text-gray-500 mb-4">
                      <div className="flex items-center">
                        <MapPin className="w-4 h-4 mr-2" />
                        {opportunity.location}
                      </div>
                      <div className="flex items-center">
                        <Clock className="w-4 h-4 mr-2" />
                        {opportunity.date} • {opportunity.time}
                      </div>
                    </div>
                    {opportunity.raised && (
                      <div className="mb-4">
                        <div className="flex justify-between text-sm mb-1">
                          <span className="text-gray-600">Raised</span>
                          <span className="font-semibold">${opportunity.raised.toLocaleString()}</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-disaster-600 h-2 rounded-full"
                            style={{ width: `${(opportunity.raised / opportunity.goal) * 100}%` }}
                          />
                        </div>
                        <div className="text-right text-sm text-gray-500 mt-1">
                          Goal: ${opportunity.goal.toLocaleString()}
                        </div>
                      </div>
                    )}
                    <div className="bg-disaster-50 rounded-lg p-3 mb-4">
                      <p className="text-sm text-disaster-700">{opportunity.impact}</p>
                    </div>
                    <button className="w-full bg-disaster-600 text-white py-2 rounded-lg hover:bg-disaster-700 transition-colors">
                      {opportunity.type === 'financial' ? 'Donate' : 'Sign Up'}
                    </button>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}
        </div>
      </section>

      {/* Emergency Call to Action */}
      <section className="py-12 bg-gradient-to-r from-disaster-600 to-red-600">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <h2 className="text-3xl font-bold text-white mb-4">Emergency Response Needed</h2>
            <p className="text-xl text-white/90 mb-8">
              Multiple disasters require immediate assistance. Your contribution can save lives today.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button className="px-8 py-4 bg-white text-disaster-600 rounded-lg hover:bg-gray-100 transition-all transform hover:scale-105 font-semibold">
                Emergency Fund
              </button>
              <Link
                to="/volunteers/disaster"
                className="px-8 py-4 bg-white/20 backdrop-blur text-white border-2 border-white rounded-lg hover:bg-white/30 transition-all transform hover:scale-105 font-semibold"
              >
                Volunteer Now
              </Link>
            </div>
          </motion.div>
        </div>
      </section>
    </div>
  );
};

export default DisasterDonations;
