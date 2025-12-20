# Test Smell Rank - Frontend

React + Vite frontend with authentication UI.

## Setup Instructions

### Prerequisites

- Node.js 16+ and npm

### Installation

1. Navigate to the frontend directory:

```bash
cd frontend
```

2. Install dependencies:

```bash
npm install
```

### Running the Development Server

```bash
npm run dev
```

The application will be available at: http://localhost:5173

### Building for Production

```bash
npm run build
```

## Features

- ✅ User Registration
- ✅ User Login
- ✅ JWT Token Authentication
- ✅ Protected Dashboard Routes
- ✅ Modern UI with gradient design
- ✅ Test Smell Detection Dashboard

## Pages

- `/login` - Login page
- `/register` - Registration page
- `/dashboard` - Protected dashboard (requires authentication)

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   └── ProtectedRoute.jsx
│   ├── context/
│   │   └── AuthContext.jsx
│   ├── pages/
│   │   ├── Login.jsx
│   │   ├── Register.jsx
│   │   ├── Dashboard.jsx
│   │   ├── Auth.css
│   │   └── Dashboard.css
│   ├── services/
│   │   └── api.js
│   ├── App.jsx
│   ├── main.jsx
│   └── index.css
├── index.html
├── vite.config.js
└── package.json
```
