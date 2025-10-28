# Auth0 Dynamic Client Registration Setup

This document describes how Dynamic Client Registration (DCR) is configured for ChatGPT integration with the YouTube MCP server.

## Architecture

```
┌──────────┐         ┌─────────────┐         ┌─────────────┐
│ ChatGPT  │────────▶│   Auth0     │◀────────│  MCP Server │
│ (Client) │  OAuth  │   (Auth     │  Verify │  (Resource  │
│          │  + DCR  │   Server)   │  Token  │   Server)   │
└──────────┘         └─────────────┘         └─────────────┘
```

- **ChatGPT**: OAuth Client (registers dynamically with Auth0)
- **Auth0**: Authorization Server (handles DCR, OAuth, issues tokens)
- **MCP Server**: Resource Server (validates tokens, serves MCP tools)

## Current Status: ✅ CONFIGURED

Dynamic Client Registration is **already enabled** on your Auth0 tenant.

### Verification

```bash
# Check OIDC configuration
curl -s https://dev-x1k2ea1lh5dffa3a.us.auth0.com/.well-known/openid-configuration | grep registration_endpoint

# Expected output:
# "registration_endpoint":"https://dev-x1k2ea1lh5dffa3a.us.auth0.com/oidc/register"
```

### Test DCR Endpoint

```bash
curl -X POST "https://dev-x1k2ea1lh5dffa3a.us.auth0.com/oidc/register" \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Test Client",
    "redirect_uris": ["https://example.com/callback"],
    "grant_types": ["authorization_code"],
    "response_types": ["code"]
  }'
```

Should return `client_id` and `client_secret`.

## Auth0 Configuration

### 1. API Configuration

**Location**: Auth0 Dashboard → Applications → APIs

- **Name**: YouTube MCP Server (or your API name)
- **Identifier (Audience)**: `https://yt-mcp-remote-production.up.railway.app`
- **Signing Algorithm**: RS256
- **Dynamic Client Registration**: ✅ Enabled

### 2. Required Settings for ChatGPT

Ensure these settings are configured:

1. **OIDC Conformant**: Enabled (tenant-level setting)
2. **Allow Dynamic Client Registration**: Enabled (API-level setting)
3. **Default Connections**: Enabled for new applications

### 3. Database Connections

**Location**: Auth0 Dashboard → Authentication → Database

For each database connection (e.g., "Username-Password-Authentication"):
- Navigate to **Applications** tab
- Enable: **"Use for all new applications"**

This ensures dynamically registered clients (like ChatGPT) can authenticate users.

### 4. Social Connections (Optional)

**Location**: Auth0 Dashboard → Authentication → Social

If using social login (Google, GitHub, etc.):
- Enable each provider for new applications
- This allows users to log in via social providers when ChatGPT initiates OAuth

## ChatGPT Configuration

When adding this MCP server to ChatGPT, provide:

### OAuth Configuration

- **Authorization URL**: `https://dev-x1k2ea1lh5dffa3a.us.auth0.com/authorize`
- **Token URL**: `https://dev-x1k2ea1lh5dffa3a.us.auth0.com/oauth/token`
- **Scope**: `openid profile email`
- **Client ID**: (leave blank - ChatGPT will register dynamically)
- **Client Secret**: (leave blank - ChatGPT will register dynamically)

### Additional Parameters

You may need to include the `audience` parameter:
- **Audience**: `https://yt-mcp-remote-production.up.railway.app`

ChatGPT will:
1. Discover the registration endpoint from `/.well-known/openid-configuration`
2. Register itself as a client via `/oidc/register`
3. Receive `client_id` and `client_secret`
4. Use these credentials for the OAuth flow

## OAuth Flow

### 1. Discovery
```
ChatGPT → GET /.well-known/openid-configuration
Auth0 → Returns metadata (includes registration_endpoint)
```

### 2. Dynamic Client Registration
```
ChatGPT → POST /oidc/register
Auth0 → Returns client_id and client_secret
```

### 3. Authorization Request
```
User → Clicks "Connect" in ChatGPT
ChatGPT → Redirects to Auth0 /authorize
User → Logs in and authorizes
Auth0 → Redirects back with authorization code
```

### 4. Token Exchange
```
ChatGPT → POST /oauth/token with authorization code
Auth0 → Returns access_token (JWT)
```

### 5. API Request
```
ChatGPT → POST /sse with Bearer token
MCP Server → Validates token with Auth0TokenVerifier
MCP Server → Returns MCP tool results
```

## Environment Variables

The MCP server requires:

```bash
# Auth0 Configuration
AUTH0_DOMAIN=dev-x1k2ea1lh5dffa3a.us.auth0.com
AUTH0_AUDIENCE=https://yt-mcp-remote-production.up.railway.app

# Server URL (used for OAuth metadata)
RESOURCE_SERVER_URL=https://yt-mcp-remote-production.up.railway.app
```

## Security Notes

1. **Token Validation**: The MCP server validates all tokens against Auth0's JWKS
2. **Client Secrets**: Auth0 generates unique secrets for each registered client
3. **Token Expiration**: Default 24 hours (configurable in Auth0 API settings)
4. **Rate Limiting**: Auth0 limits DCR to ~10 registrations per IP per hour
5. **Client Cleanup**: Dynamically created clients persist in Auth0 - clean up periodically if needed

## Monitoring

### Auth0 Logs

**Location**: Auth0 Dashboard → Monitoring → Logs

Look for:
- `dcr` - Dynamic Client Registration events
- `s` - Successful login
- `fapi` - Failed API operations
- `feacft` - Failed token exchange

### Check Registered Clients

**Location**: Auth0 Dashboard → Applications → Applications

Dynamically registered clients will appear here with names like:
- "ChatGPT Connector for yt-mcp"
- "Test MCP Client"

## Troubleshooting

### Issue: ChatGPT Can't Register

**Check**:
1. Verify registration endpoint is in OIDC config
2. Check Auth0 logs for DCR errors
3. Ensure OIDC Conformant is enabled

### Issue: Users Can't Log In

**Check**:
1. Database/Social connections enabled for new apps
2. At least one login method is available
3. Check Auth0 logs for authentication errors

### Issue: Token Validation Fails

**Check**:
1. Token audience matches `AUTH0_AUDIENCE`
2. Token not expired
3. JWKS URL is accessible
4. Check MCP server logs for verification errors

## References

- [Auth0 Dynamic Client Registration](https://auth0.com/docs/get-started/applications/dynamic-client-registration)
- [RFC 7591 - OAuth 2.0 Dynamic Client Registration](https://datatracker.ietf.org/doc/html/rfc7591)
- [RFC 8414 - OAuth 2.0 Authorization Server Metadata](https://datatracker.ietf.org/doc/html/rfc8414)
