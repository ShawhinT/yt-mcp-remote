#!/bin/bash
# Test Auth0 Dynamic Client Registration
# This script tests that Auth0's DCR endpoint is working

set -e

AUTH0_DOMAIN="dev-x1k2ea1lh5dffa3a.us.auth0.com"
REGISTRATION_ENDPOINT="https://${AUTH0_DOMAIN}/oidc/register"

echo "======================================"
echo "Testing Auth0 Dynamic Client Registration"
echo "======================================"
echo ""

echo "1. Testing OIDC Discovery Endpoint..."
curl -s "https://${AUTH0_DOMAIN}/.well-known/openid-configuration" | \
  python3 -c "import sys, json; data = json.load(sys.stdin); print('✅ Issuer:', data['issuer']); print('✅ Registration Endpoint:', data.get('registration_endpoint', 'NOT FOUND')); print('✅ Authorization Endpoint:', data['authorization_endpoint']); print('✅ Token Endpoint:', data['token_endpoint'])"

echo ""
echo "2. Attempting Dynamic Client Registration..."
echo "   (This will create a test client in Auth0)"

RESPONSE=$(curl -s -X POST "${REGISTRATION_ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Test MCP Client - '"$(date +%s)"'",
    "redirect_uris": ["https://example.com/callback"],
    "grant_types": ["authorization_code"],
    "response_types": ["code"],
    "token_endpoint_auth_method": "client_secret_post"
  }')

echo ""
if echo "$RESPONSE" | grep -q "client_id"; then
  echo "✅ Dynamic Client Registration SUCCESSFUL!"
  echo ""
  echo "$RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print('Client ID:', data['client_id']); print('Client Name:', data.get('client_name', 'N/A')); print('Client Secret:', data['client_secret'][:20] + '...' if 'client_secret' in data else 'N/A')"
  echo ""
  echo "⚠️  Note: This test client was created in your Auth0 tenant."
  echo "   You can delete it from: Applications > Applications > Test MCP Client"
else
  echo "❌ Dynamic Client Registration FAILED"
  echo ""
  echo "Response:"
  echo "$RESPONSE"
  echo ""
  echo "Possible issues:"
  echo "- DCR may not be enabled in Auth0 API settings"
  echo "- Tenant may not be OIDC Conformant"
  echo "- Check Auth0 dashboard: Applications > APIs > Settings"
fi

echo ""
echo "======================================"
echo "Test Complete"
echo "======================================"
