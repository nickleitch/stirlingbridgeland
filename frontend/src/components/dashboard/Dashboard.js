import React, { memo } from 'react';
import LayerSidebar from '../layers/LayerSidebar';
import MapContainer from '../map/MapContainer';

const Dashboard = memo(() => {
  return (
    <div className="flex-1 flex bg-gray-50 gap-6 p-6">
      <LayerSidebar />
      <MapContainer />
    </div>
  );
});

Dashboard.displayName = 'Dashboard';

export default Dashboard;