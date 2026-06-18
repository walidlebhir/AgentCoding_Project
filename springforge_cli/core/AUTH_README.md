"""
Authentication module for SpringForge CLI

This module provides token-based authentication for communicating with the FastAPI backend.
Tokens are securely stored locally and automatically included in API requests.

Features:
- User registration and login
- Secure token storage in ~/.springforge/
- Automatic token injection in API requests
- Token management (logout, user switching)
"""

# Token Storage Location
# Tokens are stored in: ~/.springforge/auth.json
# File permissions: 600 (rw-------)
# Contains: {
#   "current_user": "user@example.com",
#   "users": {
#     "user@example.com": {
#       "token": "<jwt_token>",
#       "token_type": "bearer"
#     }
#   }
# }

# API Authentication Flow
# 1. Client registers with: POST /api/register
#    Body: {
#      "name": "John Doe",
#      "email": "john@example.com",
#      "password": "secure_password"
#    }
#    Response: {
#      "id": "user_id",
#      "name": "John Doe",
#      "email": "john@example.com",
#      "role": "USER"
#    }

# 2. Client logs in with: POST /api/login
#    Body: {
#      "email": "john@example.com",
#      "password": "secure_password"
#    }
#    Response: {
#      "access_token": "<jwt_token>",
#      "token_type": "bearer"
#    }

# 3. Client stores token locally and includes in all requests:
#    Headers: {
#      "Authorization": "Bearer <jwt_token>"
#    }

# 4. Server validates token and associates request with user
#    - Token contains user_id and role
#    - User info is extracted and available in handlers
#    - Projects are linked to authenticated user

# CLI Commands

# /login
#   Interactive login prompt
#   Email and password required
#   Token stored automatically

# /register
#   Interactive registration prompt
#   Name, email, password required
#   Automatically logs in after registration

# /logout
#   Logs out current user
#   Removes token from storage

# /user
#   Shows current logged-in user email

# /users
#   Lists all stored user emails
#   Marks current user with *

# Command Line Usage

# springforge login
# springforge register
# springforge logout
# springforge user
# springforge users
