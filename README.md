# Test Smell Rank

A comprehensive test smell detection and ranking system with authentication.

## Project Overview

Test Smell Rank is a web application that helps developers detect and rank test smells in their codebase. The system includes:

- **Backend**: FastAPI with MongoDB for authentication and data storage
- **Frontend**: React + Vite with modern UI design
- **Authentication**: JWT-based authentication system

## Quick Start

### 1. Start MongoDB

Make sure MongoDB is running on your local machine (default: mongodb://localhost:27017)

### 2. Start Backend

```bash
cd backend
python -m venv venv
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt
python main.py
```

Backend will run at: http://localhost:8000

### 3. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend will run at: http://localhost:5173

## Features

### Authentication

- ✅ User Registration with validation
- ✅ Secure Login with JWT tokens
- ✅ Password hashing with bcrypt
- ✅ Protected routes

### Dashboard

- ✅ Test statistics overview
- ✅ Smell detection interface
- ✅ Ranking analysis
- ✅ Report generation
- ✅ Multiple test smell types supported

### Test Smells Detected

- Assertion Roulette
- Empty Test
- Magic Number
- Conditional Test
- Lazy Test
- Duplicate Code
- Resource Optimism
- Verbose Test
- Slow Test
- Flaky Test
- Exception Handling

## Technology Stack

### Backend

- FastAPI
- MongoDB (Motor - async driver)
- JWT (python-jose)
- Passlib (password hashing)
- Pydantic (data validation)

### Frontend

- React 18
- Vite
- React Router DOM
- Axios
- CSS3 with modern gradients

## Project Structure

```
testsmellRank/
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── auth.py
│   ├── models.py
│   ├── routes/
│   │   └── auth.py
│   ├── requirements.txt
│   ├── .env
│   └── README.md
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── context/
│   │   ├── pages/
│   │   ├── services/
│   │   └── App.jsx
│   ├── package.json
│   ├── vite.config.js
│   └── README.md
└── README.md
```

## Environment Variables

### Backend (.env)

```
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=testsmellrank
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## API Documentation

Once the backend is running, visit:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Screenshots

The application features a modern gradient design with:

- Purple-blue gradient background
- Clean white cards with rounded corners
- Smooth hover animations
- Responsive layout

## Future Enhancements

- File upload for test code analysis
- Real-time smell detection
- Detailed reports with graphs
- Team collaboration features
- CI/CD integration

## License

This project is part of the Test Smell Rank research initiative.
