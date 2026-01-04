'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function PolicyPage() {
  const [policy, setPolicy] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPolicy();
  }, []);

  const fetchPolicy = async () => {
    try {
      const res = await axios.get(`${API_URL}/api/policy`);
      setPolicy(res.data);
    } catch (err) {
      console.error('Failed to fetch policy:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-plum-600 mx-auto"></div>
      </div>
    );
  }

  if (!policy) {
    return (
      <div className="card text-center py-12">
        <p className="text-gray-600">Failed to load policy information</p>
      </div>
    );
  }

  const coverage = policy.coverage_details;

  return (
    <div className="space-y-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900">{policy.policy_name}</h1>
        <p className="mt-2 text-gray-600">Policy ID: {policy.policy_id}</p>
      </div>

      {/* Coverage Limits */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">Coverage Limits</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-plum-50 rounded-lg text-center">
            <p className="text-sm text-plum-600">Annual Limit</p>
            <p className="text-2xl font-bold text-plum-700">₹{coverage.annual_limit?.toLocaleString()}</p>
          </div>
          <div className="p-4 bg-plum-50 rounded-lg text-center">
            <p className="text-sm text-plum-600">Per Claim Limit</p>
            <p className="text-2xl font-bold text-plum-700">₹{coverage.per_claim_limit?.toLocaleString()}</p>
          </div>
          <div className="p-4 bg-plum-50 rounded-lg text-center">
            <p className="text-sm text-plum-600">Family Floater</p>
            <p className="text-2xl font-bold text-plum-700">₹{coverage.family_floater_limit?.toLocaleString()}</p>
          </div>
        </div>
      </div>

      {/* Category Details */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Consultation */}
        <div className="card">
          <div className="flex items-center space-x-3 mb-4">
            <span className="text-3xl">🩺</span>
            <h3 className="text-lg font-semibold">Consultation</h3>
          </div>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Sub-limit:</span>
              <span className="font-medium">₹{coverage.consultation_fees?.sub_limit?.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Co-pay:</span>
              <span className="font-medium">{coverage.consultation_fees?.copay_percentage}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Network Discount:</span>
              <span className="font-medium">{coverage.consultation_fees?.network_discount}%</span>
            </div>
          </div>
        </div>

        {/* Diagnostic */}
        <div className="card">
          <div className="flex items-center space-x-3 mb-4">
            <span className="text-3xl">🔬</span>
            <h3 className="text-lg font-semibold">Diagnostic Tests</h3>
          </div>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Sub-limit:</span>
              <span className="font-medium">₹{coverage.diagnostic_tests?.sub_limit?.toLocaleString()}</span>
            </div>
            <div className="mt-2">
              <span className="text-gray-600">Covered Tests:</span>
              <ul className="mt-1 text-xs text-gray-500">
                {coverage.diagnostic_tests?.covered_tests?.slice(0, 5).map((test, i) => (
                  <li key={i}>• {test}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* Pharmacy */}
        <div className="card">
          <div className="flex items-center space-x-3 mb-4">
            <span className="text-3xl">💊</span>
            <h3 className="text-lg font-semibold">Pharmacy</h3>
          </div>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Sub-limit:</span>
              <span className="font-medium">₹{coverage.pharmacy?.sub_limit?.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Branded Drug Co-pay:</span>
              <span className="font-medium">{coverage.pharmacy?.branded_drugs_copay}%</span>
            </div>
          </div>
        </div>

        {/* Dental */}
        <div className="card">
          <div className="flex items-center space-x-3 mb-4">
            <span className="text-3xl">🦷</span>
            <h3 className="text-lg font-semibold">Dental</h3>
          </div>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Sub-limit:</span>
              <span className="font-medium">₹{coverage.dental?.sub_limit?.toLocaleString()}</span>
            </div>
            <div className="mt-2">
              <span className="text-gray-600">Covered Procedures:</span>
              <ul className="mt-1 text-xs text-gray-500">
                {coverage.dental?.procedures_covered?.map((proc, i) => (
                  <li key={i}>• {proc}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* Vision */}
        <div className="card">
          <div className="flex items-center space-x-3 mb-4">
            <span className="text-3xl">👁️</span>
            <h3 className="text-lg font-semibold">Vision</h3>
          </div>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Sub-limit:</span>
              <span className="font-medium">₹{coverage.vision?.sub_limit?.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Eye Test:</span>
              <span className="font-medium">{coverage.vision?.eye_test_covered ? '✓' : '✗'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Glasses/Lenses:</span>
              <span className="font-medium">{coverage.vision?.glasses_contact_lenses ? '✓' : '✗'}</span>
            </div>
          </div>
        </div>

        {/* Alternative Medicine */}
        <div className="card">
          <div className="flex items-center space-x-3 mb-4">
            <span className="text-3xl">🌿</span>
            <h3 className="text-lg font-semibold">Alternative Medicine</h3>
          </div>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Sub-limit:</span>
              <span className="font-medium">₹{coverage.alternative_medicine?.sub_limit?.toLocaleString()}</span>
            </div>
            <div className="mt-2">
              <span className="text-gray-600">Covered:</span>
              <ul className="mt-1 text-xs text-gray-500">
                {coverage.alternative_medicine?.covered_treatments?.map((t, i) => (
                  <li key={i}>• {t}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Waiting Periods */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">Waiting Periods</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-3 bg-yellow-50 rounded-lg text-center">
            <p className="text-sm text-yellow-700">Initial</p>
            <p className="font-bold text-yellow-800">{policy.waiting_periods?.initial_waiting} days</p>
          </div>
          <div className="p-3 bg-yellow-50 rounded-lg text-center">
            <p className="text-sm text-yellow-700">Pre-existing</p>
            <p className="font-bold text-yellow-800">{policy.waiting_periods?.pre_existing_diseases} days</p>
          </div>
          <div className="p-3 bg-yellow-50 rounded-lg text-center">
            <p className="text-sm text-yellow-700">Diabetes</p>
            <p className="font-bold text-yellow-800">{policy.waiting_periods?.specific_ailments?.diabetes} days</p>
          </div>
          <div className="p-3 bg-yellow-50 rounded-lg text-center">
            <p className="text-sm text-yellow-700">Hypertension</p>
            <p className="font-bold text-yellow-800">{policy.waiting_periods?.specific_ailments?.hypertension} days</p>
          </div>
        </div>
      </div>

      {/* Exclusions */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">Exclusions</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
          {policy.exclusions?.map((exclusion, i) => (
            <div key={i} className="flex items-center text-sm text-red-600">
              <span className="mr-2">✗</span>
              {exclusion}
            </div>
          ))}
        </div>
      </div>

      {/* Network Hospitals */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">Network Hospitals</h2>
        <div className="flex flex-wrap gap-2">
          {policy.network_hospitals?.map((hospital, i) => (
            <span key={i} className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm">
              {hospital}
            </span>
          ))}
        </div>
      </div>

      {/* Claim Requirements */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">Claim Requirements</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h3 className="font-medium mb-2">Documents Required:</h3>
            <ul className="space-y-1 text-sm text-gray-600">
              {policy.claim_requirements?.documents_required?.map((doc, i) => (
                <li key={i} className="flex items-start">
                  <span className="text-plum-500 mr-2">•</span>
                  {doc}
                </li>
              ))}
            </ul>
          </div>
          <div className="space-y-2">
            <div className="p-3 bg-gray-50 rounded">
              <p className="text-sm text-gray-600">Submission Timeline</p>
              <p className="font-semibold">{policy.claim_requirements?.submission_timeline_days} days</p>
            </div>
            <div className="p-3 bg-gray-50 rounded">
              <p className="text-sm text-gray-600">Minimum Claim Amount</p>
              <p className="font-semibold">₹{policy.claim_requirements?.minimum_claim_amount}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
