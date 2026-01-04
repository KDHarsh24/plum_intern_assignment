'use client';

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const CLAIM_CATEGORIES = [
  { value: 'consultation', label: 'Consultation', icon: '🩺' },
  { value: 'diagnostic', label: 'Diagnostic Tests', icon: '🔬' },
  { value: 'pharmacy', label: 'Pharmacy', icon: '💊' },
  { value: 'dental', label: 'Dental', icon: '🦷' },
  { value: 'vision', label: 'Vision', icon: '👁️' },
  { value: 'alternative', label: 'Alternative Medicine', icon: '🌿' },
];

export default function Home() {
  const [formData, setFormData] = useState({
    patient_name: '',
    employee_id: '',
    claim_amount: '',
    claim_category: 'consultation',
    treatment_date: '',
    hospital_name: '',
    notes: '',
  });
  const [files, setFiles] = useState([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const onDrop = useCallback((acceptedFiles) => {
    setFiles(prev => [...prev, ...acceptedFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpg', '.jpeg', '.png'],
      'application/pdf': ['.pdf'],
    },
    maxSize: 10 * 1024 * 1024,
  });

  const removeFile = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);
    setResult(null);

    try {
      const formDataObj = new FormData();
      formDataObj.append('patient_name', formData.patient_name);
      formDataObj.append('employee_id', formData.employee_id);
      formDataObj.append('claim_amount', formData.claim_amount);
      formDataObj.append('claim_category', formData.claim_category);
      formDataObj.append('treatment_date', formData.treatment_date);
      formDataObj.append('hospital_name', formData.hospital_name || '');
      formDataObj.append('notes', formData.notes || '');
      
      files.forEach(file => {
        formDataObj.append('documents', file);
      });

      // Step 1: Submit claim
      const submitRes = await axios.post(`${API_URL}/api/claims/submit`, formDataObj, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      const claim = submitRes.data;

      // Step 2: Process claim
      await axios.post(`${API_URL}/api/claims/${claim.claim_id}/process`);
      
      // Get updated claim
      const claimRes = await axios.get(`${API_URL}/api/claims/${claim.claim_id}`);
      
      setResult(claimRes.data);
      
      // Reset form on success
      setFormData({
        patient_name: '',
        employee_id: '',
        claim_amount: '',
        claim_category: 'consultation',
        treatment_date: '',
        hospital_name: '',
        notes: '',
      });
      setFiles([]);
      
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to submit claim');
    } finally {
      setIsSubmitting(false);
    }
  };

  const getStatusStyle = (status) => {
    const styles = {
      APPROVED: 'status-approved',
      REJECTED: 'status-rejected',
      PENDING: 'status-pending',
      PARTIAL: 'status-partial',
      MANUAL_REVIEW: 'status-manual_review',
    };
    return styles[status] || 'status-pending';
  };

  return (
    <div className="space-y-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900">Submit OPD Claim</h1>
        <p className="mt-2 text-gray-600">
          Upload your medical documents and we'll process your claim using AI
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Claim Form */}
        <div className="card">
          <h2 className="text-xl font-semibold mb-6">Claim Details</h2>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label">Patient Name *</label>
                <input
                  type="text"
                  className="input"
                  value={formData.patient_name}
                  onChange={e => setFormData({...formData, patient_name: e.target.value})}
                  required
                />
              </div>
              <div>
                <label className="label">Employee ID *</label>
                <input
                  type="text"
                  className="input"
                  value={formData.employee_id}
                  onChange={e => setFormData({...formData, employee_id: e.target.value})}
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label">Claim Amount (₹) *</label>
                <input
                  type="number"
                  className="input"
                  value={formData.claim_amount}
                  onChange={e => setFormData({...formData, claim_amount: e.target.value})}
                  min="500"
                  required
                />
              </div>
              <div>
                <label className="label">Treatment Date *</label>
                <input
                  type="date"
                  className="input"
                  value={formData.treatment_date}
                  onChange={e => setFormData({...formData, treatment_date: e.target.value})}
                  required
                />
              </div>
            </div>

            <div>
              <label className="label">Claim Category *</label>
              <div className="grid grid-cols-3 gap-2">
                {CLAIM_CATEGORIES.map(cat => (
                  <button
                    key={cat.value}
                    type="button"
                    className={`p-3 rounded-lg border-2 transition-all ${
                      formData.claim_category === cat.value
                        ? 'border-plum-500 bg-plum-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => setFormData({...formData, claim_category: cat.value})}
                  >
                    <span className="text-2xl">{cat.icon}</span>
                    <p className="text-xs mt-1">{cat.label}</p>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="label">Hospital/Clinic Name</label>
              <input
                type="text"
                className="input"
                value={formData.hospital_name}
                onChange={e => setFormData({...formData, hospital_name: e.target.value})}
                placeholder="e.g., Apollo Hospitals"
              />
            </div>

            <div>
              <label className="label">Additional Notes</label>
              <textarea
                className="input"
                rows={3}
                value={formData.notes}
                onChange={e => setFormData({...formData, notes: e.target.value})}
                placeholder="Any additional information..."
              />
            </div>

            <button
              type="submit"
              disabled={isSubmitting || files.length === 0}
              className="w-full btn-primary py-3 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Processing...
                </span>
              ) : (
                'Submit & Process Claim'
              )}
            </button>
          </form>
        </div>

        {/* Document Upload */}
        <div className="space-y-6">
          <div className="card">
            <h2 className="text-xl font-semibold mb-4">Upload Documents</h2>
            <p className="text-sm text-gray-500 mb-4">
              Upload prescriptions, bills, and test reports (JPG, PNG, PDF)
            </p>
            
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                isDragActive ? 'border-plum-500 bg-plum-50' : 'border-gray-300 hover:border-plum-400'
              }`}
            >
              <input {...getInputProps()} />
              <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              <p className="mt-2 text-sm text-gray-600">
                {isDragActive ? 'Drop files here...' : 'Drag & drop files or click to browse'}
              </p>
            </div>

            {files.length > 0 && (
              <div className="mt-4 space-y-2">
                <h3 className="text-sm font-medium text-gray-700">Uploaded Files:</h3>
                {files.map((file, index) => (
                  <div key={index} className="flex items-center justify-between bg-gray-50 p-2 rounded">
                    <span className="text-sm text-gray-600 truncate">{file.name}</span>
                    <button
                      type="button"
                      onClick={() => removeFile(index)}
                      className="text-red-500 hover:text-red-700"
                    >
                      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Result Display */}
          {error && (
            <div className="card bg-red-50 border-red-200">
              <h3 className="text-red-800 font-semibold">Error</h3>
              <p className="text-red-600 mt-1">{error}</p>
            </div>
          )}

          {result && (
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold">Claim Result</h2>
                <span className={getStatusStyle(result.status)}>{result.status}</span>
              </div>
              
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">Claim ID:</span>
                  <span className="font-mono">{result.claim_id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Claimed Amount:</span>
                  <span className="font-semibold">₹{result.claim_amount?.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Approved Amount:</span>
                  <span className="font-semibold text-green-600">₹{result.approved_amount?.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Confidence:</span>
                  <span>{(result.confidence_score * 100).toFixed(0)}%</span>
                </div>
                
                {result.decision_reasons?.length > 0 && (
                  <div className="pt-3 border-t">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Reasons:</h4>
                    <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                      {result.decision_reasons.map((reason, i) => (
                        <li key={i}>{reason.replace(/_/g, ' ')}</li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {result.next_steps && (
                  <div className="pt-3 border-t">
                    <h4 className="text-sm font-medium text-gray-700 mb-1">Next Steps:</h4>
                    <p className="text-sm text-gray-600">{result.next_steps}</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
