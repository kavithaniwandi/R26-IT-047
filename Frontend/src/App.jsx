import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import Map from './pages/Map'
import Donations from './pages/Donations'
import Contacts from './pages/Contacts'
import SignIn from './pages/SignIn'
import SOS from './pages/SOS'
import Profile from './pages/Profile'
import DisasterDonationRequest from './pages/DisasterDonationRequest'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/map" element={<Map />} />
        <Route path="/donations" element={<Donations />} />
        <Route path="/contacts" element={<Contacts />} />
        <Route path="/signin" element={<SignIn />} />
        <Route path="/sos" element={<SOS />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/disaster-donation-request" element={<DisasterDonationRequest />} />
      </Routes>
    </Router>
  )
}

export default App
