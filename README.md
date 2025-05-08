# DIP Analytics

## Traffic Analysis System

This system provides real-time traffic analysis based on sensor data from vehicles. It calculates various traffic metrics including:

- Average speed using moving average
- Traffic flow rate (vehicles per hour)
- Traffic density (vehicles per kilometer)
- Congestion levels
- Traffic status (FREE/DENSE/JAM)
- Speed trends

### Project Structure

```
dip-analytics/
├── alembic/              # Database migrations
├── src/
│   ├── analytics/        # Traffic analysis components
│   │   ├── cruds/       # CRUD operations
│   │   ├── routers/     # API endpoints
│   │   └── services/    # Business logic
│   ├── commons/         # Shared components
│   │   ├── models.py    # Database models
│   │   └── schemas.py   # Pydantic schemas
│   ├── config/          # Configuration
│   └── services/        # Core services
├── tests/               # Test suite
└── logs/               # Application logs
```

### Key Features

- Real-time traffic monitoring
- Moving average calculations for stable metrics
- Congestion level analysis
- Traffic state classification
- Historical data storage
- Trend analysis

### Data Models

#### Car
- Plate number
- Model
- Average speed
- Current road location

#### Road
- Start and end points
- Length
- City and street information
- Associated cars

#### Traffic Measurement
- Average speed
- Flow rate
- Density
- Timestamp
- Associated road

#### Road Capacity
- Number of lanes
- Speed limit
- Maximum capacity
- Associated road

### Installation

1. Clone the repository
2. Install dependencies:
```bash
uv sync
```

3. Run database migrations:
```bash
alembic upgrade head
```

4. Start the service:
```bash
uvicorn main:app --reload
```

### Configuration

The system uses environment variables for configuration. Create a `.env` file with:

```env
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname
```

### Traffic Analysis Algorithms

The system implements several traffic analysis algorithms:

1. Moving Average Speed:
   - Uses a configurable time window (default: 5 minutes)
   - Calculates average speed of vehicles in the window
   - Helps smooth out short-term fluctuations

2. Congestion Analysis:
   - Compares current flow rate to road capacity
   - Considers speed relative to speed limit
   - Classifies traffic state (FREE/DENSE/JAM)

3. Trend Analysis:
   - Compares current metrics to historical data
   - Identifies trends (STABLE/INCREASING/DECREASING)
   - Helps predict potential congestion

### API Endpoints

The service provides REST API endpoints for:

#### Traffic Analysis
```
GET /traffic/{road_id}/analysis
```
Returns current traffic analysis including:
- Current average speed
- Flow rate
- Density
- Congestion level
- Traffic status
- Speed trend

#### Car Data
```
POST /cars/sensor-data
```
Process sensor data from vehicles:
- Updates car information
- Triggers traffic analysis
- Returns updated car record

#### Road Information
```
GET /roads/{road_id}
POST /roads/
```
Manage road information and capacity data

### Error Handling

The system implements comprehensive error handling:

1. HTTP Errors:
   - 404: Resource not found
   - 400: Invalid request data
   - 500: Internal server error

2. Business Logic Errors:
   - Invalid sensor data
   - Missing road capacity information
   - Calculation errors

All errors are logged with appropriate context for debugging.

### Logging

The system uses Loguru for structured logging:

- Log levels: DEBUG, INFO, WARNING, ERROR
- Log rotation enabled
- Logs stored in `logs/` directory
- Includes timestamps and context information

### Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

### License

MIT
