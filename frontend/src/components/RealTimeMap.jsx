import React, { useState, useEffect } from 'react';
import { 
  MapContainer, 
  TileLayer, 
  Marker, 
  Popup, 
  Circle, 
  useMap, 
  useMapEvents 
} from 'react-leaflet';
import L from 'leaflet';
import { 
  Layers, 
  Navigation, 
  ShieldAlert, 
  Tent, 
  Waves, 
  Mountain, 
  RefreshCw, 
  MapPin,
  CheckCircle2,
  AlertTriangle,
  Compass
} from 'lucide-react';

// Fix default Leaflet icon assets
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

// Custom Professional SVG Pin Generators
const createSOSIcon = (priority, count) => {
  const isCritical = priority >= 85;
  const isHigh = priority >= 70;
  const color = isCritical ? 'hsl(350, 89%, 60%)' : isHigh ? 'hsl(38, 92%, 50%)' : 'hsl(217, 91%, 60%)';
  const shadowColor = isCritical ? 'hsla(350, 89%, 60%, 0.6)' : isHigh ? 'hsla(38, 92%, 50%, 0.6)' : 'hsla(217, 91%, 60%, 0.6)';

  return L.divIcon({
    className: 'custom-leaflet-sos-icon',
    html: `
      <div style="
        position: relative;
        width: 38px;
        height: 38px;
        border-radius: 50%;
        background-color: ${color};
        border: 3px solid white;
        box-shadow: 0 0 16px ${shadowColor};
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        animation: map-pulse 1.8s infinite;
      ">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        <div style="
          position: absolute;
          top: -8px;
          right: -8px;
          background: #0f172a;
          border: 1.5px solid white;
          color: white;
          border-radius: 9999px;
          padding: 1px 5px;
          font-size: 9px;
          font-weight: 800;
          font-family: monospace;
        ">P:${Math.round(priority)}</div>
      </div>
    `,
    iconSize: [38, 38],
    iconAnchor: [19, 19],
    popupAnchor: [0, -20],
  });
};

const createCampIcon = (status) => {
  const isApproved = status === 'approved' || status === 'operational';
  const color = isApproved ? 'hsl(150, 84%, 42%)' : 'hsl(217, 91%, 60%)';

  return L.divIcon({
    className: 'custom-leaflet-camp-icon',
    html: `
      <div style="
        width: 34px;
        height: 34px;
        border-radius: 8px;
        background-color: ${color};
        border: 2px solid white;
        box-shadow: 0 2px 10px rgba(0,0,0,0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
      ">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M3.5 21 12 3l8.5 18"/>
          <path d="M12 3v18"/>
          <path d="M6 18h12"/>
        </svg>
      </div>
    `,
    iconSize: [34, 34],
    iconAnchor: [17, 17],
    popupAnchor: [0, -18],
  });
};

const createHazardIcon = (hazard) => {
  const isFlood = hazard === 'Flood';
  return L.divIcon({
    className: 'custom-leaflet-hazard-icon',
    html: `
      <div style="
        width: 30px;
        height: 30px;
        border-radius: 50%;
        background-color: ${isFlood ? 'hsl(217, 91%, 50%)' : 'hsl(350, 89%, 55%)'};
        border: 2px solid white;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.4);
      ">
        ${isFlood ? `
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
            <path d="M2 6c.6.5 1.2 1 2.5 1C7 7 7 5 9.5 5c2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"/>
            <path d="M2 12c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"/>
            <path d="M2 18c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"/>
          </svg>
        ` : `
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
            <path d="m8 3 4 8 5-5 5 15H2L8 3z"/>
          </svg>
        `}
      </div>
    `,
    iconSize: [30, 30],
    iconAnchor: [15, 15],
    popupAnchor: [0, -16],
  });
};

// Map click listener component
function MapClickHandler({ onMapClick }) {
  useMapEvents({
    click(e) {
      if (onMapClick) {
        onMapClick(e.latlng.lat, e.latlng.lng);
      }
    },
  });
  return null;
}

// Controller to programmatic re-center
function MapController({ center, zoom }) {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.flyTo(center, zoom, { duration: 1.2 });
    }
  }, [center, zoom, map]);
  return null;
}

export function RealTimeMap({ 
  sosPoints = [], 
  hazardZones = [], 
  camps = [], 
  height = '540px',
  onMapClick = null,
  onResolveSOS = null,
  selectedLocation = null,
  showControls = true,
  autoRefreshInterval = 8000,
  onRefresh = null,
}) {
  // Layer Toggles
  const [showSOS, setShowSOS] = useState(true);
  const [showFloods, setShowFloods] = useState(true);
  const [showLandslides, setShowLandslides] = useState(true);
  const [showCamps, setShowCamps] = useState(true);

  // Map view centre (Default: Kelani River Basin / Kaduwela)
  const [mapCenter, setMapCenter] = useState([6.936419, 79.957216]);
  const [mapZoom, setMapZoom] = useState(12);
  const [lastUpdated, setLastUpdated] = useState(new Date());

  // Real-Time Polling Timer
  useEffect(() => {
    if (!autoRefreshInterval || !onRefresh) return;
    const interval = setInterval(() => {
      onRefresh();
      setLastUpdated(new Date());
    }, autoRefreshInterval);
    return () => clearInterval(interval);
  }, [autoRefreshInterval, onRefresh]);

  const handleFlyTo = (lat, lng, zoom = 14) => {
    setMapCenter([lat, lng]);
    setMapZoom(zoom);
  };

  const handleLocateMe = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          handleFlyTo(pos.coords.latitude, pos.coords.longitude, 15);
        },
        (err) => alert('GPS location unavailable: ' + err.message)
      );
    }
  };

  return (
    <div style={{ position: 'relative', width: '100%', borderRadius: 'var(--radius-lg)', overflow: 'hidden', border: '1px solid var(--border-subtle)' }}>
      {/* Top Floating Action Bar */}
      {showControls && (
        <div style={{
          position: 'absolute',
          top: '12px',
          left: '12px',
          right: '12px',
          zIndex: 999,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '8px',
          pointerEvents: 'none'
        }}>
          {/* Layer Filter Toggles */}
          <div style={{
            backgroundColor: 'hsla(222, 24%, 9%, 0.92)',
            backdropFilter: 'blur(10px)',
            border: '1px solid var(--border-default)',
            borderRadius: 'var(--radius-md)',
            padding: '6px 10px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            pointerEvents: 'auto',
            boxShadow: 'var(--shadow-md)'
          }}>
            <span style={{ fontSize: '0.72rem', fontWeight: '800', color: 'var(--text-muted)', marginRight: '4px', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              LAYERS:
            </span>

            <button
              className={`btn btn-sm ${showSOS ? 'btn-danger' : 'btn-secondary'}`}
              style={{ padding: '4px 9px', fontSize: '0.74rem' }}
              onClick={() => setShowSOS(!showSOS)}
            >
              <ShieldAlert size={13} />
              <span>SOS ({sosPoints.length})</span>
            </button>

            <button
              className={`btn btn-sm ${showFloods ? 'btn-primary' : 'btn-secondary'}`}
              style={{ padding: '4px 9px', fontSize: '0.74rem' }}
              onClick={() => setShowFloods(!showFloods)}
            >
              <Waves size={13} />
              <span>Kelani Flood</span>
            </button>

            <button
              className={`btn btn-sm ${showLandslides ? 'btn-warning' : 'btn-secondary'}`}
              style={{ padding: '4px 9px', fontSize: '0.74rem' }}
              onClick={() => setShowLandslides(!showLandslides)}
            >
              <Mountain size={13} />
              <span>Landslides</span>
            </button>

            <button
              className={`btn btn-sm ${showCamps ? 'btn-success' : 'btn-secondary'}`}
              style={{ padding: '4px 9px', fontSize: '0.74rem' }}
              onClick={() => setShowCamps(!showCamps)}
            >
              <Tent size={13} />
              <span>Camps ({camps.length})</span>
            </button>
          </div>

          {/* Quick Positioning & Live Sync Badge */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            pointerEvents: 'auto'
          }}>
            <div style={{
              backgroundColor: 'hsla(222, 24%, 9%, 0.92)',
              backdropFilter: 'blur(10px)',
              border: '1px solid var(--border-default)',
              borderRadius: 'var(--radius-md)',
              padding: '6px 12px',
              fontSize: '0.74rem',
              display: 'flex',
              alignItems: 'center',
              gap: '7px',
              color: 'var(--text-secondary)'
            }}>
              <span className="live-dot" />
              <span>Telemetry: {lastUpdated.toLocaleTimeString()}</span>
            </div>

            <button
              className="btn btn-secondary btn-sm"
              style={{ backgroundColor: 'hsla(222, 24%, 9%, 0.92)', backdropFilter: 'blur(10px)' }}
              onClick={() => handleFlyTo(6.936419, 79.957216, 12)}
              title="Reset View to Kelani Basin"
            >
              <Compass size={13} />
              <span>Kelani Basin</span>
            </button>

            <button
              className="btn btn-secondary btn-sm"
              style={{ backgroundColor: 'hsla(222, 24%, 9%, 0.92)', backdropFilter: 'blur(10px)' }}
              onClick={() => handleFlyTo(6.940000, 80.490000, 11)}
              title="Focus on Nuwara Eliya Landslide Zone"
            >
              <Mountain size={13} />
              <span>Nuwara Eliya</span>
            </button>

            <button
              className="btn btn-primary btn-sm"
              onClick={handleLocateMe}
              title="Center on My GPS Location"
            >
              <Navigation size={13} />
              <span>Locate Me</span>
            </button>
          </div>
        </div>
      )}

      {/* Leaflet Map Canvas */}
      <MapContainer
        center={mapCenter}
        zoom={mapZoom}
        style={{ height, width: '100%', background: '#11141c' }}
        scrollWheelZoom={true}
      >
        <MapController center={mapCenter} zoom={mapZoom} />
        {onMapClick && <MapClickHandler onMapClick={onMapClick} />}

        {/* High-Contrast CartoDB Dark Matter / Voyager Tiles */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
          maxZoom={19}
        />

        {/* Selected Coordinates Pin */}
        {selectedLocation && (
          <Marker position={[selectedLocation.lat, selectedLocation.lng]}>
            <Popup>
              <div style={{ color: '#111', fontSize: '0.85rem' }}>
                <strong>Pinpointed Location Coordinates</strong>
                <p style={{ margin: '4px 0', fontSize: '0.78rem', fontFamily: 'monospace' }}>
                  Lat: {selectedLocation.lat.toFixed(5)}<br/>
                  Lng: {selectedLocation.lng.toFixed(5)}
                </p>
                <span style={{ fontSize: '0.72rem', color: '#16a34a', fontWeight: '700' }}>Coordinates synchronized to SOS form</span>
              </div>
            </Popup>
          </Marker>
        )}

        {/* 1. Flood Hazard Polygons & Threat Hotspots */}
        {showFloods && (
          <>
            {/* Kelani Main River Flood Inundation Buffer Zones */}
            <Circle
              center={[6.936419, 79.957216]}
              radius={2800}
              pathOptions={{
                color: 'hsl(217, 91%, 60%)',
                fillColor: 'hsl(217, 91%, 60%)',
                fillOpacity: 0.22,
                weight: 2,
                dashArray: '6, 6'
              }}
            >
              <Popup>
                <div style={{ color: '#111', fontSize: '0.85rem' }}>
                  <strong style={{ color: 'hsl(217, 91%, 50%)' }}>Kelani River Primary Flood Basin</strong>
                  <p style={{ margin: '4px 0 0', fontSize: '0.78rem' }}>
                    <strong>Risk Tier:</strong> HIGH (88.5/100)<br/>
                    <strong>Catchment Exposure:</strong> Ranala, Nawagamuwa, Kaduwela<br/>
                    <strong>River Stage Height:</strong> 4.2m (Major Flood Warning)
                  </p>
                </div>
              </Popup>
            </Circle>

            <Circle
              center={[6.923639, 80.002176]}
              radius={1800}
              pathOptions={{
                color: 'hsl(350, 89%, 60%)',
                fillColor: 'hsl(350, 89%, 60%)',
                fillOpacity: 0.25,
                weight: 2
              }}
            >
              <Popup>
                <div style={{ color: '#111', fontSize: '0.85rem' }}>
                  <strong style={{ color: 'hsl(350, 89%, 50%)' }}>Kaduwela Bridge Critical Inundation Zone</strong>
                  <p style={{ margin: '4px 0 0', fontSize: '0.78rem' }}>
                    <strong>Model 1 Score:</strong> 91.0/100 (Critical Flash Flood Threat)<br/>
                    <strong>Low-Level Road Status:</strong> Submerged & Closed
                  </p>
                </div>
              </Popup>
            </Circle>
          </>
        )}

        {/* 2. Hazard Points from Dataset (Flood & Landslide) */}
        {hazardZones.map((zone, idx) => {
          if (zone.hazard === 'Flood' && !showFloods) return null;
          if (zone.hazard === 'Landslide' && !showLandslides) return null;

          return (
            <Marker
              key={`hazard-${idx}`}
              position={[zone.lat, zone.lng]}
              icon={createHazardIcon(zone.hazard)}
            >
              <Popup>
                <div style={{ color: '#111', fontSize: '0.85rem', minWidth: '180px' }}>
                  <strong style={{ display: 'block', fontSize: '0.95rem' }}>
                    {zone.name}
                  </strong>
                  <div style={{ display: 'flex', justifyContent: 'space-between', margin: '6px 0', fontSize: '0.8rem' }}>
                    <span>Threat Hazard:</span>
                    <strong style={{ color: zone.hazard === 'Flood' ? '#0066cc' : '#cc0000' }}>{zone.hazard}</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                    <span>Model Risk Score:</span>
                    <strong>{zone.score} / 100</strong>
                  </div>
                  <div style={{ marginTop: '6px', fontSize: '0.72rem', color: '#666' }}>
                    Severity: <strong>{zone.risk_level.toUpperCase()}</strong>
                  </div>
                </div>
              </Popup>
            </Marker>
          );
        })}

        {/* 3. Real-Time Active SOS Emergency Markers */}
        {showSOS && sosPoints.map((sos) => (
          <Marker
            key={`sos-${sos.id}`}
            position={[sos.lat || sos.latitude, sos.lng || sos.longitude]}
            icon={createSOSIcon(sos.priority || sos.priority_score || 50, sos.people || sos.affected_people || 1)}
          >
            <Popup>
              <div style={{ color: '#111', fontSize: '0.85rem', minWidth: '220px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #ddd', paddingBottom: '4px', marginBottom: '6px' }}>
                  <strong style={{ color: '#cc0000', fontSize: '1rem' }}>Emergency SOS #{sos.id}</strong>
                  <span style={{ background: '#cc0000', color: '#fff', padding: '1px 6px', borderRadius: '4px', fontSize: '0.72rem', fontWeight: '800' }}>
                    P: {Math.round(sos.priority || sos.priority_score || 50)}/100
                  </span>
                </div>

                <p style={{ margin: '4px 0', fontSize: '0.8rem', lineHeight: '1.4' }}>
                  <strong>Location:</strong> {sos.gn || sos.gn_division || sos.district || 'Kelani Basin'}<br/>
                  <strong>Casualties:</strong> {sos.people || sos.affected_people || 1} Persons<br/>
                  {sos.medical_needs_summary && (
                    <span style={{ color: '#d97706', display: 'block', marginTop: '3px' }}>
                      <strong>Medical Need:</strong> {sos.medical_needs_summary}
                    </span>
                  )}
                </p>

                {onResolveSOS && sos.status === 'active' && (
                  <button
                    onClick={() => onResolveSOS(sos.id, 'triaged')}
                    style={{
                      marginTop: '6px',
                      width: '100%',
                      padding: '6px',
                      background: '#16a34a',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontWeight: '700',
                      fontSize: '0.75rem',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '4px'
                    }}
                  >
                    <span>Mark Triaged by Responders</span>
                  </button>
                )}
              </div>
            </Popup>
          </Marker>
        ))}

        {/* 4. Approved & Operational Medical Relief Camps */}
        {showCamps && camps.map((camp) => (
          <Marker
            key={`camp-${camp.id}`}
            position={[camp.lat || camp.latitude, camp.lng || camp.longitude]}
            icon={createCampIcon(camp.status)}
          >
            <Popup>
              <div style={{ color: '#111', fontSize: '0.85rem', minWidth: '200px' }}>
                <strong style={{ color: '#16a34a', fontSize: '0.95rem' }}>{camp.name}</strong>
                <p style={{ margin: '4px 0', fontSize: '0.78rem' }}>
                  <strong>Location:</strong> {camp.gn_division || camp.ds_division}, {camp.district}<br/>
                  <strong>Capacity:</strong> {camp.current_occupancy || 0} / {camp.estimated_capacity || camp.capacity || 100} beds<br/>
                  <strong>Suitability:</strong> {camp.suitability || camp.suitability_score || 85}/100<br/>
                  <strong>Status:</strong> <span style={{ color: '#16a34a', fontWeight: '700' }}>{camp.status?.toUpperCase()}</span>
                </p>
                <a
                  href={`https://www.google.com/maps/search/?api=1&query=${camp.lat || camp.latitude},${camp.lng || camp.longitude}`}
                  target="_blank"
                  rel="noreferrer"
                  style={{ color: '#2563eb', fontSize: '0.75rem', fontWeight: '700', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '4px', marginTop: '4px' }}
                >
                  <span>Open GPS Navigation in Google Maps &rarr;</span>
                </a>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>

      {/* Map Legend Overlay */}
      <div style={{
        position: 'absolute',
        bottom: '12px',
        right: '12px',
        zIndex: 999,
        backgroundColor: 'hsla(222, 24%, 9%, 0.92)',
        backdropFilter: 'blur(10px)',
        border: '1px solid var(--border-default)',
        borderRadius: 'var(--radius-md)',
        padding: '10px 14px',
        fontSize: '0.74rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '6px',
        boxShadow: 'var(--shadow-md)',
        pointerEvents: 'none'
      }}>
        <strong style={{ color: 'var(--text-primary)', marginBottom: '2px', letterSpacing: '0.04em' }}>GIS MAP LEGEND</strong>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-rose)' }}>
          <ShieldAlert size={14} />
          <span>Critical Emergency SOS (P &ge; 85)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-blue)' }}>
          <Waves size={14} />
          <span>Kelani Flood Inundation Buffer</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-amber)' }}>
          <Mountain size={14} />
          <span>Nuwara Eliya Landslide Threat</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-emerald)' }}>
          <Tent size={14} />
          <span>Approved Medical Relief Camp</span>
        </div>
      </div>
    </div>
  );
}
