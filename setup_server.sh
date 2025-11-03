#!/bin/bash
# Setup script for QuantifyMeteringSystem on Ubuntu server

echo "=========================================="
echo "QuantifyMeteringSystem - Server Setup"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "⚠️  Please run as root or with sudo"
    exit 1
fi

# Set working directory
cd /opt/QuantifyMeteringSystem

echo "📦 Step 1: Installing system dependencies..."
apt-get update
apt-get install -y python3-pip python3-venv python3-dev libpq-dev

echo ""
echo "🐍 Step 2: Creating Python virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

echo ""
echo "📚 Step 3: Installing Python dependencies..."
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "🔧 Step 4: Checking .env file..."
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cat > .env << 'EOF'
SECRET_KEY=ilovequantifymetering94t253
DATABASE_URL=postgresql+psycopg2://admin:a3OH72lD4tl8@localhost:5432/quantify
EOF
    echo "✅ .env file created"
else
    echo "✅ .env file exists"
    cat .env
fi

echo ""
echo "🗄️  Step 5: Setting up database..."
read -p "Do you want to apply database migration now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Applying migration..."
    python migrations/add_lorawan_fields.py
fi

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Register your LoRaWAN device (24e124136f215917) in the database"
echo "2. Set up systemd service (optional)"
echo "3. Start the application"
echo ""
echo "To run manually:"
echo "  cd /opt/QuantifyMeteringSystem"
echo "  source .venv/bin/activate"
echo "  python application.py"
echo ""
