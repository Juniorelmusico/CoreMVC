# Melocuore - Music Analysis Platform

Melocuore is a powerful music analysis platform designed for DJs and music producers. It provides automatic audio analysis, track management, and a REST API for integration with other applications.

## Features

- Audio file upload and management
- Automatic audio analysis using librosa
- BPM detection
- Genre and mood classification
- REST API for track management
- User authentication and authorization
- Artist profiles and track organization

## Tech Stack

### Backend
- Django 5.0.1
- Django REST Framework 3.14.0
- Celery 5.3.6
- Redis
- Librosa 0.10.1
- NumPy 1.26.3

### Frontend
- React
- Material-UI
- Axios

## Setup

### Prerequisites
- Python 3.8+
- Node.js 14+
- Redis
- PostgreSQL

### Backend Setup
1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Start Redis:
```bash
redis-server
```

6. Start Celery worker:
```bash
celery -A melocuore worker -l info
```

7. Run the development server:
```bash
python manage.py runserver
```

### Frontend Setup
1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start the development server:
```bash
npm start
```

## API Endpoints

### Authentication
- POST /api/token/ - Get JWT token
- POST /api/token/refresh/ - Refresh JWT token

### Tracks
- GET /api/tracks/ - List tracks
- POST /api/tracks/upload/ - Upload new track
- GET /api/tracks/{id}/ - Get track details
- GET /api/tracks/{id}/analysis/ - Get track analysis

### Artists
- GET /api/artists/ - List artists
- POST /api/artists/ - Create artist
- GET /api/artists/{id}/ - Get artist details

### Genres & Moods
- GET /api/genres/ - List genres
- GET /api/moods/ - List moods

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

⌨️ with ❤️ by Junior Espin 

## 🎤 Deploy
https://d4a892c7-6446-4a2d-b9de-cee972a1db3a.e1-us-east-azure.choreoapps.dev

## 🎵 Video Youtube
https://youtu.be/fBV4Kan45R4




