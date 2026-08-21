#!/bin/bash
DB_PATH="/home/ubuntu/quant_trading_bot/markov_1.db"
BACKUP_DIR="/home/ubuntu/quant_trading_bot/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

mkdir -p $BACKUP_DIR

# Create a compressed backup copy
sqlite3 $DB_PATH ".backup '$BACKUP_DIR/markov_1_$TIMESTAMP.db'"
gzip "$BACKUP_DIR/markov_1_$TIMESTAMP.db"

# Re-index and reclaim unused storage
sqlite3 $DB_PATH "VACUUM; REINDEX;"

# Keep only the last 14 days of backups
find $BACKUP_DIR -type f -name "*.db.gz" -mtime +14 -exec rm {} \;
