# Urban Cortex AI – API Contract

This document provides a detailed specification of all existing APIs in the **Urban Cortex AI** backend, outlining the exact JSON request bodies and response structures.

**Base URL:** `/api/v1`

---

## ── General Response Formats ──

### Success Response Wrapping
All successful requests will wrap their data in this format:
```json
{
  "status": "success",
  "message": "Human readable message",
  "data": { } // Requested payload
}
```

### Error Response Wrapping
```json
{
  "status": "error",
  "message": "Error description",
  "errors": ["Detail 1", "Detail 2"]
}
```

Below, whenever a `Response` is shown, it represents the contents of the `"data"` field in a successful response.

---

## ── 1. Authentication ──
**Prefix:** `/auth` | **Tags:** `Authentication`

### GET `/auth/me`
*   **Summary:** Get current user profile.
*   **Method:** `GET`
*   **Requirement:** `Authorization: Bearer <token>`
*   **Response (UserProfile):**
    ```json
    {
      "user_id": "string",
      "name": "string",
      "email": "user@example.com",
      "role": "citizen | admin | driver",
      "assigned_truck_id": "string (optional)",
      "city": "string",
      "is_active": true,
      "created_at": "ISO-8601 string",
      "last_login": "ISO-8601 string (optional)"
    }
    ```

### POST `/auth/signup`
*   **Summary:** Register new citizen user.
*   **Method:** `POST`
*   **Request Body:**
    ```json
    {
      "name": "John Doe",
      "email": "user@example.com",
      "password": "strongpassword123",
      "city": "Metropolis"
    }
    ```
*   **Response (UserProfile):** Same as `GET /auth/me`.

### POST `/auth/login`
*   **Summary:** Login and get JWT token.
*   **Method:** `POST`
*   **Request Body:**
    ```json
    {
      "email": "user@example.com",
      "password": "strongpassword123"
    }
    ```
*   **Response:**
    ```json
    {
      "access_token": "jwt_token_string_here",
      "token_type": "bearer"
    }
    ```

---

## ── 2. Bins ──
**Prefix:** `/bins` | **Tags:** `Bins`

### GET `/bins`
*   **Summary:** Get all bins.
*   **Method:** `GET`
*   **Query Params:**
    *   `city`: string (optional)
    *   `status`: string (optional)
    *   `limit`: integer (default: 100, max: 500)
*   **Response:** List of `BinResponse` objects:
    ```json
    [
      {
        "bin_id": "BIN-001",
        "city": "Metropolis",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "fill_level": 75.5,
        "fill_rate": 2.1,
        "status": "normal | urgent | overflow",
        "urgency_score": 8.5,
        "predicted_overflow_time": "ISO-8601 string",
        "time_to_overflow_minutes": 120.5,
        "created_at": "ISO-8601 string",
        "last_updated": "ISO-8601 string"
      }
    ]
    ```

### POST `/bins`
*   **Summary:** Create new bin.
*   **Method:** `POST`
*   **Request Body:**
    ```json
    {
      "bin_id": "BIN-001",
      "city": "Metropolis",
      "latitude": 40.7128,
      "longitude": -74.0060,
      "fill_level": 10.0
    }
    ```
*   **Response (BinResponse):** Same structure as a single object from `GET /bins`.

### GET `/bins/{bin_id}`
*   **Summary:** Get bin by ID.
*   **Method:** `GET`
*   **Response (BinResponse):** Same structure as a single object from `GET /bins`.

### PUT `/bins/{bin_id}`
*   **Summary:** Update bin.
*   **Method:** `PUT`
*   **Request Body:** (All fields optional)
    ```json
    {
      "city": "Metropolis",
      "latitude": 40.7128,
      "longitude": -74.0060,
      "fill_level": 85.0,
      "fill_rate": 3.0
    }
    ```
*   **Response (BinResponse):** Same structure as a single object from `GET /bins`.

### DELETE `/bins/{bin_id}`
*   **Summary:** Delete bin.
*   **Method:** `DELETE`
*   **Response:**
    ```json
    {
      "bin_id": "BIN-001"
    }
    ```

### POST `/bins/update-from-iot`
*   **Summary:** Ingest data from IoT Simulator.
*   **Method:** `POST`
*   **Request Body:**
    ```json
    {
      "bin_id": "BIN-001",
      "city": "Metropolis",
      "latitude": 40.7128,
      "longitude": -74.0060,
      "fill_level": 88.0,
      "fill_rate": 2.5,
      "last_updated": "ISO-8601 string (optional)"
    }
    ```
*   **Response (BinResponse):** Same structure as a single object from `GET /bins`.

---

## ── 3. Complaints ──
**Prefix:** `/complaints` | **Tags:** `Complaints`

### GET `/complaints`
*   **Summary:** List complaints (Admin).
*   **Method:** `GET`
*   **Query Params:**
    *   `status`: "pending" | "investigating" | "resolved" (optional)
    *   `city`: string (optional)
    *   `type`: "overflow" | "not_collected" | "new_bin_request" (optional)
*   **Response:** List of Complaint objects:
    ```json
    [
      {
        "complaint_id": "CMP-12345",
        "type": "overflow",
        "city": "Metropolis",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "description": "Bin is overflowing and smelly.",
        "created_by": "USER-987",
        "status": "pending",
        "created_at": "ISO-8601 string",
        "resolved_at": "ISO-8601 string (optional)"
      }
    ]
    ```

### POST `/complaints`
*   **Summary:** Create a complaint (Citizen).
*   **Method:** `POST`
*   **Request Body:**
    ```json
    {
      "type": "overflow",
      "city": "Metropolis",
      "latitude": 40.7128,
      "longitude": -74.0060,
      "description": "Bin is overflowing completely."
    }
    ```
*   **Response:** Created Complaint object (same structure as above list items).

### GET `/complaints/{complaint_id}`
*   **Summary:** Get complaint by ID.
*   **Method:** `GET`
*   **Response:** Complaint object.

### PUT `/complaints/{complaint_id}/status`
*   **Summary:** Update complaint status (Admin).
*   **Method:** `PUT`
*   **Request Body:**
    ```json
    {
      "status": "investigating"
    }
    ```
*   **Response:** Updated Complaint object.

### DELETE `/complaints/{complaint_id}`
*   **Summary:** Delete complaint (Admin).
*   **Method:** `DELETE`
*   **Response:**
    ```json
    {
      "complaint_id": "CMP-12345"
    }
    ```

---

## ── 4. Investigations ──
**Prefix:** `/investigations` | **Tags:** `Investigations`

### GET `/investigations`
*   **Summary:** List investigations.
*   **Method:** `GET`
*   **Query Params:**
    *   `status`: "open" | "closed" (optional)
*   **Response:** List of Investigation objects:
    ```json
    [
      {
        "investigation_id": "INV-777",
        "complaint_id": "CMP-12345",
        "assigned_admin": "ADMIN-001",
        "status": "open",
        "result": "valid | invalid | new_bin_required | pending",
        "notes": "Admin notes here (optional)",
        "created_at": "ISO-8601 string",
        "closed_at": "ISO-8601 string (optional)"
      }
    ]
    ```

### POST `/investigations`
*   **Summary:** Create an investigation.
*   **Method:** `POST`
*   **Request Body:**
    ```json
    {
      "complaint_id": "CMP-12345",
      "assigned_admin": "ADMIN-001"
    }
    ```
*   **Response:** Created Investigation object.

### GET `/investigations/{investigation_id}`
*   **Summary:** Get investigation by ID.
*   **Method:** `GET`
*   **Response:** Investigation object.

### PUT `/investigations/{investigation_id}/status`
*   **Summary:** Update investigation status/result.
*   **Method:** `PUT`
*   **Request Body:**
    ```json
    {
      "status": "closed",
      "result": "valid",
      "notes": "Verified overflow. Truck dispatched."
    }
    ```
*   **Response:** Updated Investigation object.

---

## ── 5. Routes ──
**Prefix:** `/routes` | **Tags:** `Routes`

### GET `/routes`
*   **Summary:** Get all routes.
*   **Method:** `GET`
*   **Query Params:**
    *   `city`: string (optional)
    *   `limit`: integer (default 100)
*   **Response:** List of `RouteResponse` objects:
    ```json
    [
      {
        "route_id": "RT-999",
        "city": "Metropolis",
        "truck_id": "TRK-001 (optional)",
        "ordered_bin_ids": ["BIN-1", "BIN-2"],
        "total_distance": 15.2,
        "estimated_time_minutes": 45.0,
        "status": "generated | in_progress | completed",
        "started_at": "ISO-8601 string (optional)",
        "completed_at": "ISO-8601 string (optional)",
        "created_at": "ISO-8601 string"
      }
    ]
    ```

### POST `/routes/generate`
*   **Summary:** Generate routes for urgent bins.
*   **Method:** `POST`
*   **Request Body:** None
*   **Response:** List of generated `RouteResponse` objects (same structure as above list items).

### GET `/routes/{route_id}`
*   **Summary:** Get route by ID.
*   **Method:** `GET`
*   **Response:** `RouteResponse` object.

### POST `/routes/assign-urgent-bin/{bin_id}`
*   **Summary:** Handle new urgent bin dynamically.
*   **Method:** `POST`
*   **Request Body:** None
*   **Response:**
    ```json
    {
      "message": "Assigned to existing route RT-999",
      "route_id": "RT-999",
      "truck_id": "TRK-001"
    }
    ```

### DELETE `/routes/{route_id}`
*   **Summary:** Delete route.
*   **Method:** `DELETE`
*   **Response:** 
    ```json
    {
      "route_id": "RT-999"
    }
    ```

---

## ── 6. Trucks ──
**Prefix:** `/trucks` | **Tags:** `trucks`

### GET `/trucks`
*   **Summary:** Get all trucks.
*   **Method:** `GET`
*   **Query Params:**
    *   `city`: string
    *   `limit`: integer
*   **Response:** List of `TruckResponse` objects:
    ```json
    [
      {
        "truck_id": "TRK-001",
        "city": "Metropolis",
        "max_capacity": 1000.0,
        "current_load": 250.0,
        "status": "idle | assigned | in_transit",
        "assigned_route_id": "RT-999 (optional)",
        "driver_id": "DRV-123 (optional)",
        "current_latitude": 40.7128,
        "current_longitude": -74.0060,
        "created_at": "ISO-8601 string"
      }
    ]
    ```

### POST `/trucks`
*   **Summary:** Create new truck with driver.
*   **Method:** `POST`
*   **Request Body:**
    ```json
    {
      "truck_id": "TRK-001",
      "city": "Metropolis",
      "max_capacity": 1000.0,
      "name": "Driver Name",
      "email": "driver@example.com",
      "password": "securepassword"
    }
    ```
*   **Response:**
    ```json
    {
      "truck_id": "TRK-001",
      "driver_id": "string"
    }
    ```

### GET `/trucks/{truck_id}`
*   **Summary:** Get truck by ID.
*   **Method:** `GET`
*   **Response:** `TruckResponse` object.

### PUT `/trucks/{truck_id}`
*   **Summary:** Update truck.
*   **Method:** `PUT`
*   **Request Body:**
    ```json
    {
      "max_capacity": 1500.0,
      "assigned_route_id": "RT-888",
      "driver_id": "DRV-456"
    }
    ```
*   **Response:** `TruckResponse` object.

### DELETE `/trucks/{truck_id}`
*   **Summary:** Delete truck.
*   **Method:** `DELETE`
*   **Response:**
    ```json
    {
      "truck_id": "TRK-001"
    }
    ```

### POST `/trucks/{truck_id}/assign-route/{route_id}`
*   **Summary:** Assign route to truck.
*   **Method:** `POST`
*   **Request Body:** None
*   **Response:** `TruckResponse` object.

### POST `/trucks/{truck_id}/start`
*   **Summary:** Start trip simulation.
*   **Method:** `POST`
*   **Request Body:** None
*   **Response:**
    ```json
    {
      "truck_id": "TRK-001",
      "route_id": "RT-999",
      "status": "in_progress",
      "message": "Trip started successfully"
    }
    ```

---

## ── 7. System ──
**Prefix:** `/system` | **Tags:** `System`

### GET `/system/health`
*   **Summary:** System health check.
*   **Method:** `GET`
*   **Response:**
    ```json
    {
      "status": "healthy | degraded",
      "timestamp": "ISO-8601 string",
      "version": "1.0.0",
      "environment": "development | production",
      "components": {
        "api": { "status": "healthy" },
        "firestore": { "status": "healthy" },
        "iot_simulator": {
          "configured_url": "url",
          "sync_interval_seconds": 60,
          "status": "configured"
        }
      }
    }
    ```

### GET `/system/firestore-health`
*   **Summary:** Firestore connectivity check.
*   **Method:** `GET`
*   **Response:**
    ```json
    {
      "status": "healthy"
    }
    ```

### POST `/system/sync-iot`
*   **Summary:** Sync bins from IoT simulator.
*   **Method:** `POST`
*   **Request Body:** None
*   **Response:**
    ```json
    {
      "bins_synced": 42,
      "message": "IoT sync completed manually"
    }
    ```

---

## ── 8. WebSocket ──
**Path:** `/ws/live`

### WebSocket Connection
*   **Summary:** Real-time event broadcasting.
*   **Endpoint:** `ws://<domain>/api/v1/ws/live`
*   **Broadcast Events (JSON payload structures varying by event):**
    *   `truck_location_update`: Real-time truck movement.
    *   `bin_collected`: Triggered when a truck collects a bin.
    *   `route_progress`: Percentage of route completion.
    *   `route_completed`: Fired when a trip ends.
    *   `complaint_created`: Fired when a citizen submits a complaint.
    *   `metrics_updated`: Triggered by significant system changes.

---

## ── 9. Metrics ──
**Prefix:** `/metrics` | **Tags:** `Metrics`
*All endpoints require Admin role.*

### GET `/metrics/dashboard`
*   **Summary:** Dashboard KPIs.
*   **Method:** `GET`
*   **Response:**
    ```json
    {
      "total_bins": 100,
      "urgent_bins": 15,
      "total_trucks": 10,
      "active_trucks": 3,
      "avg_fill_percentage": 42.5,
      "efficiency_percentage": 85.0,
      "trips_avoided": 12
    }
    ```

### GET `/metrics/fleet`
*   **Summary:** Fleet metrics.
*   **Method:** `GET`
*   **Response:**
    ```json
    {
      "total_routes": 50,
      "completed_routes": 45,
      "route_completion_rate": 90.0,
      "avg_route_distance": 22.5,
      "avg_estimated_time": 3600.0,
      "avg_truck_utilization": 75.2
    }
    ```

### GET `/metrics/bins`
*   **Summary:** Bin metrics.
*   **Method:** `GET`
*   **Response:**
    ```json
    {
      "total_bins": 100,
      "normal_bins": 75,
      "urgent_bins": 20,
      "overflow_bins": 5,
      "avg_fill_level": 48.2,
      "bins_predicted_to_overflow_next_2_hours": 8
    }
    ```

### GET `/metrics/complaints`
*   **Summary:** Complaint metrics.
*   **Method:** `GET`
*   **Response:**
    ```json
    {
      "total_complaints": 30,
      "pending_complaints": 5,
      "investigating_complaints": 10,
      "resolved_complaints": 15,
      "resolution_rate": 50.0,
      "avg_resolution_time": 24.5
    }
    ```
