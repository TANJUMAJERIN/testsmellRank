# Test Smell Rank - Backend

FastAPI backend with MongoDB authentication.

## Setup Instructions

### Prerequisites

- Python 3.8+
- MongoDB Atlas account (Cloud MongoDB)

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
   - Update MONGODB_URL with your MongoDB Atlas connection string
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

## MongoDB Atlas Setup

This project uses MongoDB Atlas (cloud database). Make sure to:

1. Create a MongoDB Atlas account at https://www.mongodb.com/cloud/atlas
2. Create a cluster and database
3. Get your connection string from Atlas
4. Update the MONGODB_URL in your `.env` file with the Atlas connection string
5. Whitelist your IP address in Atlas Network Access settings
