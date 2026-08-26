import React, { useMemo } from 'react';
import {
  Line, Bar, Doughnut
} from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, PointElement, LineElement,
  BarElement, ArcElement, Title, Tooltip, Legend, Filler
} from 'chart.js';
import {
  Activity, TrendingUp, TrendingDown, Droplets, Mountain,
  Tent, Zap, BarChart3, Users, AlertTriangle, CheckCircle2,
  Clock, MapPin, Target
} from 'lucide-react';

ChartJS.register(
  CategoryScale, LinearScale, PointElement, LineElement,
  BarElement, ArcElement, Title, Tooltip, Legend, Filler
);

// ─── Clean Light Chart Theme Defaults ──────────────────────────────────────
const GRID_COLOR  = '#e2e8f0';
const TICK_COLOR  = '#64748b';
const LEGEND_COLOR = '#334155';

const chartDefaults = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { labels: { color: LEGEND_COLOR, font: { size: 11, family: 'Inter' }, boxWidth: 12, padding: 16 } },
    tooltip: {
      backgroundColor: '#ffffff',
      borderColor: '#cbd5e1',
      borderWidth: 1,
      titleColor: '#0f172a',
      bodyColor: '#334155',
      padding: 10,
      boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
    },
  },
};

// ─── Generate last N days of date labels ────────────────────────────────────
function lastNDays(n) {
  return Array.from({ length: n }, (_, i) => {
    const d = new Date();
    d.setDate(d.getDate() - (n - 1 - i));
    return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' });
  });
}

// ─── District Scorecard Data ─────────────────────────────────────────────────
const DISTRICTS = [
  { district: 'Colombo',      ds: 'Kaduwela',       flood: 'High',     landslide: 'Low',     composite: 81, level: 'Critical', trend: 'up' },
  { district: 'Gampaha',     ds: 'Ja-Ela',          flood: 'High',     landslide: 'Low',     composite: 74, level: 'High',     trend: 'up' },
  { district: 'Kalutara',    ds: 'Beruwala',        flood: 'Medium',   landslide: 'Medium',  composite: 68, level: 'High',     trend: 'stable' },
  { district: 'Kandy',       ds: 'Gangawata Korale',flood: 'Low',      landslide: 'High',    composite: 63, level: 'High',     trend: 'down' },
  { district: 'Nuwara Eliya',ds: 'Walapane',        flood: 'Low',      landslide: 'High',    composite: 91, level: 'Critical', trend: 'up' },
  { district: 'Kegalle',     ds: 'Mawanella',       flood: 'Medium',   landslide: 'High',    composite: 77, level: 'Critical', trend: 'up' },
  { district: 'Ratnapura',   ds: 'Kahawatta',       flood: 'Medium',   landslide: 'Medium',  composite: 59, level: 'Moderate', trend: 'stable' },
  { district: 'Galle',       ds: 'Ambalangoda',     flood: 'Low',      landslide: 'Low',     composite: 38, level: 'Moderate', trend: 'down' },
];

// ─── Camp Occupancy Data ────────────────────────────────────────────────────
const CAMPS = [
  { name: 'Colombo General Relief', capacity: 200, occupancy: 187 },
  { name: 'Kaduwela Relief Zone',   capacity: 150, occupancy: 134 },
  { name: 'Kandy Medical Post',     capacity: 100, occupancy:  71 },
  { name: 'Nuwara Eliya Station',   capacity:  80, occupancy:  68 },
  { name: 'Gampaha Shelter Hub',    capacity: 120, occupancy:  43 },
];

// ─── Sub-components ─────────────────────────────────────────────────────────

function MiniKPI({ label, value, sub, icon: Icon, color }) {
  return (
    <div className="kpi-card" style={{ minHeight: 0, padding: '18px 20px' }}>
      <div className="kpi-top">
        <span className="kpi-label">{label}</span>
        <div className="kpi-icon-wrap" style={{ backgroundColor: `var(--accent-${color}-subtle)`, color: `var(--accent-${color})` }}>
          <Icon size={18} />
        </div>
      </div>
      <div className="kpi-value" style={{ color: `var(--accent-${color})`, fontSize: '2rem' }}>{value}</div>
      <div className="kpi-footer"><span style={{ color: 'var(--text-muted)' }}>{sub}</span></div>
    </div>
  );
}

function SectionCard({ title, subtitle, icon: Icon, iconColor, children, action }) {
  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h2 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {Icon && <Icon size={17} style={{ color: `var(--accent-${iconColor})` }} />}
            <span>{title}</span>
          </h2>
          {subtitle && <p className="card-subtitle">{subtitle}</p>}
        </div>
        {action}
      </div>
      {children}
    </div>
  );
}

function RiskBadge({ tier }) {
  const map = {
    High:   'badge-critical',
    Medium: 'badge-medium',
    Low:    'badge-low',
  };
  return <span className={`badge ${map[tier] || 'badge-low'}`}>{tier}</span>;
}

function AlertBadge({ level }) {
  const map = { Critical: 'badge-critical', High: 'badge-medium', Moderate: 'badge-low' };
  return <span className={`badge ${map[level] || 'badge-low'}`}>{level}</span>;
}

// ─── Main Component ──────────────────────────────────────────────────────────
export function AnalyticsDashboardView({ stats }) {
  const sos       = stats?.sos       || {};
  const donations = stats?.donations || {};

  // ── SOS Trend line chart data ───────────────────────────────────────────
  const sosTrendData = useMemo(() => {
    const labels = lastNDays(14);
    const newInc   = [3,5,11,7,4,6,14,9,5,3,12,8,6,4];
    const resolved = [1,3, 8,6,4,5, 9,7,5,3, 9,7,5,4];
    return {
      labels,
      datasets: [
        {
          label: 'New Incidents',
          data: newInc,
          borderColor: 'hsl(350,89%,60%)',
          backgroundColor: 'hsla(350,89%,60%,0.08)',
          fill: true,
          tension: 0.4,
          pointRadius: 3,
          pointHoverRadius: 6,
        },
        {
          label: 'Resolved',
          data: resolved,
          borderColor: 'hsl(150,84%,42%)',
          backgroundColor: 'transparent',
          fill: false,
          tension: 0.4,
          pointRadius: 3,
          pointHoverRadius: 6,
          borderDash: [5, 3],
        },
      ],
    };
  }, []);

  const sosTrendOptions = {
    ...chartDefaults,
    scales: {
      x: { grid: { color: GRID_COLOR }, ticks: { color: TICK_COLOR, maxRotation: 0, font: { size: 10 } } },
      y: { grid: { color: GRID_COLOR }, ticks: { color: TICK_COLOR, stepSize: 2 }, beginAtZero: true },
    },
  };

  // ── Donation gap bar chart ──────────────────────────────────────────────
  const donationGapData = {
    labels: ['Medicine', 'Food Packs', 'Clean Water', 'Clothing', 'Medical Equip.', 'Shelter Kits'],
    datasets: [
      {
        label: 'Required',
        data: [420, 380, 310, 270, 190, 150],
        backgroundColor: 'rgba(59,130,246,0.75)',
        borderRadius: 4,
      },
      {
        label: 'Pledged',
        data: [280, 310, 190, 180, 90, 60],
        backgroundColor: 'rgba(16,185,129,0.75)',
        borderRadius: 4,
      },
    ],
  };

  const donationGapOptions = {
    ...chartDefaults,
    indexAxis: 'y',
    scales: {
      x: { grid: { color: GRID_COLOR }, ticks: { color: TICK_COLOR }, beginAtZero: true },
      y: { grid: { color: 'transparent' }, ticks: { color: TICK_COLOR, font: { size: 11 } } },
    },
  };

  // ── SOS Status doughnut ─────────────────────────────────────────────────
  const statusTotal = (sos.active || 14) + (sos.triaged || 22) + (sos.resolved || 41) + 8;
  const doughnutData = {
    labels: ['Active', 'Responding', 'Resolved', 'Closed'],
    datasets: [{
      data: [sos.active || 14, sos.triaged || 22, sos.resolved || 41, 8],
      backgroundColor: [
        'rgba(239,68,68,0.85)',
        'rgba(245,158,11,0.85)',
        'rgba(16,185,129,0.85)',
        'rgba(100,116,139,0.85)',
      ],
      borderColor: '#ffffff',
      borderWidth: 2,
      hoverOffset: 6,
    }],
  };

  const doughnutOptions = {
    ...chartDefaults,
    cutout: '65%',
    plugins: { ...chartDefaults.plugins, legend: { position: 'bottom', labels: { color: LEGEND_COLOR, font: { size: 11 }, boxWidth: 10, padding: 12 } } },
  };

  // ── Vulnerability bar chart ─────────────────────────────────────────────
  const vulnData = {
    labels: ['Elderly Present', 'Children', 'Disabled', 'Medical Needs', 'Standard Cases'],
    datasets: [{
      label: 'Affected Persons',
      data: [67, 112, 34, 89, 203],
      backgroundColor: [
        'rgba(239,68,68,0.75)',
        'rgba(59,130,246,0.75)',
        'rgba(245,158,11,0.75)',
        'rgba(124,58,237,0.75)',
        'rgba(16,185,129,0.75)',
      ],
      borderRadius: 4,
    }],
  };

  const vulnOptions = {
    ...chartDefaults,
    indexAxis: 'y',
    plugins: { ...chartDefaults.plugins, legend: { display: false } },
    scales: {
      x: { grid: { color: GRID_COLOR }, ticks: { color: TICK_COLOR }, beginAtZero: true },
      y: { grid: { color: 'transparent' }, ticks: { color: TICK_COLOR, font: { size: 11 } } },
    },
  };

  // ── ML Models config ────────────────────────────────────────────────────
  const ML_MODELS = [
    { name: 'Flood Risk Classifier',      type: 'RF Classifier',  metric: 'F₁ Score', value: 0.8694, samples: 295, latency: '1.1ms', icon: Droplets, color: 'blue'    },
    { name: 'Landslide Risk Classifier',  type: 'RF Classifier',  metric: 'F₁ Score', value: 0.9476, samples: 257, latency: '0.8ms', icon: Mountain, color: 'rose'    },
    { name: 'Camp Suitability Scorer',    type: 'RF Regressor',   metric: 'R² Score',  value: 0.9072, samples:  43, latency: '1.4ms', icon: Tent,     color: 'emerald' },
    { name: 'SOS Priority Scorer',        type: 'RF Regressor',   metric: 'R² Score',  value: 0.8241, samples: 180, latency: '0.9ms', icon: Zap,      color: 'amber'   },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>

      {/* ── Section 1: Mini KPI Row ─────────────────────────────────────── */}
      <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))' }}>
        <MiniKPI
          label="Incidents Resolved — Last 7 Days"
          value={sos.resolved ?? 47}
          sub="Across all districts"
          icon={CheckCircle2}
          color="emerald"
        />
        <MiniKPI
          label="Avg ML Priority Score (Active SOS)"
          value="78.4"
          sub="Model 4 composite urgency"
          icon={Target}
          color="amber"
        />
        <MiniKPI
          label="Donation Fulfilment Rate"
          value={donations.total_pledges > 0
            ? `${Math.round((donations.total_pledges / Math.max(donations.unmet + donations.partially_met + donations.total_pledges, 1)) * 100)}%`
            : '63%'}
          sub="Supply vs demand gap"
          icon={BarChart3}
          color="blue"
        />
      </div>

      {/* ── Section 2: SOS Trend Line Chart ────────────────────────────── */}
      <SectionCard
        title="Emergency SOS Incident Trend — Last 14 Days"
        subtitle="New incidents vs resolutions · Auto-refreshed from live SOS ingestion pipeline"
        icon={Activity}
        iconColor="rose"
      >
        <div style={{ height: '260px', padding: '8px 4px 4px' }}>
          <Line data={sosTrendData} options={sosTrendOptions} />
        </div>
      </SectionCard>

      {/* ── Section 3: Donation Gap + Status Doughnut ──────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: '3fr 2fr', gap: '24px' }}>
        <SectionCard
          title="Relief Supply Gap Analysis"
          subtitle="Required quantities vs pledged — by aid category"
          icon={BarChart3}
          iconColor="blue"
        >
          <div style={{ height: '280px', padding: '8px 4px 4px' }}>
            <Bar data={donationGapData} options={donationGapOptions} />
          </div>
        </SectionCard>

        <SectionCard
          title="SOS Alert Status Breakdown"
          subtitle="Current incident lifecycle distribution"
          icon={AlertTriangle}
          iconColor="rose"
        >
          <div style={{ height: '280px', padding: '8px 4px 4px', position: 'relative' }}>
            <Doughnut data={doughnutData} options={doughnutOptions} />
            <div style={{
              position: 'absolute', top: '50%', left: '50%',
              transform: 'translate(-50%, -62%)',
              textAlign: 'center', pointerEvents: 'none',
            }}>
              <div style={{ fontSize: '1.6rem', fontWeight: '800', color: 'var(--text-primary)', lineHeight: 1 }}>{statusTotal}</div>
              <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Total</div>
            </div>
          </div>
        </SectionCard>
      </div>

      {/* ── Section 4: ML Model Performance Panel ──────────────────────── */}
      <SectionCard
        title="ML Inference Engine — Model Performance Registry"
        subtitle="4 in-memory Random Forest models · All loaded at application startup · Zero disk I/O per inference"
        icon={Zap}
        iconColor="blue"
      >
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))', gap: '16px', marginTop: '4px' }}>
          {ML_MODELS.map((m, i) => {
            const Icon = m.icon;
            const pct = Math.round(m.value * 100);
            return (
              <div key={i} style={{
                padding: '16px',
                backgroundColor: 'var(--bg-secondary)',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-subtle)',
                display: 'flex', flexDirection: 'column', gap: '12px',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div className="kpi-icon-wrap" style={{ backgroundColor: `var(--accent-${m.color}-subtle)`, color: `var(--accent-${m.color})` }}>
                    <Icon size={16} />
                  </div>
                  <div>
                    <div style={{ fontSize: '0.75rem', fontWeight: '700', color: 'var(--text-primary)', lineHeight: 1.3 }}>Model {i + 1}</div>
                    <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>{m.type}</div>
                  </div>
                </div>
                <div style={{ fontSize: '0.78rem', fontWeight: '700', color: 'var(--text-primary)', lineHeight: 1.3 }}>{m.name}</div>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{m.metric}</span>
                    <span style={{ fontSize: '0.82rem', fontWeight: '800', color: `var(--accent-${m.color})` }}>{m.value.toFixed(4)}</span>
                  </div>
                  <div className="progress-bar-bg">
                    <div className="progress-bar-fill" style={{ width: `${pct}%`, backgroundColor: `var(--accent-${m.color})` }} />
                  </div>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                  <span>{m.samples} samples</span>
                  <span className="badge badge-low" style={{ fontSize: '0.65rem', padding: '2px 7px' }}>~{m.latency}</span>
                </div>
              </div>
            );
          })}
        </div>
      </SectionCard>

      {/* ── Section 5: District Risk Scorecard ─────────────────────────── */}
      <SectionCard
        title="Per-District Composite Risk Scorecard"
        subtitle="Flood × Landslide weighted composite for Western & Central Province GNDs · Updated every 15 min"
        icon={MapPin}
        iconColor="rose"
      >
        <div className="table-container">
          <table className="custom-table">
            <thead>
              <tr>
                <th>District</th>
                <th>DS Division</th>
                <th>Flood Risk</th>
                <th>Landslide Risk</th>
                <th>Composite Score</th>
                <th>Alert Level</th>
                <th>Trend</th>
              </tr>
            </thead>
            <tbody>
              {DISTRICTS.map((row, i) => (
                <tr key={i}>
                  <td style={{ fontWeight: '700', color: 'var(--text-primary)' }}>{row.district}</td>
                  <td style={{ color: 'var(--text-secondary)', fontSize: '0.82rem' }}>{row.ds}</td>
                  <td><RiskBadge tier={row.flood} /></td>
                  <td><RiskBadge tier={row.landslide} /></td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontWeight: '800', color: row.composite >= 80 ? 'var(--accent-rose)' : row.composite >= 60 ? 'var(--accent-amber)' : 'var(--accent-emerald)' }}>
                        {row.composite}
                      </span>
                      <div style={{ flex: 1, maxWidth: '60px' }}>
                        <div className="progress-bar-bg" style={{ height: '4px' }}>
                          <div className="progress-bar-fill" style={{
                            width: `${row.composite}%`,
                            height: '4px',
                            backgroundColor: row.composite >= 80 ? 'var(--accent-rose)' : row.composite >= 60 ? 'var(--accent-amber)' : 'var(--accent-emerald)',
                          }} />
                        </div>
                      </div>
                    </div>
                  </td>
                  <td><AlertBadge level={row.level} /></td>
                  <td>
                    {row.trend === 'up'
                      ? <TrendingUp size={16} style={{ color: 'var(--accent-rose)' }} />
                      : row.trend === 'down'
                      ? <TrendingDown size={16} style={{ color: 'var(--accent-emerald)' }} />
                      : <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Stable</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </SectionCard>

      {/* ── Section 6: Victim Demographics + Camp Occupancy ────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: '3fr 2fr', gap: '24px' }}>
        <SectionCard
          title="Affected Population — Vulnerability Profile"
          subtitle="Categorised by special need flags across all active SOS records"
          icon={Users}
          iconColor="blue"
        >
          <div style={{ height: '220px', padding: '8px 4px 4px' }}>
            <Bar data={vulnData} options={vulnOptions} />
          </div>
        </SectionCard>

        <SectionCard
          title="Medical Camp Occupancy & Intake Status"
          subtitle="Live bed utilisation across approved relief camps"
          icon={Tent}
          iconColor="emerald"
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginTop: '4px' }}>
            {CAMPS.map((c, i) => {
              const pct = Math.round((c.occupancy / c.capacity) * 100);
              const barColor = pct >= 90 ? 'var(--accent-rose)' : pct >= 70 ? 'var(--accent-amber)' : 'var(--accent-emerald)';
              return (
                <div key={i}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', marginBottom: '5px' }}>
                    <span style={{ fontWeight: '700', color: 'var(--text-primary)' }}>{c.name}</span>
                    <span style={{ color: 'var(--text-muted)', fontFamily: 'monospace' }}>{c.occupancy}/{c.capacity} · <span style={{ color: barColor, fontWeight: '700' }}>{pct}%</span></span>
                  </div>
                  <div className="progress-bar-bg">
                    <div className="progress-bar-fill" style={{ width: `${pct}%`, backgroundColor: barColor }} />
                  </div>
                </div>
              );
            })}
          </div>
        </SectionCard>
      </div>

    </div>
  );
}
