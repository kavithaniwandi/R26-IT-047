import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { 
  Heart, 
  Shield, 
  Users, 
  Phone, 
  ArrowRight, 
  AlertCircle,
  MapPin
} from 'lucide-react';

const Home = () => {
  const [scrollY, setScrollY] = useState(0);
  const [activeStat, setActiveStat] = useState(0);
  const [currentVideo, setCurrentVideo] = useState(0);
  const parallaxRef = useRef(null);

  useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveStat((prev) => (prev + 1) % 4);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    // Switch between videos every 10 seconds
    const videoInterval = setInterval(() => {
      setCurrentVideo((prev) => (prev + 1) % 2);
    }, 10000);
    return () => clearInterval(videoInterval);
  }, []);

  const stats = [
    { number: '10,000+', label: 'Lives Impacted', icon: Heart },
    { number: '500+', label: 'Active Volunteers', icon: Users },
    { number: '50+', label: 'Partner Organizations', icon: Shield },
    { number: '24/7', label: 'Emergency Response', icon: Phone }
  ];

  const features = [
    {
      title: 'Disaster Relief',
      description: 'Immediate response to natural disasters, providing shelter, food, and essential supplies.',
      icon: Shield,
      color: 'disaster',
      link: '/disaster-donations'
    },
    {
      title: 'Medical Support',
      description: 'Connecting patients with medical resources, volunteers, and emergency healthcare services.',
      icon: Heart,
      color: 'donation',
      link: '/medical-donations'
    },
    {
      title: 'Volunteer Network',
      description: 'Join thousands of volunteers making a difference in their communities during crises.',
      icon: Users,
      color: 'accent',
      link: '/volunteers'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-gray-50">
      {/* Hero Section with Video Background */}
      <section 
        ref={parallaxRef}
        className="relative min-h-screen flex items-center justify-center overflow-hidden"
      >
        {/* Video Background */}
        <div className="absolute inset-0 z-0">
          <video
            className="w-full h-full object-cover"
            autoPlay
            muted
            loop
            playsInline
            key={currentVideo}
          >
            <source src={`/assets/${currentVideo + 1}.mp4`} type="video/mp4" />
            Your browser does not support the video tag.
          </video>
          {/* Dark Overlay */}
          <div className="absolute inset-0 bg-black/50" />
        </div>
        
        {/* Floating Elements */}
        <motion.div
          className="absolute top-20 left-10 w-20 h-20 bg-disaster-500/20 rounded-full blur-xl z-10"
          animate={{
            y: [0, -20, 0],
            x: [0, 10, 0],
          }}
          transition={{
            duration: 6,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
        <motion.div
          className="absolute bottom-20 right-10 w-32 h-32 bg-donation-500/20 rounded-full blur-xl z-10"
          animate={{
            y: [0, 20, 0],
            x: [0, -10, 0],
          }}
          transition={{
            duration: 8,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />

        <div className="relative z-20 text-center px-4 max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <h1 className="text-5xl md:text-7xl font-bold mb-6 bg-gradient-to-r from-white to-gray-200 bg-clip-text text-transparent">
              Hope in Crisis
            </h1>
            <p className="text-xl md:text-2xl text-white mb-8 max-w-3xl mx-auto">
              Connecting communities, providing relief, and saving lives when disaster strikes. 
              Every second counts, every donation matters.
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="flex flex-col sm:flex-row gap-4 justify-center"
          >
            <Link
              to="/disaster-donations"
              className="inline-flex items-center justify-center px-8 py-4 bg-disaster-600 text-white rounded-lg hover:bg-disaster-700 transition-all transform hover:scale-105 shadow-lg"
            >
              <AlertCircle className="w-5 h-5 mr-2" />
              Emergency Relief
              <ArrowRight className="w-5 h-5 ml-2" />
            </Link>
            <Link
              to="/medical-donations"
              className="inline-flex items-center justify-center px-8 py-4 bg-donation-600 text-white rounded-lg hover:bg-donation-700 transition-all transform hover:scale-105 shadow-lg"
            >
              <Heart className="w-5 h-5 mr-2" />
              Medical Support
              <ArrowRight className="w-5 h-5 ml-2" />
            </Link>
          </motion.div>

          {/* Emergency Hotline */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="mt-12 inline-flex items-center px-6 py-3 bg-red-50/90 backdrop-blur border border-red-200 rounded-lg"
          >
            <Phone className="w-5 h-5 text-red-600 mr-3" />
            <div className="text-left">
              <p className="text-sm text-red-600 font-medium">24/7 Emergency Hotline</p>
              <p className="text-lg font-bold text-red-700">1-800-RELIEF</p>
            </div>
          </motion.div>
        </div>

        {/* Scroll Indicator */}
        <motion.div
          className="absolute bottom-8 left-1/2 transform -translate-x-1/2 z-20"
          animate={{ y: [0, 10, 0] }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          <div className="w-6 h-10 border-2 border-white rounded-full flex justify-center">
            <div className="w-1 h-3 bg-white rounded-full mt-2" />
          </div>
        </motion.div>
      </section>

      {/* Stats Section */}
      <section className="py-20 bg-white">
        <div className="max-w-6xl mx-auto px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat, index) => {
              const Icon = stat.icon;
              return (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  className={`text-center p-6 rounded-lg transition-all cursor-pointer ${
                    activeStat === index ? 'bg-primary-50 scale-105' : 'hover:bg-gray-50'
                  }`}
                  onMouseEnter={() => setActiveStat(index)}
                >
                  <Icon className={`w-12 h-12 mx-auto mb-4 ${
                    activeStat === index ? 'text-primary-600' : 'text-gray-400'
                  } transition-colors`} />
                  <div className="text-3xl font-bold text-gray-800 mb-2">{stat.number}</div>
                  <div className="text-gray-600">{stat.label}</div>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-gradient-to-b from-gray-50 to-white">
        <div className="max-w-6xl mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-bold mb-4 text-gray-800">
              How We Help
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Comprehensive support system for disaster relief and medical emergencies
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: index * 0.2 }}
                  whileHover={{ y: -10 }}
                  className="bg-white rounded-2xl shadow-xl p-8 hover:shadow-2xl transition-all"
                >
                  <div className={`w-16 h-16 bg-${feature.color}-100 rounded-lg flex items-center justify-center mb-6`}>
                    <Icon className={`w-8 h-8 text-${feature.color}-600`} />
                  </div>
                  <h3 className="text-2xl font-bold mb-4 text-gray-800">{feature.title}</h3>
                  <p className="text-gray-600 mb-6">{feature.description}</p>
                  <Link
                    to={feature.link}
                    className={`inline-flex items-center text-${feature.color}-600 font-medium hover:text-${feature.color}-700 transition-colors`}
                  >
                    Learn More
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Link>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Live Activity Feed */}
      <section className="py-20 bg-white">
        <div className="max-w-6xl mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-bold mb-4 text-gray-800">
              Live Activity Feed
            </h2>
            <p className="text-xl text-gray-600">Real-time updates from our relief efforts</p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              { type: 'disaster', title: 'Flood Response', location: 'Coastal Region', time: '2 hours ago', status: 'active' },
              { type: 'medical', title: 'Medical Camp', location: 'Central Hospital', time: '4 hours ago', status: 'completed' },
              { type: 'volunteer', title: 'Volunteer Drive', location: 'Community Center', time: '6 hours ago', status: 'ongoing' },
              { type: 'donation', title: 'Supply Distribution', location: 'North District', time: '8 hours ago', status: 'completed' },
              { type: 'emergency', title: 'Rescue Operation', location: 'Mountain Area', time: '12 hours ago', status: 'active' },
              { type: 'medical', title: 'Blood Donation Camp', location: 'City Hospital', time: '1 day ago', status: 'completed' }
            ].map((activity, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="bg-gray-50 rounded-lg p-6 hover:shadow-lg transition-all"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className={`w-3 h-3 rounded-full ${
                    activity.status === 'active' ? 'bg-green-500' : 
                    activity.status === 'ongoing' ? 'bg-yellow-500' : 'bg-gray-400'
                  }`} />
                  <span className="text-sm text-gray-500">{activity.time}</span>
                </div>
                <h4 className="font-semibold text-gray-800 mb-2">{activity.title}</h4>
                <div className="flex items-center text-gray-600 text-sm">
                  <MapPin className="w-4 h-4 mr-1" />
                  {activity.location}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section className="py-20 bg-gradient-to-b from-white to-gray-50">
        <div className="max-w-6xl mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-bold mb-4 text-gray-800">
              Stories of Hope
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Real impact from real people. See how your contributions make a difference.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                name: "Sarah Johnson",
                role: "Flood Survivor",
                story: "The relief team arrived within hours. They provided shelter, food, and medical care when we had nothing. They saved our family.",
                location: "Coastal Region",
                impact: "Family of 5 rescued"
              },
              {
                name: "Dr. Michael Chen",
                role: "Medical Volunteer",
                story: "Volunteering with ReliefHub has been the most rewarding experience. I've been able to provide critical care to communities that desperately need it.",
                location: "Rural Areas",
                impact: "200+ patients treated"
              },
              {
                name: "Maria Rodriguez",
                role: "Donor",
                story: "Every donation counts. I've seen firsthand how my contributions have helped rebuild lives and bring hope to desperate situations.",
                location: "City Center",
                impact: "10 families supported"
              }
            ].map((testimonial, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.2 }}
                className="bg-white rounded-2xl shadow-xl p-8 hover:shadow-2xl transition-all"
              >
                <div className="flex items-center mb-6">
                  <div className="w-12 h-12 bg-gradient-to-r from-disaster-500 to-donation-500 rounded-full flex items-center justify-center text-white font-bold text-lg">
                    {testimonial.name.charAt(0)}
                  </div>
                  <div className="ml-4">
                    <h4 className="font-semibold text-gray-800">{testimonial.name}</h4>
                    <p className="text-sm text-gray-600">{testimonial.role}</p>
                  </div>
                </div>
                <p className="text-gray-700 mb-4 italic">"{testimonial.story}"</p>
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center text-gray-500">
                    <MapPin className="w-4 h-4 mr-1" />
                    {testimonial.location}
                  </div>
                  <span className="text-disaster-600 font-medium">{testimonial.impact}</span>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Impact Metrics Section */}
      <section className="py-20 bg-white">
        <div className="max-w-6xl mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-bold mb-4 text-gray-800">
              Our Impact This Year
            </h2>
            <p className="text-xl text-gray-600">Numbers that represent lives changed and communities rebuilt</p>
          </motion.div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-12">
            {[
              { number: '50,000+', label: 'People Helped', color: 'disaster' },
              { number: '1,200+', label: 'Volunteers', color: 'accent' },
              { number: '89', label: 'Active Missions', color: 'primary' },
              { number: '$5.2M', label: 'Relief Funds', color: 'donation' }
            ].map((metric, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, scale: 0.8 }}
                whileInView={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="text-center"
              >
                <div className={`w-20 h-20 bg-${metric.color}-100 rounded-full flex items-center justify-center mx-auto mb-4`}>
                  <span className={`text-2xl font-bold text-${metric.color}-600`}>{metric.number}</span>
                </div>
                <p className="text-gray-600 font-medium">{metric.label}</p>
              </motion.div>
            ))}
          </div>

          {/* Progress Bars */}
          <div className="max-w-4xl mx-auto space-y-6">
            {[
              { label: 'Emergency Response Time', progress: 92, color: 'disaster' },
              { label: 'Medical Supplies Delivered', progress: 87, color: 'donation' },
              { label: 'Volunteer Satisfaction', progress: 95, color: 'accent' },
              { label: 'Community Recovery', progress: 78, color: 'primary' }
            ].map((item, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -50 }}
                whileInView={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
              >
                <div className="flex justify-between mb-2">
                  <span className="text-gray-700 font-medium">{item.label}</span>
                  <span className={`text-${item.color}-600 font-bold`}>{item.progress}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <motion.div
                    className={`bg-${item.color}-600 h-3 rounded-full`}
                    initial={{ width: 0 }}
                    whileInView={{ width: `${item.progress}%` }}
                    transition={{ duration: 1, delay: 0.5 }}
                  />
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Partners Section */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-6xl mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-bold mb-4 text-gray-800">
              Trusted Partners
            </h2>
            <p className="text-xl text-gray-600">Working together with leading organizations</p>
          </motion.div>

          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-8">
            {['Red Cross', 'UNICEF', 'WHO', 'Save Children', 'Habitat', 'Water.org'].map((partner, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, scale: 0.8 }}
                whileInView={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="bg-white rounded-lg p-6 flex items-center justify-center hover:shadow-lg transition-all"
              >
                <span className="text-gray-600 font-medium text-center">{partner}</span>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Enhanced Call to Action */}
      <section className="py-20 bg-gradient-to-r from-disaster-600 via-primary-600 to-donation-600 relative overflow-hidden">
        {/* Background Pattern */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 left-0 w-40 h-40 bg-white rounded-full blur-3xl" />
          <div className="absolute top-20 right-20 w-60 h-60 bg-white rounded-full blur-3xl" />
          <div className="absolute bottom-0 left-1/2 w-80 h-80 bg-white rounded-full blur-3xl" />
        </div>
        
        <div className="max-w-4xl mx-auto px-4 text-center relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-4xl md:text-5xl font-bold mb-6 text-white">
              Be the Hope Someone Needs
            </h2>
            <p className="text-xl text-white/90 mb-8 max-w-2xl mx-auto">
              Join thousands of volunteers and donors making a real difference in crisis situations. 
              Your compassion can save lives and rebuild communities.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                to="/signup"
                className="inline-flex items-center justify-center px-8 py-4 bg-white text-disaster-600 rounded-lg hover:bg-gray-100 transition-all transform hover:scale-105 font-semibold shadow-lg"
              >
                <Users className="w-5 h-5 mr-2" />
                Become a Volunteer
              </Link>
              <Link
                to="/disaster-donations"
                className="inline-flex items-center justify-center px-8 py-4 bg-white/20 backdrop-blur text-white border-2 border-white rounded-lg hover:bg-white/30 transition-all transform hover:scale-105 font-semibold"
              >
                <Heart className="w-5 h-5 mr-2" />
                Make a Donation
              </Link>
            </div>
            
            <div className="mt-12 grid grid-cols-3 gap-8 text-white">
              <div className="text-center">
                <div className="text-3xl font-bold mb-2">24/7</div>
                <div className="text-white/80">Emergency Support</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold mb-2">100+</div>
                <div className="text-white/80">Active Volunteers</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold mb-2">$2.5M</div>
                <div className="text-white/80">Funds Raised</div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>
    </div>
  );
};

export default Home;
