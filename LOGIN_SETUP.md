# Login Authentication Setup Guide

## Implementation Complete ✅

This guide explains how to set up and test the login authentication system for DQTimes.

---

## Backend Setup

### 1. Install Python Dependencies

Navigate to the `dqtimes` directory and install the new authentication dependencies:

```bash
cd dqtimes
pip install -r requirements.txt
```

**New dependencies added:**
- `python-jose[cryptography]` - JWT token creation and validation
- `passlib[bcrypt]` - Password hashing with bcrypt

### 2. Configure Environment Variables

Create or update your `.env` file in the `dqtimes` directory:

```bash
# Database (already configured in docker-compose)
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/db

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-change-in-production-use-long-random-string
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours

# Redis (already configured)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

**⚠️ IMPORTANT:** Change `JWT_SECRET_KEY` to a secure random string in production!

Generate a secure key with:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Initialize Database

The User table will be created automatically when you start the FastAPI server. Make sure PostgreSQL is running:

```bash
# Using docker-compose (recommended)
docker-compose up -d postgres

# OR run the full stack
docker-compose up --build
```

### 4. Start the Backend

```bash
# From dqtimes directory
uvicorn app.main:app --reload --host 0.0.0.0 --port 80

# OR using docker-compose
docker-compose up backend
```

**Backend will be available at:** `http://localhost:80`

---

## Frontend Setup

### 1. Install Dependencies

The React Router dependency has already been added. Install it:

```bash
cd frontend
npm install
```

### 2. Start Development Server

```bash
npm run dev
```

**Frontend will be available at:** `http://localhost:5173`

---

## Testing the Authentication

### 1. Create a Test User (Option A: via Register UI)

1. Navigate to `http://localhost:5173/register`
2. Fill in email and password (min 8 characters)
3. Click "Create Account"
4. You'll be redirected to login page

### 2. Create a Test User (Option B: via API)

Using cURL:
```bash
curl -X POST http://localhost:80/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123"
  }'
```

Using Python:
```python
import requests

response = requests.post(
    "http://localhost:80/auth/register",
    json={"email": "test@example.com", "password": "testpass123"}
)
print(response.json())
```

### 3. Login via UI

1. Navigate to `http://localhost:5173/login`
2. Enter your credentials
3. On successful login, you'll be redirected to the home page
4. You should see your user info displayed

### 4. Login via API

```bash
curl -X POST http://localhost:80/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 5. Test Protected Endpoint

```bash
# Get current user info (requires authentication)
curl -X GET http://localhost:80/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"
```

---

## File Structure

### Backend Files Created/Modified

```
dqtimes/
├── requirements.txt          # ✅ Added auth dependencies
├── app/
    ├── main.py              # ✅ Added CORS + auth endpoints
    ├── db.py                # ✅ Added User model
    ├── config.py            # ✅ Added JWT settings
    ├── auth.py              # ✅ NEW - JWT utilities
    └── schemas.py           # ✅ NEW - Pydantic models
```

### Frontend Files Created/Modified

```
frontend/
├── package.json             # ✅ Added react-router-dom
├── src/
    ├── App.jsx              # ✅ Added routing
    ├── services/
    │   └── api.js           # ✅ Added auth functions + interceptors
    ├── context/
    │   └── AuthContext.jsx  # ✅ NEW - Auth state management
    └── components/
        ├── Login.jsx        # ✅ NEW - Login form
        ├── Register.jsx     # ✅ NEW - Registration form
        ├── Home.jsx         # ✅ NEW - Protected home page
        └── ProtectedRoute.jsx # ✅ NEW - Route protection
```

---

## API Endpoints

### Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/register` | Create new user | No |
| POST | `/auth/login` | Login and get token | No |
| GET | `/auth/me` | Get current user info | Yes |

### Existing Forecasting Endpoints (Now with optional auth)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/projecao_lista/` | Single series forecast |
| POST | `/projecao_dataframe/` | Batch CSV forecast |

---

## How Authentication Works

### 1. Login Flow

```
User enters credentials → Frontend calls /auth/login
→ Backend validates credentials
→ Backend generates JWT token (expires in 24h)
→ Frontend stores token in localStorage
→ Frontend redirects to home page
```

### 2. Protected Route Access

```
User navigates to protected route
→ ProtectedRoute checks if token exists in localStorage
→ If no token: redirect to /login
→ If token exists: verify with backend (/auth/me)
→ If valid: render protected content
→ If invalid: clear storage and redirect to /login
```

### 3. API Request with Auth

```
Frontend makes API request
→ Axios interceptor adds Authorization header
→ Backend validates JWT token
→ If valid: process request
→ If invalid: return 401 error
→ Frontend intercepts 401, clears storage, redirects to login
```

### 4. Logout Flow

```
User clicks logout button
→ Frontend clears localStorage (token + user data)
→ Frontend redirects to /login
```

---

## Security Features

✅ **Password Hashing:** bcrypt with automatic salt generation  
✅ **JWT Tokens:** HS256 algorithm with expiration  
✅ **CORS Protection:** Only allows localhost:5173 and localhost:3000  
✅ **Token Validation:** Every protected endpoint validates JWT  
✅ **Secure Storage:** Tokens in localStorage (HTTPS recommended in production)  
✅ **Auto Logout:** Invalid tokens automatically clear session  

---

## Common Issues & Solutions

### Issue: "CORS error" when making API calls

**Solution:** Make sure backend CORS middleware includes your frontend URL:
```python
# In app/main.py
allow_origins=["http://localhost:5173", "http://localhost:3000"]
```

### Issue: "Could not validate credentials"

**Solutions:**
- Check if JWT_SECRET_KEY is set correctly
- Verify token hasn't expired (default 24h)
- Ensure Authorization header format: `Bearer <token>`

### Issue: "Email already registered"

**Solution:** Use a different email or manually delete the user from database:
```sql
DELETE FROM users WHERE email = 'test@example.com';
```

### Issue: Database connection error

**Solution:** Make sure PostgreSQL is running:
```bash
docker-compose up -d postgres
# Check logs
docker-compose logs postgres
```

### Issue: Token persists after logout

**Solution:** Check browser localStorage:
```javascript
// In browser console
localStorage.clear()
```

---

## Testing Checklist

- [ ] Backend starts without errors
- [ ] Frontend starts on port 5173
- [ ] Can access `/login` page
- [ ] Can access `/register` page
- [ ] Can create new user
- [ ] Login with valid credentials succeeds
- [ ] Login with invalid credentials fails
- [ ] Redirected to home after successful login
- [ ] Home page shows user information
- [ ] Logout button clears session
- [ ] Can't access home page without login
- [ ] Token persists after page refresh
- [ ] Invalid token redirects to login

---

## Next Steps / Enhancements

### Optional Improvements

1. **Refresh Token System**
   - Implement refresh tokens for better security
   - Store refresh tokens in Redis
   - Add `/auth/refresh` endpoint

2. **Password Reset**
   - Email verification
   - Password reset flow
   - Token-based reset links

3. **User Profile Management**
   - Update profile endpoint
   - Change password functionality
   - Account deletion

4. **Rate Limiting**
   - Limit login attempts
   - Use Redis for rate limiting
   - Add CAPTCHA for repeated failures

5. **Email Verification**
   - Send verification email on registration
   - Verify email before allowing login
   - Add `is_verified` field to User model

6. **Remember Me Functionality**
   - Checkbox in login form
   - Longer token expiry (30 days)
   - Store preference in localStorage

7. **Social Login**
   - Google OAuth
   - GitHub OAuth
   - Microsoft OAuth

---

## Production Deployment Checklist

Before deploying to production:

- [ ] Change `JWT_SECRET_KEY` to secure random value
- [ ] Set `ACCESS_TOKEN_EXPIRE_MINUTES` appropriately
- [ ] Use HTTPS for all connections
- [ ] Update CORS origins to production URLs
- [ ] Set secure environment variables (not in code)
- [ ] Enable database backups
- [ ] Add rate limiting
- [ ] Implement logging and monitoring
- [ ] Add email verification
- [ ] Consider refresh token strategy
- [ ] Add password complexity requirements
- [ ] Implement account lockout after failed attempts

---

## Support

For issues or questions:
- Check FastAPI docs: https://fastapi.tiangolo.com/tutorial/security/
- Check React Router docs: https://reactrouter.com/
- Review the API_CONTRACT.md for endpoint specifications

---

**Implementation Date:** November 25, 2025  
**Status:** ✅ Complete and Ready for Testing
