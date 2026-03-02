require('dotenv').config();

const config = {
  thresholds: {
    cpu: parseInt(process.env.THRESHOLD_CPU || '85'),
    memory: parseInt(process.env.THRESHOLD_MEM || '90'),
    disk: parseInt(process.env.THRESHOLD_DISK || '80'),
    swap: parseInt(process.env.THRESHOLD_SWAP || '50'),
    zombieProcesses: parseInt(process.env.THRESHOLD_ZOMBIES || '5'),
    dbConnections: parseInt(process.env.THRESHOLD_DB_CONNECTIONS || '80'),
  },
  intervals: {
    check: parseInt(process.env.CHECK_INTERVAL || '300000'),
    alertCooldown: parseInt(process.env.ALERT_COOLDOWN || '1800000'),
    dailyReportHour: parseInt(process.env.DAILY_REPORT_HOUR || '8'),
  },
  telegram: {
    botToken: process.env.TELEGRAM_BOT_TOKEN,
    chatId: process.env.TELEGRAM_CHAT_ID,
  },
  smtp: {
    host: process.env.SMTP_HOST,
    port: parseInt(process.env.SMTP_PORT || '587'),
    user: process.env.SMTP_USER,
    pass: process.env.SMTP_PASS,
    from: process.env.SMTP_FROM || 'server-monitor@localhost',
  },
  alertEmail: process.env.ALERT_EMAIL,
  database: {
    name: process.env.DB_NAME || 'postgres',
    user: process.env.DB_USER || 'postgres',
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT || '5432'),
  },
  cleanup: {
    autoClean: process.env.AUTO_CLEAN === 'true',
    logsDays: parseInt(process.env.CLEAN_LOGS_DAYS || '30'),
  },
  logFile: process.env.LOG_FILE || '/var/log/server-monitor/alerts.log',
};

module.exports = config;
