# SpringForge CLI - Quick Authentication Reference

## Authentication Commands

### `/login` - Authenticate User
```bash
/login
```
Prompts for email and password. Stores token locally for authenticated requests.

### `/register` - Create New Account
```bash
/register
```
Creates a new user account. Prompts for name, email, and password. Automatically logs in after registration.

### `/logout` - End Current Session
```bash
/logout
```
Removes token for current user. Prompts for confirmation.

### `/user` - Show Current User
```bash
/user
```
Displays currently authenticated user email.

### `/users` - List Stored Users
```bash
/users
```
Shows all user emails stored locally. Current user marked with `*`.

## Common Workflows

### First Time Setup
```
1. springforge                    # Start CLI
2. /register                      # Create account
3. generate "your description"    # Use authenticated agent
4. /help                          # See all commands
```

### Switching Users
```
1. /logout                        # Logout current user
2. /login                         # Login as different user
3. generate "your description"    # Agent uses new user's credentials
```

### Command Line Login
```bash
springforge register              # Interactive registration
springforge login                 # Interactive login
springforge generate "REST API"   # Authenticated generation
springforge logout                # Logout
```

## Token Storage
- **Location**: `~/.springforge/auth.json`
- **Permissions**: `600` (owner only)
- **Contains**: User emails and JWT tokens

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No user logged in" | Run `/login` or `/register` |
| "Invalid credentials" | Check email and password |
| "API unreachable" | Verify server is running: `springforge health` |
| "Token expired" | Login again: `/login` |
| "Need to clear tokens" | Delete `~/.springforge/auth.json` |

## Security Tips

1. **Unique Passwords**: Use strong, unique passwords
2. **Don't Share Tokens**: Tokens in `~/.springforge/auth.json` are personal
3. **Public Computers**: Logout after use (`/logout`)
4. **HTTPS Recommended**: Use HTTPS URLs in production
5. **Regular Login**: Re-authenticate periodically

## Token Details

- **Type**: JWT (JSON Web Token)
- **Algorithm**: HS256
- **Contains**: User ID, role, expiration time
- **Expiration**: 30 minutes (configurable on server)
- **Storage**: Encrypted in local file with restricted permissions
