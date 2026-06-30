'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function DashboardPage() {
  const [user, setUser] = useState<any>(null);
  const [tickets, setTickets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedTicket, setSelectedTicket] = useState<any>(null);
  const [actionReason, setActionReason] = useState('');
  const [newComment, setNewComment] = useState('');
  const [submittingAction, setSubmittingAction] = useState(false);
  const router = useRouter();

  useEffect(() => {
    // Check if session cookie exists by making a request to fetch tickets
    const fetchInitialData = async () => {
      try {
        const res = await fetch('/api/tickets');
        if (res.status === 401) {
          router.push('/');
          return;
        }

        const data = await res.json();
        if (data.success) {
          setTickets(data.tickets);
          
          // Get user info from cookie/session
          // In a real app we'd decode JWT, here we read from sessionStorage or local state set at login,
          // but we can also parse the session from a secondary route or local storage.
          // For simplicity, we store session info in localStorage on login and retrieve here.
          const storedUser = localStorage.getItem('user');
          if (storedUser) {
            const parsedUser = JSON.parse(storedUser);
            if (Date.now() > parsedUser.expiresAt) {
              handleLogout();
            } else {
              setUser(parsedUser);
            }
          } else {
            // Fallback if user cleared storage but cookie exists
            setUser({ name: 'Authorized User', role: 'Approver' });
          }
        } else {
          setError(data.error || 'Failed to fetch tickets');
        }
      } catch (err) {
        setError('Error connecting to server');
      } finally {
        setLoading(false);
      }
    };

    fetchInitialData();
  }, [router]);

  const handleLogout = async () => {
    try {
      await fetch('/api/auth/logout', { method: 'POST' });
    } catch (e) {}
    localStorage.removeItem('user');
    router.push('/');
  };

  const handleTicketAction = async (ticketId: string, action: 'approve' | 'reject') => {
    setSubmittingAction(true);
    try {
      const res = await fetch(`/api/tickets/${ticketId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, reason: actionReason }),
      });

      if (res.status === 401) {
        handleLogout();
        return;
      }

      const data = await res.json();
      if (data.success) {
        // Refresh local tickets list
        setTickets(prev => prev.map(t => t.ticket_id === ticketId ? data.ticket : t));
        setSelectedTicket(data.ticket);
        setActionReason('');
      } else {
        alert(data.error || 'Action failed');
      }
    } catch (err) {
      alert('Error updating ticket');
    } finally {
      setSubmittingAction(false);
    }
  };

  const handleAddComment = async (ticketId: string) => {
    if (!newComment.trim()) return;
    setSubmittingAction(true);
    try {
      const res = await fetch(`/api/tickets/${ticketId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'comment', comment: newComment.trim() }),
      });

      if (res.status === 401) {
        handleLogout();
        return;
      }

      const data = await res.json();
      if (data.success) {
        setTickets(prev => prev.map(t => t.ticket_id === ticketId ? data.ticket : t));
        setSelectedTicket(data.ticket);
        setNewComment('');
      } else {
        alert(data.error || 'Failed to add comment');
      }
    } catch (err) {
      alert('Error adding comment');
    } finally {
      setSubmittingAction(false);
    }
  };

  if (loading) {
    return <div className="container"><p>Loading dashboard...</p></div>;
  }

  if (error) {
    return (
      <div className="container">
        <p className="error-message">{error}</p>
        <button onClick={handleLogout}>Back to Login</button>
      </div>
    );
  }

  return (
    <div className="container">
      <div className="header">
        <div>
          <h1>IT Support Portal</h1>
          {user && (
            <div className="user-info">
              Logged in as: <strong>{user.name}</strong> ({user.role}) | ID: <code>{user.employeeId}</code>
            </div>
          )}
        </div>
        <button className="secondary" onClick={handleLogout}>Logout</button>
      </div>

      <h2>Incoming Laptop Requests</h2>
      {tickets.length === 0 ? (
        <p style={{ color: '#666', fontStyle: 'italic' }}>No tickets found requiring your attention.</p>
      ) : (
        <table className="ticket-table">
          <thead>
            <tr>
              <th>Ticket ID</th>
              <th>Requester</th>
              <th>Request Type</th>
              <th>Device Category</th>
              <th>Status</th>
              <th>Date Created</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {tickets.map((ticket) => (
              <tr key={ticket.ticket_id}>
                <td><code>{ticket.ticket_id}</code></td>
                <td>
                  <div><strong>{ticket.requester.name}</strong></div>
                  <div style={{ fontSize: '12px', color: '#666' }}>{ticket.requester.designation}</div>
                </td>
                <td>{ticket.request.type}</td>
                <td>{ticket.request.device_category || ticket.request.device}</td>
                <td>
                  <span className={`status-badge status-${ticket.status}`}>
                    {ticket.status.replace(/_/g, ' ')}
                  </span>
                </td>
                <td>{new Date(ticket.created_at).toLocaleDateString()}</td>
                <td>
                  <button className="secondary" onClick={() => setSelectedTicket(ticket)}>
                    View Details
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* Ticket Details Modal */}
      {selectedTicket && (
        <div className="modal-backdrop" onClick={() => setSelectedTicket(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h2>Ticket Details: {selectedTicket.ticket_id}</h2>
              <button className="secondary" onClick={() => setSelectedTicket(null)}>Close</button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '20px' }}>
              <div>
                <h3>Requester Info</h3>
                <p><strong>Name:</strong> {selectedTicket.requester.name}</p>
                <p><strong>Employee ID:</strong> <code>{selectedTicket.requester.employee_id}</code></p>
                <p><strong>Department:</strong> {selectedTicket.requester.department}</p>
                <p><strong>Designation:</strong> {selectedTicket.requester.designation}</p>
                <p><strong>Manager ID:</strong> <code>{selectedTicket.requester.manager}</code></p>
              </div>
              <div>
                <h3>Request Details</h3>
                <p><strong>Type:</strong> {selectedTicket.request.type}</p>
                <p><strong>Device Tier:</strong> {selectedTicket.request.device_category || selectedTicket.request.device}</p>
                <p><strong>Justification:</strong> {selectedTicket.request.justification}</p>
                <p><strong>Date Required:</strong> {selectedTicket.request.required_date}</p>
                <p><strong>Accessories:</strong> {selectedTicket.request.accessories || 'None'}</p>
                <p><strong>Status:</strong> <span className={`status-badge status-${selectedTicket.status}`}>{selectedTicket.status.replace(/_/g, ' ')}</span></p>
                {selectedTicket.manager_override && (
                  <p style={{ color: '#856404', backgroundColor: '#fff3cd', padding: '8px', borderRadius: '4px', fontSize: '13px' }}>
                    ⚠️ <strong>Manager Override Applied</strong>
                  </p>
                )}
              </div>
            </div>

            {/* Approval Actions */}
            {((user?.role === 'Manager' && selectedTicket.status === 'pending_manager_approval') ||
              (user?.role === 'Finance' && selectedTicket.status === 'approved')) && (
              <div style={{ backgroundColor: '#fafafa', padding: '15px', borderRadius: '4px', marginBottom: '20px' }}>
                <h3>Review Action</h3>
                <div className="form-group">
                  <label htmlFor="actionReason">Reason/Notes (optional):</label>
                  <input
                    id="actionReason"
                    type="text"
                    placeholder="Enter approval/rejection notes..."
                    value={actionReason}
                    onChange={(e) => setActionReason(e.target.value)}
                  />
                </div>
                <div style={{ display: 'flex', gap: '10px' }}>
                  <button 
                    style={{ backgroundColor: '#28a745' }}
                    onClick={() => handleTicketAction(selectedTicket.ticket_id, 'approve')}
                    disabled={submittingAction}
                  >
                    Approve Request
                  </button>
                  <button 
                    className="danger"
                    onClick={() => handleTicketAction(selectedTicket.ticket_id, 'reject')}
                    disabled={submittingAction}
                  >
                    Reject Request
                  </button>
                </div>
              </div>
            )}

            {/* Audit Trail & Comments */}
            <h3>Audit History</h3>
            <ul className="audit-list">
              {selectedTicket.audit_trail.map((log: any, idx: number) => (
                <li key={idx} className="audit-item" style={{ borderLeftColor: log.action.includes('reject') ? '#ff3b30' : log.action.includes('approve') ? '#28a745' : '#0070f3' }}>
                  <div className="audit-item-time">{new Date(log.timestamp).toLocaleString()}</div>
                  <div><strong>[{log.actor.toUpperCase()}] {log.action.replace(/_/g, ' ').toUpperCase()}:</strong> {log.details}</div>
                </li>
              ))}
            </ul>

            {/* Add Comments */}
            <div className="comment-box">
              <h3>Add Comment</h3>
              <div className="comment-input-group">
                <textarea
                  placeholder="Type a comment..."
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  disabled={submittingAction}
                  style={{ height: '60px', resize: 'none' }}
                />
                <button 
                  onClick={() => handleAddComment(selectedTicket.ticket_id)}
                  disabled={submittingAction || !newComment.trim()}
                >
                  Send
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
