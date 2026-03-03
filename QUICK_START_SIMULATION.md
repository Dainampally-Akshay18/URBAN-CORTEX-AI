# 🚀 Quick Start - Truck Simulation Testing

## Prerequisites

1. Backend server running:
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. Swagger UI open: http://localhost:8000/docs

---

## 🎯 5-Minute Test Scenario

### Step 1: Sync IoT Data (30 seconds)

**Endpoint:** `POST /api/v1/system/sync-iot`

Click "Execute" - this fetches real bins from the IoT simulator.

**Expected:** Multiple bins created with various fill levels.

---

### Step 2: Generate Route (15 seconds)

**Endpoint:** `POST /api/v1/routes/generate`

Click "Execute" - this creates optimized routes for urgent bins.

**Expected Response:**
```json
{
  "success": true,
  "data": [
    {
      "route_id": "abc-123-def",
      "city": "Hyderabad",
      "ordered_bin_ids": ["BIN_001", "BIN_002", "BIN_003"],
      "status": "generated"
    }
  ]
}
```

**📋 Copy the `route_id` value!**

---

### Step 3: Create Truck (15 seconds)

**Endpoint:** `POST /api/v1/trucks`

**Request Body:**
```json
{
  "truck_id": "TRUCK_DEMO_01",
  "city": "Hyderabad",
  "max_capacity": 300
}
```

Click "Execute"

**Expected:** Truck created with status "idle"

---

### Step 4: Assign Route (15 seconds)

**Endpoint:** `POST /api/v1/trucks/{truck_id}/assign-route/{route_id}`

**Parameters:**
- truck_id: `TRUCK_DEMO_01`
- route_id: `<paste route_id from Step 2>`

Click "Execute"

**Expected:** Truck status changes to "assigned"

---

### Step 5: Connect WebSocket (30 seconds)

Open browser console (F12) and paste:

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/live');

ws.onopen = () => console.log('✅ Connected');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`📨 ${data.event}:`, data.data);
};
```

Press Enter. You should see: `✅ Connected`

---

### Step 6: Start Trip! (15 seconds)

**Endpoint:** `POST /api/v1/trucks/{truck_id}/start`

**Parameters:**
- truck_id: `TRUCK_DEMO_01`

Click "Execute"

**Expected Response:**
```json
{
  "success": true,
  "message": "Trip started successfully",
  "data": {
    "truck_id": "TRUCK_DEMO_01",
    "status": "in_transit"
  }
}
```

---

### Step 7: Watch the Magic! ✨

**In Browser Console:**

You'll see events streaming in real-time:

```
📨 truck_location_update: {truck_id: "TRUCK_DEMO_01", latitude: 17.385, longitude: 78.486}
📨 bin_collected: {bin_id: "BIN_001", collected_at: "2024-03-03T..."}
📨 route_progress: {route_id: "abc-123-def", progress_percent: 33.3}
📨 truck_location_update: {truck_id: "TRUCK_DEMO_01", latitude: 17.390, longitude: 78.490}
📨 bin_collected: {bin_id: "BIN_002", collected_at: "2024-03-03T..."}
📨 route_progress: {route_id: "abc-123-def", progress_percent: 66.7}
📨 truck_location_update: {truck_id: "TRUCK_DEMO_01", latitude: 17.395, longitude: 78.495}
📨 bin_collected: {bin_id: "BIN_003", collected_at: "2024-03-03T..."}
📨 route_progress: {route_id: "abc-123-def", progress_percent: 100.0}
📨 route_completed: {route_id: "abc-123-def", completed_at: "2024-03-03T..."}
```

**In Swagger UI:**

Refresh these endpoints to see updates:

1. **GET /api/v1/trucks/TRUCK_DEMO_01**
   - Watch `current_latitude` and `current_longitude` change
   - Watch `status` change: "in_transit" → "idle"

2. **GET /api/v1/bins/{bin_id}** (use any bin from route)
   - Watch `fill_level` become 0
   - Watch `status` become "normal"

3. **GET /api/v1/routes/{route_id}**
   - Watch `status` change: "in_progress" → "completed"
   - See `started_at` and `completed_at` timestamps

---

## 🎬 What Just Happened?

1. ✅ Truck moved to each bin location
2. ✅ Truck coordinates updated in Firestore
3. ✅ Each bin was collected (fill_level reset to 0)
4. ✅ Bin status reset to "normal"
5. ✅ Route progress tracked (33% → 67% → 100%)
6. ✅ Route marked as completed
7. ✅ Truck returned to idle status
8. ✅ All events broadcasted via WebSocket
9. ✅ All data persisted in Firestore

---

## 🔍 Verification Checklist

### Firestore Verification

**Truck Document:**
```
✅ status: "idle" (was "in_transit")
✅ assigned_route_id: null (was route_id)
✅ current_latitude: <last bin's latitude>
✅ current_longitude: <last bin's longitude>
```

**Route Document:**
```
✅ status: "completed" (was "generated")
✅ started_at: <timestamp>
✅ completed_at: <timestamp>
✅ truck_id: "TRUCK_DEMO_01"
```

**Bin Documents:**
```
✅ fill_level: 0 (was 70-100)
✅ status: "normal" (was "urgent" or "overflow")
✅ urgency_score: 0 (was 70-100)
✅ predicted_overflow_time: <recalculated>
✅ time_to_overflow_minutes: <recalculated>
```

### WebSocket Verification

```
✅ Received truck_location_update events (3x)
✅ Received bin_collected events (3x)
✅ Received route_progress events (3x)
✅ Received route_completed event (1x)
✅ Total: 10 events
```

---

## 🐛 Troubleshooting

### "No urgent bins found"
**Solution:** Lower fill levels in Step 1, or manually create bins with fill_level > 70

### "Truck has no assigned route"
**Solution:** Make sure you completed Step 4 (assign route)

### "Route status is not 'generated'"
**Solution:** Route was already used. Generate a new route (Step 2)

### WebSocket not connecting
**Solution:** 
- Check server is running
- Use `ws://` not `wss://` for local testing
- Check browser console for errors

### No events received
**Solution:**
- Verify WebSocket is connected (see "✅ Connected")
- Check if simulation started (truck status should be "in_transit")
- Look at server logs for errors

---

## 🎯 Advanced Testing

### Test Multiple Trucks

Repeat Steps 3-6 with different truck IDs:
- `TRUCK_DEMO_02`
- `TRUCK_DEMO_03`

All simulations run concurrently!

### Test Long Routes

1. Create more bins manually (10-15 bins)
2. Set all to high fill levels (>70)
3. Generate route
4. Watch longer simulation

### Test WebSocket Reconnection

1. Disconnect WebSocket: `ws.close()`
2. Reconnect: Run Step 5 again
3. Start new trip
4. Events should still arrive

---

## 📊 Expected Timeline

For a route with 3 bins:

```
t=0s    : Trip starts
t=2.5s  : Bin 1 collected (33% progress)
t=5.0s  : Bin 2 collected (67% progress)
t=7.5s  : Bin 3 collected (100% progress)
t=7.5s  : Route completed, truck idle
```

**Total duration:** ~7.5 seconds for 3 bins

---

## 🎉 Success!

If you saw all the events and verified the data updates, congratulations! 

The Truck Simulation Engine is working perfectly. 🚀

**Next Steps:**
- Build frontend visualization
- Add multiple truck support
- Implement pause/resume
- Add real-time map updates

---

## 📝 Notes

- Simulation runs asynchronously (non-blocking)
- Multiple simulations can run simultaneously
- WebSocket broadcasts to all connected clients
- Failed clients are automatically disconnected
- All data persists in Firestore

**Status: FULLY OPERATIONAL** ✅
