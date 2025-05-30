import React, { memo } from 'react';
import LayerSection from './LayerSection';
import LayerSearch from './LayerSearch';
import { LAYER_SECTIONS } from '../../config/layerConfig';

const LayerSidebar = memo(() => {
  return (
    <div className="w-80 bg-white shadow-lg flex flex-col">
      {/* Search */}
      <LayerSearch />

      {/* Layer Sections */}
      <div className="flex-1 overflow-y-auto">
        {Object.entries(LAYER_SECTIONS).map(([sectionName, section]) => (
          <LayerSection
            key={sectionName}
            sectionName={sectionName}
            section={section}
          />
        ))}
      </div>
    </div>
  );
});

LayerSidebar.displayName = 'LayerSidebar';

export default LayerSidebar;