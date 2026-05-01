import { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Phone, 
  Mail, 
  MapPin, 
  Clock, 
  Send, 
  MessageCircle,
  AlertCircle,
  Shield,
  Heart,
  Users,
  Building,
  Globe
} from 'lucide-react';

const Contacts = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: '',
    message: '',
    contactType: 'general'
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    // Simulate form submission
    setTimeout(() => {
      setIsSubmitting(false);
      setSubmitted(true);
      setFormData({
        name: '',
        email: '',
        subject: '',
        message: '',
        contactType: 'general'
      });
    }, 1500);
  };

  const contactInfo = [
    {
      title: 'Emergency Hotline',
      value: '1-800-RELIEF',
      description: '24/7 Emergency Response',
      icon: Phone,
      color: 'disaster',
      type: 'phone'
    },
    {
      title: 'General Inquiries',
      value: 'info@reliefhub.org',
      description: 'General questions and information',
      icon: Mail,
      color: 'primary',
      type: 'email'
    },
    {
      title: 'Volunteer Support',
      value: 'volunteers@reliefhub.org',
      description: 'Volunteer coordination and support',
      icon: Users,
      color: 'accent',
      type: 'email'
    },
    {
      title: 'Donor Relations',
      value: 'donors@reliefhub.org',
      description: 'Donation inquiries and acknowledgments',
      icon: Heart,
      color: 'donation',
      type: 'email'
    }
  ];

  const offices = [
    {
      city: 'New York Headquarters',
      address: '123 Relief Street, New York, NY 10001',
      phone: '+1 (212) 555-0123',
      hours: 'Mon-Fri: 9:00 AM - 6:00 PM',
      services: ['Emergency Response', 'Volunteer Training', 'Donor Relations']
    },
    {
      city: 'Los Angeles Office',
      address: '456 Hope Avenue, Los Angeles, CA 90001',
      phone: '+1 (310) 555-0456',
      hours: 'Mon-Fri: 8:00 AM - 5:00 PM',
      services: ['Disaster Relief', 'Medical Support', 'Community Outreach']
    },
    {
      city: 'Chicago Regional Hub',
      address: '789 Unity Boulevard, Chicago, IL 60601',
      phone: '+1 (312) 555-0789',
      hours: 'Mon-Fri: 9:00 AM - 6:00 PM',
      services: ['Midwest Operations', 'Logistics', 'Training Center']
    }
  ];

  const emergencyContacts = [
    { service: 'Medical Emergency', number: '911', description: 'Life-threatening medical emergencies' },
    { service: 'Fire Department', number: '911', description: 'Fire emergencies and rescue' },
    { service: 'Police', number: '911', description: 'Security and law enforcement' },
    { service: 'Poison Control', number: '1-800-222-1222', description: 'Poison emergencies and information' },
    { service: 'Crisis Hotline', number: '988', description: 'Mental health crisis support' },
    { service: 'Disaster Relief', number: '1-800-RELIEF', description: 'Our 24/7 disaster response line' }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Hero Section */}
      <section className="bg-gradient-to-r from-primary-600 to-secondary-600 text-white py-16">
        <div className="max-w-6xl mx-auto px-4 text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h1 className="text-4xl md:text-5xl font-bold mb-4">Contact Us</h1>
            <p className="text-xl text-white/90 max-w-3xl mx-auto">
              We're here to help. Reach out to us for emergencies, volunteer opportunities, 
              or any questions about our disaster relief and medical support services.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Emergency Contacts */}
      <section className="py-12 bg-red-50 border-b border-red-200">
        <div className="max-w-6xl mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-red-100 rounded-lg p-6"
          >
            <div className="flex items-center space-x-3 mb-4">
              <AlertCircle className="w-8 h-8 text-red-600" />
              <h2 className="text-2xl font-bold text-red-900">Emergency Contacts</h2>
            </div>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {emergencyContacts.map((contact, index) => (
                <div key={index} className="bg-white rounded-lg p-4 border border-red-200">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-semibold text-gray-800">{contact.service}</h3>
                      <p className="text-2xl font-bold text-red-600 my-1">{contact.number}</p>
                      <p className="text-sm text-gray-600">{contact.description}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      {/* Main Contact Info */}
      <section className="py-16">
        <div className="max-w-6xl mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl md:text-4xl font-bold text-gray-800 mb-4">Get in Touch</h2>
            <p className="text-lg text-gray-600">Choose the best way to reach us based on your needs</p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
            {contactInfo.map((contact, index) => {
              const Icon = contact.icon;
              return (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-all"
                >
                  <div className={`w-14 h-14 bg-${contact.color}-100 rounded-lg flex items-center justify-center mb-4`}>
                    <Icon className={`w-7 h-7 text-${contact.color}-600`} />
                  </div>
                  <h3 className="font-semibold text-gray-800 mb-2">{contact.title}</h3>
                  <p className={`text-lg font-bold text-${contact.color}-600 mb-1`}>
                    {contact.value}
                  </p>
                  <p className="text-sm text-gray-600">{contact.description}</p>
                </motion.div>
              );
            })}
          </div>

          {/* Contact Form */}
          <div className="grid lg:grid-cols-2 gap-12">
            <motion.div
              initial={{ opacity: 0, x: -50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6 }}
            >
              <h3 className="text-2xl font-bold text-gray-800 mb-6">Send us a Message</h3>
              
              {submitted ? (
                <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
                  <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Send className="w-8 h-8 text-green-600" />
                  </div>
                  <h4 className="text-xl font-semibold text-green-900 mb-2">Message Sent!</h4>
                  <p className="text-green-700">We'll get back to you within 24 hours.</p>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div>
                    <label htmlFor="contactType" className="block text-sm font-medium text-gray-700 mb-2">
                      Contact Type
                    </label>
                    <select
                      id="contactType"
                      name="contactType"
                      value={formData.contactType}
                      onChange={handleChange}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    >
                      <option value="general">General Inquiry</option>
                      <option value="emergency">Emergency</option>
                      <option value="volunteer">Volunteer Question</option>
                      <option value="donation">Donation Information</option>
                      <option value="partnership">Partnership</option>
                    </select>
                  </div>

                  <div className="grid md:grid-cols-2 gap-6">
                    <div>
                      <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                        Your Name *
                      </label>
                      <input
                        type="text"
                        id="name"
                        name="name"
                        value={formData.name}
                        onChange={handleChange}
                        required
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                        placeholder="John Doe"
                      />
                    </div>
                    <div>
                      <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                        Email Address *
                      </label>
                      <input
                        type="email"
                        id="email"
                        name="email"
                        value={formData.email}
                        onChange={handleChange}
                        required
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                        placeholder="your@email.com"
                      />
                    </div>
                  </div>

                  <div>
                    <label htmlFor="subject" className="block text-sm font-medium text-gray-700 mb-2">
                      Subject *
                    </label>
                    <input
                      type="text"
                      id="subject"
                      name="subject"
                      value={formData.subject}
                      onChange={handleChange}
                      required
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                      placeholder="How can we help you?"
                    />
                  </div>

                  <div>
                    <label htmlFor="message" className="block text-sm font-medium text-gray-700 mb-2">
                      Message *
                    </label>
                    <textarea
                      id="message"
                      name="message"
                      value={formData.message}
                      onChange={handleChange}
                      required
                      rows={5}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
                      placeholder="Tell us more about your inquiry..."
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="w-full bg-gradient-to-r from-primary-600 to-secondary-600 text-white py-3 rounded-lg hover:from-primary-700 hover:to-secondary-700 transition-all transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
                  >
                    {isSubmitting ? (
                      <>
                        <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        <span>Sending...</span>
                      </>
                    ) : (
                      <>
                        <Send className="w-5 h-5" />
                        <span>Send Message</span>
                      </>
                    )}
                  </button>
                </form>
              )}
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6 }}
              className="space-y-8"
            >
              <div>
                <h3 className="text-2xl font-bold text-gray-800 mb-6">Our Offices</h3>
                <div className="space-y-6">
                  {offices.map((office, index) => (
                    <div key={index} className="bg-white rounded-lg shadow-lg p-6">
                      <div className="flex items-start space-x-4">
                        <Building className="w-6 h-6 text-primary-600 mt-1 flex-shrink-0" />
                        <div className="flex-1">
                          <h4 className="font-semibold text-gray-800 mb-2">{office.city}</h4>
                          <div className="space-y-2 text-sm">
                            <div className="flex items-center text-gray-600">
                              <MapPin className="w-4 h-4 mr-2 flex-shrink-0" />
                              {office.address}
                            </div>
                            <div className="flex items-center text-gray-600">
                              <Phone className="w-4 h-4 mr-2 flex-shrink-0" />
                              {office.phone}
                            </div>
                            <div className="flex items-center text-gray-600">
                              <Clock className="w-4 h-4 mr-2 flex-shrink-0" />
                              {office.hours}
                            </div>
                          </div>
                          <div className="mt-3">
                            <p className="text-sm font-medium text-gray-700 mb-2">Services:</p>
                            <div className="flex flex-wrap gap-2">
                              {office.services.map((service, idx) => (
                                <span
                                  key={idx}
                                  className="px-2 py-1 bg-primary-100 text-primary-700 rounded text-xs"
                                >
                                  {service}
                                </span>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-gradient-to-r from-primary-50 to-secondary-50 rounded-lg p-6">
                <div className="flex items-center space-x-3 mb-4">
                  <MessageCircle className="w-6 h-6 text-primary-600" />
                  <h4 className="font-semibold text-gray-800">Live Chat Support</h4>
                </div>
                <p className="text-gray-600 mb-4">
                  Get instant help from our support team through live chat.
                </p>
                <button className="w-full bg-primary-600 text-white py-2 rounded-lg hover:bg-primary-700 transition-colors">
                  Start Live Chat
                </button>
              </div>
            </motion.div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Contacts;
