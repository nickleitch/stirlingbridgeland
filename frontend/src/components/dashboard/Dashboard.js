import React, { memo } from 'react';
import ProjectProgressSummary from './ProjectProgressSummary';
import LayerSidebar from '../layers/LayerSidebar';
import MapContainer from '../map/MapContainer';

const Dashboard = memo(() => {
  return (
    <div className="flex-1 flex flex-col bg-gray-50">
      {/* Progress Summary */}
      <div className="px-6 pt-6">
        <ProjectProgressSummary />
      </div>

      {/* Main Dashboard Content */}
      <div className="flex-1 flex px-6 pb-6 gap-6">
        <LayerSidebar />
        <MapContainer />
      </div>
    </div>
  );
});

Dashboard.displayName = 'Dashboard';

export default Dashboard;