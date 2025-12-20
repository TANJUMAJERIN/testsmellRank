# Test Smell Rank - Backend

FastAPI backend with MongoDB authentication.

## Setup Instructions

### Prerequisites

- Python 3.8+
- MongoDB installed and running locally (default port 27017)

### Installation

1. Navigate to the backend directory:

```bash
cd backend
```

2. Create a virtual environment:

```bash
python -m venv venv
```

3. Activate the virtual environment:

```bash
# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Configure environment variables:
   - Copy `.env.example` to `.env`
   - Update MongoDB URL if needed (default: mongodb://localhost:27017)
   - Change SECRET_KEY in production

### Running the Server

```bash
python main.py
```

Or with uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: http://localhost:8000

API Documentation (Swagger): http://localhost:8000/docs

## API Endpoints

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token
- `GET /api/auth/me` - Get current user info (requires authentication)

## MongoDB Collections

- `users` - Stores user information with hashed passwords
