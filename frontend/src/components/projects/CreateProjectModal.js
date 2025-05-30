import React, { memo, useState } from 'react';
import { useProject } from '../../contexts/ProjectContext';
import { projectAPI } from '../../services/projectAPI';
import ErrorMessage from '../common/ErrorMessage';
import LoadingSpinner from '../common/LoadingSpinner';

const CreateProjectModal = memo(({ isOpen, onClose, onProjectCreated }) => {
  const { createProject, loading, error, clearError } = useProject();
  const [formData, setFormData] = useState({
    name: '',
    latitude: '',
    longitude: ''
  });
  const [validationError, setValidationError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (validationError) setValidationError('');
    if (error) clearError();
  };

  const validateForm = () => {
    if (!formData.name.trim()) {
      setValidationError('Please enter a project name');
      return false;
    }

    const latitude = parseFloat(formData.latitude);
    const longitude = parseFloat(formData.longitude);

    if (!formData.latitude || !formData.longitude) {
      setValidationError('Please enter both latitude and longitude');
      return false;
    }

    const validation = projectAPI.validateCoordinates(latitude, longitude);
    if (!validation.valid) {
      if (validation.warning) {
        const confirmed = window.confirm(validation.error);
        if (!confirmed) return false;
      } else {
        setValidationError(validation.error);
        return false;
      }
    }

    return true;
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;

    const projectData = {
      name: formData.name.trim(),
      latitude: parseFloat(formData.latitude),
      longitude: parseFloat(formData.longitude)
    };

    const result = await createProject(projectData);
    
    if (result.success) {
      // Reset form
      setFormData({ name: '', latitude: '', longitude: '' });
      setValidationError('');
      
      // Notify parent and close modal
      if (onProjectCreated) {
        onProjectCreated(result.project);
      }
      onClose();
    }
  };

  const handleClose = () => {
    setFormData({ name: '', latitude: '', longitude: '' });
    setValidationError('');
    clearError();
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-2xl p-8 max-w-md w-full mx-4">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Create New Project</h2>

        {(error || validationError) && (
          <ErrorMessage 
            error={error || validationError}
            onDismiss={() => {
              if (error) clearError();
              if (validationError) setValidationError('');
            }}
            className="mb-4"
          />
        )}

        <div className="space-y-4">
          <div>
            <label htmlFor="project-name" className="block text-sm font-medium text-gray-700 mb-2">
              Project Name
            </label>
            <input
              id="project-name"
              type="text"
              value={formData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              placeholder="Enter project name"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={loading}
            />
          </div>

          <div>
            <label htmlFor="latitude" className="block text-sm font-medium text-gray-700 mb-2">
              Latitude (Decimal Degrees)
            </label>
            <input
              id="latitude"
              type="number"
              step="any"
              value={formData.latitude}
              onChange={(e) => handleInputChange('latitude', e.target.value)}
              placeholder="-29.47088"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={loading}
            />
          </div>

          <div>
            <label htmlFor="longitude" className="block text-sm font-medium text-gray-700 mb-2">
              Longitude (Decimal Degrees)
            </label>
            <input
              id="longitude"
              type="number"
              step="any"
              value={formData.longitude}
              onChange={(e) => handleInputChange('longitude', e.target.value)}
              placeholder="31.17807"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={loading}
            />
          </div>
        </div>

        <div className="flex space-x-4 mt-8">
          <button
            onClick={handleClose}
            className="flex-1 px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-all"
            disabled={loading}
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            className="flex-1 bg-gradient-to-r from-green-600 to-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:from-green-700 hover:to-blue-700 transition-all flex items-center justify-center"
            disabled={loading}
          >
            {loading ? (
              <LoadingSpinner size="small" color="gray" />
            ) : (
              'Create Project'
            )}
          </button>
        </div>
      </div>
    </div>
  );
});

CreateProjectModal.displayName = 'CreateProjectModal';

export default CreateProjectModal;