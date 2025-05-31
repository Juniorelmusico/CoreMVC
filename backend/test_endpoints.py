#!/usr/bin/env python
"""
Script de diagnóstico para probar endpoints de la API
"""
import requests
import json

# Tu token de authorization
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQ4ODEzNjE3LCJpYXQiOjE3NDg3MjcyMTcsImp0aSI6IjkyODE4NDIzZTViNTRmODBiYWU2YjE3ZGVlY2Y1OWU3IiwidXNlcl9pZCI6MTgsInVzZXJuYW1lIjoiYXJtaW4iLCJpc19zdXBlcnVzZXIiOnRydWUsImVtYWlsIjoiYXJtaW5AZ21haWwuY29tIn0.DEUDpfn1FqfMFrp6yUGvJO1SO5jRcbXUGvcHdYD0hy8"

BASE_URL = "http://localhost:8000/api"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def test_endpoint(url, description):
    print(f"\n🧪 Testing: {description}")
    print(f"URL: {url}")
    try:
        response = requests.get(url, headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ SUCCESS: {response.json()}")
        else:
            print(f"❌ FAILED: {response.text}")
    except Exception as e:
        print(f"💥 ERROR: {str(e)}")

# Tests de endpoints
print("🔍 DIAGNÓSTICO DE ENDPOINTS DE API")
print("=" * 50)

# 1. Test sin autenticación
test_endpoint(f"{BASE_URL}/test-no-auth/", "Endpoint sin autenticación")

# 2. Test con autenticación
test_endpoint(f"{BASE_URL}/test-auth/", "Endpoint con autenticación")

# 3. Lista de tracks
test_endpoint(f"{BASE_URL}/tracks/", "Lista de tracks")

# 4. Endpoints de prueba específicos para track 50
test_endpoint(f"{BASE_URL}/tracks/50/simple-test/", "Simple test para track 50")
test_endpoint(f"{BASE_URL}/tracks/50/test-endpoint/", "Test endpoint para track 50")

# 5. El endpoint problemático
test_endpoint(f"{BASE_URL}/tracks/50/analysis/", "ANÁLISIS para track 50 (PROBLEMÁTICO)")

print("\n" + "=" * 50)
print("🏁 DIAGNÓSTICO COMPLETADO") 