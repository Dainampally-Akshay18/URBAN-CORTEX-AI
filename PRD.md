# 📄 PRODUCT REQUIREMENTS DOCUMENT (PRD)

# 🏷 Product Name: **Urban Cortex AI**

Smart Urban Waste Intelligence Platform

---

# 1️⃣ EXECUTIVE SUMMARY

## 1.1 Product Overview

Urban Cortex AI is a full-stack intelligent urban waste management platform that integrates:

* IoT bin simulation (external service)
* Predictive overflow analytics
* Capacity-aware multi-truck assignment
* Route optimization engine
* Real-time truck simulation
* Complaint & governance layer
* Admin, Driver, and Citizen dashboards

The system is fully virtual (no physical hardware required) and is designed for:

* Hackathon demo readiness
* Production-grade architecture
* Future real IoT hardware integration

---

## 1.2 Technology Stack (MANDATORY)

### Frontend

* Vite
* React JS
* React Router
* Context API (or Zustand for state)
* Leaflet + OpenStreetMap
* Axios
* TailwindCSS (recommended)

### Backend

* FastAPI
* Uvicorn
* Async Python
* Pydantic Models
* Background Tasks
* WebSockets (for live updates)

### Database

* Firebase Firestore Database
* Firebase Authentication

### IoT Layer

External Simulator (already completed):

```
https://urban-simulator.onrender.com/docs
```

Backend must consume this simulator API.

---

# 2️⃣ PRODUCT VISION

Urban Cortex AI transforms reactive waste collection into:

> Predictive, adaptive, optimized, and intelligent urban waste governance.

The platform must:

* Predict bin overflow before it happens
* Dynamically assign bins to trucks
* Optimize routes per truck
* Simulate real-time truck movement
* Support citizen participation
* Provide transparent operational analytics

---

# 3️⃣ SYSTEM ARCHITECTURE (FULL STACK DESIGN)

## 3.1 High-Level Architecture

```
IoT Simulator  →  FastAPI Backend  →  Firebase
                      ↓
                WebSocket Layer
                      ↓
                React Frontend
```

---

## 3.2 Architectural Principles

The AI building this system must follow:

* Modular architecture
* Service-layer separation
* Async-first backend
* Stateless API design
* Role-based access control
* Scalable Firestore schema
* Clear separation between:

  * Data ingestion
  * Business logic
  * Simulation engine
  * UI rendering

---

# 4️⃣ BACKEND ARCHITECTURE (FastAPI)

## 4.1 Backend Modules (MANDATORY STRUCTURE)

menioned at the end of the document 

---

## 4.2 IoT Integration Requirements

The backend must:

* Periodically fetch bin data from:

  ```
  https://urban-simulator.onrender.com
  ```
* OR expose endpoint:

  ```
  POST /bin-update
  ```

  for simulator push model.

### Required Fields From Simulator

* bin_id
* city
* latitude
* longitude
* fill_level
* last_updated
* fill_history (if provided)

The backend must:

* Store/update bin in Firebase
* Trigger overflow prediction
* Recalculate urgency score

---


# 5️⃣ DATABASE DESIGN (Firebase Firestore – REVISED)

Urban Cortex AI uses Firebase Firestore as the primary database.

Firestore must be structured for:

* Role-based authentication
* Ownership enforcement
* Real-time updates
* Scalable queries
* Multi-city expansion

---

# 5.1 Collections Structure (UPDATED)

---

# 👤 users (Collection) ✅ **MANDATORY**

This collection stores application-level user metadata.

Authentication is handled by Firebase Auth.
Authorization and roles are handled here.

---

## Document ID:

```
user_id (same as Firebase UID)
```

---

## Document Structure:

```json
{
  "user_id": "UID_123",
  "name": "Rahul",
  "email": "driver@email.com",
  "role": "admin" | "driver" | "citizen",
  "assigned_truck_id": "TRUCK_01", // nullable
  "city": "Hyderabad",
  "is_active": true,
  "created_at": timestamp,
  "last_login": timestamp
}
```

---

## 🔐 Role Rules

* Admin → assigned_truck_id = null
* Driver → assigned_truck_id MUST exist
* Citizen → assigned_truck_id = null

---

## 🔗 Relationships

* Driver → references trucks.truck_id
* Citizen → references complaints via created_by
* Admin → can manage all collections

---

# 🗑 bins (Collection)

Document ID:

```
bin_id
```

```json
{
  "bin_id": "BIN_001",
  "city": "Hyderabad",
  "latitude": 17.385,
  "longitude": 78.486,
  "fill_level": 72,
  "predicted_overflow_time": timestamp,
  "urgency_score": 81,
  "status": "normal" | "urgent" | "overflow",
  "last_updated": timestamp,
  "created_at": timestamp
}
```

---

# 🚛 trucks (Collection)

Document ID:

```
truck_id
```

```json
{
  "truck_id": "TRUCK_01",
  "city": "Hyderabad",
  "max_capacity": 300,
  "current_load": 120,
  "status": "idle" | "assigned" | "in_transit",
  "assigned_route_id": "ROUTE_001",
  "driver_id": "UID_123", 
  "created_at": timestamp
}
```

---

## 🔗 Relationship

* driver_id → references users.user_id
* assigned_route_id → references routes.route_id

---

# 🗺 routes (Collection)

Document ID:

```
route_id
```

```json
{
  "route_id": "ROUTE_001",
  "truck_id": "TRUCK_01",
  "driver_id": "UID_123",
  "ordered_bin_ids": ["BIN_01", "BIN_02"],
  "total_distance": 145.6,
  "estimated_time": 5400,
  "status": "generated" | "in_progress" | "completed",
  "started_at": timestamp,
  "completed_at": timestamp,
  "created_at": timestamp
}
```

---

# 📢 complaints (Collection)

Document ID:

```
complaint_id
```

```json
{
  "complaint_id": "CMP_101",
  "type": "overflow" | "not_collected" | "new_bin_request",
  "city": "Hyderabad",
  "latitude": 17.386,
  "longitude": 78.487,
  "description": "Bin overflowing",
  "status": "pending" | "investigating" | "resolved",
  "created_by": "UID_789", 
  "assigned_admin": "UID_001",
  "created_at": timestamp,
  "resolved_at": timestamp
}
```

---

## 🔗 Relationship

* created_by → references users.user_id
* assigned_admin → references users.user_id (role = admin)

---

# 🕵️ investigations (Collection)

Document ID:

```
investigation_id
```

```json
{
  "investigation_id": "INV_201",
  "complaint_id": "CMP_101",
  "assigned_admin": "UID_001",
  "result": "valid" | "invalid" | "new_bin_required",
  "status": "open" | "closed",
  "notes": "Site inspected",
  "created_at": timestamp,
  "closed_at": timestamp
}
```

---

# 🏙 cities (Collection) – For Scalability

Document ID:

```
city_id
```

```json
{
  "city_id": "HYD",
  "name": "Hyderabad",
  "country": "India",
  "is_active": true,
  "created_at": timestamp
}
```

---

# 🔐 Role-Based Data Access Logic (Database-Level Enforcement)

Backend must enforce:

### 1️⃣ Driver Access Rule

* Can only read:

  * Their own truck
  * Their own route
* Must validate:

  ```
  user.assigned_truck_id == truck.truck_id
  ```

---

### 2️⃣ Citizen Access Rule

* Can only:

  * View public bins
  * View own complaints
* Must validate:

  ```
  complaint.created_by == user.user_id
  ```

---

### 3️⃣ Admin Access Rule

* Full access to all collections

---

# 📊 INDEXING REQUIREMENTS (IMPORTANT)

Firestore composite indexes required:

* bins (city + status)
* bins (urgency_score descending)
* routes (truck_id)
* complaints (status + city)
* users (role)

---


# 6️⃣ CORE INTELLIGENCE MODULES

## 6.1 Overflow Prediction Engine

Method:
Linear Regression

Inputs:

* fill_history
* timestamps

Output:

* predicted_overflow_time
* time_remaining
* urgency_score (calculated metric)

Trigger:

* On every bin update

---

## 6.2 Assignment Engine (Multi-Truck)

Steps:

1. Filter urgent bins:

   * fill_level > threshold (e.g., 70%)
     OR
   * overflow < X hours

2. Apply KMeans clustering:

   * k = number of active trucks

3. For each cluster:

   * Assign to one truck
   * Ensure:

     * current_load + expected_load <= max_capacity

4. Save route request

---

## 6.3 Route Optimization Engine

Algorithm:
Nearest Neighbor Heuristic

Distance:
Haversine formula

Outputs:

* ordered_bin_ids
* total_distance
* estimated_time

Stored in Firestore under routes collection.

---

## 6.4 Truck Simulation Engine (Async)

When driver clicks "Start Trip":

Backend must:

* Mark route as in_progress
* For each bin:

  * Simulate travel delay
  * Update truck location
  * Set bin fill_level = 0
  * Update truck current_load
* Mark route completed

Updates must be pushed via WebSocket.

---

# 7️⃣ ROLE-BASED AUTHENTICATION

Use Firebase Authentication.

Roles:

* admin
* driver
* citizen

Backend must:

* Validate JWT
* Enforce route-level permissions

Examples:

* Only admin can generate routes
* Only driver can start trip
* Citizen cannot access truck data

---

# 8️⃣ ENTERPRISE FRONTEND ARCHITECTURE

## 8.1 Technology Stack (FINALIZED)

Frontend MUST use:

* Vite
* React 18+
* React Router v6
* TailwindCSS (custom theme + design tokens)
* Headless UI (optional)
* Heroicons / Lucide Icons
* Zustand (for scalable state management)
* Axios
* Leaflet + OpenStreetMap
* WebSocket API
* Framer Motion (micro-interactions)
* Recharts (for analytics visualization)

This is NOT a basic hackathon UI.
It must look like:

> Stripe Dashboard + Vercel UI + Linear App level polish.

---

# 9️⃣ DESIGN SYSTEM REQUIREMENTS

Urban Cortex AI must implement a structured design system.

---

## 9.1 Tailwind Configuration

Custom Tailwind theme required:

```js
// tailwind.config.js
theme: {
  extend: {
    colors: {
      primary: "#0F172A",
      secondary: "#1E293B",
      accent: "#3B82F6",
      success: "#22C55E",
      warning: "#F59E0B",
      danger: "#EF4444"
    }
  }
}
```

---

## 9.2 Design Principles

Frontend MUST follow:

* 8px spacing system
* Soft shadows (shadow-lg, shadow-xl)
* Rounded-xl containers
* Glassmorphism overlays (optional)
* Subtle hover transitions
* Smooth animated route drawing
* Skeleton loaders (no blank screens)
* Dark mode support (MANDATORY)
* Responsive design (desktop-first, tablet-ready)

---

# 🔟 ENTERPRISE FOLDER STRUCTURE

mentioned at the end of the document 

# 1️⃣1️⃣ ADMIN DASHBOARD (ENTERPRISE SPEC)

Admin Dashboard must look like a SaaS control center.

---

## 11.1 Layout Structure

Left Sidebar:

* Logo (Urban Cortex AI)
* Overview
* Fleet
* Complaints
* Investigations
* Analytics
* Settings

Topbar:

* City selector
* Dark mode toggle
* Profile dropdown

Main Panel:

* KPI grid
* Live map
* Activity feed

---

## 11.2 KPI Cards (Animated)

Cards must show:

* Total Bins
* Urgent Bins
* Active Trucks
* Efficiency %
* Trips Avoided
* Avg Response Time

Cards animate on load using Framer Motion.

---

## 11.3 Analytics Page

Use Recharts:

Charts required:

* Fill Level Distribution (Bar chart)
* Route Distance Comparison (Baseline vs Optimized)
* Complaint Trend (Line chart)
* Fleet Utilization (Pie chart)

---

# 1️⃣2️⃣ DRIVER INTERFACE (SIMPLIFIED BUT PREMIUM)

Driver UI must be minimal, clean, distraction-free.

Sections:

* Active Route Card
* Route Map
* Capacity Progress Ring (circular animated)
* Start / Pause Button
* Live Route Timeline

During trip:

* Map auto-centers
* Collected bins fade out
* Progress percentage updates live

---

# 1️⃣3️⃣ CITIZEN INTERFACE (PUBLIC VIEW)

Clean civic UI.

Features:

* Public live map
* Filter by urgency
* Overflow countdown badge
* Complaint form modal
* Track complaint status

Must feel trustworthy and transparent.

---

# 1️⃣4️⃣ REAL-TIME DATA FLOW

WebSocket must handle:

* Truck location updates
* Bin status updates
* Route status changes
* Metric recalculation triggers

UI must update WITHOUT full reload.

Fallback:

* Polling every 10 seconds.

---

# 1️⃣5️⃣ UX REQUIREMENTS

Must include:

* Loading skeletons
* Error states
* Toast notifications
* Smooth hover transitions
* Animated route drawing
* No layout shifts
* Instant visual feedback

---

# 1️⃣6️⃣ PERFORMANCE REQUIREMENTS

* Lighthouse score > 90
* Initial load < 2s
* Lazy load routes
* Memoized heavy components
* Avoid unnecessary re-renders
* WebSocket reconnect logic

---

# 1️⃣7️⃣ SECURITY

* JWT validation
* Role-based route protection
* ProtectedRoute wrapper
* Secure API layer

---

# 1️⃣8️⃣ ACCESSIBILITY

* Proper ARIA labels
* Color contrast compliance
* Keyboard navigable UI
* Screen reader support

---

# 1️⃣9️⃣ ENTERPRISE POLISH FEATURES

Urban Cortex AI frontend must include:

* Dark Mode toggle
* Animated route drawing
* Subtle sound notification (optional)
* Hover tooltips everywhere
* Dynamic filters
* Export confirmation modal
* Auto-refresh indicator

---

# 2️⃣0️⃣ PRODUCTION DEPLOYMENT

Frontend:

* Built using Vite
* Deployed on Vercel
* Environment variables:

  * VITE_API_URL
  * VITE_WS_URL
  * VITE_FIREBASE_CONFIG

---

# 🎯 FINAL FRONTEND SUCCESS CRITERIA

Frontend is considered complete when:

* Real-time truck simulation renders smoothly
* Route generation visualizes instantly
* KPI metrics animate live
* Complaint lifecycle is visible
* Efficiency % updates dynamically
* UI looks enterprise-grade
* Works in dark mode
* Fully responsive
* No visual glitches

---

Urban Cortex AI frontend must feel like:

> A city-grade AI command center built by a top-tier startup.

---


# 📘 2️⃣2️⃣ ROLE-BASED AUTHENTICATION & AUTHORIZATION (RBAC CONTRACT)

Urban Cortex AI must implement strict Role-Based Access Control (RBAC).

This is mandatory for enterprise-level architecture.

---

# 22.1 Authentication Layer (Firebase + FastAPI)

### Step 1: Firebase Authentication

Users authenticate via:

* Email & Password

Firebase returns:

```
ID Token (JWT)
```

---

### Step 2: Backend Token Verification

Every protected request must include:

```
Authorization: Bearer <JWT_TOKEN>
```

Backend must:

1. Verify JWT signature
2. Extract user_id
3. Fetch user role from Firestore
4. Attach user + role to request context

If invalid → 401 Unauthorized

---

# 22.2 Defined Roles

Urban Cortex AI has 4 roles:

| Role    | Description                |
| ------- | -------------------------- |
| Admin   | Full system control        |
| Driver  | Operates assigned truck    |
| Citizen | Public reporting + viewing |
| System  | IoT simulator service      |

---

# 22.3 Permission Matrix (STRICT ACCESS CONTROL)

Below is the official permission contract.

---

## 🔐 AUTH APIs

| Endpoint         | Admin | Driver | Citizen | System |
| ---------------- | ----- | ------ | ------- | ------ |
| POST /auth/login | ✅     | ✅      | ✅       | ❌      |
| GET /auth/me     | ✅     | ✅      | ✅       | ❌      |

---

## 🗑 BINS

| Endpoint                   | Admin | Driver | Citizen                  | System |
| -------------------------- | ----- | ------ | ------------------------ | ------ |
| GET /bins                  | ✅     | ✅      | ✅ (filtered public view) | ❌      |
| GET /bins/{id}             | ✅     | ✅      | ❌                        | ❌      |
| POST /bins                 | ✅     | ❌      | ❌                        | ❌      |
| PUT /bins/{id}             | ✅     | ❌      | ❌                        | ❌      |
| DELETE /bins/{id}          | ✅     | ❌      | ❌                        | ❌      |
| POST /bins/update-from-iot | ❌     | ❌      | ❌                        | ✅      |
| GET /bins/{id}/prediction  | ✅     | ✅      | ❌                        | ❌      |

---

## 🚛 TRUCKS

| Endpoint                | Admin | Driver       | Citizen | System |
| ----------------------- | ----- | ------------ | ------- | ------ |
| GET /trucks             | ✅     | ❌            | ❌       | ❌      |
| GET /trucks/{id}        | ✅     | ✅ (own only) | ❌       | ❌      |
| POST /trucks            | ✅     | ❌            | ❌       | ❌      |
| PUT /trucks/{id}        | ✅     | ❌            | ❌       | ❌      |
| DELETE /trucks/{id}     | ✅     | ❌            | ❌       | ❌      |
| GET /trucks/{id}/route  | ✅     | ✅ (own only) | ❌       | ❌      |
| POST /trucks/{id}/start | ❌     | ✅ (own only) | ❌       | ❌      |

---

## 🗺 ROUTES

| Endpoint                 | Admin | Driver        | Citizen | System |
| ------------------------ | ----- | ------------- | ------- | ------ |
| POST /routes/generate    | ✅     | ❌             | ❌       | ❌      |
| GET /routes              | ✅     | ❌             | ❌       | ❌      |
| GET /routes/{id}         | ✅     | ✅ (own route) | ❌       | ❌      |
| DELETE /routes/{id}      | ✅     | ❌             | ❌       | ❌      |
| POST /routes/recalculate | ✅     | ❌             | ❌       | ❌      |

---

## 📢 COMPLAINTS

| Endpoint                    | Admin | Driver | Citizen      | System |
| --------------------------- | ----- | ------ | ------------ | ------ |
| POST /complaints            | ❌     | ❌      | ✅            | ❌      |
| GET /complaints             | ✅     | ❌      | ❌            | ❌      |
| GET /complaints/{id}        | ✅     | ❌      | ✅ (own only) | ❌      |
| PUT /complaints/{id}/status | ✅     | ❌      | ❌            | ❌      |
| DELETE /complaints/{id}     | ✅     | ❌      | ❌            | ❌      |

---

## 📊 METRICS

| Endpoint       | Admin | Driver | Citizen | System |
| -------------- | ----- | ------ | ------- | ------ |
| GET /metrics   | ✅     | ❌      | ❌       | ❌      |
| GET /metrics/* | ✅     | ❌      | ❌       | ❌      |

---

## 📦 EXPORT

| Endpoint      | Admin | Driver | Citizen | System |
| ------------- | ----- | ------ | ------- | ------ |
| GET /export/* | ✅     | ❌      | ❌       | ❌      |

---

## 🏙 CITIES

| Endpoint            | Admin | Driver | Citizen | System |
| ------------------- | ----- | ------ | ------- | ------ |
| GET /cities         | ✅     | ✅      | ✅       | ❌      |
| POST /cities        | ✅     | ❌      | ❌       | ❌      |
| DELETE /cities/{id} | ✅     | ❌      | ❌       | ❌      |

---

# 22.4 Backend Enforcement Strategy (MANDATORY)

FastAPI must implement:

### Role Dependency Guard

Example:

```python
def require_role(allowed_roles: list):
    def role_checker(user=Depends(get_current_user)):
        if user.role not in allowed_roles:
            raise HTTPException(status_code=403)
        return user
    return role_checker
```

Usage:

```python
@router.post("/routes/generate")
async def generate_routes(
    user=Depends(require_role(["admin"]))
):
```

This ensures strict enforcement.

---

# 22.5 Ownership Enforcement

Some endpoints require ownership validation:

Example:

* Driver can only access own truck
* Citizen can only view own complaints

Backend must:

1. Compare user_id from JWT
2. Compare resource.owner_id
3. Deny if mismatch

---

# 22.6 Frontend Role Guards

React must implement:

### ProtectedRoute Component

Rules:

* If not logged in → redirect to login
* If role mismatch → show 403 page
* Sidebar must dynamically render menu based on role

Example:

Admin sees:

* Analytics
* Fleet
* Complaints
* Investigation

Driver sees:

* Active Route
* My Truck

Citizen sees:

* Public Map
* My Complaints

---

# 22.7 IoT System Role

The IoT simulator must:

* Use API key or system token
* Only allowed to call:

  * POST /bins/update-from-iot

This prevents public abuse.

---

# 22.8 Security Requirements

* All APIs except login require JWT
* HTTPS mandatory
* No sensitive data in responses
* Role checks BEFORE business logic
* Rate limiting for public endpoints

---



# 📘 URBAN CORTEX AI

# 🔐 OFFICIAL API CONTRACT – VERSION 1.0

(Base for FastAPI Implementation)

---

# 🏗 ARCHITECTURE PRINCIPLES (MANDATORY)

Before listing APIs, these rules must be enforced:

1. All endpoints are under:

```
/api/v1/
```

2. Modular router structure:

```python
api/
 ├── auth_router.py
 ├── users_router.py
 ├── bins_router.py
 ├── trucks_router.py
 ├── routes_router.py
 ├── complaints_router.py
 ├── investigations_router.py
 ├── metrics_router.py
 ├── export_router.py
 ├── system_router.py
```

3. All responses MUST follow unified response format:

```json
{
  "success": true,
  "message": "Optional",
  "data": {},
  "errors": null
}
```

4. No endpoint outside this document may be created.

---

# 🔐 MODULE 1: AUTH MODULE

## Base Path:

```
/api/v1/auth
```

---

### 1.1 POST `/login`

Purpose: Authenticate using Firebase token

Request:

```json
{
  "firebase_token": "string"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "user_id": "UID",
    "role": "admin | driver | citizen",
    "assigned_truck_id": "nullable"
  }
}
```

---

### 1.2 GET `/me`

Returns authenticated user profile

Headers:

```
Authorization: Bearer <JWT>
```

---

---

# 👤 MODULE 2: USERS MODULE

## Base Path:

```
/api/v1/users
```

---

### 2.1 POST `/register`

Role: Public
Creates citizen only

---

### 2.2 POST `/create-driver`

Role: Admin

---

### 2.3 POST `/create-admin`

Role: Admin

---

### 2.4 GET `/`

Role: Admin
Returns all users

---

### 2.5 PUT `/{user_id}/role`

Role: Admin

---

### 2.6 DELETE `/{user_id}`

Role: Admin

---

# 🗑 MODULE 3: BINS MODULE

## Base Path:

```
/api/v1/bins
```

---

### 3.1 GET `/`

Query params:

* city
* status
* min_fill
* max_fill

Role: All (filtered by role)

---

### 3.2 GET `/{bin_id}`

Role: Admin, Driver

---

### 3.3 POST `/`

Role: Admin
Create new bin manually

---

### 3.4 PUT `/{bin_id}`

Role: Admin

---

### 3.5 DELETE `/{bin_id}`

Role: Admin

---

### 3.6 POST `/update-from-iot`

Role: System (API key protected)

This is the ONLY IoT ingestion endpoint.

---

### 3.7 GET `/{bin_id}/prediction`

Role: Admin, Driver

---

### 3.8 GET `/urgent/list`

Role: Admin

Returns urgent bins only

---

# 🚛 MODULE 4: TRUCKS MODULE

## Base Path:

```
/api/v1/trucks
```

---

### 4.1 GET `/`

Role: Admin

---

### 4.2 GET `/{truck_id}`

Role: Admin, Driver (own only)

---

### 4.3 POST `/`

Role: Admin

---

### 4.4 PUT `/{truck_id}`

Role: Admin

---

### 4.5 DELETE `/{truck_id}`

Role: Admin

---

### 4.6 GET `/{truck_id}/route`

Role: Admin, Driver (own only)

---

### 4.7 POST `/{truck_id}/start`

Role: Driver (own truck only)

Triggers async route simulation

---

### 4.8 POST `/{truck_id}/pause`

Role: Driver

---

### 4.9 POST `/{truck_id}/complete`

Role: Driver

---

# 🗺 MODULE 5: ROUTES MODULE

## Base Path:

```
/api/v1/routes
```

---

### 5.1 POST `/generate`

Role: Admin

Runs:

* Urgency filtering
* Clustering
* Assignment
* Optimization

---

### 5.2 GET `/`

Role: Admin

---

### 5.3 GET `/{route_id}`

Role: Admin, Driver (own only)

---

### 5.4 DELETE `/{route_id}`

Role: Admin

---

### 5.5 POST `/recalculate`

Role: Admin

Triggers dynamic rerouting

---
# 📢 MODULE 6: COMPLAINTS MODULE

## Base Path:

```plaintext
/api/v1/complaints
```

---

### 6.1 POST `/`

Role: Citizen

Purpose: Create complaint

Request:

```json
{
  "type": "overflow | not_collected | new_bin_request",
  "city": "Hyderabad",
  "latitude": 17.385,
  "longitude": 78.486,
  "description": "Bin overflowing since morning"
}
```

Behavior:

* Create complaint
* Set status = "pending"
* Store created_by from JWT

---

### 6.2 GET `/`

Role: Admin

Query params:

* status
* city
* type

---

### 6.3 GET `/{complaint_id}`

Role:

* Admin (any)
* Citizen (own only)

Ownership rule:

```
complaint.created_by == user.user_id
```

---

### 6.4 PUT `/{complaint_id}/status`

Role: Admin

Request:

```json
{
  "status": "investigating | resolved"
}
```

---

### 6.5 DELETE `/{complaint_id}`

Role: Admin

---

# 🕵️ MODULE 7: INVESTIGATIONS MODULE

## Base Path:

```plaintext
/api/v1/investigations
```

---

### 7.1 POST `/`

Role: Admin

Purpose: Create investigation for complaint

Request:

```json
{
  "complaint_id": "CMP_101",
  "assigned_admin": "UID_001"
}
```

---

### 7.2 GET `/`

Role: Admin

Query:

* status

---

### 7.3 GET `/{investigation_id}`

Role: Admin

---

### 7.4 PUT `/{investigation_id}/status`

Role: Admin

Request:

```json
{
  "status": "closed",
  "result": "valid | invalid | new_bin_required",
  "notes": "Inspection completed"
}
```

If result == new_bin_required:
→ Admin must create bin manually (via bins module)

---

# 📊 MODULE 8: METRICS MODULE

## Base Path:

```plaintext
/api/v1/metrics
```

---

### 8.1 GET `/dashboard`

Role: Admin

Returns aggregated KPIs:

* total_bins
* urgent_bins
* total_trucks
* active_trucks
* efficiency_percentage
* trips_avoided
* avg_fill_percentage

---

### 8.2 GET `/fleet`

Role: Admin

Returns:

* utilization %
* route completion rate
* avg route distance

---

### 8.3 GET `/bins`

Role: Admin

Returns:

* fill distribution
* overflow prediction accuracy

---

### 8.4 GET `/complaints`

Role: Admin

Returns:

* total complaints
* resolution rate
* avg resolution time

---

# 📦 MODULE 9: EXPORT MODULE

## Base Path:

```plaintext
/api/v1/export
```

---

### 9.1 GET `/bins`

Role: Admin
Returns CSV file

---

### 9.2 GET `/routes`

Role: Admin

---

### 9.3 GET `/complaints`

Role: Admin

---

### 9.4 GET `/metrics`

Role: Admin

---

All exports:

* Generated dynamically
* Expire after short duration

---

# ⚙ MODULE 10: SYSTEM MODULE

## Base Path:

```plaintext
/api/v1/system
```

---

### 10.1 GET `/health`

Role: Public

Returns:

* API status
* DB status
* IoT connectivity status

---

### 10.2 GET `/status`

Role: Admin

Returns:

* Active routes count
* WebSocket clients count
* Last IoT sync time

---

### 10.3 POST `/force-sync-iot`

Role: Admin

Manually triggers IoT pull.

---

### 10.4 POST `/recalculate-urgency`

Role: Admin

Recomputes urgency scores for all bins.

---

# 🌐 MODULE 11: WEBSOCKET CONTRACT

## Endpoint:

```plaintext
wss://api.urbancortex.ai/api/v1/ws/live
```

Authentication:

* JWT required during connection

---

## Event Types (Server → Client)

---

### truck_location_update

```json
{
  "event": "truck_location_update",
  "data": {
    "truck_id": "TRUCK_01",
    "latitude": 17.39,
    "longitude": 78.48
  }
}
```

---

### bin_collected

```json
{
  "event": "bin_collected",
  "data": {
    "bin_id": "BIN_001",
    "collected_at": "timestamp"
  }
}
```

---

### route_progress

```json
{
  "event": "route_progress",
  "data": {
    "route_id": "ROUTE_001",
    "progress_percent": 65
  }
}
```

---

### route_completed

```json
{
  "event": "route_completed",
  "data": {
    "route_id": "ROUTE_001"
  }
}
```

---

### complaint_created

```json
{
  "event": "complaint_created",
  "data": {
    "complaint_id": "CMP_101"
  }
}
```

---

### metrics_updated

```json
{
  "event": "metrics_updated"
}
```

---

# 🛡 RATE LIMITING RULES

* Public endpoints → 60 requests/minute
* Citizen endpoints → 100 requests/minute
* Admin endpoints → 200 requests/minute
* IoT ingestion → configurable

---

# 🔄 VERSIONING STRATEGY

* All APIs are under `/api/v1/`
* Breaking changes → `/api/v2/`
* Deprecated endpoints must:

  * Remain for 90 days
  * Return warning header

---

# 🧱 MODULAR EXPANSION DESIGN

Each module is independent.

Future additions must:

1. Create new router file
2. Use new prefix `/api/v1/<module>`
3. Not modify existing contracts
4. Maintain response envelope

Example future modules:

* `/carbon-tracking`
* `/ai-forecasting`
* `/predictive-maintenance`

---

# 🧠 FINAL API SURFACE SUMMARY

| Module         | Count |
| -------------- | ----- |
| Auth           | 2     |
| Users          | 6     |
| Bins           | 8     |
| Trucks         | 9     |
| Routes         | 5     |
| Complaints     | 5     |
| Investigations | 4     |
| Metrics        | 4     |
| Export         | 4     |
| System         | 4     |
| WebSocket      | 1     |

Total REST APIs: **51**

* 1 WebSocket endpoint

This is your FINAL locked contract.

---

Now we are locking the **final production-grade project structure** for:

# 🚀 Urban Cortex AI

Root folder name:

```bash
urban-cortex-AI/
```

Inside it:

* `frontend/` (Vite + React + TailwindCSS Enterprise UI)
* `backend/` (FastAPI + Modular + WebSocket + Firebase)
* Clean separation
* Scalable
* AI-friendly
* Startup-grade architecture

This is the **final recommended structure**.

---

# 🏗 ROOT DIRECTORY STRUCTURE

```bash
urban-cortex-AI/
│
├── frontend/
├── backend/
├── docker-compose.yml
├── .env.example
├── README.md
├── docs/
│   ├── API_CONTRACT.md
│   ├── ARCHITECTURE.md
│   └── DEPLOYMENT.md
```

---

# 🧠 BACKEND STRUCTURE (FastAPI – Enterprise Modular)

```bash
backend/
│
├── app/
│   ├── main.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── firebase.py
│   │   ├── dependencies.py
│   │   ├── rate_limiter.py
│   │
│   ├── models/
│   │   ├── user_model.py
│   │   ├── bin_model.py
│   │   ├── truck_model.py
│   │   ├── route_model.py
│   │   ├── complaint_model.py
│   │   ├── investigation_model.py
│   │
│   ├── schemas/
│   │   ├── auth_schema.py
│   │   ├── user_schema.py
│   │   ├── bin_schema.py
│   │   ├── truck_schema.py
│   │   ├── route_schema.py
│   │   ├── complaint_schema.py
│   │   ├── investigation_schema.py
│   │   ├── metrics_schema.py
│   │   ├── common_schema.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── bin_service.py
│   │   ├── prediction_service.py
│   │   ├── assignment_service.py
│   │   ├── routing_service.py
│   │   ├── truck_simulation_service.py
│   │   ├── complaint_service.py
│   │   ├── investigation_service.py
│   │   ├── metrics_service.py
│   │   ├── export_service.py
│   │   ├── iot_service.py
│   │
│   ├── api/
│   │   ├── api_router.py
│   │   │
│   │   ├── v1/
│   │   │   ├── auth_router.py
│   │   │   ├── users_router.py
│   │   │   ├── bins_router.py
│   │   │   ├── trucks_router.py
│   │   │   ├── routes_router.py
│   │   │   ├── complaints_router.py
│   │   │   ├── investigations_router.py
│   │   │   ├── metrics_router.py
│   │   │   ├── export_router.py
│   │   │   ├── system_router.py
│   │
│   ├── websocket/
│   │   ├── connection_manager.py
│   │   ├── ws_router.py
│   │
│   ├── utils/
│   │   ├── haversine.py
│   │   ├── clustering.py
│   │   ├── csv_generator.py
│   │   ├── response_formatter.py
│   │
│   ├── middleware/
│   │   ├── auth_middleware.py
│   │   ├── logging_middleware.py
│   │
│   └── tasks/
│       ├── background_tasks.py
│
├── tests/
│   ├── test_auth.py
│   ├── test_bins.py
│   ├── test_routes.py
│
├── requirements.txt
├── Dockerfile
├── .env
```

---

# 🧩 BACKEND DESIGN EXPLANATION

### app/core

* Config
* JWT verification
* Firebase initialization
* Global dependencies

### models

Database entity definitions (Firestore mapping logic)

### schemas

Pydantic request/response validation

### services

Business logic layer (NO logic inside routers)

### api/v1

All endpoints grouped modularly

### websocket

Real-time truck updates

### utils

Reusable helper functions

### middleware

Authentication & logging

### tasks

Async background route simulation

This structure allows:

* Easy module addition
* API versioning
* Clean separation of concerns
* Future microservice split

---

# 🎨 FRONTEND STRUCTURE (Vite + React + Tailwind Enterprise)

```bash
frontend/
│
├── public/
│
├── src/
│   │
│   ├── main.jsx
│   ├── App.jsx
│   │
│   ├── app/
│   │   ├── routes.jsx
│   │   ├── providers.jsx
│   │
│   ├── layouts/
│   │   ├── DashboardLayout.jsx
│   │   ├── AuthLayout.jsx
│   │
│   ├── pages/
│   │   ├── auth/
│   │   │   ├── Login.jsx
│   │   │
│   │   ├── admin/
│   │   │   ├── Overview.jsx
│   │   │   ├── Fleet.jsx
│   │   │   ├── Routes.jsx
│   │   │   ├── Complaints.jsx
│   │   │   ├── Investigations.jsx
│   │   │   ├── Analytics.jsx
│   │   │
│   │   ├── driver/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── ActiveRoute.jsx
│   │   │
│   │   ├── citizen/
│   │   │   ├── PublicMap.jsx
│   │   │   ├── MyComplaints.jsx
│   │
│   ├── components/
│   │   ├── ui/
│   │   │   ├── Button.jsx
│   │   │   ├── Card.jsx
│   │   │   ├── Badge.jsx
│   │   │   ├── Modal.jsx
│   │   │   ├── Table.jsx
│   │   │   ├── Loader.jsx
│   │   │   ├── Skeleton.jsx
│   │   │
│   │   ├── dashboard/
│   │   │   ├── KPIGrid.jsx
│   │   │   ├── MetricCard.jsx
│   │   │
│   │   ├── map/
│   │   │   ├── SmartMap.jsx
│   │   │   ├── BinLayer.jsx
│   │   │   ├── TruckLayer.jsx
│   │   │   ├── RouteLayer.jsx
│   │   │
│   │   ├── complaints/
│   │   │   ├── ComplaintForm.jsx
│   │   │   ├── ComplaintTable.jsx
│   │   │
│   │   ├── trucks/
│   │   │   ├── RouteCard.jsx
│   │   │   ├── CapacityRing.jsx
│   │
│   ├── store/
│   │   ├── authStore.js
│   │   ├── binStore.js
│   │   ├── truckStore.js
│   │   ├── routeStore.js
│   │   ├── complaintStore.js
│   │
│   ├── services/
│   │   ├── api.js
│   │   ├── socket.js
│   │   ├── authService.js
│   │
│   ├── hooks/
│   │   ├── useAuth.js
│   │   ├── useSocket.js
│   │
│   ├── utils/
│   │   ├── constants.js
│   │   ├── helpers.js
│   │
│   ├── styles/
│   │   ├── globals.css
│
├── tailwind.config.js
├── postcss.config.js
├── vite.config.js
├── package.json
├── .env
```

---

# 🧠 FRONTEND DESIGN LOGIC

### layouts

Role-based dashboards

### pages

Strict role separation

### components/ui

Reusable design system

### store

Global state (Zustand)

### services

All API calls centralized

### hooks

Reusable logic

This structure ensures:

* Enterprise-level maintainability
* Easy refactor
* Component reusability
* Scalable UI growth
* Clean separation

---

