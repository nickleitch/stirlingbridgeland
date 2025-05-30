import React, { memo } from 'react';
import LayerItem from './LayerItem';
import { useLayer } from '../../contexts/LayerContext';

const LayerSection = memo(({ sectionName, section }) => {
  const { expandedSections, toggleSection } = useLayer();
  const isExpanded = expandedSections[sectionName];

  return (
    <div className="border-b border-gray-100">
      <button
        onClick={() => toggleSection(sectionName)}
        className="w-full flex items-center justify-between p-4 hover:bg-gray-50 text-left transition-colors"
        aria-expanded={isExpanded}
        aria-controls={`section-${sectionName}`}
      >
        <div className="flex items-center">
          <div 
            className="w-3 h-3 rounded-full mr-3"
            style={{ backgroundColor: section.color }}
            aria-hidden="true"
          ></div>
          <span className="font-medium text-gray-900">{sectionName}</span>
          <span className="ml-2 text-sm text-gray-500">{section.layers.length} layers</span>
        </div>
        <span 
          className={`transition-transform ${isExpanded ? 'rotate-180' : ''}`}
          aria-hidden="true"
        >
          ▼
        </span>
      </button>

      {isExpanded && (
        <div id={`section-${sectionName}`} className="pb-2">
          {section.layers.map(layer => (
            <LayerItem
              key={layer.id}
              layer={layer}
            />
          ))}
        </div>
      )}
    </div>
  );
});

LayerSection.displayName = 'LayerSection';

export default LayerSection;