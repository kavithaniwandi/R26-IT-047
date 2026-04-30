import { Heart, Phone, Mail, MapPin, Shield, Users, AlertCircle } from 'lucide-react';

const Footer = () => {
  return (
    <footer className="bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {/* Organization Info */}
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <div className="w-10 h-10 bg-gradient-to-r from-disaster-500 to-donation-500 rounded-lg flex items-center justify-center">
                <Heart className="w-6 h-6 text-white" />
              </div>
              <span className="text-xl font-bold">ReliefHub</span>
            </div>
            <p className="text-gray-300 text-sm leading-relaxed">
              Connecting communities in times of crisis. We provide disaster relief and medical support to those who need it most.
            </p>
            <div className="flex space-x-3">
              <a href="#" className="w-10 h-10 bg-gray-700 rounded-full flex items-center justify-center hover:bg-gray-600 transition-colors">
                <Mail className="w-5 h-5" />
              </a>
              <a href="#" className="w-10 h-10 bg-gray-700 rounded-full flex items-center justify-center hover:bg-gray-600 transition-colors">
                <Phone className="w-5 h-5" />
              </a>
            </div>
          </div>

          {/* Quick Links */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-white">Quick Links</h3>
            <ul className="space-y-2">
              <li>
                <a href="/" className="text-gray-300 hover:text-white transition-colors text-sm">Home</a>
              </li>
              <li>
                <a href="/contacts" className="text-gray-300 hover:text-white transition-colors text-sm">Contact Us</a>
              </li>
              <li>
                <a href="/medical-donations" className="text-gray-300 hover:text-white transition-colors text-sm">Medical Donations</a>
              </li>
              <li>
                <a href="/disaster-donations" className="text-gray-300 hover:text-white transition-colors text-sm">Disaster Relief</a>
              </li>
              <li>
                <a href="/volunteers" className="text-gray-300 hover:text-white transition-colors text-sm">Volunteer</a>
              </li>
            </ul>
          </div>

          {/* Services */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-white">Our Services</h3>
            <ul className="space-y-3">
              <li className="flex items-start space-x-3">
                <Shield className="w-5 h-5 text-disaster-400 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-white text-sm font-medium">Disaster Response</p>
                  <p className="text-gray-400 text-xs">24/7 emergency assistance</p>
                </div>
              </li>
              <li className="flex items-start space-x-3">
                <Heart className="w-5 h-5 text-donation-400 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-white text-sm font-medium">Medical Support</p>
                  <p className="text-gray-400 text-xs">Healthcare and supplies</p>
                </div>
              </li>
              <li className="flex items-start space-x-3">
                <Users className="w-5 h-5 text-accent-400 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-white text-sm font-medium">Volunteer Network</p>
                  <p className="text-gray-400 text-xs">Community helpers</p>
                </div>
              </li>
            </ul>
          </div>

          {/* Contact Info */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-white">Contact Info</h3>
            <ul className="space-y-3">
              <li className="flex items-center space-x-3">
                <Phone className="w-5 h-5 text-primary-400 flex-shrink-0" />
                <div>
                  <p className="text-white text-sm">Emergency Hotline</p>
                  <p className="text-gray-300 text-sm">+1 (555) 123-4567</p>
                </div>
              </li>
              <li className="flex items-center space-x-3">
                <Mail className="w-5 h-5 text-primary-400 flex-shrink-0" />
                <div>
                  <p className="text-white text-sm">Email Us</p>
                  <p className="text-gray-300 text-sm">help@reliefhub.org</p>
                </div>
              </li>
              <li className="flex items-center space-x-3">
                <MapPin className="w-5 h-5 text-primary-400 flex-shrink-0" />
                <div>
                  <p className="text-white text-sm">Headquarters</p>
                  <p className="text-gray-300 text-sm">123 Relief Street, Hope City, HC 12345</p>
                </div>
              </li>
            </ul>
          </div>
        </div>

        {/* Emergency Alert */}
        <div className="mt-8 p-4 bg-disaster-900/30 border border-disaster-700/50 rounded-lg">
          <div className="flex items-center space-x-3">
            <AlertCircle className="w-6 h-6 text-disaster-400 flex-shrink-0" />
            <div>
              <p className="text-white font-medium">24/7 Emergency Response</p>
              <p className="text-gray-300 text-sm">If you're in immediate danger, call your local emergency services first.</p>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="mt-8 pt-8 border-t border-gray-700">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            <p className="text-gray-400 text-sm">
              © 2024 ReliefHub. All rights reserved. Made with <Heart className="w-4 h-4 inline text-red-500" /> for humanity.
            </p>
            <div className="flex space-x-6 text-sm">
              <a href="#" className="text-gray-400 hover:text-white transition-colors">Privacy Policy</a>
              <a href="#" className="text-gray-400 hover:text-white transition-colors">Terms of Service</a>
              <a href="#" className="text-gray-400 hover:text-white transition-colors">Cookie Policy</a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
