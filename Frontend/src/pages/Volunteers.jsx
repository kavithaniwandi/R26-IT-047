import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  Users, 
  Plus, 
  Search, 
  Filter,
  Clock,
  MapPin,
  Calendar,
  Award,
  Heart,
  Shield,
  Stethoscope,
  CheckCircle,
  AlertCircle,
  TrendingUp,
  Activity,
  Star
} from 'lucide-react';

const Volunteers = () => {
  const [activeSection, setActiveSection] = useState('disaster');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSkill, setSelectedSkill] = useState('all');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    // Check if user is logged in
    const userData = localStorage.getItem('user');
    setIsAuthenticated(!!userData);
    
    // Set active section based on URL path
    if (location.pathname.includes('medical')) {
      setActiveSection('medical');
    } else if (location.pathname.includes('disaster')) {
      setActiveSection('disaster');
    }
  }, [location]);

  const skills = [
    { id: 'all', name: 'All Skills' },
    { id: 'first-aid', name: 'First Aid' },
    { id: 'medical', name: 'Medical Support' },
    { id: 'rescue', name: 'Search & Rescue' },
    { id: 'logistics', name: 'Logistics' },
    { id: 'communication', name: 'Communication' },
    { id: 'translation', name: 'Translation' },
    { id: 'counseling', name: 'Counseling' }
  ];

  const disasterOpportunities = [
    {
      id: 1,
      title: 'Flood Response Team',
      organization: 'Emergency Response Network',
      location: 'East Coast Region',
      urgency: 'critical',
      duration: '2 weeks',
      volunteersNeeded: 50,
      volunteersSigned: 32,
      skills: ['first-aid', 'rescue', 'logistics'],
      description: 'Join our team responding to severe flooding in coastal areas.',
      startDate: 'Immediate',
      type: 'disaster'
    },
    {
      id: 2,
      title: 'Earthquake Relief Operations',
      organization: 'Disaster Relief Coalition',
      location: 'Mountain Valley',
      urgency: 'high',
      duration: '3 weeks',
      volunteersNeeded: 75,
      volunteersSigned: 28,
      skills: ['rescue', 'medical', 'logistics'],
      description: 'Support earthquake victims with rescue and relief operations.',
      startDate: 'In 3 days',
      type: 'disaster'
    },
    {
      id: 3,
      title: 'Wildfire Evacuation Support',
      organization: 'Forest Service Emergency',
      location: 'Forest District',
      urgency: 'high',
      duration: '1 week',
      volunteersNeeded: 30,
      volunteersSigned: 15,
      skills: ['logistics', 'communication', 'first-aid'],
      description: 'Assist with evacuation and support for affected communities.',
      startDate: 'Tomorrow',
      type: 'disaster'
    }
  ];

  const medicalOpportunities = [
    {
      id: 4,
      title: 'Emergency Medical Camp',
      organization: 'Healthcare Without Borders',
      location: 'Rural Health Center',
      urgency: 'high',
      duration: '2 weeks',
      volunteersNeeded: 20,
      volunteersSigned: 8,
      skills: ['medical', 'first-aid', 'counseling'],
      description: 'Provide medical care in underserved communities.',
      startDate: 'Next Monday',
      type: 'medical'
    },
    {
      id: 5,
      title: 'Vaccination Drive',
      organization: 'Public Health Initiative',
      location: 'Multiple Locations',
      urgency: 'medium',
      duration: '1 month',
      volunteersNeeded: 40,
      volunteersSigned: 22,
      skills: ['medical', 'communication', 'logistics'],
      description: 'Support vaccination campaigns across the region.',
      startDate: 'Ongoing',
      type: 'medical'
    },
    {
      id: 6,
      title: 'Mental Health Support',
      organization: 'Crisis Counseling Network',
      location: 'Community Centers',
      urgency: 'medium',
      duration: '6 weeks',
      volunteersNeeded: 15,
      volunteersSigned: 9,
      skills: ['counseling', 'communication', 'translation'],
      description: 'Provide mental health support for trauma victims.',
      startDate: 'In 1 week',
      type: 'medical'
    }
  ];

  const allOpportunities = activeSection === 'disaster' ? disasterOpportunities : medicalOpportunities;

  const filteredOpportunities = allOpportunities.filter(opportunity => {
    const matchesSearch = opportunity.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         opportunity.organization.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesSkill = selectedSkill === 'all' || opportunity.skills.includes(selectedSkill);
    return matchesSearch && matchesSkill;
  });

  const getUrgencyColor = (urgency) => {
    switch (urgency) {
      case 'critical': return 'text-red-600 bg-red-50';
      case 'high': return 'text-orange-600 bg-orange-50';
      case 'medium': return 'text-yellow-600 bg-yellow-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const handleVolunteer = (opportunityId) => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
    // Handle volunteer signup logic here
    console.log('Volunteering for opportunity:', opportunityId);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Hero Section */}
      <section className="bg-gradient-to-r from-accent-600 to-primary-600 text-white py-16">
        <div className="max-w-6xl mx-auto px-4 text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <div className="w-20 h-20 bg-white/20 rounded-full flex items-center justify-center mx-auto mb-6">
              <Users className="w-12 h-12 text-white" />
            </div>
            <h1 className="text-4xl md:text-5xl font-bold mb-4">Volunteer Network</h1>
            <p className="text-xl text-white/90 max-w-3xl mx-auto">
              Join thousands of volunteers making a real difference in disaster response 
              and medical emergencies. Your time and skills save lives.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Section Toggle */}
      <section className="py-8 bg-white border-b">
        <div className="max-w-6xl mx-auto px-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <button
              onClick={() => setActiveSection('disaster')}
              className={`flex-1 px-6 py-4 rounded-lg font-medium transition-all flex items-center justify-center space-x-3 ${
                activeSection === 'disaster'
                  ? 'bg-disaster-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <Shield className="w-5 h-5" />
              <span>Disaster Rescue Volunteers</span>
            </button>
            <button
              onClick={() => setActiveSection('medical')}
              className={`flex-1 px-6 py-4 rounded-lg font-medium transition-all flex items-center justify-center space-x-3 ${
                activeSection === 'medical'
                  ? 'bg-donation-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <Stethoscope className="w-5 h-5" />
              <span>Medical Volunteers</span>
            </button>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-12 bg-white border-b">
        <div className="max-w-6xl mx-auto px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {[
              { value: '12,000+', label: 'Active Volunteers', icon: Users },
              { value: '450+', label: 'Missions Completed', icon: Shield },
              { value: '89', label: 'Current Operations', icon: Activity },
              { value: '4.8', label: 'Volunteer Rating', icon: Star }
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
                  <Icon className="w-8 h-8 text-accent-600 mx-auto mb-2" />
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
          {/* Search and Filter */}
          <div className="bg-white rounded-lg shadow p-4 mb-8">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="text"
                  placeholder={`Search ${activeSection} opportunities...`}
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent"
                />
              </div>
              <div className="flex items-center space-x-2">
                <Filter className="w-5 h-5 text-gray-400" />
                <select
                  value={selectedSkill}
                  onChange={(e) => setSelectedSkill(e.target.value)}
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent"
                >
                  {skills.map(skill => (
                    <option key={skill.id} value={skill.id}>
                      {skill.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Opportunities Grid */}
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredOpportunities.map((opportunity) => (
              <motion.div
                key={opportunity.id}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                whileHover={{ y: -5 }}
                className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-all"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                    opportunity.type === 'disaster' ? 'bg-disaster-100' : 'bg-donation-100'
                  }`}>
                    {opportunity.type === 'disaster' ? (
                      <Shield className="w-6 h-6 text-disaster-600" />
                    ) : (
                      <Stethoscope className="w-6 h-6 text-donation-600" />
                    )}
                  </div>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getUrgencyColor(opportunity.urgency)}`}>
                    {opportunity.urgency}
                  </span>
                </div>

                <h3 className="text-lg font-semibold text-gray-800 mb-2">{opportunity.title}</h3>
                <p className="text-gray-600 text-sm mb-4">{opportunity.description}</p>

                <div className="space-y-2 text-sm text-gray-500 mb-4">
                  <div className="flex items-center">
                    <MapPin className="w-4 h-4 mr-2" />
                    {opportunity.location}
                  </div>
                  <div className="flex items-center">
                    <Calendar className="w-4 h-4 mr-2" />
                    {opportunity.duration} • Starts {opportunity.startDate}
                  </div>
                  <div className="flex items-center">
                    <Users className="w-4 h-4 mr-2" />
                    {opportunity.volunteersSigned}/{opportunity.volunteersNeeded} volunteers
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="mb-4">
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${
                        opportunity.type === 'disaster' ? 'bg-disaster-600' : 'bg-donation-600'
                      }`}
                      style={{ width: `${(opportunity.volunteersSigned / opportunity.volunteersNeeded) * 100}%` }}
                    />
                  </div>
                </div>

                {/* Skills Tags */}
                <div className="flex flex-wrap gap-2 mb-4">
                  {opportunity.skills.map((skill) => (
                    <span
                      key={skill}
                      className="px-2 py-1 bg-accent-100 text-accent-700 rounded text-xs"
                    >
                      {skill.replace('-', ' ')}
                    </span>
                  ))}
                </div>

                <button
                  onClick={() => handleVolunteer(opportunity.id)}
                  className={`w-full py-2 rounded-lg transition-colors ${
                    opportunity.type === 'disaster'
                      ? 'bg-disaster-600 text-white hover:bg-disaster-700'
                      : 'bg-donation-600 text-white hover:bg-donation-700'
                  }`}
                >
                  {isAuthenticated ? 'Volunteer Now' : 'Login to Volunteer'}
                </button>
              </motion.div>
            ))}
          </div>

          {filteredOpportunities.length === 0 && (
            <div className="text-center py-12">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Search className="w-8 h-8 text-gray-400" />
              </div>
              <h3 className="text-xl font-semibold text-gray-800 mb-2">No opportunities found</h3>
              <p className="text-gray-600">Try adjusting your search or filters</p>
            </div>
          )}
        </div>
      </section>

      {/* Call to Action */}
      <section className="py-16 bg-gradient-to-r from-accent-600 to-primary-600">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <h2 className="text-3xl font-bold text-white mb-4">
              Ready to Make a Difference?
            </h2>
            <p className="text-xl text-white/90 mb-8">
              Join our volunteer network and be the hope someone needs in their darkest hour.
            </p>
            {!isAuthenticated ? (
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <button
                  onClick={() => navigate('/signup')}
                  className="px-8 py-4 bg-white text-accent-600 rounded-lg hover:bg-gray-100 transition-all transform hover:scale-105 font-semibold"
                >
                  <Plus className="w-5 h-5 inline mr-2" />
                  Become a Volunteer
                </button>
                <button
                  onClick={() => navigate('/login')}
                  className="px-8 py-4 bg-white/20 backdrop-blur text-white border-2 border-white rounded-lg hover:bg-white/30 transition-all transform hover:scale-105 font-semibold"
                >
                  Login to Continue
                </button>
              </div>
            ) : (
              <div className="bg-white/10 backdrop-blur rounded-lg p-6">
                <div className="flex items-center justify-center space-x-3 mb-4">
                  <CheckCircle className="w-6 h-6 text-green-400" />
                  <span className="text-white font-semibold">You're ready to volunteer!</span>
                </div>
                <p className="text-white/80">
                  Browse the opportunities above and sign up for missions that match your skills.
                </p>
              </div>
            )}
          </motion.div>
        </div>
      </section>

      {/* Impact Section */}
      <section className="py-12 bg-white">
        <div className="max-w-6xl mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl font-bold text-gray-800 mb-4">Volunteer Impact</h2>
            <p className="text-lg text-gray-600">See the difference our volunteers make every day</p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-disaster-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Shield className="w-8 h-8 text-disaster-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-800 mb-2">Disaster Response</h3>
              <p className="text-gray-600">
                Our disaster volunteers have helped over 50,000 people affected by natural disasters 
                through rescue operations, shelter management, and relief distribution.
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-donation-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Stethoscope className="w-8 h-8 text-donation-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-800 mb-2">Medical Support</h3>
              <p className="text-gray-600">
                Medical volunteers provide critical healthcare services to underserved communities, 
                saving lives through emergency care, health education, and ongoing support.
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-accent-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Heart className="w-8 h-8 text-accent-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-800 mb-2">Community Building</h3>
              <p className="text-gray-600">
                Beyond immediate relief, our volunteers help rebuild communities, provide emotional 
                support, and create lasting positive change in crisis-affected areas.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Volunteers;
