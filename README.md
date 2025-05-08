# 🎵 Music Analysis Platform - Django React Full Stack App 🚀

## 📋 Overview

This is a full-stack web application built with Django REST Framework and React that allows users to upload, organize, and analyze music files. It includes user authentication, file management, and an admin dashboard for monitoring system usage and music analysis.


## ✨ Features

- 🔐 **User Authentication** - Register, login, and JWT token-based authentication
- 📁 **File Management** - Upload and view audio files (MP3, WAV)
- 🎧 **Music Analysis** - Track, artist, genre, and mood management
- 📊 **Admin Dashboard** - Complete overview of users, files, and system usage
- 🛠️ **CRUD Operations** - Full admin control over music metadata
- 📱 **Responsive Design** - Modern UI built with React and styled for all devices

## 🔧 Technologies

### Backend 🖥️
- **Django** - Web framework
- **Django REST Framework** - API development
- **JWT Authentication** - Secure user authentication
- **PostgreSQL** - Database (via psycopg2)

### Frontend 🎨
- **React** - UI library
- **React Router** - Navigation
- **Axios** - HTTP client
- **Vite** - Build tool
- **Tailwind CSS** - Styling

## 🚀 Installation

### Prerequisites
- Python 3.7+
- Node.js 14+
- npm or yarn
- PostgreSQL (optional, can use SQLite for development)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/Django-React-Full-Stack-App.git
   cd Django-React-Full-Stack-App
   ```

2. **Backend setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py runserver
   ```

3. **Frontend setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## 🌟 Usage

1. **User Registration/Login**
   - Create a new account or login with existing credentials
   - JWT tokens are automatically managed for authentication

2. **File Upload**
   - Upload MP3 or WAV audio files from the user dashboard
   - View your uploaded files

3. **Admin Dashboard**
   - Access comprehensive statistics about users and files
   - Manage artists, genres, moods, and tracks
   - Analyze audio content

## 👥 User Roles

- **Regular Users**: Upload and manage their own audio files
- **Administrators**: Full access to all users' data, files, and system management features

## 📝 API Endpoints

### Authentication
- `/api/user/register/` - Create new user account
- `/api/token/` - Get JWT tokens

### User Operations
- `/api/files/` - List user's files
- `/api/upload/` - Upload new file

### Admin Operations
- `/api/admin/dashboard/` - Get admin dashboard stats
- `/api/admin/users/` - List all users
- `/api/admin/files/` - List all files
- `/api/admin/crud/artists/` - Manage artists
- `/api/admin/crud/genres/` - Manage genres
- `/api/admin/crud/moods/` - Manage moods
- `/api/admin/crud/tracks/` - Manage tracks
- `/api/admin/crud/analyses/` - Manage analyses

## 🔒 Environment Variables

Create a `.env` file in the backend directory with:

```
SECRET_KEY=your_secret_key
DEBUG=True
DATABASE_URL=your_database_url (optional)
```

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

## 📄 License

This project is licensed under the MIT License.

⌨️ with ❤️ by Junior Espin 

## 🎤 Deploy
https://d4a892c7-6446-4a2d-b9de-cee972a1db3a.e1-us-east-azure.choreoapps.dev

## 🎵 Video Youtube
https://youtu.be/fBV4Kan45R4




