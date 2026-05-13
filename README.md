Smart Medical Donation System with Disaster Response
<div align="center">
Intelligent Disaster Healthcare Support & Resource Optimization Platform

An offline-first disaster management platform designed to support victims, hospitals, donors, and emergency response teams during natural disasters such as floods, landslides, and pandemics.

Built using Progressive Web Applications (PWA), Machine Learning, and GIS technologies to ensure emergency medical requests can be collected, synchronized, analyzed, and visualized in real time — even in low-connectivity environments.

</div>
System Pipeline
Capture Offline → Store & Sync → ML Geo-Intel → Resource Map → Donation Match
Project Overview

During disasters, emergency medical response systems often fail because of:

Unstable or unavailable internet connectivity
Lost or delayed emergency requests
Poor visibility into high-demand medical zones
Inefficient donation management
Poor placement of temporary medical camps

The Smart Medical Donation System addresses these challenges through an integrated disaster-response architecture that combines:

Offline-first data collection
Reliable synchronization mechanisms
Machine learning–driven geographic intelligence
Real-time GIS visualization
Intelligent donation matching
Core Features
Feature	Description
Offline-First PWA	Emergency requests can be submitted without internet connectivity using IndexedDB and Service Workers
Store-and-Forward Synchronization	Automatically synchronizes offline data when connectivity becomes available
ML Camp Recommendation	Predicts optimal locations for temporary medical camps
GIS Heatmaps	Displays live medical demand density maps using Leaflet.js and OpenStreetMap
Smart Donation Matching	Matches donors with verified urgent medical requirements
Clinical Priority Queue	Rule-based triage system that prioritizes patients by urgency
Disaster Relief Prediction	Predicts medicine demand in affected regions using ML forecasting
Multi-Channel Input	Supports both PWA and SMS-based emergency submissions
Architecture Overview
 ┌──────────────────────┐
 │  Victims / Volunteers │
 └──────────┬───────────┘
            │
            ▼
 ┌──────────────────────┐
 │ Offline-First PWA    │
 │ React + ServiceWorker│
 └──────────┬───────────┘
            │
            ▼
 ┌──────────────────────┐
 │ IndexedDB Local Queue│
 └──────────┬───────────┘
            │ Sync
            ▼
 ┌──────────────────────┐
 │ Node.js + Express API│
 └──────────┬───────────┘
            │
            ▼
 ┌──────────────────────┐
 │ MongoDB Central Store│
 └──────────┬───────────┘
            │
 ┌──────────┴───────────┐
 │                      │
 ▼                      ▼
ML Analytics      GIS Visualization
(Python)          (Leaflet.js)
Team & Components
IT22104076 — E. M. K. N. Ekanayake
Component 01 — Offline-First Progressive Web Application (PWA)
Purpose

Ensures the platform continues functioning even when internet connectivity is unavailable during disasters.

Key Functionalities
Offline emergency request submission
Local persistent storage using IndexedDB
Automatic background synchronization
Installable PWA support
Reliable request preservation across sessions
Workflow
User Submits Request
        ↓
Service Worker Detects Offline State
        ↓
Request Stored in IndexedDB
        ↓
Network Connectivity Restored
        ↓
Automatic Synchronization to Server
Technologies
React.js
Service Workers
IndexedDB
PWA Manifest
Component 02 — Store-and-Forward Synchronization
Purpose

Guarantees reliable transmission of offline-collected disaster data to the central server.

Synchronization Pipeline
Offline Request
      ↓
Local Queue Storage
      ↓
Connectivity Monitoring
      ↓
Automatic Batch Synchronization
      ↓
Server Confirmation
      ↓
Queue Clearance
Key Features
Automatic synchronization
Duplicate prevention
Batch request handling
Timestamp integrity maintenance
Reliable low-bandwidth operation
Technologies
Service Worker Background Sync API
IndexedDB
Node.js
Express.js
MongoDB
Component 03 — GIS Dynamic Resource Mapping
Purpose

Provides real-time situational awareness through interactive disaster maps.

GIS Layers
Layer	Description
Hospital Markers	Active hospitals and status
Medical Camps	Temporary camp locations
Donation Centers	Donation collection points
Emergency Zones	High-priority response regions
Heatmaps	Live medical demand density
Key Benefits
Faster deployment decisions
Better coordination between agencies
Reduced resource duplication
Real-time operational visibility
Technologies
Leaflet.js
OpenStreetMap
GeoJSON
MongoDB Geospatial Queries
Component 04 — ML-Based Geo-Intelligence for Camp Recommendation
Purpose

Uses machine learning to recommend optimal temporary medical camp locations.

Input Features
Feature	Description
Geographic Coordinates	Latitude & longitude
Disaster Type	Flood, landslide, pandemic
Population Density	Population concentration
Request Volume	Emergency demand count
Road Accessibility	Reachability analysis
Nearby Hospitals	Existing healthcare infrastructure
ML Processing Pipeline
Historical Disaster Data
            ↓
Data Preprocessing
            ↓
ML Model Training
            ↓
Live Disaster Data Input
            ↓
Demand Analysis
            ↓
Camp Location Recommendations
            ↓
GIS Visualization
Outputs
Recommended camp coordinates
Demand heatmaps
High-risk escalation zones
Technologies
Python
Scikit-learn
Pandas
Leaflet.js
MongoDB
IT22128522 — Perera D. K. S. D.
Patient Onboarding & Clinical Priority Queue
Three-Step Workflow
Step 01 — Patient Identification
Name, age, NIC collection
Financial constraint identification
GN division verification
Step 02 — Hospital & Medical Officer Verification
HIN/HNO validation
Fuzzy alias matching
SLMC medical officer verification
Step 03 — Medical Priority Assessment
Free-text medical summary analysis
Rule-based clinical scoring engine
Clinical Priority Engine (Rules v2)
Scoring Categories
Category	Examples
Diseases	Dengue, stroke, sepsis
Severity Indicators	ICU required, unstable
Symptoms	Bleeding, respiratory failure
Situational Factors	Financial constraints
Priority Levels
Level	Score Range
LOW	0 – 24
MEDIUM	25 – 49
HIGH	50 – 79
EMERGENCY	80+
IT22177414 — Fernando R. U.
Intelligent Donor Matching & Disaster Relief Prediction
Component 01 — Intelligent Donor Matching System
Purpose

Provides personalized donation recommendations using AI-powered compatibility scoring.

Matching Factors
Geographic proximity
Donor preference matching
Medicine category similarity
Urgency scoring
Affordability estimation
Historical donor interactions
Evaluated ML Models
Model	RMSE	MAE	R² Score	Status
Random Forest	0.023981	0.008663	0.988118	Selected
CatBoost	0.027504	0.014963	0.984370	Evaluated
XGBoost	0.084982	0.060729	0.850782	Evaluated
Component 02 — Disaster Relief Prediction System
Purpose

Forecasts medicine demand for disaster-affected areas using machine learning.

Selected Model
Model	MAE	RMSE	R² Score	Status
XGBoost Regressor	0.004691	0.008356	0.5990	Selected
Outputs
Predicted medicine demand
Relief request generation
Population-based analysis
Real-time Streamlit dashboards
Technology Stack
Frontend
React.js
Progressive Web App (PWA)
Service Workers
Backend
Node.js
Express.js
Databases
MongoDB
IndexedDB
GIS & Mapping
Leaflet.js
OpenStreetMap
Machine Learning
Python
Scikit-learn
Pandas
XGBoost
CatBoost
Streamlit
Installation Guide
Prerequisites
Node.js v18+
Python 3.9+
MongoDB
Getting Started
Clone Repository
git clone https://github.com/kavithaniwandi/R26-IT-047.git

cd smart-medical-donation-system
Install Dependencies
npm install
Install Python Requirements
pip install -r requirements.txt
Start Backend Server
npm run server
Start Frontend PWA
npm run client
Launch Streamlit Dashboard
streamlit run disaster_prediction/dashboard.py
Environment Variables

Create a .env file in the project root:

MONGO_URI=mongodb+srv://YOUR_CONNECTION_STRING
PORT=5000
Functional Requirements
Requirement	Description
Offline Submission	Support emergency requests without internet
Auto Synchronization	Sync data automatically when online
Multi-Channel Input	PWA + SMS support
Live Heatmapping	Geographic demand visualization
ML Recommendation	Camp location prediction
Smart Donation Matching	Intelligent donor allocation
Priority Triage	Emergency prioritization
Non-Functional Requirements
Requirement	Description
Reliability	Prevent data loss
Availability	Support offline and low-bandwidth environments
Scalability	Handle large disaster traffic
Accuracy	Maintain ML precision
Usability	High-contrast emergency-focused UI
Security	Protect sensitive victim data
ML Models & Performance
Camp Location Recommendation
Property	Details
Algorithm	Scikit-learn clustering/classification
Inputs	Coordinates, disaster type, population density
Outputs	Camp recommendations & heatmaps
Clinical Priority Engine
Property	Details
Type	Rule-based scoring
Explainability	Fully transparent
NLP	Optional spaCy tokenization
Donor Matching Model
Selected Model	R² Score
Random Forest	0.9881
Medicine Demand Forecasting
Selected Model	R² Score
XGBoost Regressor	0.5990
Evaluation Plan
Technical Evaluation
Synchronization success rate
ML prediction accuracy
Dashboard update latency
Donation matching efficiency
User-Centered Evaluation
Stress-condition usability testing
Decision efficiency measurements
Volunteer feedback surveys
Low-connectivity field simulations
Knowledge Domains
Offline-First Software Architecture
Geographic Information Systems (GIS)
Machine Learning & Predictive Analytics
Humanitarian Logistics
Emergency-Centered UI/UX Design
Future Enhancements
AI-powered disaster severity prediction
Mobile native application support
Drone-assisted medical delivery integration
Real-time government alert integration
Multi-language emergency support
License

This project is licensed under the MIT License.

See the LICENSE file for more information.

<div align="center">
Smart Medical Donation System with Disaster Response

Building resilient healthcare response systems for disaster-affected communities through intelligent technology.

</div>
