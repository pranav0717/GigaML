from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Tuple
import math
import uuid
from enum import Enum

app = FastAPI(
    title="Ride Dispatch System",
    description="Ride-hailing dispatch system with intelligent driver assignment",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Enums
class DriverStatus(str, Enum):
    AVAILABLE = "available"
    ON_TRIP = "on_trip"
    OFFLINE = "offline"

class RideRequestStatus(str, Enum):
    WAITING = "waiting"
    ASSIGNED = "assigned"
    REJECTED = "rejected"
    COMPLETED = "completed"
    FAILED = "failed"

# Pydantic Models
class Location(BaseModel):
    x: int
    y: int

class Driver(BaseModel):
    id: str
    location: Location
    status: DriverStatus = DriverStatus.AVAILABLE
    current_ride_id: Optional[str] = None
    target_location: Optional[Location] = None
    is_moving_to_pickup: bool = False

class Rider(BaseModel):
    id: str
    pickup_location: Location
    dropoff_location: Location

class RideRequestCreate(BaseModel):
    rider_id: str

class RideRequest(BaseModel):
    id: str
    rider_id: str
    pickup_location: Location
    dropoff_location: Location
    status: RideRequestStatus = RideRequestStatus.WAITING
    assigned_driver_id: Optional[str] = None
    rejected_drivers: List[str] = []

# Global state
drivers: Dict[str, Driver] = {}
riders: Dict[str, Rider] = {}
ride_requests: Dict[str, RideRequest] = {}
current_tick: int = 0
dispatch_algorithm: str = "balanced"

def calculate_distance(loc1: Location, loc2: Location) -> float:
    return math.sqrt((loc1.x - loc2.x) ** 2 + (loc1.y - loc2.y) ** 2)

def calculate_eta(driver_loc: Location, pickup_loc: Location) -> float:
    return calculate_distance(driver_loc, pickup_loc)

def get_driver_fairness_score(driver_id: str) -> float:
    driver = drivers[driver_id]
    completed_rides = sum(1 for req in ride_requests.values() 
                         if req.assigned_driver_id == driver_id and req.status == RideRequestStatus.COMPLETED)
    return completed_rides

def find_best_driver(ride_request: RideRequest) -> Optional[str]:
    available_drivers = [d for d in drivers.values() if d.status == DriverStatus.AVAILABLE 
                        and d.id not in ride_request.rejected_drivers]
    
    if not available_drivers:
        return None
    
    best_driver = None
    best_score = float('inf')
    
    for driver in available_drivers:
        eta = calculate_eta(driver.location, ride_request.pickup_location)
        fairness_penalty = get_driver_fairness_score(driver.id)
        
        if dispatch_algorithm == "eta_only":
            total_score = eta
        elif dispatch_algorithm == "fairness_only":
            total_score = fairness_penalty
        else:  # balanced
            total_score = eta + (fairness_penalty * 0.5)
        
        if total_score < best_score:
            best_score = total_score
            best_driver = driver
    
    return best_driver.id if best_driver else None

def move_driver_towards_target(driver: Driver, target: Location):
    if driver.location.x < target.x:
        driver.location.x += 1
    elif driver.location.x > target.x:
        driver.location.x -= 1
    
    if driver.location.y < target.y:
        driver.location.y += 1
    elif driver.location.y > target.y:
        driver.location.y -= 1

def calculate_average_eta() -> float:
    completed_requests = [req for req in ride_requests.values() if req.status == RideRequestStatus.COMPLETED]
    if not completed_requests:
        return 0
    
    total_eta = 0
    for req in completed_requests:
        for driver in drivers.values():
            if driver.id == req.assigned_driver_id:
                total_eta += calculate_eta(driver.location, req.pickup_location)
                break
    
    return round(total_eta / len(completed_requests), 2)

def calculate_system_efficiency() -> float:
    if len(drivers) == 0 or len(ride_requests) == 0:
        return 0
    
    completion_rate = len([req for req in ride_requests.values() if req.status == RideRequestStatus.COMPLETED]) / len(ride_requests)
    driver_utilization = len([d for d in drivers.values() if d.status == DriverStatus.ON_TRIP]) / len(drivers)
    
    efficiency = (completion_rate * 0.7) + (driver_utilization * 0.3)
    return round(efficiency * 100, 2)

@app.get("/", tags=["System"])
async def root():
    return {
        "message": "Ride Dispatch System API",
        "version": "1.0.0",
        "docs": "/docs",
        "frontend": "/static/index.html",
        "endpoints": {
            "drivers": "/drivers",
            "riders": "/riders", 
            "ride_requests": "/ride-requests",
            "tick": "/tick",
            "state": "/state"
        }
    }

@app.post("/drivers", response_model=Driver, tags=["Drivers"])
async def create_driver(location: Location):
    driver_id = str(uuid.uuid4())
    driver = Driver(id=driver_id, location=location)
    drivers[driver_id] = driver
    return driver

@app.delete("/drivers/{driver_id}")
async def delete_driver(driver_id: str):
    if driver_id not in drivers:
        raise HTTPException(status_code=404, detail="Driver not found")
    del drivers[driver_id]
    return {"message": "Driver deleted"}

@app.get("/drivers", response_model=List[Driver], tags=["Drivers"])
async def get_drivers():
    return list(drivers.values())

@app.post("/riders", response_model=Rider, tags=["Riders"])
async def create_rider(pickup_location: Location, dropoff_location: Location):
    rider_id = str(uuid.uuid4())
    rider = Rider(id=rider_id, pickup_location=pickup_location, dropoff_location=dropoff_location)
    riders[rider_id] = rider
    return rider

@app.delete("/riders/{rider_id}")
async def delete_rider(rider_id: str):
    if rider_id not in riders:
        raise HTTPException(status_code=404, detail="Rider not found")
    del riders[rider_id]
    return {"message": "Rider deleted"}

@app.get("/riders", response_model=List[Rider])
async def get_riders():
    return list(riders.values())

@app.post("/ride-requests", response_model=RideRequest, tags=["Ride Requests"])
async def create_ride_request(request: RideRequestCreate):
    rider_id = request.rider_id
    if rider_id not in riders:
        raise HTTPException(status_code=404, detail="Rider not found")
    
    rider = riders[rider_id]
    request_id = str(uuid.uuid4())
    ride_request = RideRequest(
        id=request_id,
        rider_id=rider_id,
        pickup_location=rider.pickup_location,
        dropoff_location=rider.dropoff_location
    )
    ride_requests[request_id] = ride_request
    
    best_driver_id = find_best_driver(ride_request)
    if best_driver_id:
        ride_request.status = RideRequestStatus.ASSIGNED
        ride_request.assigned_driver_id = best_driver_id
        drivers[best_driver_id].status = DriverStatus.ON_TRIP
        drivers[best_driver_id].current_ride_id = request_id
        drivers[best_driver_id].target_location = rider.pickup_location
        drivers[best_driver_id].is_moving_to_pickup = True
    
    return ride_request

@app.post("/ride-requests/{request_id}/reject")
async def reject_ride_request(request_id: str, driver_id: str):
    if request_id not in ride_requests:
        raise HTTPException(status_code=404, detail="Ride request not found")
    
    ride_request = ride_requests[request_id]
    if ride_request.assigned_driver_id != driver_id:
        raise HTTPException(status_code=400, detail="Driver not assigned to this ride")
    
    ride_request.rejected_drivers.append(driver_id)
    ride_request.status = RideRequestStatus.WAITING
    ride_request.assigned_driver_id = None
    
    drivers[driver_id].status = DriverStatus.AVAILABLE
    drivers[driver_id].current_ride_id = None
    drivers[driver_id].target_location = None
    drivers[driver_id].is_moving_to_pickup = False
    
    best_driver_id = find_best_driver(ride_request)
    if best_driver_id:
        ride_request.status = RideRequestStatus.ASSIGNED
        ride_request.assigned_driver_id = best_driver_id
        drivers[best_driver_id].status = DriverStatus.ON_TRIP
        drivers[best_driver_id].current_ride_id = request_id
        drivers[best_driver_id].target_location = ride_request.pickup_location
        drivers[best_driver_id].is_moving_to_pickup = True
    
    return ride_request

@app.get("/ride-requests", response_model=List[RideRequest])
async def get_ride_requests():
    return list(ride_requests.values())

@app.post("/tick", tags=["Simulation"])
async def advance_tick():
    global current_tick
    current_tick += 1
    
    for driver in drivers.values():
        if driver.status == DriverStatus.ON_TRIP and driver.target_location:
            move_driver_towards_target(driver, driver.target_location)
            
            if driver.location.x == driver.target_location.x and driver.location.y == driver.target_location.y:
                ride_request = ride_requests[driver.current_ride_id]
                
                if driver.is_moving_to_pickup:
                    driver.is_moving_to_pickup = False
                    driver.target_location = ride_request.dropoff_location
                else:
                    ride_request.status = RideRequestStatus.COMPLETED
                    driver.status = DriverStatus.AVAILABLE
                    driver.current_ride_id = None
                    driver.target_location = None
                    driver.is_moving_to_pickup = False
    
    return {"tick": current_tick, "message": "Time advanced"}

@app.get("/state", tags=["System"])
async def get_system_state():
    return {
        "tick": current_tick,
        "drivers": list(drivers.values()),
        "riders": list(riders.values()),
        "ride_requests": list(ride_requests.values())
    }

@app.post("/dispatch-algorithm", tags=["System"])
async def set_dispatch_algorithm(algorithm: str):
    global dispatch_algorithm
    
    valid_algorithms = ["balanced", "eta_only", "fairness_only"]
    if algorithm not in valid_algorithms:
        raise HTTPException(status_code=400, detail=f"Invalid algorithm. Must be one of: {valid_algorithms}")
    
    dispatch_algorithm = algorithm
    return {
        "current_algorithm": dispatch_algorithm,
        "available_algorithms": valid_algorithms,
        "message": f"Dispatch algorithm changed to {algorithm}"
    }

@app.get("/dispatch-algorithm", tags=["System"])
async def get_dispatch_algorithm():
    return {
        "current_algorithm": dispatch_algorithm,
        "available_algorithms": ["balanced", "eta_only", "fairness_only"],
        "description": {
            "balanced": "Balances ETA and fairness (default)",
            "eta_only": "Only considers distance to pickup",
            "fairness_only": "Only considers driver fairness"
        }
    }

@app.get("/metrics", tags=["System"])
async def get_system_metrics():
    total_requests = len(ride_requests)
    completed_rides = sum(1 for req in ride_requests.values() if req.status == RideRequestStatus.COMPLETED)
    waiting_rides = sum(1 for req in ride_requests.values() if req.status == RideRequestStatus.WAITING)
    assigned_rides = sum(1 for req in ride_requests.values() if req.status == RideRequestStatus.ASSIGNED)
    
    available_drivers = sum(1 for d in drivers.values() if d.status == DriverStatus.AVAILABLE)
    busy_drivers = sum(1 for d in drivers.values() if d.status == DriverStatus.ON_TRIP)
    
    completion_rate = (completed_rides / total_requests * 100) if total_requests > 0 else 0
    driver_utilization = (busy_drivers / len(drivers) * 100) if len(drivers) > 0 else 0
    
    return {
        "total_requests": total_requests,
        "completed_rides": completed_rides,
        "waiting_rides": waiting_rides,
        "assigned_rides": assigned_rides,
        "completion_rate_percent": round(completion_rate, 2),
        "available_drivers": available_drivers,
        "busy_drivers": busy_drivers,
        "driver_utilization_percent": round(driver_utilization, 2),
        "total_drivers": len(drivers),
        "total_riders": len(riders),
        "current_tick": current_tick,
        "dispatch_algorithm": dispatch_algorithm,
        "average_eta": calculate_average_eta() if total_requests > 0 else 0,
        "system_efficiency": calculate_system_efficiency()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 