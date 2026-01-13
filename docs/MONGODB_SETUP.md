# MongoDB Setup for macOS

## Quick Installation

### 1. Install MongoDB Community Edition
```bash
# Add MongoDB tap to Homebrew
brew tap mongodb/brew

# Install MongoDB
brew install mongodb-community
```

### 2. Start MongoDB
```bash
# Start MongoDB service (runs in background)
brew services start mongodb/brew/mongodb-community

# Or start manually for this session only
mongod --config /opt/homebrew/etc/mongod.conf
```

### 3. Verify Installation
```bash
# Connect to MongoDB shell
mongosh

# You should see:
# Current Mongosh Log ID: ...
# Connecting to: mongodb://127.0.0.1:27017/
```

### 4. Install Python Driver
```bash
pip install pymongo
```

## Test Your Setup

### 1. Test MongoDB Connection
```bash
# In terminal, run:
python -c "from pymongo import MongoClient; print('MongoDB connection:', MongoClient().admin.command('ping'))"

# Should output: MongoDB connection: {'ok': 1.0}
```

### 2. Test Pipeline Log System
```bash
cd src/
python mongo_query.py setup
```

## MongoDB Configuration

### Default Settings
- **Host**: localhost
- **Port**: 27017
- **Data Directory**: `/opt/homebrew/var/mongodb`
- **Log File**: `/opt/homebrew/var/log/mongodb/mongo.log`
- **Config File**: `/opt/homebrew/etc/mongod.conf`

### Check Status
```bash
# Check if MongoDB is running
brew services list | grep mongodb

# View MongoDB logs
tail -f /opt/homebrew/var/log/mongodb/mongo.log
```

## Troubleshooting

### MongoDB Won't Start
```bash
# Check permissions
sudo chown -R $(whoami) /opt/homebrew/var/mongodb
sudo chown -R $(whoami) /opt/homebrew/var/log/mongodb

# Restart service
brew services restart mongodb/brew/mongodb-community
```

### Connection Issues
```bash
# Check if MongoDB is listening
lsof -i :27017

# Test connection
mongosh --eval "db.adminCommand('ping')"
```

### Reset MongoDB (if needed)
```bash
# Stop MongoDB
brew services stop mongodb/brew/mongodb-community

# Remove data (WARNING: deletes all data)
rm -rf /opt/homebrew/var/mongodb/*

# Start MongoDB
brew services start mongodb/brew/mongodb-community
```

## MongoDB Compass (GUI - Optional)

### Install MongoDB Compass
```bash
brew install --cask mongodb-compass
```

### Connect to Local MongoDB
- Open MongoDB Compass
- Connection String: `mongodb://localhost:27017`
- Click "Connect"

## Usage with Pipeline Logs

### 1. Setup and Ingest Logs
```bash
cd src/
python mongo_query.py setup
```

### 2. Query Examples
```bash
# Search for critical issues
python mongo_query.py search "CRITICAL"

# View specific run
python mongo_query.py run YOUR_RUN_ID

# Show failed validations
python mongo_query.py failed --days 7

# Pipeline statistics
python mongo_query.py stats --days 30
```

### 3. Direct MongoDB Queries
```bash
# Connect to MongoDB shell
mongosh pipeline_logs

# Example queries
db.logs.find({"log_type": "validation_report"}).limit(5)
db.logs.find({"content.severity": "CRITICAL"})
db.pipeline_runs.find().sort({"ingested_at": -1}).limit(10)
```

## Auto-Start MongoDB (Optional)

To start MongoDB automatically on system boot:
```bash
# Enable auto-start
brew services start mongodb/brew/mongodb-community

# Disable auto-start
brew services stop mongodb/brew/mongodb-community
```

## Uninstall (if needed)

```bash
# Stop MongoDB
brew services stop mongodb/brew/mongodb-community

# Uninstall
brew uninstall mongodb-community

# Remove data directories
rm -rf /opt/homebrew/var/mongodb
rm -rf /opt/homebrew/var/log/mongodb
```

## Next Steps

Once MongoDB is running:
1. Run `python mongo_query.py setup` to initialize the log system
2. Run your pipeline with `python batch_load.py` 
3. Query logs with `python mongo_query.py search "term"`

Your pipeline logs will be automatically stored in MongoDB for powerful querying and analysis!