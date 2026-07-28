import React from "react";
import { Link } from "react-router-dom";
import {
  FaHospital,
  FaHeartbeat,
  FaMapMarkedAlt,
  FaHandsHelping,
  FaAmbulance,
  FaBoxes,
  FaShieldAlt,
  FaUserFriends,
  FaArrowRight,
  FaTint,
  FaLocationArrow
} from "react-icons/fa";

import Navigation from "../components/Navigation";
import Footer from "../components/Footer";
import "./Home.css";


function Home() {

  return (

    <div className="home">

      <Navigation />


      {/* ================= HERO SECTION ================= */}

      <section className="hero-section">

        <div className="hero-overlay"></div>

        <div className="hero-container">

          <div className="hero-content">

            <h1>
              Smart Medical Donation
              <br />
              & Emergency Response System
            </h1>


            <p>
              Connecting donors, hospitals, volunteers and emergency
              responders to deliver medical resources faster during
              disasters and critical situations.
            </p>


            <div className="hero-buttons">

              <Link
                to="/donations"
                className="primary-btn"
              >
                Donate Now
              </Link>


              <Link
                to="/map"
                className="secondary-btn"
              >
                View Disaster Map
              </Link>

            </div>


          </div>

        </div>

      </section>



      {/* ================= STATISTICS ================= */}


      <section className="statistics-section">

        <div className="container">


          <div className="statistics-grid">


            <div className="stat-card">

              <h2>
                12K+
              </h2>

              <p>
                Registered Donors
              </p>

            </div>



            <div className="stat-card">

              <h2>
                350+
              </h2>

              <p>
                Healthcare Partners
              </p>

            </div>



            <div className="stat-card">

              <h2>
                8K+
              </h2>

              <p>
                Emergency Requests
              </p>

            </div>



            <div className="stat-card">

              <h2>
                24/7
              </h2>

              <p>
                Emergency Support
              </p>

            </div>


          </div>


        </div>

      </section>





      {/* ================= ABOUT ================= */}


      <section className="about-section">


        <div className="container">


          <div className="section-title">


            <span>
              ABOUT OUR SYSTEM
            </span>


            <h2>
              Saving Lives Through
              Intelligent Coordination
            </h2>


            <p>

              Our platform provides a centralized solution for medical
              donations, disaster monitoring, emergency requests and
              resource allocation. It helps deliver essential medical
              support to affected communities quickly and efficiently.

            </p>


          </div>





          <div className="about-grid">


            <div className="info-card">


              <FaHospital className="card-icon"/>


              <h3>
                Hospital Network
              </h3>


              <p>
                Connect hospitals and healthcare organizations
                with available medical resources.
              </p>


            </div>





            <div className="info-card">


              <FaHeartbeat className="card-icon"/>


              <h3>
                Medical Donations
              </h3>


              <p>
                Manage medicine, equipment and emergency
                supply donations securely.
              </p>


            </div>





            <div className="info-card">


              <FaMapMarkedAlt className="card-icon"/>


              <h3>
                Disaster Mapping
              </h3>


              <p>
                Monitor flood and landslide affected areas
                using interactive maps.
              </p>


            </div>





            <div className="info-card">


              <FaHandsHelping className="card-icon"/>


              <h3>
                Volunteer Network
              </h3>


              <p>
                Coordinate volunteers for emergency support
                and supply distribution.
              </p>


            </div>


          </div>


        </div>


      </section>





      {/* ================= SERVICES ================= */}


      <section className="services-section">


        <div className="container">


          <div className="section-title">

            <span>
              OUR SERVICES
            </span>


            <h2>
              Complete Disaster Response Solution
            </h2>


          </div>





          <div className="services-grid">



            <div className="service-card">

              <FaAmbulance className="service-icon"/>

              <h3>
                Emergency Response
              </h3>

              <p>
                Rapid coordination between victims,
                responders and healthcare providers.
              </p>

            </div>




            <div className="service-card">

              <FaTint className="service-icon"/>

              <h3>
                Blood Donation
              </h3>

              <p>
                Match blood donors with urgent medical
                requirements.
              </p>

            </div>





            <div className="service-card">

              <FaBoxes className="service-icon"/>

              <h3>
                Inventory Management
              </h3>

              <p>
                Track available medicines and medical
                equipment.
              </p>

            </div>





            <div className="service-card">

              <FaLocationArrow className="service-icon"/>

              <h3>
                Location Tracking
              </h3>

              <p>
                Identify affected areas and optimize
                resource delivery.
              </p>

            </div>





            <div className="service-card">

              <FaShieldAlt className="service-icon"/>

              <h3>
                Secure Platform
              </h3>

              <p>
                Protect user information with
                authentication and verification.
              </p>

            </div>





            <div className="service-card">

              <FaUserFriends className="service-icon"/>

              <h3>
                Community Support
              </h3>

              <p>
                Connect volunteers and communities
                during emergencies.
              </p>

            </div>



          </div>


        </div>


      </section>





      {/* ================= DISASTER MAP PREVIEW ================= */}



      <section className="map-section">


        <div className="container map-container">


          <div className="map-content">


            <span>
              REAL TIME MONITORING
            </span>


            <h2>
              Disaster Intelligence Dashboard
            </h2>


            <p>
              Monitor disaster locations, affected communities,
              emergency requests and available resources through
              a centralized mapping system.
            </p>


            <Link
              to="/map"
              className="map-btn"
            >

              Explore Map
              <FaArrowRight/>

            </Link>


          </div>



          <div className="map-box">

            <h3>
              Live Disaster Map
            </h3>


            <p>
              Floods • Landslides • Emergency Requests
            </p>


          </div>



        </div>


      </section>






      {/* ================= CTA ================= */}


      <section className="cta-section">


        <div className="container">


          <h2>
            Together We Can Save More Lives
          </h2>


          <p>
            Become a donor or volunteer and support
            communities during emergencies.
          </p>



          <div className="cta-buttons">


            <Link
              to="/donations"
              className="primary-btn"
            >
              Become A Donor
            </Link>



            <Link
              to="/contacts"
              className="secondary-btn"
            >
              Join Volunteers
            </Link>


          </div>


        </div>


      </section>




      <Footer />


    </div>

  );

}


export default Home;