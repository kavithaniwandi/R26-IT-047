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
  Radio,
  Phone,
  Mail,
  FileText,
  Send,
  Heart
} from 'lucide-react';

const DisasterDonations = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedDisaster, setSelectedDisaster] = useState('all');
  const [emergencyForm, setEmergencyForm] = useState({
    name: '',
    phone: '',
    email: '',
    location: '',
    disasterType: '',
    urgency: 'medium',
    description: '',
    peopleAffected: '',
    immediateNeeds: ''
  });

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
    }
  ];

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'text-red-600 bg-red-50';
      case 'high': return 'text-orange-600 bg-orange-50';
      case 'medium': return 'text-yellow-600 bg-yellow-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const handleEmergencySubmit = (e) => {
    e.preventDefault();
    console.log('Emergency request submitted:', emergencyForm);
    // Handle form submission logic here
    alert('Emergency request submitted successfully! We will contact you shortly.');
    setEmergencyForm({
      name: '',
      phone: '',
      email: '',
      location: '',
      disasterType: '',
      urgency: 'medium',
      description: '',
      peopleAffected: '',
      immediateNeeds: ''
    });
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
            <h1 className="text-4xl md:text-5xl font-bold mb-4">Disaster Relief Dashboard</h1>
            <p className="text-xl text-white/90 max-w-3xl mx-auto">
              Coordinate relief efforts, track emergencies, and provide critical support 
              during natural disasters and crises.
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
                <div key={disaster.id} className={`bg-white rounded-lg p-4 border ${getSeverityColor(disaster.severity)}`}>
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

      {/* Main Content with Tabs */}
      <section className="py-12">
        <div className="max-w-6xl mx-auto px-4">
          {/* Tabs */}
          <div className="flex flex-wrap gap-4 mb-8">
            <button
              onClick={() => setActiveTab('overview')}
              className={`px-6 py-3 rounded-lg font-medium transition-all ${
                activeTab === 'overview'
                  ? 'bg-disaster-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              Overview
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
              onClick={() => setActiveTab('emergency')}
              className={`px-6 py-3 rounded-lg font-medium transition-all ${
                activeTab === 'emergency'
                  ? 'bg-disaster-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              Emergency Request
            </button>
            <button
              onClick={() => setActiveTab('donations')}
              className={`px-6 py-3 rounded-lg font-medium transition-all ${
                activeTab === 'donations'
                  ? 'bg-disaster-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              Make Donation
            </button>
          </div>

          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-8"
            >
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

              <div className="bg-white rounded-xl shadow-lg p-8">
                <h3 className="text-2xl font-bold text-gray-800 mb-6">Recent Activities</h3>
                <div className="space-y-4">
                  {[
                    { action: 'Shelter provided', location: 'Coastal Region', time: '2 hours ago' },
                    { action: 'Medical supplies delivered', location: 'Mountain Valley', time: '4 hours ago' },
                    { action: 'Volunteer team deployed', location: 'Forest District', time: '6 hours ago' }
                  ].map((activity, index) => (
                    <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                      <div>
                        <p className="font-medium text-gray-800">{activity.action}</p>
                        <p className="text-sm text-gray-600">{activity.location}</p>
                      </div>
                      <span className="text-sm text-gray-500">{activity.time}</span>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          )}

          {/* Relief Requests Tab */}
          {activeTab === 'requests' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
            >
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

              <div className="grid gap-6">
                {reliefRequests.map((request) => (
                  <motion.div
                    key={request.id}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
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

          {/* Emergency Request Tab */}
          {activeTab === 'emergency' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="max-w-4xl mx-auto"
            >
              <div className="bg-white rounded-xl shadow-lg p-8">
                <div className="flex items-center space-x-3 mb-6">
                  <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
                    <AlertTriangle className="w-6 h-6 text-red-600" />
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-gray-800">Emergency Request Form</h2>
                    <p className="text-gray-600">Get immediate help for disaster situations</p>
                  </div>
                </div>

                <form onSubmit={handleEmergencySubmit} className="space-y-6">
                  <div className="grid md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Your Name *
                      </label>
                      <input
                        type="text"
                        required
                        value={emergencyForm.name}
                        onChange={(e) => setEmergencyForm({...emergencyForm, name: e.target.value})}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-disaster-500 focus:border-transparent"
                        placeholder="Enter your full name"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Phone Number *
                      </label>
                      <input
                        type="tel"
                        required
                        value={emergencyForm.phone}
                        onChange={(e) => setEmergencyForm({...emergencyForm, phone: e.target.value})}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-disaster-500 focus:border-transparent"
                        placeholder="Enter your phone number"
                      />
                    </div>
                  </div>

                  <div className="grid md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Email Address
                      </label>
                      <input
                        type="email"
                        value={emergencyForm.email}
                        onChange={(e) => setEmergencyForm({...emergencyForm, email: e.target.value})}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-disaster-500 focus:border-transparent"
                        placeholder="Enter your email"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Location *
                      </label>
                      <input
                        type="text"
                        required
                        value={emergencyForm.location}
                        onChange={(e) => setEmergencyForm({...emergencyForm, location: e.target.value})}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-disaster-500 focus:border-transparent"
                        placeholder="City, State/Area"
                      />
                    </div>
                  </div>

                  <div className="grid md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Disaster Type *
                      </label>
                      <select
                        required
                        value={emergencyForm.disasterType}
                        onChange={(e) => setEmergencyForm({...emergencyForm, disasterType: e.target.value})}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-disaster-500 focus:border-transparent"
                      >
                        <option value="">Select disaster type</option>
                        <option value="flood">Flood</option>
                        <option value="earthquake">Earthquake</option>
                        <option value="fire">Wildfire</option>
                        <option value="hurricane">Hurricane</option>
                        <option value="tornado">Tornado</option>
                        <option value="other">Other</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Urgency Level *
                      </label>
                      <select
                        required
                        value={emergencyForm.urgency}
                        onChange={(e) => setEmergencyForm({...emergencyForm, urgency: e.target.value})}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-disaster-500 focus:border-transparent"
                      >
                        <option value="low">Low - Non-life threatening</option>
                        <option value="medium">Medium - Urgent but not immediate danger</option>
                        <option value="high">High - Immediate assistance needed</option>
                        <option value="critical">Critical - Life-threatening situation</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Description of Situation *
                    </label>
                    <textarea
                      required
                      rows={4}
                      value={emergencyForm.description}
                      onChange={(e) => setEmergencyForm({...emergencyForm, description: e.target.value})}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-disaster-500 focus:border-transparent"
                      placeholder="Describe the current situation and what help is needed..."
                    />
                  </div>

                  <div className="grid md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Number of People Affected
                      </label>
                      <input
                        type="number"
                        value={emergencyForm.peopleAffected}
                        onChange={(e) => setEmergencyForm({...emergencyForm, peopleAffected: e.target.value})}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-disaster-500 focus:border-transparent"
                        placeholder="Approximate number"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Immediate Needs
                      </label>
                      <input
                        type="text"
                        value={emergencyForm.immediateNeeds}
                        onChange={(e) => setEmergencyForm({...emergencyForm, immediateNeeds: e.target.value})}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-disaster-500 focus:border-transparent"
                        placeholder="e.g., Food, Water, Medical, Shelter"
                      />
                    </div>
                  </div>

                  <div className="flex items-center space-x-4">
                    <button
                      type="submit"
                      className="flex-1 bg-disaster-600 text-white px-6 py-3 rounded-lg hover:bg-disaster-700 transition-colors font-medium"
                    >
                      <Send className="w-5 h-5 inline mr-2" />
                      Submit Emergency Request
                    </button>
                    <button
                      type="button"
                      className="px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </form>

                <div className="mt-6 p-4 bg-red-50 rounded-lg">
                  <div className="flex items-start space-x-3">
                    <Phone className="w-5 h-5 text-red-600 mt-0.5" />
                    <div>
                      <p className="font-medium text-red-900">24/7 Emergency Hotline</p>
                      <p className="text-red-700">1-800-RELIEF (1-800-735-4333)</p>
                      <p className="text-sm text-red-600 mt-1">For life-threatening emergencies, call 911 immediately</p>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {/* Make Donation Tab */}
          {activeTab === 'donations' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-8"
            >
              <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                {donationCategories.slice(1).map((category) => {
                  const Icon = category.icon;
                  return (
                    <motion.div
                      key={category.id}
                      whileHover={{ scale: 1.05 }}
                      className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-all"
                    >
                      <Icon className="w-12 h-12 text-disaster-600 mb-4" />
                      <h3 className="font-semibold text-gray-800 mb-2">{category.name}</h3>
                      <button className="w-full bg-disaster-600 text-white py-2 rounded-lg hover:bg-disaster-700 transition-colors">
                        Donate
                      </button>
                    </motion.div>
                  );
                })}
              </div>

              <div className="bg-white rounded-xl shadow-lg p-8">
                <h3 className="text-2xl font-bold text-gray-800 mb-6">Quick Donation</h3>
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
        </div>
      </section>
    </div>
  );
};

export default DisasterDonations;
