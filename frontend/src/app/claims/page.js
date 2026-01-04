'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import { format } from 'date-fns';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function ClaimsPage() {
  const [claims, setClaims] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedClaim, setSelectedClaim] = useState(null);
  const [statusFilter, setStatusFilter] = useState('');

  useEffect(() => {
    fetchClaims();
  }, [statusFilter]);

  const fetchClaims = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (statusFilter) params.append('status', statusFilter);
      
      const res = await axios.get(`${API_URL}/api/claims?${params}`);
      setClaims(res.data.claims);
    } catch (err) {
      setError(err.message || 'Failed to fetch claims');
    } finally {
      setLoading(false);
    }
  };

  const getStatusStyle = (status) => {
    const styles = {
      APPROVED: 'bg-green-100 text-green-800',
      REJECTED: 'bg-red-100 text-red-800',
      PENDING: 'bg-yellow-100 text-yellow-800',
      PARTIAL: 'bg-blue-100 text-blue-800',
      MANUAL_REVIEW: 'bg-purple-100 text-purple-800',
      PROCESSING: 'bg-gray-100 text-gray-800',
    };
    return styles[status] || 'bg-gray-100 text-gray-800';
  };

  const getCategoryIcon = (category) => {
    const icons = {
      consultation: '🩺',
      diagnostic: '🔬',
      pharmacy: '💊',
      dental: '🦷',
      vision: '👁️',
      alternative: '🌿',
    };
    return icons[category] || '📋';
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">My Claims</h1>
        
        <select
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)}
          className="input w-48"
        >
          <option value="">All Status</option>
          <option value="APPROVED">Approved</option>
          <option value="REJECTED">Rejected</option>
          <option value="PARTIAL">Partial</option>
          <option value="PENDING">Pending</option>
          <option value="MANUAL_REVIEW">Manual Review</option>
        </select>
      </div>

      {loading && (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-plum-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading claims...</p>
        </div>
      )}

      {error && (
        <div className="card bg-red-50 border-red-200">
          <p className="text-red-600">{error}</p>
        </div>
      )}

      {!loading && claims.length === 0 && (
        <div className="card text-center py-12">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="mt-4 text-lg font-medium text-gray-900">No claims found</h3>
          <p className="mt-2 text-gray-600">Submit your first claim to get started.</p>
          <a href="/" className="mt-4 inline-block btn-primary">Submit Claim</a>
        </div>
      )}

      {!loading && claims.length > 0 && (
        <div className="grid gap-4">
          {claims.map(claim => (
            <div
              key={claim.id}
              className="card hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => setSelectedClaim(claim)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <span className="text-3xl">{getCategoryIcon(claim.claim_category)}</span>
                  <div>
                    <div className="flex items-center space-x-2">
                      <h3 className="font-semibold text-gray-900">{claim.claim_id}</h3>
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getStatusStyle(claim.status)}`}>
                        {claim.status}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600">
                      {claim.patient_name} • {claim.claim_category}
                    </p>
                    <p className="text-xs text-gray-400">
                      {claim.submitted_at && format(new Date(claim.submitted_at), 'MMM d, yyyy h:mm a')}
                    </p>
                  </div>
                </div>
                
                <div className="text-right">
                  <p className="text-sm text-gray-600">Claimed</p>
                  <p className="font-semibold">₹{claim.claim_amount?.toFixed(2)}</p>
                  {claim.approved_amount > 0 && (
                    <>
                      <p className="text-sm text-gray-600 mt-1">Approved</p>
                      <p className="font-semibold text-green-600">₹{claim.approved_amount?.toFixed(2)}</p>
                    </>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Claim Detail Modal */}
      {selectedClaim && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold">Claim Details</h2>
                <button
                  onClick={() => setSelectedClaim(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div>
                    <p className="text-sm text-gray-600">Claim ID</p>
                    <p className="font-mono font-semibold">{selectedClaim.claim_id}</p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusStyle(selectedClaim.status)}`}>
                    {selectedClaim.status}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-600">Patient Name</p>
                    <p className="font-medium">{selectedClaim.patient_name}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Employee ID</p>
                    <p className="font-medium">{selectedClaim.employee_id}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Category</p>
                    <p className="font-medium capitalize">{selectedClaim.claim_category}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Treatment Date</p>
                    <p className="font-medium">
                      {selectedClaim.treatment_date && format(new Date(selectedClaim.treatment_date), 'MMM d, yyyy')}
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
                  <div>
                    <p className="text-sm text-gray-600">Claimed Amount</p>
                    <p className="text-2xl font-bold">₹{selectedClaim.claim_amount?.toFixed(2)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Approved Amount</p>
                    <p className="text-2xl font-bold text-green-600">₹{selectedClaim.approved_amount?.toFixed(2)}</p>
                  </div>
                </div>

                <div>
                  <p className="text-sm text-gray-600">Confidence Score</p>
                  <div className="mt-1 flex items-center">
                    <div className="flex-1 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-plum-600 h-2 rounded-full"
                        style={{ width: `${selectedClaim.confidence_score * 100}%` }}
                      />
                    </div>
                    <span className="ml-2 text-sm font-medium">{(selectedClaim.confidence_score * 100).toFixed(0)}%</span>
                  </div>
                </div>

                {selectedClaim.decision_reasons?.length > 0 && (
                  <div>
                    <p className="text-sm text-gray-600 mb-2">Decision Reasons</p>
                    <ul className="list-disc list-inside text-sm space-y-1">
                      {selectedClaim.decision_reasons.map((reason, i) => (
                        <li key={i} className="text-gray-700">{reason.replace(/_/g, ' ')}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {selectedClaim.notes && (
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Notes</p>
                    <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded">{selectedClaim.notes}</p>
                  </div>
                )}

                {selectedClaim.next_steps && (
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Next Steps</p>
                    <p className="text-sm text-gray-700 bg-blue-50 p-3 rounded">{selectedClaim.next_steps}</p>
                  </div>
                )}

                {selectedClaim.extracted_data && (
                  <div>
                    <p className="text-sm text-gray-600 mb-2">Extracted Data</p>
                    <pre className="text-xs bg-gray-100 p-3 rounded overflow-x-auto">
                      {JSON.stringify(selectedClaim.extracted_data, null, 2)}
                    </pre>
                  </div>
                )}
              </div>

              <div className="mt-6 flex justify-end">
                <button onClick={() => setSelectedClaim(null)} className="btn-secondary">
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
