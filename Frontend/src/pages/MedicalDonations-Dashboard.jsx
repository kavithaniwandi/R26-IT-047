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
  CheckCircle,
  Activity,
  Stethoscope,
  Droplet,
  Pill,
  Ambulance,
  Calendar,
  FileText,
  Send,
  Phone,
  Mail,
  AlertCircle,
  User,
  Hospital
} from 'lucide-react';

const MedicalDonations = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [donationForm, setDonationForm] = useState({
    name: '',
    email: '',
    phone: '',
    donationType: 'blood',
    amount: '',
    frequency: 'one-time',
    message: ''
  });

  const medicalCategories = [
    { id: 'all', name: 'All Categories', icon: Heart },
    { id: 'blood', name: 'Blood Donation', icon: Droplet },
    { id: 'organs', name: 'Organ Donation', icon: Heart },
    { id: 'medical', name: 'Medical Supplies', icon: Pill },
    { id: 'equipment', name: 'Medical Equipment', icon: Stethoscope }
  ];

  const bloodRequests = [
    {
      id: 1,
      bloodType: 'O+',
      hospital: 'City General Hospital',
      urgency: 'critical',
      units: '10 units',
      timeLeft: '6 hours',
      location: 'Downtown',
      description: 'Emergency surgery requires O+ blood immediately',
      category: 'blood',
      severity: 'critical'
    },
    {
      id: 2,
      bloodType: 'A-',
      hospital: 'Memorial Medical Center',
      urgency: 'high',
      units: '5 units',
      timeLeft: '12 hours',
      location: 'West Side',
      description: 'Cancer patient needs A- blood for chemotherapy',
      category: 'blood',
      severity: 'high'
    },
    {
      id: 3,
      bloodType: 'B+',
      hospital: 'Children\'s Hospital',
      urgency: 'medium',
      units: '3 units',
      timeLeft: '24 hours',
      location: 'North District',
      description: 'Pediatric surgery scheduled for tomorrow',
      category: 'blood',
      severity: 'medium'
    }
  ];

  const medicalSupplies = [
    {
      id: 1,
      item: 'Ventilators',
      hospital: 'ICU Wing - Central Hospital',
      urgency: 'critical',
      quantity: '5 units',
      timeLeft: 'Immediate',
      description: 'COVID-19 patients requiring ventilator support',
      category: 'equipment'
    },
    {
      id: 2,
      item: 'Surgical Masks',
      hospital: 'All Regional Hospitals',
      urgency: 'high',
      quantity: '50,000 units',
      timeLeft: '2 days',
      description: 'PPE shortage for medical staff',
      category: 'supplies'
    },
    {
      id: 3,
      item: 'Insulin',
      hospital: 'Diabetes Care Center',
      urgency: 'medium',
      quantity: '1,000 vials',
      timeLeft: '1 week',
      description: 'Diabetic patients need insulin supply',
      category: 'medical'
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

  const handleDonationSubmit = (e) => {
    e.preventDefault();
    console.log('Medical donation submitted:', donationForm);
    alert('Thank you for your medical donation! We will contact you shortly.');
    setDonationForm({
      name: '',
      email: '',
      phone: '',
      donationType: 'blood',
      amount: '',
      frequency: 'one-time',
      message: ''
    });
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
            <h1 className="text-4xl md:text-5xl font-bold mb-4">Medical Donations Dashboard</h1>
            <p className="text-xl text-white/90 max-w-3xl mx-auto">
              Save lives through medical donations. Connect blood donors, 
              medical supplies, and healthcare facilities in need.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-12 bg-white border-b">
        <div className="max-w-6xl mx-auto px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {[
              { value: '8,500+', label: 'Lives Saved', icon: Heart },
              { value: '2,000+', label: 'Blood Donors', icon: Droplet },
              { value: '150', label: 'Partner Hospitals', icon: Hospital },
              { value: '24/7', label: 'Emergency Support', icon: Ambulance }
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

      {/* Main Content with Tabs */}
      <section className="py-12">
        <div className="max-w-6xl mx-auto px-4">
          {/* Tabs */}
          <div className="flex flex-wrap gap-4 mb-8">
            <button
              onClick={() => setActiveTab('overview')}
              className={`px-6 py-3 rounded-lg font-medium transition-all ${
                activeTab === 'overview'
                  ? 'bg-donation-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              Overview
            </button>
            <button
              onClick={() => setActiveTab('blood')}
              className={`px-6 py-3 rounded-lg font-medium transition-all ${
                activeTab === 'blood'
                  ? 'bg-donation-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              Blood Donation
            </button>
            <button
              onClick={() => setActiveTab('supplies')}
              className={`px-6 py-3 rounded-lg font-medium transition-all ${
                activeTab === 'supplies'
                  ? 'bg-donation-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              Medical Supplies
            </button>
            <button
              onClick={() => setActiveTab('donate')}
              className={`px-6 py-3 rounded-lg font-medium transition-all ${
                activeTab === 'donate'
                  ? 'bg-donation-600 text-white'
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
                {medicalCategories.map((category) => {
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

              <div className="grid md:grid-cols-2 gap-8">
                <div className="bg-white rounded-xl shadow-lg p-6">
                  <h3 className="text-xl font-bold text-gray-800 mb-4">Recent Blood Donations</h3>
                  <div className="space-y-3">
                    {[
                      { donor: 'John Smith', type: 'O+', hospital: 'City General', time: '2 hours ago' },
                      { donor: 'Sarah Johnson', type: 'A-', hospital: 'Memorial Medical', time: '4 hours ago' },
                      { donor: 'Mike Davis', type: 'B+', hospital: 'Children\'s Hospital', time: '6 hours ago' }
                    ].map((donation, index) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div>
                          <p className="font-medium text-gray-800">{donation.donor}</p>
                          <p className="text-sm text-gray-600">{donation.type} • {donation.hospital}</p>
                        </div>
                        <span className="text-sm text-gray-500">{donation.time}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-white rounded-xl shadow-lg p-6">
                  <h3 className="text-xl font-bold text-gray-800 mb-4">Critical Needs</h3>
                  <div className="space-y-3">
                    {[
                      { item: 'O+ Blood', urgency: 'critical', location: 'City General' },
                      { item: 'Ventilators', urgency: 'high', location: 'ICU Wing' },
                      { item: 'Surgical Masks', urgency: 'medium', location: 'All Hospitals' }
                    ].map((need, index) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                        <div>
                          <p className="font-medium text-gray-800">{need.item}</p>
                          <p className="text-sm text-gray-600">{need.location}</p>
                        </div>
                        <span className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(need.urgency)}`}>
                          {need.urgency}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-xl font-bold text-gray-800 mb-4">Upcoming Blood Drives</h3>
                <div className="grid md:grid-cols-2 gap-4">
                  {[
                    { date: 'Dec 15', location: 'City Center', time: '9:00 AM - 5:00 PM' },
                    { date: 'Dec 18', location: 'Community College', time: '10:00 AM - 4:00 PM' },
                    { date: 'Dec 22', location: 'Shopping Mall', time: '11:00 AM - 6:00 PM' },
                    { date: 'Dec 25', location: 'Hospital Campus', time: '8:00 AM - 2:00 PM' }
                  ].map((drive, index) => (
                    <div key={index} className="p-4 border border-gray-200 rounded-lg hover:border-donation-300 transition-colors">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium text-gray-800">{drive.date}</span>
                        <Calendar className="w-4 h-4 text-donation-600" />
                      </div>
                      <p className="text-sm text-gray-600">{drive.location}</p>
                      <p className="text-sm text-gray-500">{drive.time}</p>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          )}

          {/* Blood Donation Tab */}
          {activeTab === 'blood' && (
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
                      placeholder="Search blood requests..."
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
                      <option value="all">All Blood Types</option>
                      <option value="O+">O+</option>
                      <option value="O-">O-</option>
                      <option value="A+">A+</option>
                      <option value="A-">A-</option>
                      <option value="B+">B+</option>
                      <option value="B-">B-</option>
                      <option value="AB+">AB+</option>
                      <option value="AB-">AB-</option>
                    </select>
                  </div>
                </div>
              </div>

              <div className="grid gap-6">
                {bloodRequests.map((request) => (
                  <motion.div
                    key={request.id}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-all"
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
                            <Droplet className="w-6 h-6 text-red-600" />
                          </div>
                          <div>
                            <h3 className="text-xl font-semibold text-gray-800">{request.bloodType} Blood Needed</h3>
                            <p className="text-gray-600">{request.hospital}</p>
                          </div>
                        </div>
                        <p className="text-gray-600 mb-4">{request.description}</p>
                        <div className="flex flex-wrap items-center gap-4 text-sm">
                          <div className="flex items-center text-gray-500">
                            <MapPin className="w-4 h-4 mr-1" />
                            {request.location}
                          </div>
                          <div className="flex items-center text-gray-500">
                            <Clock className="w-4 h-4 mr-1" />
                            {request.timeLeft}
                          </div>
                          <div className="flex items-center text-gray-500">
                            <Users className="w-4 h-4 mr-1" />
                            {request.units}
                          </div>
                        </div>
                      </div>
                      <div className="flex flex-col items-end space-y-3">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(request.severity)}`}>
                          {request.urgency}
                        </span>
                        <button className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors">
                          Donate Blood
                        </button>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}

          {/* Medical Supplies Tab */}
          {activeTab === 'supplies' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
            >
              <div className="grid gap-6">
                {medicalSupplies.map((supply) => (
                  <motion.div
                    key={supply.id}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-all"
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                            <Pill className="w-6 h-6 text-green-600" />
                          </div>
                          <div>
                            <h3 className="text-xl font-semibold text-gray-800">{supply.item}</h3>
                            <p className="text-gray-600">{supply.hospital}</p>
                          </div>
                        </div>
                        <p className="text-gray-600 mb-4">{supply.description}</p>
                        <div className="flex flex-wrap items-center gap-4 text-sm">
                          <div className="flex items-center text-gray-500">
                            <MapPin className="w-4 h-4 mr-1" />
                            {supply.location}
                          </div>
                          <div className="flex items-center text-gray-500">
                            <Clock className="w-4 h-4 mr-1" />
                            {supply.timeLeft}
                          </div>
                          <div className="flex items-center text-gray-500">
                            <Package className="w-4 h-4 mr-1" />
                            {supply.quantity}
                          </div>
                        </div>
                      </div>
                      <div className="flex flex-col items-end space-y-3">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(supply.urgency)}`}>
                          {supply.urgency}
                        </span>
                        <button className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors">
                          Donate Supplies
                        </button>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}

          {/* Make Donation Tab */}
          {activeTab === 'donate' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="max-w-4xl mx-auto"
            >
              <div className="bg-white rounded-xl shadow-lg p-8">
                <div className="flex items-center space-x-3 mb-6">
                  <div className="w-12 h-12 bg-donation-100 rounded-lg flex items-center justify-center">
                    <Heart className="w-6 h-6 text-donation-600" />
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-gray-800">Medical Donation Form</h2>
                    <p className="text-gray-600">Your donation can save lives</p>
                  </div>
                </div>

                <form onSubmit={handleDonationSubmit} className="space-y-6">
                  <div className="grid md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Full Name *
                      </label>
                      <input
                        type="text"
                        required
                        value={donationForm.name}
                        onChange={(e) => setDonationForm({...donationForm, name: e.target.value})}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-donation-500 focus:border-transparent"
                        placeholder="Enter your full name"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Email Address *
                      </label>
                      <input
                        type="email"
                        required
                        value={donationForm.email}
                        onChange={(e) => setDonationForm({...donationForm, email: e.target.value})}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-donation-500 focus:border-transparent"
                        placeholder="Enter your email"
                      />
                    </div>
                  </div>

                  <div className="grid md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Phone Number *
                      </label>
                      <input
                        type="tel"
                        required
                        value={donationForm.phone}
                        onChange={(e) => setDonationForm({...donationForm, phone: e.target.value})}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-donation-500 focus:border-transparent"
                        placeholder="Enter your phone number"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Donation Type *
                      </label>
                      <select
                        required
                        value={donationForm.donationType}
                        onChange={(e) => setDonationForm({...donationForm, donationType: e.target.value})}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-donation-500 focus:border-transparent"
                      >
                        <option value="blood">Blood Donation</option>
                        <option value="organs">Organ Donation</option>
                        <option value="supplies">Medical Supplies</option>
                        <option value="equipment">Medical Equipment</option>
                        <option value="financial">Financial Support</option>
                      </select>
                    </div>
                  </div>

                  <div className="grid md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Donation Amount
                      </label>
                      <div className="grid grid-cols-4 gap-2 mb-4">
                        {['25', '50', '100', '500'].map((amount) => (
                          <button
                            key={amount}
                            type="button"
                            className="py-2 border border-gray-300 rounded-lg hover:bg-donation-50 hover:border-donation-600 transition-colors"
                            onClick={() => setDonationForm({...donationForm, amount: amount})}
                          >
                            ${amount}
                          </button>
                        ))}
                      </div>
                      <input
                        type="number"
                        value={donationForm.amount}
                        onChange={(e) => setDonationForm({...donationForm, amount: e.target.value})}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-donation-500 focus:border-transparent"
                        placeholder="Custom amount"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Donation Frequency
                      </label>
                      <select
                        value={donationForm.frequency}
                        onChange={(e) => setDonationForm({...donationForm, frequency: e.target.value})}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-donation-500 focus:border-transparent"
                      >
                        <option value="one-time">One-time Donation</option>
                        <option value="monthly">Monthly Recurring</option>
                        <option value="quarterly">Quarterly</option>
                        <option value="annual">Annual</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Additional Message
                    </label>
                    <textarea
                      rows={4}
                      value={donationForm.message}
                      onChange={(e) => setDonationForm({...donationForm, message: e.target.value})}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-donation-500 focus:border-transparent"
                      placeholder="Any additional information or special requirements..."
                    />
                  </div>

                  <div className="flex items-center space-x-4">
                    <button
                      type="submit"
                      className="flex-1 bg-donation-600 text-white px-6 py-3 rounded-lg hover:bg-donation-700 transition-colors font-medium"
                    >
                      <Send className="w-5 h-5 inline mr-2" />
                      Submit Donation
                    </button>
                    <button
                      type="button"
                      className="px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </form>

                <div className="mt-6 p-4 bg-donation-50 rounded-lg">
                  <div className="flex items-start space-x-3">
                    <Phone className="w-5 h-5 text-donation-600 mt-0.5" />
                    <div>
                      <p className="font-medium text-donation-900">24/7 Medical Hotline</p>
                      <p className="text-donation-700">1-800-MEDICAL (1-800-633-4225)</p>
                      <p className="text-sm text-donation-600 mt-1">For urgent medical donations and emergencies</p>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </div>
      </section>
    </div>
  );
};

export default MedicalDonations;
