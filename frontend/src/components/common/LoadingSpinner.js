import React, { memo } from 'react';

const LoadingSpinner = memo(({ 
  size = 'medium', 
  color = 'blue', 
  overlay = false, 
  message = 'Loading...' 
}) => {
  const sizeClasses = {
    small: 'h-4 w-4',
    medium: 'h-8 w-8',
    large: 'h-12 w-12'
  };
  
  const colorClasses = {
    blue: 'border-blue-600 border-t-transparent',
    green: 'border-green-500 border-t-transparent',
    gray: 'border-gray-500 border-t-transparent'
  };

  const spinner = (
    <div className={`animate-spin rounded-full border-2 ${sizeClasses[size]} ${colorClasses[color]}`}></div>
  );

  if (overlay) {
    return (
      <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white p-6 rounded-lg shadow-xl">
          <div className="flex flex-col items-center">
            {spinner}
            {message && <p className="text-gray-600 mt-4">{message}</p>}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center space-x-2">
      {spinner}
      {message && <span className="text-sm text-gray-600">{message}</span>}
    </div>
  );
});

LoadingSpinner.displayName = 'LoadingSpinner';

export default LoadingSpinner;