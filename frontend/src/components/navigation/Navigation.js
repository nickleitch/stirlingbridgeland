import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

const Navigation = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const menuItems = [
    {
      name: 'Projects',
      path: '/',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-4m-5 0H3m2 0h2M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
      )
    },
    {
      name: 'API Management',
      path: '/api-management',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v14a2 2 0 002 2z" />
        </svg>
      )
    },
    {
      name: 'User Profile',
      path: '/profile',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
      )
    }
  ];

  const isActiveRoute = (path) => {
    if (path === '/') {
      return location.pathname === '/' || location.pathname.startsWith('/dashboard/');
    }
    return location.pathname.startsWith(path);
  };

  const handleNavigation = (path) => {
    navigate(path);
    setIsMobileMenuOpen(false);
  };

  return (
    <nav className="bg-white shadow-lg border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo and App Name */}
          <div className="flex items-center">
            <div className="flex-shrink-0 flex items-center">
              {/* Landstream Logo SVG */}
              <div className="h-10 w-10 mr-3">
                <svg viewBox="0 0 100 100" className="h-10 w-10">
                  <circle 
                    cx="50" 
                    cy="50" 
                    r="45" 
                    fill="none" 
                    stroke="#374151" 
                    strokeWidth="8"
                  />
                  {/* Horizontal line */}
                  <line 
                    x1="20" 
                    y1="50" 
                    x2="80" 
                    y2="50" 
                    stroke="#374151" 
                    strokeWidth="6"
                  />
                  {/* Vertical line */}
                  <line 
                    x1="50" 
                    y1="20" 
                    x2="50" 
                    y2="80" 
                    stroke="#374151" 
                    strokeWidth="6"
                  />
                  {/* Bottom extension */}
                  <line 
                    x1="50" 
                    y1="80" 
                    x2="50" 
                    y2="95" 
                    stroke="#374151" 
                    strokeWidth="6"
                  />
                </svg>
              </div>
              <div className="ml-1">
                <h1 className="text-xl font-bold text-gray-900 tracking-wider">
                  LANDSTREAM
                </h1>
                <p className="text-xs text-gray-500 -mt-1 tracking-wide">
                  URBAN PLANNING & DEVELOPMENT PROCESS
                </p>
              </div>
            </div>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            {menuItems.map((item) => (
              <button
                key={item.name}
                onClick={() => handleNavigation(item.path)}
                className={`inline-flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 ${
                  isActiveRoute(item.path)
                    ? 'text-teal-600 bg-teal-50 border-b-2 border-teal-600'
                    : 'text-gray-700 hover:text-teal-600 hover:bg-teal-50'
                }`}
              >
                {item.icon}
                <span className="ml-2">{item.name}</span>
              </button>
            ))}
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden flex items-center">
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="inline-flex items-center justify-center p-2 rounded-md text-gray-700 hover:text-teal-600 hover:bg-teal-50 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-teal-500"
            >
              <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                {isMobileMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Navigation Menu */}
      {isMobileMenuOpen && (
        <div className="md:hidden">
          <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3 bg-white shadow-lg">
            {menuItems.map((item) => (
              <button
                key={item.name}
                onClick={() => handleNavigation(item.path)}
                className={`w-full text-left flex items-center px-3 py-2 rounded-md text-base font-medium transition-colors duration-200 ${
                  isActiveRoute(item.path)
                    ? 'text-teal-600 bg-teal-50'
                    : 'text-gray-700 hover:text-teal-600 hover:bg-teal-50'
                }`}
              >
                {item.icon}
                <span className="ml-3">{item.name}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navigation;