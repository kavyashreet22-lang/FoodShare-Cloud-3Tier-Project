# FoodShare - AWS Cloud 3-Tier Project

## Project Overview
FoodShare is a cloud-based food donation application.
It allows users to submit food donations and view available donations.

## Technology Stack

- Frontend: HTML, CSS, JavaScript
- Web Server: Nginx
- Backend: Python Flask
- Database: MySQL
- Cloud Platform: Amazon Web Services (AWS)
- Cloud Service: Amazon EC2
- Operating System: Amazon Linux

## 3-Tier Architecture

### 1. Presentation Layer
HTML, CSS and JavaScript provide the user interface.

### 2. Application Layer
Python Flask handles API requests and application logic.
Nginx serves the frontend and forwards API requests to Flask.

### 3. Database Layer
MySQL stores food donation information.

## Features

- Submit food donations
- View available donations
- Admin donation management
- Mark donations as collected

## Project Structure

FoodShare-Cloud-Project/
- backend/
  - app.py
  - requirements.txt
- frontend/
  - index.html
  - admin.html
  - donations.html
- .gitignore
- README.md

## Deployment
The application is hosted on an AWS EC2 instance.

## Author
Student Cloud Computing Project
