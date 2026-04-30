import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  User, 
  Mail, 
  Phone, 
  MapPin, 
  Heart, 
  Shield, 
  Users, 
  Calendar,
  Award,
  Activity,
  Settings,
  LogOut,
  Edit,
  Camera,
  TrendingUp,
  Clock,
  CheckCircle
} from 'lucide-react';

const Profile = () => {
  const [user, setUser] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const navigate = useNavigate();

  useEffect(() => {
    const userData = localStorage.getItem('user');
    if (userData) {
      setUser(JSON.parse(userData));
    } else {
      navigate('/login');
    }
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem('user');
    navigate('/');
  };

  const stats = [
    { label: 'Total Donations', value: '$2,450', icon: Heart, color: 'donation' },
    { label: 'Volunteer Hours', value: '124', icon: Clock, color: 'primary' },
    { label: 'Lives Impacted', value: '47', icon: Users, color: 'accent' },
    { label: 'Missions Completed', value: '12', icon: Shield, color: 'disaster' }
  ];

  const activities = [
    { type: 'donation', title: 'Emergency Medical Supplies', date: '2 days ago', amount: '$250', status: 'completed' },
    { type: 'volunteer', title: 'Flood Relief Operation', date: '1 week ago', hours: '8 hours', status: 'completed' },
    { type: 'donation', title: 'Food Distribution Program', date: '2 weeks ago', amount: '$100', status: 'completed' },
    { type: 'volunteer', title: 'Medical Camp Volunteer', date: '3 weeks ago', hours: '6 hours', status: 'completed' }
  ];

  const achievements = [
    { title: 'First Responder', description: 'Completed first emergency mission', icon: Shield, earned: true },
    { title: 'Dedicated Volunteer', description: '50+ volunteer hours', icon: Clock, earned: true },
    { title: 'Life Saver', description: 'Helped 25+ people', icon: Heart, earned: true },
    { title: 'Team Leader', description: 'Led 5+ missions', icon: Users, earned: false }
  ];

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 py-8">
      <div className="max-w-6xl mx-auto px-4">
        {/* Profile Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl shadow-xl overflow-hidden mb-8"
        >
          <div className="bg-gradient-to-r from-primary-600 to-secondary-600 h-32"></div>
          <div className="px-8 pb-8">
            <div className="flex flex-col sm:flex-row items-center sm:items-end -mt-16 sm:-mt-12 space-y-4 sm:space-y-0 sm:space-x-6">
              <div className="relative">
                <div className="w-32 h-32 bg-gray-200 rounded-full border-4 border-white shadow-lg flex items-center justify-center">
                  <User className="w-16 h-16 text-gray-400" />
                </div>
                <button className="absolute bottom-0 right-0 w-10 h-10 bg-primary-600 rounded-full flex items-center justify-center text-white hover:bg-primary-700 transition-colors">
                  <Camera className="w-5 h-5" />
                </button>
              </div>
              
              <div className="flex-1 text-center sm:text-left">
                <h1 className="text-3xl font-bold text-gray-800 mb-2">{user.name}</h1>
                <p className="text-gray-600 mb-2">{user.role}</p>
                <div className="flex flex-wrap items-center justify-center sm:justify-start gap-4 text-sm text-gray-500">
                  <div className="flex items-center">
                    <Mail className="w-4 h-4 mr-1" />
                    {user.email}
                  </div>
                  {user.phone && (
                    <div className="flex items-center">
                      <Phone className="w-4 h-4 mr-1" />
                      {user.phone}
                    </div>
                  )}
                </div>
              </div>

              <div className="flex space-x-3">
                <button
                  onClick={() => setIsEditing(!isEditing)}
                  className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors flex items-center space-x-2"
                >
                  <Edit className="w-4 h-4" />
                  <span>Edit Profile</span>
                </button>
                <button
                  onClick={handleLogout}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors flex items-center space-x-2"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Logout</span>
                </button>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
          {stats.map((stat, index) => {
            const Icon = stat.icon;
            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-all"
              >
                <div className={`w-12 h-12 bg-${stat.color}-100 rounded-lg flex items-center justify-center mb-4`}>
                  <Icon className={`w-6 h-6 text-${stat.color}-600`} />
                </div>
                <div className="text-2xl font-bold text-gray-800 mb-1">{stat.value}</div>
                <div className="text-sm text-gray-600">{stat.label}</div>
              </motion.div>
            );
          })}
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8 px-8">
              {['overview', 'activities', 'achievements'].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm capitalize transition-colors ${
                    activeTab === tab
                      ? 'border-primary-600 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  {tab}
                </button>
              ))}
            </nav>
          </div>

          <div className="p-8">
            {/* Overview Tab */}
            {activeTab === 'overview' && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-8"
              >
                <div>
                  <h3 className="text-xl font-semibold text-gray-800 mb-4">About Me</h3>
                  <p className="text-gray-600">
                    Passionate about making a difference in communities during times of crisis. 
                    Dedicated volunteer with expertise in emergency response and medical support.
                  </p>
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-gray-800 mb-4">Skills & Expertise</h3>
                  <div className="flex flex-wrap gap-2">
                    {user.skills?.map((skill, index) => (
                      <span
                        key={index}
                        className="px-3 py-1 bg-primary-100 text-primary-700 rounded-full text-sm"
                      >
                        {skill}
                      </span>
                    )) || (
                      <span className="text-gray-500">No skills added yet</span>
                    )}
                  </div>
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-gray-800 mb-4">Impact Summary</h3>
                  <div className="grid md:grid-cols-2 gap-6">
                    <div className="bg-green-50 rounded-lg p-6">
                      <div className="flex items-center justify-between mb-4">
                        <TrendingUp className="w-8 h-8 text-green-600" />
                        <span className="text-2xl font-bold text-green-600">+23%</span>
                      </div>
                      <h4 className="font-semibold text-green-900 mb-2">Monthly Impact</h4>
                      <p className="text-green-700 text-sm">Increased contribution compared to last month</p>
                    </div>
                    <div className="bg-blue-50 rounded-lg p-6">
                      <div className="flex items-center justify-between mb-4">
                        <Activity className="w-8 h-8 text-blue-600" />
                        <span className="text-2xl font-bold text-blue-600">Active</span>
                      </div>
                      <h4 className="font-semibold text-blue-900 mb-2">Current Status</h4>
                      <p className="text-blue-700 text-sm">Available for emergency response</p>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {/* Activities Tab */}
            {activeTab === 'activities' && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-4"
              >
                <h3 className="text-xl font-semibold text-gray-800 mb-4">Recent Activities</h3>
                {activities.map((activity, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <div className={`w-2 h-2 rounded-full ${
                            activity.type === 'donation' ? 'bg-donation-500' : 'bg-primary-500'
                          }`} />
                          <h4 className="font-semibold text-gray-800">{activity.title}</h4>
                          <CheckCircle className="w-4 h-4 text-green-500" />
                        </div>
                        <div className="flex items-center space-x-4 text-sm text-gray-600">
                          <span>{activity.date}</span>
                          {activity.amount && <span>• {activity.amount}</span>}
                          {activity.hours && <span>• {activity.hours}</span>}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </motion.div>
            )}

            {/* Achievements Tab */}
            {activeTab === 'achievements' && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-4"
              >
                <h3 className="text-xl font-semibold text-gray-800 mb-4">Achievements & Badges</h3>
                <div className="grid md:grid-cols-2 gap-4">
                  {achievements.map((achievement, index) => {
                    const Icon = achievement.icon;
                    return (
                      <div
                        key={index}
                        className={`border rounded-lg p-6 transition-all ${
                          achievement.earned
                            ? 'border-yellow-300 bg-yellow-50 hover:shadow-md'
                            : 'border-gray-200 bg-gray-50 opacity-60'
                        }`}
                      >
                        <div className="flex items-start space-x-4">
                          <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                            achievement.earned
                              ? 'bg-yellow-200 text-yellow-700'
                              : 'bg-gray-200 text-gray-400'
                          }`}>
                            <Icon className="w-6 h-6" />
                          </div>
                          <div className="flex-1">
                            <h4 className={`font-semibold mb-1 ${
                              achievement.earned ? 'text-yellow-900' : 'text-gray-600'
                            }`}>
                              {achievement.title}
                            </h4>
                            <p className={`text-sm ${
                              achievement.earned ? 'text-yellow-700' : 'text-gray-500'
                            }`}>
                              {achievement.description}
                            </p>
                            {achievement.earned && (
                              <div className="mt-2 text-xs text-yellow-600 font-medium">
                                ✓ Earned
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </motion.div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;
