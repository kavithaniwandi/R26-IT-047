import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { 
  Heart, 
  Plus, 
  Search, 
  Filter,
  Clock,
  MapPin,
  Users,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Activity,
  Droplet,
  Pill,
  Stethoscope,
  Ambulance
} from 'lucide-react';

const MedicalDonations = () => {
  const [activeTab, setActiveTab] = useState('donate');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');

  const donationCategories = [
    { id: 'all', name: 'All Categories', icon: Heart },
    { id: 'blood', name: 'Blood Donation', icon: Droplet },
    { id: 'medicines', name: 'Medicines', icon: Pill },
    { id: 'equipment', name: 'Medical Equipment', icon: Stethoscope },
    { id: 'emergency', name: 'Emergency Supplies', icon: Ambulance }
  ];

  const donationRequests = [
    {
      id: 1,
      title: 'Urgent: Blood Type O- Needed',
      hospital: 'City General Hospital',
      location: 'Downtown District',
      urgency: 'critical',
      amount: '5 units',
      timeLeft: '2 hours',
      description: 'Emergency surgery requires immediate blood supply',
      category: 'blood'
    },
    {
      id: 2,
      title: 'Diabetes Medication Drive',
      hospital: 'Community Health Center',
      location: 'Westside',
      urgency: 'high',
      amount: '200 insulin pens',
      timeLeft: '3 days',
      description: 'Low-income patients need diabetes medication',
      category: 'medicines'
    },
    {
      id: 3,
      title: 'Portable Ventilators Needed',
      hospital: 'St. Mary\'s Hospital',
      location: 'North District',
      urgency: 'critical',
      amount: '10 units',
      timeLeft: '6 hours',
      description: 'ICU capacity overwhelmed due to emergency',
      category: 'equipment'
    },
    {
      id: 4,
      title: 'First Aid Supplies Campaign',
      hospital: 'Rural Health Clinic',
      location: 'Rural Area',
      urgency: 'medium',
      amount: '500 kits',
      timeLeft: '1 week',
      description: 'Equipping remote communities with emergency supplies',
      category: 'emergency'
    }
  ];

  const donationOpportunities = [
    {
      id: 1,
      title: 'Blood Donation Camp',
      organization: 'Red Cross',
      location: 'Community Center',
      date: 'Every Saturday',
      time: '9:00 AM - 4:00 PM',
      type: 'blood',
      impact: 'Save up to 3 lives per donation'
    },
    {
      id: 2,
      title: 'Medical Equipment Drive',
      organization: 'Healthcare Foundation',
      location: 'City Hall',
      date: 'This Weekend',
      time: '10:00 AM - 6:00 PM',
      type: 'equipment',
      impact: 'Help equip rural clinics'
    },
    {
      id: 3,
      title: 'Unused Medicines Collection',
      organization: 'MedShare',
      location: 'Multiple Locations',
      date: 'Ongoing',
      time: 'Business Hours',
      type: 'medicines',
      impact: 'Provide medicines to underserved communities'
    }
  ];

  const filteredRequests = donationRequests.filter(request => {
    const matchesSearch = request.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         request.hospital.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || request.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const getUrgencyColor = (urgency) => {
    switch (urgency) {
      case 'critical': return 'text-red-600 bg-red-50';
      case 'high': return 'text-orange-600 bg-orange-50';
      case 'medium': return 'text-yellow-600 bg-yellow-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Hero Section */}
      <section className="bg-gradient-to-r from-donation-600 to-green-600 text-white py-16">
        <div className="max-w-6xl mx-auto px-4 text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <div className="w-20 h-20 bg-white/20 rounded-full flex items-center justify-center mx-auto mb-6">
              <Heart className="w-12 h-12 text-white" />
            </div>
            <h1 className="text-4xl md:text-5xl font-bold mb-4">Medical Donations</h1>
            <p className="text-xl text-white/90 max-w-3xl mx-auto">
              Save lives through medical donations. Every contribution helps provide critical healthcare 
              to those who need it most.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-12 bg-white border-b">
        <div className="max-w-6xl mx-auto px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {[
              { value: '2,847', label: 'Lives Saved', icon: Heart },
              { value: '15,000+', label: 'Blood Units', icon: Droplet },
              { value: '$450K', label: 'Medical Supplies', icon: Pill },
              { value: '892', label: 'Active Donors', icon: Users }
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
                  <Icon className="w-8 h-8 text-donation-600 mx-auto mb-2" />
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
                  ? 'bg-donation-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              Make a Donation
            </button>
            <button
              onClick={() => setActiveTab('requests')}
              className={`px-6 py-3 rounded-lg font-medium transition-all ${
                activeTab === 'requests'
                  ? 'bg-donation-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              Donation Requests
            </button>
            <button
              onClick={() => setActiveTab('opportunities')}
              className={`px-6 py-3 rounded-lg font-medium transition-all ${
                activeTab === 'opportunities'
                  ? 'bg-donation-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              Donation Opportunities
            </button>
          </div>

          {/* Donate Tab */}
          {activeTab === 'donate' && (
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
                        selectedCategory === category.id ? 'ring-2 ring-donation-600' : ''
                      }`}
                    >
                      <Icon className="w-12 h-12 text-donation-600 mb-4" />
                      <h3 className="font-semibold text-gray-800">{category.name}</h3>
                    </motion.div>
                  );
                })}
              </div>

              <div className="bg-white rounded-xl shadow-lg p-8">
                <h3 className="text-2xl font-bold text-gray-800 mb-6">Quick Donation Form</h3>
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Donation Type
                    </label>
                    <select className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-donation-500 focus:border-transparent">
                      <option>Blood Donation</option>
                      <option>Medicines</option>
                      <option>Medical Equipment</option>
                      <option>Emergency Supplies</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Location
                    </label>
                    <select className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-donation-500 focus:border-transparent">
                      <option>Nearest Center</option>
                      <option>Downtown</option>
                      <option>Westside</option>
                      <option>North District</option>
                    </select>
                  </div>
                </div>
                <button className="mt-6 bg-donation-600 text-white px-8 py-3 rounded-lg hover:bg-donation-700 transition-colors">
                  Schedule Donation
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
                      placeholder="Search donation requests..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-donation-500 focus:border-transparent"
                    />
                  </div>
                  <div className="flex items-center space-x-2">
                    <Filter className="w-5 h-5 text-gray-400" />
                    <select
                      value={selectedCategory}
                      onChange={(e) => setSelectedCategory(e.target.value)}
                      className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-donation-500 focus:border-transparent"
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
                        <h3 className="text-xl font-semibold text-gray-800 mb-2">{request.title}</h3>
                        <p className="text-gray-600 mb-4">{request.description}</p>
                        <div className="flex flex-wrap items-center gap-4 text-sm">
                          <div className="flex items-center text-gray-500">
                            <MapPin className="w-4 h-4 mr-1" />
                            {request.location}
                          </div>
                          <div className="flex items-center text-gray-500">
                            <Activity className="w-4 h-4 mr-1" />
                            {request.hospital}
                          </div>
                          <div className="flex items-center text-gray-500">
                            <Clock className="w-4 h-4 mr-1" />
                            {request.timeLeft}
                          </div>
                        </div>
                      </div>
                      <div className="flex flex-col items-end space-y-3">
                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${getUrgencyColor(request.urgency)}`}>
                          {request.urgency}
                        </span>
                        <div className="text-right">
                          <div className="text-2xl font-bold text-donation-600">{request.amount}</div>
                        </div>
                        <button className="bg-donation-600 text-white px-4 py-2 rounded-lg hover:bg-donation-700 transition-colors">
                          Donate Now
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
                    <div className="w-12 h-12 bg-donation-100 rounded-lg flex items-center justify-center mb-4">
                      <Heart className="w-6 h-6 text-donation-600" />
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
                    <div className="bg-donation-50 rounded-lg p-3 mb-4">
                      <p className="text-sm text-donation-700">{opportunity.impact}</p>
                    </div>
                    <button className="w-full bg-donation-600 text-white py-2 rounded-lg hover:bg-donation-700 transition-colors">
                      Sign Up
                    </button>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}
        </div>
      </section>

      {/* Emergency Alert */}
      <section className="py-8 bg-red-50">
        <div className="max-w-6xl mx-auto px-4">
          <div className="bg-red-100 rounded-lg p-6 flex items-center space-x-4">
            <AlertCircle className="w-8 h-8 text-red-600 flex-shrink-0" />
            <div>
              <h3 className="text-lg font-semibold text-red-900 mb-1">Critical Blood Shortage</h3>
              <p className="text-red-700">
                Type O- blood urgently needed at City General Hospital. 
                <Link to="/medical-donations" className="underline ml-2 font-medium">
                  Donate now to save lives
                </Link>
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default MedicalDonations;
