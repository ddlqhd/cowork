#!/bin/bash

# WebSocket SSE Server - Comprehensive API Test Script
# This script tests all endpoints of the WebSocket SSE Server

SERVER_URL="http://localhost:8080"
TEST_USER_ID="test_user_$(date +%s)"

echo "==========================================="
echo "WebSocket SSE Server - API Test Suite"
echo "Server: $SERVER_URL"
echo "Test User ID: $TEST_USER_ID"
echo "==========================================="

# Function to print section header
print_section() {
    echo
    echo "==========================================="
    echo "$1"
    echo "==========================================="
}

# Function to make API call and display result
api_call() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4
    
    echo
    echo "Testing: $description"
    echo "Endpoint: $method $SERVER_URL$endpoint"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -o response_body.txt -w "%{http_code}" "$SERVER_URL$endpoint")
    elif [ "$method" = "POST" ]; then
        if [ -z "$data" ]; then
            response=$(curl -s -o response_body.txt -w "%{http_code}" -X POST -H "Content-Type: application/json" "$SERVER_URL$endpoint")
        else
            response=$(curl -s -o response_body.txt -w "%{http_code}" -X POST -H "Content-Type: application/json" -d "$data" "$SERVER_URL$endpoint")
        fi
    fi
    
    status_code=${response: -3}
    response_body=$(cat response_body.txt)
    
    echo "Status Code: $status_code"
    echo "Response Body:"
    echo "$response_body" | jq . 2>/dev/null || echo "$response_body"
    echo
}

# Wait for server to be ready
wait_for_server() {
    echo "Waiting for server to be ready..."
    for i in {1..10}; do
        if curl -s "$SERVER_URL/health" > /dev/null 2>&1; then
            echo "Server is ready!"
            return 0
        fi
        echo "Attempt $i: Server not ready, waiting..."
        sleep 2
    done
    echo "ERROR: Server did not become ready within timeout period"
    exit 1
}

# Test Health Endpoint
print_section "Testing Health Endpoint"
api_call "GET" "/health" "" "Health Check"

# Test Metrics Endpoint
print_section "Testing Metrics Endpoint"
api_call "GET" "/metrics" "" "Metrics Check"

# Test SSE Push Endpoint
print_section "Testing SSE Push Endpoint"
SSE_PUSH_DATA="{
    \"user_id\": \"$TEST_USER_ID\",
    \"data\": {
        \"message\": \"Hello from SSE push test\",
        \"type\": \"test\",
        \"timestamp\": $(date +%s)
    },
    \"event_type\": \"message\"
}"
api_call "POST" "/sse/push" "$SSE_PUSH_DATA" "SSE Push Message"

# Test SSE Push with invalid data
print_section "Testing SSE Push with Invalid Data"
INVALID_DATA="{\"invalid\": \"data\"}"
api_call "POST" "/sse/push" "$INVALID_DATA" "SSE Push with Invalid Data (should fail)"

# Test SSE Send Endpoint (Request-Response)
print_section "Testing SSE Send Endpoint (Request-Response)"
SSE_SEND_DATA="{
    \"user_id\": \"$TEST_USER_ID\",
    \"data\": {
        \"message\": \"Hello from SSE send test\",
        \"type\": \"request\",
        \"correlation_id\": \"corr_$(date +%s)\"
    },
    \"event_type\": \"message\"
}"
api_call "POST" "/sse/send" "$SSE_SEND_DATA" "SSE Send Message (Request-Response)"

# Test SSE Batch Push Endpoint
print_section "Testing SSE Batch Push Endpoint"
SSE_BATCH_DATA="[
    {
        \"user_id\": \"$TEST_USER_ID\_batch1\",
        \"data\": {
            \"message\": \"Batch message 1\",
            \"type\": \"test\"
        }
    },
    {
        \"user_id\": \"$TEST_USER_ID\_batch2\",
        \"data\": {
            \"message\": \"Batch message 2\",
            \"type\": \"test\"
        }
    }
]"
api_call "POST" "/sse/push/batch" "$SSE_BATCH_DATA" "SSE Batch Push Messages"

# Test SSE Batch Push with invalid data
print_section "Testing SSE Batch Push with Invalid Data"
INVALID_BATCH_DATA="[{\"invalid\": \"data\"}]"
api_call "POST" "/sse/push/batch" "$INVALID_BATCH_DATA" "SSE Batch Push with Invalid Data (should fail)"

# Test all endpoints with empty body to check error handling
print_section "Testing Error Handling - Empty Bodies"

# Test SSE Push with empty body
api_call "POST" "/sse/push" "{}" "SSE Push with Empty Body (should fail)"

# Test SSE Send with empty body
api_call "POST" "/sse/send" "{}" "SSE Send with Empty Body (should fail)"

# Test SSE Batch Push with empty array
api_call "POST" "/sse/push/batch" "[]" "SSE Batch Push with Empty Array"

# Summary
print_section "Test Summary"
echo "API Test Suite Completed!"
echo "Note: Some tests may show 'User not connected' which is expected if no WebSocket client is connected."
echo "Check the server logs for more detailed information about WebSocket connections."

# Cleanup
rm -f response_body.txt

echo
echo "==========================================="
echo "Test completed. Server endpoints tested:"
echo "- GET /health"
echo "- GET /metrics" 
echo "- POST /sse/push"
echo "- POST /sse/send"
echo "- POST /sse/push/batch"
echo "==========================================="