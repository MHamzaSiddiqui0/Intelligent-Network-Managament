import os
from datetime import timedelta

class Config:
    """Application configuration"""
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///network_management.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Log Summarization Settings
    LOG_SUMMARY_TIME_WINDOW = timedelta(hours=1)
    LOG_ANOMALY_THRESHOLD = 2.5  # Standard deviations for anomaly detection
    MAX_SUMMARY_EVENTS = 10
    
    # Alert Classification Settings
    ALERT_SEVERITY_LEVELS = ['low', 'medium', 'high', 'critical']
    ALERT_CATEGORIES = ['network', 'security', 'performance', 'system', 'application']
    AUTO_ACK_THRESHOLD = 0.3  # Below this priority score, auto-acknowledge
    
    # ChatOps Settings
    CHAT_HISTORY_LIMIT = 100
    COMMAND_TIMEOUT = 30  # seconds
    
    # Application Settings
    DEBUG = True
    TESTING = False
