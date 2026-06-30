'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const [employeeId, setEmployeeId] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!employeeId.trim()) return;

    setLoading(true);
    setError('');

    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ employeeId: employeeId.trim() }),
      });

      const data = await res.json();

      if (data.success) {
        localStorage.setItem('user', JSON.stringify(data.user));
        router.push('/dashboard');
      } else {
        setError(data.error || 'Login failed');
      }
    } catch (err) {
      setError('An error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <h1>IT Support Portal</h1>
      <p style={{ color: '#666', fontSize: '14px', marginBottom: '25px' }}>
        Manager & Finance Approvals
      </p>
      
      {error && <div className="error-message">{error}</div>}

      <form onSubmit={handleLogin}>
        <div className="form-group">
          <label htmlFor="employeeId">Employee ID</label>
          <input
            id="employeeId"
            type="text"
            placeholder="e.g., EMP-005 or FIN-001"
            value={employeeId}
            onChange={(e) => setEmployeeId(e.target.value)}
            disabled={loading}
            required
          />
        </div>
        <button type="submit" style={{ width: '100%' }} disabled={loading}>
          {loading ? 'Logging in...' : 'Login'}
        </button>
      </form>
      
      <div style={{ marginTop: '30px', fontSize: '12px', color: '#666', borderTop: '1px solid #eaeaea', paddingTop: '15px' }}>
        <p><strong>Test IDs:</strong></p>
        <p style={{ margin: '5px 0' }}>Manager: <code>EMP-005</code> (Eve Adams)</p>
        <p style={{ margin: '5px 0' }}>Finance Team: <code>FIN-001</code> (Finance Specialist)</p>
      </div>
    </div>
  );
}
