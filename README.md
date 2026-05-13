Smart Medical Donation System with Disaster Response Donation System
A disaster management platform designed to support victims, hospitals, donors, and emergency response teams during natural disasters such as floods, landslides, and pandemics. The system combines an Offline-First PWA, Machine Learning, and GIS to ensure emergency requests can be collected, stored, synchronized, analyzed, and visualized in real time — even in low-connectivity environments.

Project Overview
During disasters, affected people often cannot access medical support quickly due to:
Unstable or unavailable internet connectivity
Lost or delayed emergency requests
Inability to identify high-demand medical areas
Poorly managed donations causing duplication or shortages
Sub-optimal placement of temporary medical camps
This platform solves these problems through a five-stage pipeline:
```
Capture Offline → Store & Sync → ML Geo-Intel → Resource Map → Donation Match
```
---
Key Features
Feature	Description
Offline-First PWA	Service workers capture and store emergency requests locally using IndexedDB — no internet required
Store-and-Forward Sync	Automatically synchronizes offline data to the central server when connectivity is restored
ML Site Recommendation	Predicts optimal locations for temporary medical camps using historical disaster data
Live GIS Heatmaps	Real-time demand density maps via Leaflet.js and OpenStreetMap
Smart Donation Matching	Connects donors with verified, real-time medical needs to prevent wastage
Clinical Priority Queue	Rule-based triage engine that scores and ranks patient cases by urgency
Disaster Relief Prediction	XGBoost-powered medicine demand forecasting for disaster-affected areas
Multi-Channel Input	Accepts requests via PWA web app and SMS gateway
---
---
Team & Components
IT22104076 — E. M. K. N. Ekanayake
Component 1 — Offline-First Progressive Web Application (PWA)
What it does
This component ensures the entire platform keeps working even when internet connectivity is completely unavailable — which is the most common scenario during natural disasters such as floods or landslides.
How it works
The application is built as a Progressive Web App (PWA) using React.js, with a Service Worker running in the background at all times. When a victim, volunteer, or health worker submits an emergency medical request and there is no internet connection, the Service Worker intercepts the request and stores it locally in the browser using IndexedDB (a built-in offline database). The data stays safe on the device until connectivity is restored, at which point the system automatically synchronizes everything with the central MongoDB server — without the user needing to do anything manually.
Key behaviours
Works fully offline — no internet required to submit emergency requests
Service Worker monitors network status continuously
Emergency data is never lost, even if the device loses power after submission (IndexedDB persists across sessions)
No manual re-submission needed; sync happens automatically in the background
Supports low-bandwidth environments where connections are slow or intermittent
Technology
React.js (frontend framework)
Service Workers (background sync and offline interception)
IndexedDB (local offline data storage)
PWA manifest (installable on mobile and desktop)
---
Component 2 — Store-and-Forward Synchronization
What it does
This component handles the reliable transfer of offline-stored emergency data back to the central server once internet connectivity returns, ensuring zero data loss across the entire disaster response lifecycle.
How it works
When a request is submitted offline, it follows a structured store-and-forward pipeline:
The user submits an emergency medical request through the PWA
The Service Worker detects there is no internet and stores the request in IndexedDB locally
The Service Worker continuously monitors network connectivity in the background
As soon as a connection is detected, the queued requests are automatically packaged and sent to the central Node.js/Express backend
The backend confirms receipt and the local queue is cleared
This mechanism means that even in areas where internet access appears only briefly — for example, a few minutes of 2G signal — the system will flush all stored requests during that window.
Key behaviours
Fully automatic — no user action required after initial submission
Handles multiple queued requests in a single sync batch
Prevents duplicate submissions through request ID tracking
Maintains submission timestamp integrity (timestamps reflect when the request was originally made, not when it was synced)
Improves disaster response continuity by ensuring command centres receive complete, uninterrupted data streams
Technology
Service Workers (background sync API)
IndexedDB (persistent local queue)
Node.js + Express.js (backend receiver)
MongoDB (central data store)
---
Component 3 — GIS Dynamic Resource Mapping
What it does
This component provides a live, interactive map that gives emergency authorities, hospital administrators, and relief coordinators a real-time visual picture of where resources are, where demand is concentrated, and which zones need urgent attention.
How it works
The system integrates Leaflet.js with OpenStreetMap tiles to render an interactive map directly inside the PWA. As emergency requests are submitted and synchronized, the backend processes their geographic coordinates and updates the map in real time. The map visualizes multiple layers of information simultaneously, allowing coordinators to see the full operational picture at a glance.
A key feature is live demand heatmapping — areas with a high concentration of incoming emergency requests are rendered as heat zones on the map, making it immediately obvious where the greatest medical need is clustered, without requiring any manual analysis.
Map layers and features
Layer	Description
Hospital markers	Locations of active hospitals and their current status
Medical camp markers	Positions of deployed temporary medical camps
Donation centre markers	Locations where donations can be dropped off or collected
Emergency zone highlights	High-priority areas flagged for urgent resource deployment
Live demand heatmap	Colour-gradient overlay showing real-time request density by location
Key benefits
Helps authorities make deployment decisions in seconds rather than hours
Reduces the risk of sending resources to already-served areas
Improves coordination between multiple response teams operating in the same region
Enhances situational awareness for NGOs, government agencies, and hospital networks
Technology
Leaflet.js (interactive map rendering)
OpenStreetMap (open-source map tiles)
GeoJSON data format for location markers
Backend coordinate processing (Node.js + MongoDB geospatial queries)
---
Component 4 — ML-Based Geo-Intelligence for Camp Location Recommendation
What it does
This component uses Machine Learning to analyse disaster data and recommend the most optimal locations for setting up temporary medical camps — removing guesswork from one of the most critical decisions in disaster response.
The problem it solves
During a disaster, authorities must quickly decide where to position temporary medical camps. Poor placement wastes resources, leaves victims unreachable, and slows response times. This component automates that decision by learning from historical disaster patterns and current demand signals.
How it works
The ML pipeline ingests multiple data sources and produces a ranked list of recommended camp locations along with demand density heatmaps.
Input features used by the model:
Feature	Description
Geographic coordinates	Latitude/longitude of incoming requests
Disaster type	Flood, landslide, pandemic, etc.
Population density	Number of people in each zone
Number of medical requests	Volume of emergency submissions per area
Road accessibility	Whether the location can be physically reached
Nearby hospitals	Distance to existing healthcare infrastructure
Processing pipeline:
Historical disaster records are used to train the Scikit-learn model
During a live disaster, real-time request data is fed into the trained model
The model identifies high-demand medical zones and predicts where urgent assistance will be needed next
It outputs a ranked list of safe, accessible, and strategically optimal camp locations
Results are overlaid on the GIS map as heatmaps and location markers
Expected outputs:
Recommended coordinates for new temporary medical camps
Demand density heatmaps showing predicted pressure zones
Risk flags for areas where demand is projected to escalate
Key benefits
Reduces decision-making time from hours to minutes for field commanders
Accounts for road accessibility, preventing camps from being placed in unreachable areas
Learns from past disasters, improving recommendations over time
Integrates directly with the GIS map so recommendations are immediately actionable
Technology
Python (ML pipeline)
Scikit-learn (clustering and prediction algorithms)
Pandas (data preprocessing and feature engineering)
Leaflet.js + OpenStreetMap (visualization of recommendations)
MongoDB (storage of historical and real-time disaster data)
---
IT22128522 - Perera D. K. S. D.
Patient Onboarding & Clinical Priority Queue
A structured three-step workflow for registering and triaging patients:
Step 1 — Patient Identification: Captures name, age, NIC, and financial constraint status with GN citizen record verification
Step 2 — Hospital & Medical Officer Verification: Validates institutions via HIN/HNO search and fuzzy alias matching; verifies medical officers against SLMC registration numbers
Step 3 — Medical Priority Assessment: Analyzes a free-text medical summary through a rule-based clinical scoring engine
Clinical Priority Engine (Rules v2)
A fully explainable, rule-based triage mechanism (no black-box ML). Scores patients across:
Category	Examples
Diseases	Dengue, stroke, sepsis, pneumonia, COVID-19
Severity Indicators	Critical, unstable, life-threatening, ICU required
Symptoms	Bleeding, respiratory failure, chest pain, shock
Situational Factors	Financial constraints, public/government hospital access
Priority Bands:
Level	Score Range
LOW	0 – 24
MEDIUM	25 – 49
HIGH	50 – 79
EMERGENCY	80+
Data Sets Used: GN Divisions, Hospital Registry, Medical Officer (MO) Registry
---
IT22177414 - Fernando R. U.
Intelligent Donor Matching & Disaster Relief Prediction
Component 1 — Intelligent Donor Request Matching & Recommendation System
An AI-powered recommendation engine that personalizes donation feeds for each donor by computing a compatibility score using:
Geographic distance between donor and hospital
Donor preference matching
Medicine category similarity
Urgency-based priority score
Donation affordability estimation
Historical donor interaction patterns
ML Models Evaluated:
Model	RMSE	MAE	R² Score	Result
Random Forest	0.023981	0.008663	0.988118	✅ Selected
CatBoost	0.027504	0.014963	0.984370	—
XGBoost	0.084982	0.060729	0.850782	—
Supports two donation workflows: Medicine Donation and Monetary Donation.
Component 2 — Integrated Disaster Relief Prediction System
Predicts medicine demand for disaster-affected GN divisions using historical OTC demand data, population demographics, and seasonal patterns.
ML Models Evaluated (Medicine Demand Forecasting):
Model	MAE	RMSE	R² Score	Result
Random Forest	0.005086	0.008808	0.5544	—
XGBoost	0.004691	0.008356	0.5990	✅ Selected
Outputs structured donation requests published to hospitals, NGOs, and relief coordinators. Includes a Streamlit dashboard for real-time visualization of predicted demand, active relief requests, and population statistics.
---
Tech Stack
Frontend
React.js
Progressive Web App (PWA)
Service Workers
Backend
Node.js
Express.js
Database
MongoDB
IndexedDB (offline storage)
Mapping & GIS
Leaflet.js
OpenStreetMap
Machine Learning
Python
Scikit-learn
XGBoost
CatBoost
Pandas
Streamlit (dashboard)
---
Getting Started
Prerequisites
Node.js (v18+)
Python 3.9+
MongoDB
Installation
```bash
# Clone the repository
git clone https://github.com/kavithaniwandi/R26-IT-047.gitcd smart-medical-donation-system

# Install frontend/backend dependencies
npm install

# Install Python ML dependencies
pip install -r requirements.txt

# Start the backend server
npm run server

# Start the frontend PWA
npm run client

# Launch the Streamlit dashboard 
streamlit run disaster_prediction/dashboard.py
```
Environment Variables
Create a `.env` file in the root directory:
```env
MONGO_URI=mongodb+srv://disadmin:rjslffvvLMIDWSgJ@cluster0.mlaz1dg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0PORT=5000
```
---
Functional Requirements
Offline Submission — Store medical requests locally using IndexedDB; support operation without internet
Auto Synchronization — Automatically send stored requests when connectivity is restored
Multi-Channel Input — Accept requests via PWA web app and SMS gateway
Live Heatmapping — Display demand density on maps using geographic coordinates
ML Site Recommendation — Recommend suitable temporary medical camp locations
Smart Donation Matching — Match donations with verified urgent needs
Priority Triage — Categorize requests into Critical, High, and Normal
---
Non-Functional Requirements
Requirement	Description
Reliability	Prevent loss of critical emergency requests
Availability	Support low-bandwidth and offline environments
Scalability	Handle large-scale disaster traffic
Accuracy	Maintain precise ML predictions and donation matching
Usability	Simple, high-contrast interface designed for stressed users
Data Security	Protect victim information and ensure authorized access
---
ML Models & Performance
Camp Location Recommendation 
Algorithm: Scikit-learn clustering/classification
Input: Geographic coordinates, disaster type, population density, number of requests, road accessibility, nearby hospitals
Output: Optimal camp locations and demand heatmaps
Clinical Priority Scoring 
Type: Rule-based (fully explainable, not ML)
Rules Version: 2
NLP: Optional lightweight spaCy tokenization (no embeddings or NER)
Donor Matching Selected Model: Random Forest (R² = 0.9881)
Medicine Demand Forecasting 
Selected Model: XGBoost Regressor (R² = 0.5990)
Data: OTC datasets 2022–2024 + Kaduwela population demographics
---
 Evaluation Plan
Technical Evaluation
Synchronization Success Rate — Measure offline-to-online sync reliability
ML Accuracy — Compare predicted camp locations with historical demand data
System Performance — Measure request-to-dashboard update latency
Matching Efficiency — Quantify reduction in resource wastage
User-Centered Evaluation
Usability Testing — Time-to-submit under stress conditions
Decision Efficiency — Donor response speed vs. traditional systems
User Surveys — Likert-scale feedback from volunteers
Field Simulations — Testing in low-connectivity disaster scenarios
---
 Knowledge Domains
Software Architecture (offline-first systems, sync mechanisms)
Geographic Information Systems (mapping, spatial analysis)
Machine Learning (predictive analytics, recommendation systems)
Humanitarian Logistics (disaster resource management)
Human-Computer Interaction (emergency-focused UI/UX)
---
 License
This project is licensed under the MIT License. See the LICENSE file for details.
