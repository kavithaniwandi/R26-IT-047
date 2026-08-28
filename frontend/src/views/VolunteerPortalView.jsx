import React, { useState, useEffect } from 'react';
import { 
  Users, 
  MapPin, 
  CheckCircle2, 
  Truck, 
  Navigation, 
  Clock, 
  AlertTriangle, 
  Package, 
  CheckSquare,
  ShieldAlert
} from 'lucide-react';
import { api } from '../api';

export function VolunteerPortalView({ currentUser, onAddToast }) {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [successMsg, setSuccessMsg] = useState(null);
  const [error, setError] = useState(null);

  const loadTasks = async () => {
    setLoading(true);
    try {
      const data = await api.getSOSRequests();
      setTasks(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTasks();
  }, []);

  const handleCompleteTask = async (taskId, newStatus) => {
    try {
      await api.updateSOSStatus(taskId, newStatus);
      const msg = `Task #${taskId} marked as '${newStatus}' by Field Responder.`;
      setSuccessMsg(msg);
      if (onAddToast) {
        onAddToast(msg, 'success', 'Mission Updated');
      }
      loadTasks();
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (err) {
      setError(err.message);
      if (onAddToast) {
        onAddToast(err.message, 'error', 'Update Failed');
      }
    }
  };

  return (
    <div>
      {/* Volunteer Banner */}
      <div style={{
        background: 'linear-gradient(135deg, hsla(38, 92%, 50%, 0.15), hsla(220, 20%, 14%, 1))',
        border: '1px solid hsla(38, 92%, 50%, 0.35)',
        borderRadius: 'var(--radius-xl)',
        padding: '24px 28px',
        marginBottom: '24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '16px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{
            width: '54px',
            height: '54px',
            borderRadius: 'var(--radius-lg)',
            backgroundColor: 'var(--accent-amber)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'black',
            boxShadow: '0 0 24px hsla(38, 92%, 50%, 0.5)'
          }}>
            <Truck size={30} />
          </div>
          <div>
            <h1 style={{ fontSize: '1.45rem', fontWeight: '800', letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>
              Field Volunteer & Rapid Responder Dispatch Client
            </h1>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              Live task routing for on-ground rescue teams, medical supply distribution, and victim status resolution.
            </p>
          </div>
        </div>

        <div style={{
          padding: '8px 16px',
          backgroundColor: 'var(--bg-secondary)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)'
        }}>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', textTransform: 'uppercase' }}>FIELD DISPATCH UNIT</span>
          <strong style={{ fontSize: '1.1rem', color: 'var(--accent-amber)' }}>{currentUser?.full_name || 'Volunteer Unit #4 (Kaduwela)'}</strong>
        </div>
      </div>

      {/* Alert Notices */}
      {successMsg && (
        <div style={{
          padding: '14px 18px',
          backgroundColor: 'var(--accent-emerald-subtle)',
          border: '1px solid hsla(150, 84%, 42%, 0.4)',
          borderRadius: 'var(--radius-md)',
          color: 'var(--accent-emerald)',
          marginBottom: '20px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <CheckCircle2 size={20} />
          <strong style={{ fontSize: '0.9rem' }}>{successMsg}</strong>
        </div>
      )}

      {error && (
        <div style={{
          padding: '14px 18px',
          backgroundColor: 'var(--accent-rose-subtle)',
          border: '1px solid hsla(350, 89%, 60%, 0.4)',
          borderRadius: 'var(--radius-md)',
          color: 'var(--accent-rose)',
          marginBottom: '20px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <AlertTriangle size={20} />
          <span>{error}</span>
        </div>
      )}

      {/* Assigned Tasks Grid */}
      <div className="card">
        <div className="card-header">
          <div>
            <h2 className="card-title">Assigned Emergency Rescue & Relief Missions</h2>
            <p className="card-subtitle">Showing {tasks.length} field missions sorted by priority</p>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '18px' }}>
          {tasks.map((task) => (
            <div
              key={task.id}
              style={{
                backgroundColor: 'var(--bg-secondary)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-lg)',
                padding: '20px',
                display: 'flex',
                flexDirection: 'column',
                gap: '14px'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <span style={{ fontSize: '1.1rem', fontWeight: '800', color: 'var(--text-primary)' }}>
                    Mission #{task.id} · {task.gn_division || task.ds_division}
                  </span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                    <MapPin size={12} style={{ color: 'var(--accent-rose)' }} />
                    <span>{task.address_text || `${task.district} Disaster Zone`}</span>
                  </div>
                </div>
                <span className={`badge ${task.priority_score >= 85 ? 'badge-critical' : task.priority_score >= 70 ? 'badge-medium' : 'badge-low'}`}>
                  Priority: {task.priority_score}
                </span>
              </div>

              {/* Demographics */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', backgroundColor: 'var(--bg-card)', padding: '12px', borderRadius: 'var(--radius-md)', fontSize: '0.82rem' }}>
                <div>
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>AFFECTED</span>
                  <div style={{ fontWeight: '700', color: 'var(--text-primary)' }}>{task.affected_people} Persons ({task.affected_families} Fam)</div>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>STATUS</span>
                  <div><span className={`badge badge-${task.status}`}>{task.status}</span></div>
                </div>
              </div>

              {/* Medical Requirements */}
              {task.medical_needs_summary && (
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                  <strong style={{ color: 'var(--accent-amber)' }}>Relief Kit: </strong>
                  <span>{task.medical_needs_summary}</span>
                </div>
              )}

              {/* Navigation Action & Complete Buttons */}
              <div style={{ marginTop: 'auto', display: 'flex', gap: '8px', paddingTop: '10px', borderTop: '1px solid var(--border-subtle)' }}>
                <a
                  href={`https://www.google.com/maps/search/?api=1&query=${task.latitude},${task.longitude}`}
                  target="_blank"
                  rel="noreferrer"
                  className="btn btn-secondary btn-sm"
                  style={{ flex: 1 }}
                >
                  <Navigation size={13} />
                  <span>GPS Route</span>
                </a>

                {task.status !== 'resolved' ? (
                  <button
                    className="btn btn-success btn-sm"
                    style={{ flex: 1 }}
                    onClick={() => handleCompleteTask(task.id, 'resolved')}
                  >
                    <CheckCircle2 size={13} />
                    <span>Confirm Delivered</span>
                  </button>
                ) : (
                  <span className="badge badge-low" style={{ alignSelf: 'center', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                    <CheckCircle2 size={12} />
                    <span>Mission Completed</span>
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
