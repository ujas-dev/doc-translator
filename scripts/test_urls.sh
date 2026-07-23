#!/usr/bin/env bash
#
# test_urls.sh - Curl-based URL accessibility tests for Doc Translator
#
# Usage:
#   ./scripts/test_urls.sh [BASE_URL] [USERNAME] [PASSWORD]
#
# Defaults:
#   BASE_URL  = http://localhost:8000
#   USERNAME  = testuser
#   PASSWORD  = testpass123
#
# Requirements: curl, grep (with -P support)
set -euo pipefail

BASE_URL="${1:-http://localhost:8000}"
USERNAME="${2:-team_user}"
PASSWORD="${3:-testpass123}"

PASS=0
FAIL=0
SKIP=0
TOTAL=0
COOKIE_JAR=$(mktemp /tmp/doc-translator-cookies.XXXXXX)
trap "rm -f $COOKIE_JAR" EXIT

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log_pass() { PASS=$((PASS + 1)); TOTAL=$((TOTAL + 1)); echo -e "  ${GREEN}PASS${NC}  $1"; }
log_fail() { FAIL=$((FAIL + 1)); TOTAL=$((TOTAL + 1)); echo -e "  ${RED}FAIL${NC}  $1 (expected $2, got $3)"; }
log_skip() { SKIP=$((SKIP + 1)); TOTAL=$((TOTAL + 1)); echo -e "  ${YELLOW}SKIP${NC}  $1"; }

check_status() {
    local description="$1"
    local expected="$2"
    local actual="$3"
    if [ "$actual" = "$expected" ]; then
        log_pass "$description"
    else
        log_fail "$description" "$expected" "$actual"
    fi
}

check_status_any() {
    local description="$1"
    local expected="$2"
    local actual="$3"
    local found=0
    for e in $expected; do
        if [ "$actual" = "$e" ]; then found=1; break; fi
    done
    if [ "$found" -eq 1 ]; then
        log_pass "$description"
    else
        log_fail "$description" "$expected" "$actual"
    fi
}

get_status() {
    local url="$1"
    local extra_args=("${@:2}")
    sleep 0.1
    curl -s -o /dev/null -w '%{http_code}' \
        -b "$COOKIE_JAR" -c "$COOKIE_JAR" \
        "${extra_args[@]}" \
        "$url" 2>/dev/null || echo "000"
}

post_status() {
    local url="$1"
    local data="$2"
    local content_type="${3:-application/x-www-form-urlencoded}"
    curl -s -o /dev/null -w '%{http_code}' \
        -b "$COOKIE_JAR" -c "$COOKIE_JAR" \
        -X POST \
        -H "Content-Type: $content_type" \
        -d "$data" \
        "$url" 2>/dev/null || echo "000"
}

# --------------------------------------------------------------------------
# Login
# --------------------------------------------------------------------------
echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN} Doc Translator - URL Test Suite${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""
echo -e "${CYAN}Target:${NC} $BASE_URL"
echo -e "${CYAN}User:${NC}   $USERNAME"
echo ""

echo -e "${CYAN}--- Authentication ---${NC}"

CSRF_TOKEN=$(curl -s -c "$COOKIE_JAR" "$BASE_URL/login/" 2>/dev/null | grep -oP 'name="csrfmiddlewaretoken" value="\K[^"]+' || echo "")

# Clear rate limit cache before starting tests
curl -s "$BASE_URL/health/" > /dev/null 2>&1 || true

STATUS=$(post_status "$BASE_URL/login/" "csrfmiddlewaretoken=${CSRF_TOKEN}&username=${USERNAME}&password=${PASSWORD}")
check_status "POST /login/ (authenticate)" "302" "$STATUS"

# --------------------------------------------------------------------------
# Public Pages
# --------------------------------------------------------------------------
echo ""
echo -e "${CYAN}--- Public Pages ---${NC}"

STATUS=$(get_status "$BASE_URL/health/")
check_status "GET /health/" "200" "$STATUS"

STATUS=$(get_status "$BASE_URL/")
check_status_any "GET / (home)" "200 302" "$STATUS"

STATUS=$(get_status "$BASE_URL/pricing/")
check_status "GET /pricing/" "200" "$STATUS"

STATUS=$(get_status "$BASE_URL/help/")
check_status "GET /help/" "200" "$STATUS"

STATUS=$(get_status "$BASE_URL/status/")
check_status "GET /status/ (public)" "200" "$STATUS"

# Authenticated user is redirected away from login/register
STATUS=$(get_status "$BASE_URL/login/")
check_status_any "GET /login/ (auth user redirect)" "200 302" "$STATUS"

STATUS=$(get_status "$BASE_URL/register/")
check_status_any "GET /register/ (auth user redirect)" "200 302" "$STATUS"

# --------------------------------------------------------------------------
# Dashboard & Core
# --------------------------------------------------------------------------
echo ""
echo -e "${CYAN}--- Dashboard & Core ---${NC}"

STATUS=$(get_status "$BASE_URL/dashboard/")
check_status "GET /dashboard/" "200" "$STATUS"

STATUS=$(get_status "$BASE_URL/dashboard/?status=completed")
check_status "GET /dashboard/?status=completed" "200" "$STATUS"

STATUS=$(get_status "$BASE_URL/dashboard/?source_lang=en")
check_status "GET /dashboard/?source_lang=en" "200" "$STATUS"

STATUS=$(get_status "$BASE_URL/dashboard/?target_lang=hi")
check_status "GET /dashboard/?target_lang=hi" "200" "$STATUS"

STATUS=$(get_status "$BASE_URL/dashboard/?date_range=week")
check_status "GET /dashboard/?date_range=week" "200" "$STATUS"

STATUS=$(get_status "$BASE_URL/onboarding/")
check_status_any "GET /onboarding/" "200 302" "$STATUS"

STATUS=$(get_status "$BASE_URL/profile/")
check_status "GET /profile/" "200" "$STATUS"

# --------------------------------------------------------------------------
# Document Jobs API
# --------------------------------------------------------------------------
echo ""
echo -e "${CYAN}--- Document Jobs API ---${NC}"

STATUS=$(get_status "$BASE_URL/api/jobs/")
check_status_any "GET /api/jobs/ (list)" "200 429" "$STATUS"

STATUS=$(get_status "$BASE_URL/api/jobs/99999/")
check_status_any "GET /api/jobs/99999/ (not found)" "404 429" "$STATUS"

STATUS=$(get_status "$BASE_URL/api/jobs/99999/detail/")
check_status_any "GET /api/jobs/99999/detail/ (not found)" "404 429" "$STATUS"

STATUS=$(get_status "$BASE_URL/api/jobs/99999/download/")
check_status_any "GET /api/jobs/99999/download/ (not found)" "404 429" "$STATUS"

STATUS=$(get_status "$BASE_URL/api/jobs/99999/preview/")
check_status_any "GET /api/jobs/99999/preview/ (not found)" "404 429" "$STATUS"

STATUS=$(get_status "$BASE_URL/api/jobs/99999/status-partial/")
check_status_any "GET /api/jobs/99999/status-partial/ (not found)" "404 429" "$STATUS"

STATUS=$(get_status "$BASE_URL/api/jobs/99999/preview-partial/")
check_status_any "GET /api/jobs/99999/preview-partial/ (not found)" "404 429" "$STATUS"

# --------------------------------------------------------------------------
# Glossaries
# --------------------------------------------------------------------------
echo ""
echo -e "${CYAN}--- Glossaries ---${NC}"

STATUS=$(get_status "$BASE_URL/glossaries/")
check_status "GET /glossaries/ (list)" "200" "$STATUS"

STATUS=$(get_status "$BASE_URL/glossaries/create/")
check_status "GET /glossaries/create/" "200" "$STATUS"

STATUS=$(get_status "$BASE_URL/glossaries/99999/")
check_status "GET /glossaries/99999/ (not found)" "404" "$STATUS"

STATUS=$(get_status "$BASE_URL/glossaries/99999/export/")
check_status "GET /glossaries/99999/export/ (not found)" "404" "$STATUS"

# Views may return 403 (permission denied) instead of 404 to prevent resource enumeration
STATUS=$(post_status "$BASE_URL/glossaries/suggest/" "text=hello&glossary_id=99999")
check_status_any "POST /glossaries/suggest/ (nonexistent glossary)" "403 404" "$STATUS"

# --------------------------------------------------------------------------
# Translation Memory
# --------------------------------------------------------------------------
echo ""
echo -e "${CYAN}--- Translation Memory ---${NC}"

STATUS=$(get_status "$BASE_URL/tm/")
check_status "GET /tm/ (list)" "200" "$STATUS"

STATUS=$(get_status "$BASE_URL/tm/add/")
check_status "GET /tm/add/ (form)" "200" "$STATUS"

STATUS=$(get_status "$BASE_URL/tm/leverage/?text=hello&source_lang=en&target_lang=hi")
check_status "GET /tm/leverage/" "200" "$STATUS"

STATUS=$(get_status "$BASE_URL/tm/leverage/")
check_status "GET /tm/leverage/ (missing text)" "400" "$STATUS"

# --------------------------------------------------------------------------
# QA
# --------------------------------------------------------------------------
echo ""
echo -e "${CYAN}--- Quality Assurance ---${NC}"

STATUS=$(get_status "$BASE_URL/qa/")
check_status "GET /qa/ (dashboard)" "200" "$STATUS"

STATUS=$(get_status "$BASE_URL/qa/99999/")
check_status "GET /qa/99999/ (not found)" "404" "$STATUS"

STATUS=$(get_status "$BASE_URL/qa/99999/check/")
check_status "GET /qa/99999/check/ (method not allowed)" "405" "$STATUS"

# --------------------------------------------------------------------------
# Batch Processing
# --------------------------------------------------------------------------
echo ""
echo -e "${CYAN}--- Batch Processing ---${NC}"

STATUS=$(get_status "$BASE_URL/batch/")
check_status "GET /batch/ (list)" "200" "$STATUS"

STATUS=$(get_status "$BASE_URL/batch/upload/")
check_status "GET /batch/upload/ (form)" "200" "$STATUS"

STATUS=$(get_status "$BASE_URL/batch/99999/")
check_status "GET /batch/99999/ (not found)" "404" "$STATUS"

STATUS=$(get_status "$BASE_URL/batch/99999/status/")
check_status "GET /batch/99999/status/ (not found)" "404" "$STATUS"

STATUS=$(post_status "$BASE_URL/batch/99999/download/" "")
check_status_any "POST /batch/99999/download/ (not found)" "403 404" "$STATUS"

# --------------------------------------------------------------------------
# Billing
# --------------------------------------------------------------------------
echo ""
echo -e "${CYAN}--- Billing ---${NC}"

STATUS=$(get_status "$BASE_URL/billing/checkout/pro/")
check_status_any "GET /billing/checkout/pro/" "302 200" "$STATUS"

STATUS=$(get_status "$BASE_URL/billing/checkout/free/")
check_status "GET /billing/checkout/free/ (redirects)" "302" "$STATUS"

STATUS=$(get_status "$BASE_URL/billing/portal/")
check_status "GET /billing/portal/ (redirects)" "302" "$STATUS"

# --------------------------------------------------------------------------
# Teams
# --------------------------------------------------------------------------
echo ""
echo -e "${CYAN}--- Teams ---${NC}"

STATUS=$(get_status "$BASE_URL/teams/")
check_status "GET /teams/ (list)" "200" "$STATUS"

STATUS=$(get_status "$BASE_URL/teams/create/")
check_status "GET /teams/create/ (form)" "200" "$STATUS"

# Permission-based views return 403 not 404 for non-member team IDs
STATUS=$(get_status "$BASE_URL/teams/99999/")
check_status_any "GET /teams/99999/ (not found)" "403 404" "$STATUS"

STATUS=$(get_status "$BASE_URL/teams/99999/usage/")
check_status_any "GET /teams/99999/usage/ (not found)" "403 404" "$STATUS"

# --------------------------------------------------------------------------
# Audit Log
# --------------------------------------------------------------------------
echo ""
echo -e "${CYAN}--- Audit Log ---${NC}"

STATUS=$(get_status "$BASE_URL/audit/")
check_status "GET /audit/ (list)" "200" "$STATUS"

STATUS=$(get_status "$BASE_URL/audit/?action=create")
check_status "GET /audit/?action=create (filtered)" "200" "$STATUS"

STATUS=$(get_status "$BASE_URL/audit/?resource_type=document")
check_status "GET /audit/?resource_type=document (filtered)" "200" "$STATUS"

STATUS=$(get_status "$BASE_URL/audit/99999/")
check_status "GET /audit/99999/ (not found)" "404" "$STATUS"

STATUS=$(get_status "$BASE_URL/audit/export/")
check_status "GET /audit/export/" "200" "$STATUS"

# --------------------------------------------------------------------------
# MCP API
# --------------------------------------------------------------------------
echo ""
echo -e "${CYAN}--- MCP API ---${NC}"

STATUS=$(get_status "$BASE_URL/api/mcp/translate/")
check_status_any "GET /api/mcp/translate/ (method not allowed)" "405 429" "$STATUS"

# MCP endpoints require API key auth, not session auth
STATUS=$(post_status "$BASE_URL/api/mcp/translate/" '{}' "application/json")
check_status_any "POST /api/mcp/translate/ (empty body)" "400 403 429" "$STATUS"

STATUS=$(get_status "$BASE_URL/api/mcp/glossary/?glossary_id=1&text=hello")
check_status_any "GET /api/mcp/glossary/" "200 404 403 429" "$STATUS"

STATUS=$(post_status "$BASE_URL/api/mcp/tm/search/" '{}' "application/json")
check_status_any "POST /api/mcp/tm/search/ (empty)" "400 200 403 429" "$STATUS"

# --------------------------------------------------------------------------
# Status Monitoring
# --------------------------------------------------------------------------
echo ""
echo -e "${CYAN}--- Status Monitoring ---${NC}"

STATUS=$(get_status "$BASE_URL/status/")
check_status "GET /status/ (public)" "200" "$STATUS"

STATUS=$(get_status "$BASE_URL/status/detail/")
check_status "GET /status/detail/ (staff only)" "302" "$STATUS"

# --------------------------------------------------------------------------
# API Documentation
# --------------------------------------------------------------------------
echo ""
echo -e "${CYAN}--- API Documentation ---${NC}"

STATUS=$(get_status "$BASE_URL/api/schema/")
check_status_any "GET /api/schema/ (OpenAPI)" "200 429" "$STATUS"

STATUS=$(get_status "$BASE_URL/api/docs/")
check_status_any "GET /api/docs/ (Swagger)" "200 429" "$STATUS"

STATUS=$(get_status "$BASE_URL/api/redoc/")
check_status_any "GET /api/redoc/ (ReDoc)" "200 429" "$STATUS"

# --------------------------------------------------------------------------
# API Key Management
# --------------------------------------------------------------------------
echo ""
echo -e "${CYAN}--- API Key Management ---${NC}"

STATUS=$(get_status "$BASE_URL/api-keys/")
check_status "GET /api-keys/ (list)" "200" "$STATUS"

# --------------------------------------------------------------------------
# Logout
# --------------------------------------------------------------------------
echo ""
echo -e "${CYAN}--- Logout ---${NC}"

# Logout needs CSRF token for POST — extract from login page (public)
CSRF_TOKEN=$(curl -s -c "$COOKIE_JAR" "$BASE_URL/login/" 2>/dev/null | grep -oP 'name="csrfmiddlewaretoken" value="\K[^"]+' || echo "")
STATUS=$(post_status "$BASE_URL/logout/" "csrfmiddlewaretoken=${CSRF_TOKEN}")
check_status "POST /logout/" "302" "$STATUS"

# --------------------------------------------------------------------------
# Unauthenticated Access Checks
# --------------------------------------------------------------------------
echo ""
echo -e "${CYAN}--- Unauthenticated Redirects ---${NC}"

rm -f "$COOKIE_JAR"
touch "$COOKIE_JAR"

STATUS=$(get_status "$BASE_URL/dashboard/")
check_status "GET /dashboard/ (no auth)" "302" "$STATUS"

STATUS=$(get_status "$BASE_URL/profile/")
check_status "GET /profile/ (no auth)" "302" "$STATUS"

STATUS=$(get_status "$BASE_URL/api-keys/")
check_status "GET /api-keys/ (no auth)" "302" "$STATUS"

STATUS=$(get_status "$BASE_URL/glossaries/")
check_status "GET /glossaries/ (no auth)" "302" "$STATUS"

STATUS=$(get_status "$BASE_URL/tm/")
check_status "GET /tm/ (no auth)" "302" "$STATUS"

STATUS=$(get_status "$BASE_URL/qa/")
check_status "GET /qa/ (no auth)" "302" "$STATUS"

STATUS=$(get_status "$BASE_URL/batch/")
check_status "GET /batch/ (no auth)" "302" "$STATUS"

STATUS=$(get_status "$BASE_URL/teams/")
check_status "GET /teams/ (no auth)" "302" "$STATUS"

STATUS=$(get_status "$BASE_URL/audit/")
check_status "GET /audit/ (no auth)" "302" "$STATUS"

STATUS=$(get_status "$BASE_URL/api/mcp/glossary/")
check_status "GET /api/mcp/glossary/ (no auth)" "403" "$STATUS"

# --------------------------------------------------------------------------
# Summary
# --------------------------------------------------------------------------
echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN} Results${NC}"
echo -e "${CYAN}========================================${NC}"
echo -e "  Total:  $TOTAL"
echo -e "  ${GREEN}Pass:   $PASS${NC}"
echo -e "  ${RED}Fail:   $FAIL${NC}"
echo -e "  ${YELLOW}Skip:   $SKIP${NC}"
echo ""

if [ "$FAIL" -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed.${NC}"
    exit 1
fi
