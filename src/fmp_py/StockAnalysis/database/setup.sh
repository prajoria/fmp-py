#!/bin/bash
# FMP Cache Database Setup Script
# This script sets up MySQL database for FMP API caching

set -e

echo "==================================="
echo "FMP Cache Database Setup"
echo "==================================="

# Configuration
DB_NAME="fmp_cache"
DB_USER="${FMP_DB_USER:-fmp_user}"
DB_PASSWORD="${FMP_DB_PASSWORD:-fmp_password}"
DB_HOST="${FMP_DB_HOST:-localhost}"
DB_PORT="${FMP_DB_PORT:-3306}"
MYSQL_ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD}"

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo ""
echo "Database Configuration:"
echo "  Host: $DB_HOST"
echo "  Port: $DB_PORT"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo ""

# Check if MySQL is installed
if ! command -v mysql &> /dev/null; then
    echo "ERROR: MySQL client not found. Please install MySQL first."
    echo ""
    echo "Ubuntu/Debian: sudo apt-get install mysql-client"
    echo "RHEL/CentOS: sudo yum install mysql"
    echo "macOS: brew install mysql-client"
    exit 1
fi

# Check MySQL connection
echo "Checking MySQL connection..."
if ! mysql -h "$DB_HOST" -P "$DB_PORT" -u root -p"${MYSQL_ROOT_PASSWORD}" -e "SELECT 1" &> /dev/null; then
    echo "ERROR: Cannot connect to MySQL server."
    echo "Please ensure MySQL is running and root password is correct."
    echo ""
    echo "You can set MYSQL_ROOT_PASSWORD environment variable or enter it when prompted."
    exit 1
fi

echo "✓ MySQL connection successful"
echo ""

# Create database and user
echo "Creating database and user..."
mysql -h "$DB_HOST" -P "$DB_PORT" -u root -p"${MYSQL_ROOT_PASSWORD}" <<EOF
-- Create database
DROP DATABASE IF EXISTS ${DB_NAME};
CREATE DATABASE ${DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create user and grant privileges
DROP USER IF EXISTS '${DB_USER}'@'localhost';
DROP USER IF EXISTS '${DB_USER}'@'%';
CREATE USER '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';
CREATE USER '${DB_USER}'@'%' IDENTIFIED BY '${DB_PASSWORD}';

GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'localhost';
GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'%';
FLUSH PRIVILEGES;

USE ${DB_NAME};
SELECT 'Database and user created successfully' AS status;
EOF

echo "✓ Database and user created"
echo ""

# Import schema
echo "Importing database schema..."
mysql -h "$DB_HOST" -P "$DB_PORT" -u root -p"${MYSQL_ROOT_PASSWORD}" "${DB_NAME}" < "${SCRIPT_DIR}/schema.sql"
echo "✓ Schema imported successfully"
echo ""

# Verify installation
echo "Verifying installation..."
TABLE_COUNT=$(mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"${DB_PASSWORD}" "${DB_NAME}" -sN -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '${DB_NAME}'")
echo "✓ Database created with ${TABLE_COUNT} tables"
echo ""

# Create .env file if it doesn't exist
ENV_FILE="${SCRIPT_DIR}/../.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "Creating .env file..."
    cat > "$ENV_FILE" <<EOF
# FMP API Configuration
FMP_API_KEY=your_api_key_here

# Database Configuration
FMP_DB_HOST=${DB_HOST}
FMP_DB_PORT=${DB_PORT}
FMP_DB_NAME=${DB_NAME}
FMP_DB_USER=${DB_USER}
FMP_DB_PASSWORD=${DB_PASSWORD}

# Cache Configuration
FMP_CACHE_ENABLED=true
FMP_CACHE_TTL_QUOTE=300
FMP_CACHE_TTL_PROFILE=86400
FMP_CACHE_TTL_HISTORICAL=3600
FMP_CACHE_TTL_FINANCIALS=86400
FMP_CACHE_TTL_NEWS=1800
EOF
    echo "✓ .env file created at ${ENV_FILE}"
    echo "  Please update FMP_API_KEY with your actual API key"
else
    echo "✓ .env file already exists at ${ENV_FILE}"
fi

echo ""
echo "==================================="
echo "Setup Complete!"
echo "==================================="
echo ""
echo "Database Connection Details:"
echo "  mysql -h ${DB_HOST} -P ${DB_PORT} -u ${DB_USER} -p${DB_PASSWORD} ${DB_NAME}"
echo ""
echo "Next Steps:"
echo "1. Update your FMP_API_KEY in ${ENV_FILE}"
echo "2. Install Python dependencies: pip install mysql-connector-python python-dotenv"
echo "3. Use the database module in your Python code"
echo ""
