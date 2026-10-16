import React, { useEffect, useMemo, useState } from 'react';
import {
  AlertTriangle, Check, Clock3, Gift, History, MapPin, RefreshCw,
  Search, Send, Sparkles, Target, UserCheck, Users,
} from 'lucide-react';
import { api } from '../api';

const severityColor = {
  Critical: '#dc2626', High: '#ea580c', Moderate: '#ca8a04', Medium: '#ca8a04', Low: '#16a34a',
};

const card = {
  background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
  borderRadius: '16px', boxShadow: '0 2px 5px rgba(15, 23, 42, 0.06)',
};

export function DonationMatchingView({ onAddToast }) {
  const [requests, setRequests] = useState([]);
  const [selectedId, setSelectedId] = useState('');
  const [matches, setMatches] = useState([]);
  const [selectedDonors, setSelectedDonors] = useState(new Set());
  const [dsFilter, setDsFilter] = useState('');
  const [gnFilter, setGnFilter] = useState('');
  const [requestSearch, setRequestSearch] = useState('');
  const [donorSearch, setDonorSearch] = useState('');
  const [loadingRequests, setLoadingRequests] = useState(true);
  const [loadingMatches, setLoadingMatches] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');

  const loadRequests = async (keepSelection = true) => {
    setLoadingRequests(true);
    setError('');
    try {
      const data = await api.getDisasterRequests();
      const open = (data || []).filter((request) =>
        request.status !== 'fulfilled' && (request.items || []).some((item) => Number(item.remainingQuantity) > 0)
      );
      setRequests(open);
      setSelectedId((current) => keepSelection && open.some((item) => item.id === current)
        ? current : (open[0]?.id || ''));
    } catch (err) {
      setError(err.message || 'Unable to load donation requests.');
    } finally {
      setLoadingRequests(false);
    }
  };

  useEffect(() => { loadRequests(false); }, []);

  useEffect(() => {
    if (!selectedId) {
      setMatches([]);
      setSelectedDonors(new Set());
      return;
    }
    let active = true;
    setLoadingMatches(true);
    setError('');
    api.getDonationDonorMatches(selectedId)
      .then((data) => {
        if (!active) return;
        const ranked = data || [];
        setMatches(ranked);
        setSelectedDonors(new Set(ranked.filter((donor) => donor.alreadyTargeted).map((donor) => donor.donorId)));
      })
      .catch((err) => active && setError(err.message || 'Unable to rank donors.'))
      .finally(() => active && setLoadingMatches(false));
    return () => { active = false; };
  }, [selectedId]);

  const dsAreas = useMemo(() => [...new Set(requests.map((item) => item.dsArea).filter(Boolean))].sort(), [requests]);
  const gnDivisions = useMemo(() => [...new Set(requests.filter((item) => !dsFilter || item.dsArea === dsFilter)
    .map((item) => item.gnDivision).filter(Boolean))].sort(), [requests, dsFilter]);
  const visibleRequests = requests.filter((request) => {
    const query = requestSearch.trim().toLowerCase();
    return (!dsFilter || request.dsArea === dsFilter)
      && (!gnFilter || request.gnDivision === gnFilter)
      && (!query || [request.reliefCamp, request.gnDivision, request.dsArea, request.disasterType]
        .some((value) => (value || '').toLowerCase().includes(query)));
  });
  const selectedRequest = requests.find((request) => request.id === selectedId);
  const visibleMatches = matches.filter((donor) => {
    const query = donorSearch.trim().toLowerCase();
    return !query || [donor.name, donor.email, donor.address, donor.proximityTier]
      .some((value) => (value || '').toLowerCase().includes(query));
  });
  const newlySelectedCount = matches.filter((donor) =>
    selectedDonors.has(donor.donorId) && !donor.alreadyTargeted
  ).length;

  const toggleDonor = (donorId) => setSelectedDonors((current) => {
    const next = new Set(current);
    if (next.has(donorId)) next.delete(donorId); else next.add(donorId);
    return next;
  });

  const selectRecommended = () => {
    const recommended = matches.filter((donor) => donor.score >= 50 || donor.alreadyTargeted).map((donor) => donor.donorId);
    setSelectedDonors(new Set(recommended.length ? recommended : matches.slice(0, 5).map((donor) => donor.donorId)));
  };

  const sendOutreach = async () => {
    const donorIds = matches
      .filter((donor) => selectedDonors.has(donor.donorId) && !donor.alreadyTargeted)
      .map((donor) => donor.donorId);
    if (!selectedId || donorIds.length === 0) {
      onAddToast?.('Select at least one donor.', 'warning', 'No Donors Selected');
      return;
    }
    setSending(true);
    setError('');
    try {
      const result = await api.sendDonationOutreach(selectedId, donorIds);
      onAddToast?.(result.message, 'success', 'Requests Published');
      await loadRequests();
      const refreshed = await api.getDonationDonorMatches(selectedId);
      setMatches(refreshed || []);
      setSelectedDonors(new Set((refreshed || []).filter((donor) => donor.alreadyTargeted).map((donor) => donor.donorId)));
    } catch (err) {
      setError(err.message || 'Unable to publish donor requests.');
      onAddToast?.(err.message, 'error', 'Outreach Failed');
    } finally {
      setSending(false);
    }
  };

  return (
    <div style={{ display: 'grid', gap: 20 }}>
      <section style={{ ...card, padding: '22px 26px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap', background: 'linear-gradient(120deg, #eef2ff, var(--bg-card) 62%)' }}>
        <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
          <div style={{ width: 54, height: 54, borderRadius: 14, display: 'grid', placeItems: 'center', background: '#4f46e5', color: 'white' }}><Target size={29} /></div>
          <div>
            <h1 style={{ margin: 0, color: 'var(--text-primary)', fontSize: '1.45rem' }}>Personalized Donor Matching</h1>
            <p style={{ margin: '5px 0 0', color: 'var(--text-muted)', fontSize: '.88rem' }}>Match camp requests with suitable donors by GN/DS proximity, donation history, item relevance, and urgency.</p>
          </div>
        </div>
        <div style={{ padding: '9px 13px', borderRadius: 10, background: '#fff7ed', color: '#9a3412', fontSize: '.78rem', display: 'flex', gap: 8, alignItems: 'center' }}>
          <MapPin size={15} /> Proximity uses registered addresses, not GPS coordinates
        </div>
      </section>

      {error && <div style={{ ...card, padding: 14, borderColor: '#fecaca', background: '#fef2f2', color: '#b91c1c', display: 'flex', gap: 9 }}><AlertTriangle size={18} />{error}</div>}

      <section className="donor-matching-grid" style={{ display: 'grid', gap: 20, alignItems: 'start' }}>
        <div style={{ ...card, overflow: 'hidden' }}>
          <div style={{ padding: '18px 20px', borderBottom: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div><h2 style={{ margin: 0, fontSize: '1.05rem' }}>Camp Requests ({visibleRequests.length})</h2><p style={{ margin: '4px 0 0', color: 'var(--text-muted)', fontSize: '.78rem' }}>Select a request under its GN division</p></div>
              <button onClick={() => loadRequests()} aria-label="Refresh requests" style={{ border: '1px solid var(--border-default)', background: 'var(--bg-card)', borderRadius: 9, padding: 8, color: 'var(--text-secondary)', cursor: 'pointer' }}><RefreshCw size={16} /></button>
            </div>
            <div style={{ display: 'grid', gap: 9, marginTop: 14 }}>
              <label style={{ position: 'relative' }}><Search size={15} style={{ position: 'absolute', left: 10, top: 10, color: 'var(--text-muted)' }} /><input value={requestSearch} onChange={(e) => setRequestSearch(e.target.value)} placeholder="Search camp or area..." style={{ width: '100%', boxSizing: 'border-box', padding: '9px 10px 9px 32px', border: '1px solid var(--border-default)', borderRadius: 9, background: 'var(--bg-secondary)' }} /></label>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 9 }}>
                <select value={dsFilter} onChange={(e) => { setDsFilter(e.target.value); setGnFilter(''); }} style={{ padding: 9, border: '1px solid var(--border-default)', borderRadius: 9, background: 'var(--bg-secondary)' }}><option value="">All DS areas</option>{dsAreas.map((area) => <option key={area}>{area}</option>)}</select>
                <select value={gnFilter} onChange={(e) => setGnFilter(e.target.value)} style={{ padding: 9, border: '1px solid var(--border-default)', borderRadius: 9, background: 'var(--bg-secondary)' }}><option value="">All GN divisions</option>{gnDivisions.map((area) => <option key={area}>{area}</option>)}</select>
              </div>
            </div>
          </div>
          <div style={{ maxHeight: 650, overflowY: 'auto', padding: 12, display: 'grid', gap: 9 }}>
            {loadingRequests ? <p style={{ padding: 25, textAlign: 'center', color: 'var(--text-muted)' }}>Loading camp requests...</p> : visibleRequests.map((request) => {
              const remaining = (request.items || []).reduce((sum, item) => sum + Number(item.remainingQuantity || 0), 0);
              const active = request.id === selectedId;
              return <button key={request.id} onClick={() => setSelectedId(request.id)} style={{ textAlign: 'left', padding: 14, borderRadius: 12, cursor: 'pointer', border: `1px solid ${active ? '#6366f1' : 'var(--border-subtle)'}`, background: active ? '#eef2ff' : 'var(--bg-secondary)', color: 'var(--text-primary)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}><strong>{request.reliefCamp}</strong><span style={{ color: severityColor[request.severity] || '#ca8a04', fontSize: '.68rem', fontWeight: 800 }}>{request.severity?.toUpperCase()}</span></div>
                <div style={{ display: 'flex', gap: 5, alignItems: 'center', marginTop: 7, color: 'var(--text-muted)', fontSize: '.76rem' }}><MapPin size={13} />{request.gnDivision}, {request.dsArea}</div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 10, fontSize: '.73rem', color: 'var(--text-secondary)' }}><span>{request.items?.length || 0} item type(s) · {remaining.toLocaleString()} outstanding</span><span>{request.targetedDonorCount || 0} targeted</span></div>
              </button>;
            })}
            {!loadingRequests && visibleRequests.length === 0 && <p style={{ padding: 30, textAlign: 'center', color: 'var(--text-muted)' }}>No open requests match these filters.</p>}
          </div>
        </div>

        <div style={{ ...card, overflow: 'hidden' }}>
          <div style={{ padding: '18px 20px', borderBottom: '1px solid var(--border-subtle)' }}>
            {selectedRequest ? <>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: 15, flexWrap: 'wrap' }}>
                <div><h2 style={{ margin: 0, fontSize: '1.05rem' }}>{selectedRequest.reliefCamp}</h2><p style={{ margin: '5px 0 0', color: 'var(--text-muted)', fontSize: '.8rem' }}>{selectedRequest.gnDivision} GN · {selectedRequest.dsArea} DS · {selectedRequest.disasterType}</p></div>
                <span style={{ alignSelf: 'start', padding: '6px 10px', borderRadius: 20, background: '#f5f3ff', color: '#6d28d9', fontSize: '.72rem', fontWeight: 800 }}><Sparkles size={13} style={{ verticalAlign: -2, marginRight: 5 }} />RANKED MATCHES</span>
              </div>
              <div style={{ display: 'flex', gap: 7, flexWrap: 'wrap', marginTop: 13 }}>{selectedRequest.items?.filter((item) => Number(item.remainingQuantity) > 0).map((item) => <span key={item.itemId || item.itemName} style={{ padding: '5px 8px', borderRadius: 7, background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)', fontSize: '.72rem' }}>{item.itemName}: <strong>{item.remainingQuantity} {item.unit}</strong></span>)}</div>
            </> : <h2 style={{ margin: 0 }}>Select a camp request</h2>}
          </div>

          {selectedRequest && <>
            <div style={{ padding: '13px 20px', display: 'flex', gap: 10, justifyContent: 'space-between', flexWrap: 'wrap', borderBottom: '1px solid var(--border-subtle)' }}>
              <label style={{ position: 'relative', flex: '1 1 240px' }}><Search size={15} style={{ position: 'absolute', left: 10, top: 10, color: 'var(--text-muted)' }} /><input value={donorSearch} onChange={(e) => setDonorSearch(e.target.value)} placeholder="Search ranked donors..." style={{ width: '100%', boxSizing: 'border-box', padding: '9px 10px 9px 32px', border: '1px solid var(--border-default)', borderRadius: 9, background: 'var(--bg-secondary)' }} /></label>
              <button onClick={selectRecommended} style={{ padding: '8px 12px', borderRadius: 9, border: '1px solid #c7d2fe', background: '#eef2ff', color: '#4338ca', fontWeight: 700, cursor: 'pointer' }}><UserCheck size={15} style={{ verticalAlign: -3, marginRight: 6 }} />Select recommended</button>
            </div>
            <div style={{ maxHeight: 530, overflowY: 'auto', padding: 12, display: 'grid', gap: 9 }}>
              {loadingMatches ? <p style={{ padding: 35, textAlign: 'center', color: 'var(--text-muted)' }}><Sparkles size={18} style={{ verticalAlign: -4, marginRight: 7 }} />Calculating donor suitability...</p> : visibleMatches.map((donor) => {
                const checked = selectedDonors.has(donor.donorId);
                return <label key={donor.donorId} style={{ padding: 14, borderRadius: 12, border: `1px solid ${checked ? '#818cf8' : 'var(--border-subtle)'}`, background: checked ? '#f5f3ff' : 'var(--bg-secondary)', cursor: 'pointer', display: 'grid', gridTemplateColumns: '22px 1fr auto', gap: 10 }}>
                  <input type="checkbox" checked={checked} disabled={donor.alreadyTargeted} onChange={() => toggleDonor(donor.donorId)} style={{ marginTop: 3 }} />
                  <div><div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}><strong>{donor.name}</strong>{donor.alreadyTargeted && <span style={{ color: '#047857', background: '#d1fae5', borderRadius: 10, padding: '2px 7px', fontSize: '.65rem', fontWeight: 800 }}><Check size={11} style={{ verticalAlign: -2 }} /> TARGETED</span>}</div><div style={{ color: 'var(--text-muted)', fontSize: '.74rem', marginTop: 3 }}>{donor.email || 'No email'} · {donor.source}</div><div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginTop: 8, fontSize: '.7rem', color: 'var(--text-secondary)' }}><span><MapPin size={12} style={{ verticalAlign: -2 }} /> {donor.proximityTier}</span><span><History size={12} style={{ verticalAlign: -2 }} /> {donor.historyCount} past pledge(s)</span><span><Gift size={12} style={{ verticalAlign: -2 }} /> {donor.relevantDonationCount} item match(es)</span></div><p style={{ margin: '7px 0 0', color: 'var(--text-muted)', fontSize: '.68rem' }}>{donor.reasons.join(' · ')}</p></div>
                  <div style={{ minWidth: 58, height: 52, borderRadius: 10, display: 'grid', placeItems: 'center', background: donor.score >= 70 ? '#dcfce7' : donor.score >= 45 ? '#fef3c7' : '#f1f5f9', color: donor.score >= 70 ? '#15803d' : donor.score >= 45 ? '#a16207' : '#475569', fontWeight: 900 }}><span>{donor.score}<small style={{ fontSize: '.6rem' }}>%</small></span></div>
                </label>;
              })}
              {!loadingMatches && visibleMatches.length === 0 && <p style={{ padding: 35, textAlign: 'center', color: 'var(--text-muted)' }}><Users size={22} /><br />No registered donors match this search.</p>}
            </div>
            <div style={{ padding: '14px 20px', borderTop: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '.78rem' }}><strong style={{ color: 'var(--text-primary)' }}>{selectedDonors.size}</strong> selected · <strong style={{ color: '#4f46e5' }}>{newlySelectedCount}</strong> new recipient(s)<br /><span style={{ fontSize: '.68rem' }}><Clock3 size={11} style={{ verticalAlign: -2 }} /> Published requests appear under “For You” in each selected donor's portal.</span></div>
              <button disabled={sending || newlySelectedCount === 0} onClick={sendOutreach} style={{ padding: '11px 17px', border: 0, borderRadius: 10, background: sending || newlySelectedCount === 0 ? '#94a3b8' : '#4f46e5', color: 'white', fontWeight: 800, cursor: sending ? 'wait' : 'pointer' }}><Send size={16} style={{ verticalAlign: -3, marginRight: 7 }} />{sending ? 'Publishing...' : 'Send Personalized Requests'}</button>
            </div>
          </>}
        </div>
      </section>
    </div>
  );
}
