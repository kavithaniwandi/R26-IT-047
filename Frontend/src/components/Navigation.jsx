import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import logo from "../assets/logo.png";
import "./Navigation.css";


function Navigation() {

  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navigate = useNavigate();

  const { user, logout } = useAuth();



  useEffect(() => {

    const handleScroll = () => {

      setScrolled(window.scrollY > 50);

    };


    window.addEventListener(
      "scroll",
      handleScroll
    );


    return () => {

      window.removeEventListener(
        "scroll",
        handleScroll
      );

    };


  }, []);





  const closeMenu = () => {

    setMobileMenuOpen(false);

  };





  const handleLogout = () => {

    logout();

    navigate("/");

    closeMenu();

  };





  return (

    <nav
      className={`navigation ${
        scrolled ? "scrolled" : ""
      }`}
    >


      <div className="nav-container">



        {/* LOGO */}

        <Link 
          to="/"
          className="nav-logo"
        >

          <img
            src={logo}
            alt="MediDonate Logo"
            className="logo-image"
          />

        </Link>





        {/* NAVIGATION LINKS */}

        <div
          className={`nav-links ${
            mobileMenuOpen ? "open" : ""
          }`}
        >



          <Link
            to="/"
            className="nav-link"
            onClick={closeMenu}
          >
            Home
          </Link>




          <Link
            to="/map"
            className="nav-link"
            onClick={closeMenu}
          >
            Disaster Map
          </Link>





          <Link
            to="/donations"
            className="nav-link"
            onClick={closeMenu}
          >
            Donations
          </Link>





          <Link
            to="/donation-appeal"
            className="nav-link"
            onClick={closeMenu}
          >
            Donation Appeal
          </Link>





          <Link
            to="/contacts"
            className="nav-link"
            onClick={closeMenu}
          >
            Contacts
          </Link>

          {
            user ? (

              <>


                <Link
                  to="/profile"
                  className="nav-link profile-link"
                  onClick={closeMenu}
                >

                  {user.name || "Profile"}

                </Link>




                <button
                  className="logout-button"
                  onClick={handleLogout}
                >

                  Logout

                </button>


              </>


            ) : (


              <Link
                to="/signin"
                className="nav-link"
                onClick={closeMenu}
              >

                Sign In

              </Link>


            )

          }

          <Link
            to="/sos"
            className="sos-button"
            onClick={closeMenu}
          >

            Emergency SOS

          </Link>




        </div>





        {/* MOBILE MENU */}

        <button

          className="mobile-menu-button"

          onClick={() =>
            setMobileMenuOpen(!mobileMenuOpen)
          }

        >

          <span
            className={`hamburger ${
              mobileMenuOpen ? "active" : ""
            }`}
          >

            <span></span>

            <span></span>

            <span></span>


          </span>


        </button>



      </div>


    </nav>

  );

}


export default Navigation;
