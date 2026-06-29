<div align="center">

# Smart Medical Donation System with Disaster Response

### Intelligent Disaster Healthcare Support & Resource Optimization Platform

An **offline-first disaster healthcare platform** designed to support victims, hospitals, donors, and emergency response teams during floods, landslides, pandemics, and other crisis situations.

The system combines **Progressive Web Applications (PWA)**, **Machine Learning**, and **Geographic Information Systems (GIS)** to ensure emergency medical requests can be captured, synchronized, analyzed, and visualized in real time — even in low-connectivity environments.

---

![React](https://img.shields.io/badge/Frontend-React.js-61DAFB?style=for-the-badge&logo=react)
![Node](https://img.shields.io/badge/Backend-Node.js-339933?style=for-the-badge&logo=node.js)
![MongoDB](https://img.shields.io/badge/Database-MongoDB-47A248?style=for-the-badge&logo=mongodb)
![Python](https://img.shields.io/badge/ML-Python-3776AB?style=for-the-badge&logo=python)
![PWA](https://img.shields.io/badge/Architecture-Offline--First-black?style=for-the-badge)

</div>

---

# System Workflow

```text
Capture Offline
       ↓
Store & Synchronize
       ↓
ML Geo-Intelligence
       ↓
GIS Resource Mapping
       ↓
Smart Donation Matching
```

---

# Overview

During disasters, emergency healthcare systems often fail because of:

- Unstable or unavailable internet connectivity
- Delayed or lost emergency requests
- Lack of visibility into high-demand medical zones
- Poorly coordinated donation distribution
- Inefficient temporary medical camp placement

The **Smart Medical Donation System** addresses these issues through an integrated disaster-response platform capable of operating reliably in both online and offline environments.

---

# Key Features

| Feature | Description |
|:--|:--|
| **Offline-First PWA** | Submit emergency medical requests without internet connectivity |
| **Automatic Synchronization** | Store-and-forward mechanism syncs requests when internet becomes available |
| **GIS Resource Mapping** | Interactive real-time disaster visualization using maps and heatmaps |
| **ML Camp Recommendation** | Predicts optimal temporary medical camp locations |
| **Clinical Priority Queue** | Rule-based triage system prioritizing patients by urgency |
| **Smart Donation Matching** | Matches donors with urgent verified medical needs |
| **Disaster Relief Prediction** | Forecasts medicine demand in affected regions |
| **Multi-Channel Support** | Supports both PWA and SMS-based submissions |

---

# System Architecture

```text
 ┌───────────────────────────┐
 │ Victims / Volunteers      │
 └─────────────┬─────────────┘
               │
               ▼
 ┌───────────────────────────┐
 │ Offline-First PWA         │
 │ React.js + ServiceWorker  │
 └─────────────┬─────────────┘
               │
               ▼
 ┌───────────────────────────┐
 │ IndexedDB Offline Queue   │
 └─────────────┬─────────────┘
               │
               ▼
 ┌───────────────────────────┐
 │ Node.js + Express Backend │
 └─────────────┬─────────────┘
               │
               ▼
 ┌───────────────────────────┐
 │ MongoDB Central Database  │
 └─────────────┬─────────────┘
               │
      ┌────────┴────────┐
      ▼                 ▼
 ML Analytics      GIS Visualization
   (Python)           (Leaflet.js)
```

---

# Team & Components

---

# IT22104076 — E. M. K. N. Ekanayake

## Component 01 — Offline-First Progressive Web Application (PWA)

### Purpose

Ensures emergency medical requests can still be submitted even when internet connectivity is unavailable.

### Core Functionalities

- Offline emergency request submission
- Local persistent storage using IndexedDB
- Automatic background synchronization
- Installable Progressive Web Application support
- Reliable request preservation across sessions

### Workflow

```text
User Submits Request
        ↓
Service Worker Detects Offline State
        ↓
Request Stored in IndexedDB
        ↓
Connectivity Restored
        ↓
Automatic Synchronization to Server
```

### Technologies

- React.js
- Service Workers
- IndexedDB
- PWA Manifest

---

## Component 02 — Store-and-Forward Synchronization

### Purpose

Ensures reliable synchronization of offline-collected disaster data with the central server.

### Synchronization Pipeline

```text
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
```

### Features

- Automatic synchronization
- Duplicate prevention
- Batch request handling
- Timestamp integrity maintenance
- Reliable low-bandwidth operation

### Technologies

- Service Worker Background Sync API
- IndexedDB
- Node.js
- Express.js
- MongoDB

---

## Component 03 — GIS Dynamic Resource Mapping

### Purpose

Provides real-time situational awareness through interactive GIS mapping.

### GIS Layers

| Layer | Description |
|:--|:--|
| Hospital Markers | Active hospitals and operational status |
| Medical Camps | Temporary medical camp locations |
| Donation Centers | Donation collection and distribution points |
| Emergency Zones | High-priority disaster response regions |
| Demand Heatmaps | Real-time medical request density visualization |

### Benefits

- Faster emergency deployment decisions
- Better coordination among agencies
- Reduced resource duplication
- Improved operational visibility

### Technologies

- Leaflet.js
- OpenStreetMap
- GeoJSON
- MongoDB Geospatial Queries

---

## Component 04 — ML-Based Geo-Intelligence for Camp Recommendation

### Purpose

Uses Machine Learning to recommend optimal temporary medical camp locations.

### Input Features

| Feature | Description |
|:--|:--|
| Geographic Coordinates | Latitude & longitude |
| Disaster Type | Flood, landslide, pandemic |
| Population Density | Population concentration |
| Emergency Request Volume | Number of incoming requests |
| Road Accessibility | Reachability analysis |
| Nearby Hospitals | Existing healthcare infrastructure |

### ML Pipeline

```text
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
```

### Outputs

- Recommended camp locations
- Demand density heatmaps
- High-risk escalation zones

### Technologies

- Python
- Scikit-learn
- Pandas
- Leaflet.js
- MongoDB

---

# IT22128522 — Perera D. K. S. D.

# Patient Onboarding & Clinical Priority Queue

## Three-Step Workflow

### Step 01 — Patient Identification

- Name, age, and NIC collection
- Financial constraint identification
- GN division verification

### Step 02 — Hospital & Medical Officer Verification

- HIN/HNO validation
- Fuzzy alias matching
- SLMC medical officer verification

### Step 03 — Medical Priority Assessment

- Free-text medical summary analysis
- Rule-based clinical scoring engine

---

## Clinical Priority Engine (Rules v2)

### Scoring Categories

| Category | Examples |
|:--|:--|
| Diseases | Dengue, stroke, sepsis |
| Severity Indicators | ICU required, unstable |
| Symptoms | Bleeding, respiratory failure |
| Situational Factors | Financial constraints |

### Priority Levels

| Level | Score Range |
|:--|:--|
| LOW | 0 – 24 |
| MEDIUM | 25 – 49 |
| HIGH | 50 – 79 |
| EMERGENCY | 80+ |

---

# IT22177414 — Fernando R. U.


## Component 01 — Intelligent Donor Matching & Disaster Relief Prediction

## Overview
A machine learning–based medical donation matching system that ranks donation requests for each donor based on compatibility, urgency, location, and donor preference. The system helps donors view the most relevant donation requests first and supports both medicine and money donation workflows.

---

# Key Features
- Personalized donor dashboard
- Compatibility score prediction
- Ranked medical donation request feed
- Medicine donation workflow
- Money donation sandbox workflow
- Request filtering and prioritization
- ML model comparison and evaluation
- Synthetic dataset generation for training/testing

---

# Tech Stack

## Frontend
- Streamlit
- HTML / CSS / JavaScript

## Backend
- Flask

## Machine Learning
- XGBoost
- CatBoost
- Random Forest

## Libraries
- pandas
- numpy
- scikit-learn
- joblib
- streamlit

---

# Input Parameters

## Donor Features
- Age
- Residence location
- Income bracket
- Preferred donation category

## Donation Request Features
- Medicine name
- Disease type
- Age group
- Hospital location
- Medicine category
- Estimated price
- Urgency level

---

# Feature Engineering
The following features were generated for model training:

- Urgency score
- Distance calculation
- Preference matching
- Compatibility ranking score

---

# Machine Learning Models Used
- XGBoost
- CatBoost
- Random Forest

---

# Model Evaluation Metrics
The models were evaluated using:

- RMSE (Root Mean Squared Error)
- MAE (Mean Absolute Error)
- R² Score

---

# Final Model Results

| Model | RMSE | MAE | R² Score |
|---|---|---|---|
| Random Forest | 0.023981 | 0.008663 | 0.988118 |
| CatBoost | 0.027504 | 0.014963 | 0.984370 |
| XGBoost | 0.084982 | 0.060729 | 0.850782 |

### Selected Final Model
**Random Forest** was selected as the best-performing model.

---

# System Flow

1. Collect donor and donation request data
2. Preprocess and clean datasets
3. Generate important matching features
4. Train ML models
5. Predict compatibility scores
6. Rank requests by compatibility
7. Display personalized donor feed
8. Continue to medicine or money donation workflow




## Component 02 — Disaster Relief Prediction System

# Disaster Medicine Demand Forecasting & Donation Request System

## Overview
This project is an AI-powered disaster medicine demand forecasting and donation request generation system developed to support emergency healthcare resource management during disaster situations.

The system predicts weekly medicine requirements for disaster-affected GN divisions using demographic population data and historical OTC medicine demand patterns. It also generates structured donation requests to assist disaster management authorities and healthcare organizations.

---

## Features

- AI-based medicine demand forecasting
- Population-based medicine requirement estimation
- Automated donation request generation
- Interactive Streamlit dashboard
- XGBoost regression model integration
- Feature importance visualization
- Model comparison using Random Forest and XGBoost

---

## Technologies Used

- Python
- Streamlit
- XGBoost
- Random Forest
- Pandas
- NumPy
- Scikit-learn
- Matplotlib
- Joblib

---

## Machine Learning Workflow

```text
Historical Medicine Data + Population Data
                ↓
        Data Preprocessing
                ↓
       Feature Engineering
                ↓
      Model Training (RF/XGB)
                ↓
         Model Evaluation
                ↓
      XGBoost Model Selection
                ↓
     Medicine Demand Prediction
                ↓
   Donation Request Generation
```

---

## Input Parameters

| Feature | Description |
|---|---|
| Medicine_Encoded | Encoded medicine category |
| Age_Encoded | Encoded demographic age group |
| Month | Seasonal forecasting month |
| Unit_Encoded | Encoded medicine unit type |

---

## Model Evaluation

| Model | MAE | RMSE | R² Score |
|---|---|---|---|
| Random Forest | 0.005086 | 0.008808 | 0.5544 |
| XGBoost | 0.004690 | 0.008355 | 0.5990 |

### Final Selected Model
- XGBoost Regressor

---

## Installation

### Clone Repository

```bash
git clone <repository-url>
cd disaster-donation-request-prediction
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Train Models

### Random Forest

```bash
python train_model.py
```

### XGBoost

```bash
python train_xgboost.py
```

---

## Run Application

```bash
streamlit run app_xgboost.py
```

---

Final Year Research Project

# Installation Guide

## Prerequisites

- Node.js v18+
- Python 3.9+
- MongoDB

---

# Getting Started

## Clone Repository

```bash
git clone https://github.com/kavithaniwandi/R26-IT-047.git

cd smart-medical-donation-system
```

---

## Install Dependencies

```bash
npm install
```

---

## Install Python Dependencies

```bash
pip install -r requirements.txt
```

---

## Run Backend Server

```bash
npm run server
```

---

## Run Frontend Application

```bash
npm run client
```

---

## Launch Streamlit Dashboard

```bash
streamlit run disaster_prediction/dashboard.py
```

---

# Environment Variables

Create a `.env` file in the project root:

```env
MONGO_URI=mongodb+srv://disadmin:rjslffvvLMIDWSgJ@cluster0.mlaz1dg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
PORT=5000
```

---

# Functional Requirements

| Requirement | Description |
|:--|:--|
| Offline Submission | Submit requests without internet |
| Auto Synchronization | Sync requests automatically |
| Multi-Channel Input | PWA and SMS support |
| Live Heatmapping | Geographic demand visualization |
| ML Recommendation | Camp location prediction |
| Smart Donation Matching | Intelligent donor allocation |
| Priority Triage | Emergency prioritization |

---

# Non-Functional Requirements

| Requirement | Description |
|:--|:--|
| Reliability | Prevent loss of emergency data |
| Availability | Support low-bandwidth environments |
| Scalability | Handle large-scale disaster traffic |
| Accuracy | Maintain ML prediction precision |
| Usability | High-contrast emergency-focused UI |
| Security | Protect sensitive victim information |

---

# ML Models & Performance

## Camp Location Recommendation

| Property | Details |
|:--|:--|
| Algorithm | Scikit-learn clustering/classification |
| Inputs | Coordinates, disaster type, population density |
| Outputs | Camp recommendations & heatmaps |

---

## Clinical Priority Engine

| Property | Details |
|:--|:--|
| Type | Rule-based scoring |
| Explainability | Fully transparent |
| NLP | Optional spaCy tokenization |

---

## Donor Matching Model

| Selected Model | R² Score |
|:--|:--|
| Random Forest | 0.9881 |

---

## Medicine Demand Forecasting

| Selected Model | R² Score |
|:--|:--|
| XGBoost Regressor | 0.5990 |

---

# Evaluation Plan

## Technical Evaluation

- Synchronization success rate
- ML prediction accuracy
- Dashboard update latency
- Donation matching efficiency

## User-Centered Evaluation

- Stress-condition usability testing
- Decision efficiency analysis
- Volunteer feedback surveys
- Low-connectivity field simulations

---

# Knowledge Domains

- Offline-First Software Architecture
- Geographic Information Systems (GIS)
- Machine Learning & Predictive Analytics
- Humanitarian Logistics
- Emergency-Focused UI/UX Design

---

# Future Enhancements

- AI-based disaster severity prediction
- Native mobile application support
- Drone-assisted medical delivery integration
- Government emergency alert integration
- Multi-language emergency support

---

# License

This project is licensed under the **MIT License**.

See the `LICENSE` file for more information.

---

<div align="center">

### Smart Medical Donation System with Disaster Response

Building resilient healthcare response systems for disaster-affected communities through intelligent technology.

</div>
