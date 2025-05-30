import React, { memo, useState } from 'react';

const LayerSearch = memo(() => {
  const [searchQuery, setSearchQuery] = useState('');

  const handleSearch = () => {
    // TODO: Implement layer search functionality
    console.log('Searching for:', searchQuery);
  };

  return (
    <div className="p-4 border-b">
      <div className="relative">
        <input
          type="text"
          placeholder="Search layers..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              handleSearch();
            }
          }}
          className="w-full pl-8 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <div className="absolute left-2 top-2.5 text-gray-400" aria-hidden="true">🔍</div>
        <button 
          onClick={handleSearch}
          className="absolute right-2 top-2 text-gray-400 hover:text-gray-600 transition-colors"
          aria-label="Search layers"
        >
          →
        </button>
      </div>
    </div>
  );
});

LayerSearch.displayName = 'LayerSearch';

export default LayerSearch;