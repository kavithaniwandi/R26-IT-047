import React from 'react'
import Navigation from '../components/Navigation'
import Footer from '../components/Footer'
import './DonorDetails.css'

const donorData = {
  name: 'Nimal Perera',
  email: 'nimal.perera@gmail.com',
  phone: '+94 77 123 4567',
  location: 'Colombo 07',
  donations: [
    {
      id: 1,
      request: 'Athurugiriya South - Flood',
      date: '2026-08-10',
      item: 'Rice',
      quantity: 40,
      status: 'Fulfilled',
    },
    {
      id: 2,
      request: 'Malabe East - Flood',
      date: '2026-08-12',
      item: 'Hygiene Kits',
      quantity: 18,
      status: 'Partial',
    },
    {
      id: 3,
      request: 'Nawagamuwa - Landslide',
      date: '2026-08-14',
      item: 'Medicine',
      quantity: 12,
      status: 'Remaining',
    },
  ],
}

function DonorDetails() {
  const totalDonated = donorData.donations.reduce((sum, item) => sum + item.quantity, 0)

  return (
    <div className="donor-page">
      <Navigation />
      <main className="donor-wrapper">
        <div className="donor-card">
          <div className="donor-header">
            <div className="donor-avatar">NP</div>
            <div>
              <span className="donor-badge">Donor Profile</span>
              <h1>{donorData.name}</h1>
            </div>
          </div>

          <div className="donor-metrics">
            <div className="donor-metric">
              <span>Total Donated</span>
              <strong>{totalDonated} units</strong>
            </div>
            <div className="donor-metric">
              <span>Requests Supported</span>
              <strong>{donorData.donations.length}</strong>
            </div>
            <div className="donor-metric">
              <span>Fulfilled</span>
              <strong>{donorData.donations.filter((d) => d.status === 'Fulfilled').length}</strong>
            </div>
          </div>

          <div className="donor-info-grid">
            <div className="info-panel">
              <h3>Donor Details</h3>
              <div className="info-row">
                <span>Email</span>
                <strong>{donorData.email}</strong>
              </div>
              <div className="info-row">
                <span>Phone</span>
                <strong>{donorData.phone}</strong>
              </div>
              <div className="info-row">
                <span>Location</span>
                <strong>{donorData.location}</strong>
              </div>
            </div>

            <div className="info-panel">
              <h3>Donation History</h3>
              {donorData.donations.map((entry) => (
                <div className="history-item" key={entry.id}>
                  <div className="history-head">
                    <strong>{entry.request}</strong>
                    <span className={`status-pill ${entry.status.toLowerCase()}`}>{entry.status}</span>
                  </div>
                  <div className="history-meta">
                    <span>{entry.date}</span>
                    <span>{entry.item}</span>
                    <span>{entry.quantity} units</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  )
}

export default DonorDetails
