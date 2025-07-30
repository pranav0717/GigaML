# Ride Dispatch System

A ride-hailing dispatch system built with FastAPI and a web frontend for visualization and simulation.

## Features

- **Grid-based City Simulation**: 100x100 grid representing a city
- **Dispatch Logic**: Intelligent driver assignment based on ETA and fairness
- **Interactive Frontend**: Visual grid with click-to-place functionality
- **Time-based Simulation**: Manual tick advancement for controlled simulation
- **Fallback Mechanism**: Automatic reassignment when drivers reject rides

## System Architecture

### Backend (FastAPI)
- **Entities**: Drivers, Riders, RideRequests
- **Dispatch Logic**: Balances ETA, fairness, and efficiency
- **Movement Simulation**: Drivers move one unit per tick
- **State Management**: In-memory storage for simulation

### Frontend (HTML/CSS/JavaScript)
- **Visual Grid**: 600x600 canvas showing 100x100 city grid
- **Real-time Updates**: Live system state visualization
- **Interactive Controls**: Add/remove entities, request rides, advance time
- **Responsive Design**: Works on desktop and mobile

## Dispatch Logic

The system uses a dispatch algorithm that balances multiple objectives:

### Core Algorithm
```python
def find_best_driver(ride_request):
    available_drivers = [d for d in drivers.values() 
                        if d.status == DriverStatus.AVAILABLE 
                        and d.id not in ride_request.rejected_drivers]
    
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
```

### Scoring Formula
```python
total_score = eta + (fairness_penalty * 0.5)
```

**Components:**
- **ETA**: Euclidean distance from driver to pickup location
- **Fairness Penalty**: Number of completed rides by driver × 0.5
- **Goal**: Lower scores = higher priority

### Available Algorithms
1. **Balanced**: Prioritizes both ETA and fairness (default)
2. **ETA Only**: Only considers distance to pickup
3. **Fairness Only**: Only considers driver fairness

## Quick Start

### Prerequisites
- Python 3.8+
- pip

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ride-dispatch-system
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the backend**
   ```bash
   python main.py
   ```

4. **Open the frontend**
   - Navigate to `http://localhost:8000/static/index.html`
   - Or visit `http://localhost:8000` and click the link

## How to Use

### Adding Entities
1. **Add Driver**: Set X,Y coordinates and click "Add Driver"
2. **Add Rider**: Set pickup and dropoff coordinates, click "Add Rider"
3. **Request Ride**: Click "Request Ride" to create a ride request

### Simulation Controls
- **Next Tick**: Advance simulation time by one unit
- **Clear All**: Remove all entities and reset simulation
- **Click Grid**: Click anywhere on the grid to set coordinates

### Visual Elements
- **Blue Circle (D)**: Available driver
- **Yellow Circle (D)**: Driver on trip
- **Green Circle (R)**: Rider
- **Yellow Circle (P)**: Pickup location
- **Red Circle (D)**: Dropoff location

## API Endpoints

### Drivers
- `POST /drivers` - Create a new driver
- `GET /drivers` - Get all drivers
- `DELETE /drivers/{driver_id}` - Remove a driver

### Riders
- `POST /riders` - Create a new rider
- `GET /riders` - Get all riders
- `DELETE /riders/{rider_id}` - Remove a rider

### Ride Requests
- `POST /ride-requests` - Create a ride request
- `GET /ride-requests` - Get all ride requests
- `POST /ride-requests/{request_id}/reject` - Reject a ride request

### Simulation
- `POST /tick` - Advance simulation time
- `GET /state` - Get complete system state

### System
- `GET /metrics` - Get system performance metrics
- `GET /dispatch-algorithm` - Get current dispatch algorithm
- `POST /dispatch-algorithm` - Change dispatch algorithm

## Technical Details

### Assumptions & Simplifications
- **Movement**: One unit per tick (no diagonal movement)
- **No Authentication**: Simple in-memory simulation
- **No Persistence**: State resets on server restart
- **Grid Size**: Fixed 100x100 city grid
- **Driver Speed**: Uniform speed for all drivers
- **Rejection Behavior**: Drivers can reject rides, triggering fallback

### Technical Decisions

#### In-Memory Storage
- **Pros**: Fast, simple, no setup required
- **Cons**: No persistence, state lost on restart
- **Rationale**: Perfect for simulation and demonstration

#### Manual Tick Advancement
- **Pros**: Controlled simulation, easy debugging
- **Cons**: Not real-time
- **Rationale**: Allows precise observation of system behavior

#### Euclidean Distance for ETA
- **Pros**: Simple, fast calculation
- **Cons**: Doesn't account for obstacles, traffic
- **Rationale**: Sufficient for grid-based simulation

#### Fairness Penalty Weight (0.5)
- **Pros**: Balances ETA and fairness
- **Cons**: May need tuning for different scenarios
- **Rationale**: Empirical balance between efficiency and fairness

#### Single Movement Direction
- **Pros**: Simple, predictable movement
- **Cons**: Not optimal pathfinding
- **Rationale**: Clear visualization of movement patterns

### Dispatch Algorithm
1. Calculate ETA for each available driver
2. Apply fairness penalty based on completed rides
3. Select driver with lowest total score
4. If no drivers available, request remains waiting
5. On rejection, retry with next-best driver

### Movement Logic
- Drivers move towards pickup location first
- After pickup, move towards dropoff location
- Movement is one unit per tick in X or Y direction
- Ride completes when driver reaches dropoff

## Future Enhancements

- **Real-time Updates**: WebSocket integration for live updates
- **Multiple Dispatch Algorithms**: Configurable dispatch strategies
- **Persistence**: Database integration for state persistence
- **Authentication**: User management and ride history
- **Analytics**: Performance metrics and optimization suggestions
- **Mobile App**: Native mobile application
- **Multi-city Support**: Multiple grid systems
