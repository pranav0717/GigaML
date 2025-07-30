#!/usr/bin/env python3
"""
Test script for the Ride Dispatch System
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_system():
    print("Testing Ride Dispatch System")
    print("=" * 50)
    
    # Test 1: Add drivers
    print("\n1. Adding drivers...")
    drivers = []
    for i in range(3):
        response = requests.post(f"{BASE_URL}/drivers", 
                               json={"x": 10 + i*5, "y": 10 + i*5})
        driver = response.json()
        drivers.append(driver)
        print(f"   Added driver {driver['id'][:8]} at ({driver['location']['x']}, {driver['location']['y']})")
    
    # Test 2: Add riders
    print("\n2. Adding riders...")
    riders = []
    for i in range(2):
        response = requests.post(f"{BASE_URL}/riders", 
                               json={
                                   "pickup_location": {"x": 20 + i*10, "y": 20 + i*10},
                                   "dropoff_location": {"x": 30 + i*10, "y": 30 + i*10}
                               })
        rider = response.json()
        riders.append(rider)
        print(f"   Added rider {rider['id'][:8]} pickup:({rider['pickup_location']['x']},{rider['pickup_location']['y']}) dropoff:({rider['dropoff_location']['x']},{rider['dropoff_location']['y']})")
    
    # Test 3: Request rides
    print("\n3. Requesting rides...")
    requests_list = []
    for rider in riders:
        response = requests.post(f"{BASE_URL}/ride-requests", 
                               json={"rider_id": rider["id"]})
        ride_request = response.json()
        requests_list.append(ride_request)
        status = "ASSIGNED" if ride_request.get("assigned_driver_id") else "WAITING"
        print(f"   Ride request {ride_request['id'][:8]} - Status: {status}")
        if ride_request.get("assigned_driver_id"):
            print(f"   Assigned to driver {ride_request['assigned_driver_id'][:8]}")
    
    # Test 4: Advance time and watch movement
    print("\n4. Advancing time to watch movement...")
    for tick in range(1, 11):
        response = requests.post(f"{BASE_URL}/tick")
        tick_data = response.json()
        print(f"   Tick {tick_data['tick']}: {tick_data['message']}")
        
        # Get current state
        state = requests.get(f"{BASE_URL}/state").json()
        completed_rides = sum(1 for req in state["ride_requests"] if req["status"] == "completed")
        print(f"   Completed rides: {completed_rides}")
        
        time.sleep(0.5)  #to see progress
    
    # Test 5: Show final state
    print("\n5. Final system state:")
    state = requests.get(f"{BASE_URL}/state").json()
    print(f"   Total drivers: {len(state['drivers'])}")
    print(f"   Total riders: {len(state['riders'])}")
    print(f"   Total ride requests: {len(state['ride_requests'])}")
    print(f"   Completed rides: {sum(1 for req in state['ride_requests'] if req['status'] == 'completed')}")
    
    print("\nTest completed successfully!")
    print("\nOpen http://localhost:8000/static/index.html in your browser to see the interface!")

if __name__ == "__main__":
    try:
        test_system()
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server.")
        print("Make sure the server is running with: python main.py")
    except Exception as e:
        print(f"Error: {e}") 