# College Management System

A comprehensive web-based college management system similar to Google Classroom, built with Flask and SQLite.

## Features

### Core Functionality
- **User Authentication**: Secure login/registration for students and teachers
- **Course Management**: Create, join, and manage courses
- **Assignment System**: Create assignments, submit work, and grade submissions
- **File Upload**: Support for file attachments in assignments
- **Real-time Messaging**: Course-based discussion system
- **Dashboard**: Personalized dashboard for each user role

### User Roles
- **Students**: Join courses, submit assignments, participate in discussions
- **Teachers**: Create courses, manage assignments, grade submissions
- **Admin**: (Future enhancement) System administration

## Installation

1. Clone or download the project
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python app.py
   ```
4. Open your browser and navigate to `http://localhost:5000`

## Usage

### Getting Started
1. Register as a student or teacher
2. **Teachers**: Create courses and share course codes with students
3. **Students**: Join courses using course codes
4. Create assignments, submit work, and engage in course discussions

### Key Features
- **Course Creation**: Teachers can create courses with unique codes
- **Assignment Management**: Full assignment lifecycle from creation to grading
- **File Sharing**: Upload and download assignment files
- **Discussion Board**: Course-specific messaging system
- **Grade Tracking**: Comprehensive grading and feedback system

## Database Schema

The system uses SQLite with the following main tables:
- `users`: User accounts and profiles
- `courses`: Course information
- `enrollments`: Student-course relationships
- `assignments`: Assignment details
- `submissions`: Student submissions and grades
- `messages`: Course discussion messages

## Technology Stack

- **Backend**: Python Flask
- **Database**: SQLite
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Icons**: Font Awesome
- **File Handling**: Werkzeug secure filename handling

## Security Features

- Password hashing using Werkzeug
- Secure file upload handling
- Session-based authentication
- SQL injection prevention with parameterized queries
- Role-based access control

## Future Enhancements

- Real-time notifications
- Calendar integration
- Video conferencing integration
- Mobile app support
- Advanced analytics and reporting
- Bulk operations for teachers
- Email notifications
- Advanced search functionality

## Contributing

Feel free to fork this project and submit pull requests for improvements.

## License

This project is open source and available under the MIT License.