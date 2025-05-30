import React, { memo } from 'react';

const ErrorMessage = memo(({ 
  error, 
  onDismiss, 
  type = 'error',
  className = '' 
}) => {
  if (!error) return null;

  const typeStyles = {
    error: 'bg-red-50 border-red-200 text-red-700',
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-700',
    info: 'bg-blue-50 border-blue-200 text-blue-700'
  };

  const iconMap = {
    error: '❌',
    warning: '⚠️',
    info: 'ℹ️'
  };

  return (
    <div className={`border px-4 py-3 rounded-lg ${typeStyles[type]} ${className}`}>
      <div className="flex items-start">
        <span className="mr-2 text-lg" role="img" aria-label={type}>
          {iconMap[type]}
        </span>
        <div className="flex-1">
          <p className="text-sm">{error}</p>
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="ml-2 text-lg hover:opacity-70 transition-opacity"
            aria-label="Dismiss error"
          >
            ×
          </button>
        )}
      </div>
    </div>
  );
});

ErrorMessage.displayName = 'ErrorMessage';

export default ErrorMessage;