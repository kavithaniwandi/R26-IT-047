import { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Menu, X, User, Heart, Shield, Users, Phone, LogIn, ChevronDown } from 'lucide-react';

const Header = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState(null);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const userData = localStorage.getItem('user');
    if (userData) {
      setUser(JSON.parse(userData));
      setIsLoggedIn(true);
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('user');
    setIsLoggedIn(false);
    setUser(null);
    setIsProfileOpen(false);
    navigate('/');
  };

  const isActivePath = (path) => location.pathname === path;

  return (
    <header className="fixed top-0 w-full bg-white/95 backdrop-blur-md shadow-lg z-50 transition-all duration-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link 
            to="/" 
            className="flex items-center space-x-2 group"
          >
            <div className="w-10 h-10 bg-gradient-to-r from-disaster-500 to-donation-500 rounded-lg flex items-center justify-center transform group-hover:scale-110 transition-transform">
              <Heart className="w-6 h-6 text-white" />
            </div>
            <span className="text-xl font-bold bg-gradient-to-r from-disaster-600 to-donation-600 bg-clip-text text-transparent">
              ReliefHub
            </span>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-8">
            <Link
              to="/"
              className={`text-gray-700 hover:text-primary-600 transition-colors font-medium ${
                isActivePath('/') ? 'text-primary-600' : ''
              }`}
            >
              Home
            </Link>
            
            <Link
              to="/contacts"
              className={`text-gray-700 hover:text-primary-600 transition-colors font-medium ${
                isActivePath('/contacts') ? 'text-primary-600' : ''
              }`}
            >
              Contacts
            </Link>

            <div className="relative group">
              <button className="flex items-center space-x-1 text-gray-700 hover:text-primary-600 transition-colors font-medium">
                <span>Medical Donations</span>
                <ChevronDown className="w-4 h-4" />
              </button>
              <div className="absolute top-full left-0 mt-2 w-48 bg-white rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 transform group-hover:translate-y-0 translate-y-2">
                <Link
                  to="/medical-donations"
                  className="block px-4 py-3 text-gray-700 hover:bg-primary-50 hover:text-primary-600 transition-colors rounded-t-lg"
                >
                  Donate Medical Supplies
                </Link>
                <Link
                  to="/medical-requests"
                  className="block px-4 py-3 text-gray-700 hover:bg-primary-50 hover:text-primary-600 transition-colors rounded-b-lg"
                >
                  Request Medical Help
                </Link>
              </div>
            </div>

            <div className="relative group">
              <button className="flex items-center space-x-1 text-gray-700 hover:text-primary-600 transition-colors font-medium">
                <span>Disaster Rescue</span>
                <ChevronDown className="w-4 h-4" />
              </button>
              <div className="absolute top-full left-0 mt-2 w-48 bg-white rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 transform group-hover:translate-y-0 translate-y-2">
                <Link
                  to="/disaster-donations"
                  className="block px-4 py-3 text-gray-700 hover:bg-disaster-50 hover:text-disaster-600 transition-colors rounded-t-lg"
                >
                  Donate for Disaster Relief
                </Link>
                <Link
                  to="/disaster-rescue"
                  className="block px-4 py-3 text-gray-700 hover:bg-disaster-50 hover:text-disaster-600 transition-colors rounded-b-lg"
                >
                  Request Rescue
                </Link>
              </div>
            </div>

            <div className="relative group">
              <button className="flex items-center space-x-1 text-gray-700 hover:text-primary-600 transition-colors font-medium">
                <span>Volunteers</span>
                <ChevronDown className="w-4 h-4" />
              </button>
              <div className="absolute top-full left-0 mt-2 w-48 bg-white rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 transform group-hover:translate-y-0 translate-y-2">
                <Link
                  to="/volunteers/disaster"
                  className="block px-4 py-3 text-gray-700 hover:bg-accent-50 hover:text-accent-600 transition-colors rounded-t-lg"
                >
                  Disaster Rescue Volunteers
                </Link>
                <Link
                  to="/volunteers/medical"
                  className="block px-4 py-3 text-gray-700 hover:bg-accent-50 hover:text-accent-600 transition-colors rounded-b-lg"
                >
                  Medical Volunteers
                </Link>
              </div>
            </div>
          </nav>

          {/* Right side buttons */}
          <div className="flex items-center space-x-4">
            {isLoggedIn ? (
              <div className="relative">
                <button
                  onClick={() => setIsProfileOpen(!isProfileOpen)}
                  className="flex items-center space-x-2 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition-colors"
                >
                  <User className="w-4 h-4" />
                  <span className="hidden sm:block">Profile</span>
                </button>
                
                {isProfileOpen && (
                  <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-xl border border-gray-100">
                    <div className="p-4 border-b border-gray-100">
                      <p className="font-semibold text-gray-800">{user?.name || 'User'}</p>
                      <p className="text-sm text-gray-500">{user?.email || 'user@example.com'}</p>
                    </div>
                    <div className="p-2">
                      <Link
                        to="/profile"
                        className="block px-3 py-2 text-gray-700 hover:bg-primary-50 hover:text-primary-600 rounded-md transition-colors"
                        onClick={() => setIsProfileOpen(false)}
                      >
                        View Profile
                      </Link>
                      <button
                        onClick={handleLogout}
                        className="w-full text-left px-3 py-2 text-gray-700 hover:bg-red-50 hover:text-red-600 rounded-md transition-colors"
                      >
                        Logout
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <Link
                to="/login"
                className="flex items-center space-x-2 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition-colors"
              >
                <LogIn className="w-4 h-4" />
                <span className="hidden sm:block">Login</span>
              </Link>
            )}

            {/* Mobile menu button */}
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="md:hidden p-2 rounded-lg hover:bg-gray-100 transition-colors"
            >
              {isMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {isMenuOpen && (
          <div className="md:hidden py-4 border-t border-gray-200">
            <nav className="flex flex-col space-y-3">
              <Link
                to="/"
                className="text-gray-700 hover:text-primary-600 transition-colors font-medium px-2 py-1"
                onClick={() => setIsMenuOpen(false)}
              >
                Home
              </Link>
              <Link
                to="/contacts"
                className="text-gray-700 hover:text-primary-600 transition-colors font-medium px-2 py-1"
                onClick={() => setIsMenuOpen(false)}
              >
                Contacts
              </Link>
              <Link
                to="/medical-donations"
                className="text-gray-700 hover:text-primary-600 transition-colors font-medium px-2 py-1"
                onClick={() => setIsMenuOpen(false)}
              >
                Medical Donations
              </Link>
              <Link
                to="/disaster-donations"
                className="text-gray-700 hover:text-primary-600 transition-colors font-medium px-2 py-1"
                onClick={() => setIsMenuOpen(false)}
              >
                Disaster Rescue Donations
              </Link>
              <Link
                to="/volunteers/disaster"
                className="text-gray-700 hover:text-primary-600 transition-colors font-medium px-2 py-1"
                onClick={() => setIsMenuOpen(false)}
              >
                Disaster Volunteers
              </Link>
              <Link
                to="/volunteers/medical"
                className="text-gray-700 hover:text-primary-600 transition-colors font-medium px-2 py-1"
                onClick={() => setIsMenuOpen(false)}
              >
                Medical Volunteers
              </Link>
            </nav>
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;
