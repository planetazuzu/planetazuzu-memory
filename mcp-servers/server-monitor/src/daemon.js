#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const MetricsCollector = require('./monitors/metrics');
const Alerter = require('./monitors/alerter');
const Notifier = require('./notifications/notifier');
const Cleaner = require('./cleaners/cleaner');
const config = require('./config');

class Daemon {
  constructor() {
    this.metricsCollector = new MetricsCollector();
    this.alerter = new Alerter();
    this.notifier = new Notifier();
    this.running = false;
    this.intervalId = null;
  }

  async check() {
    try {
      const metrics = await this.metricsCollector.getAllMetrics();
      const alerts = this.alerter.evaluateMetrics(metrics);

      for (const alert of alerts) {
        this.alerter.logAlert(alert);
      }

      await this.notifier.notify(alerts);

      if (config.cleanup.autoClean && Math.random() < 0.02) {
        const cleaner = new Cleaner(false);
        await cleaner.cleanAll();
      }

      return { metrics, alerts };
    } catch (err) {
      console.error('Check error:', err);
      return { error: err.message };
    }
  }

  async dailyReport() {
    try {
      const metrics = await this.metricsCollector.getAllMetrics();
      const report = this.alerter.formatDailyReport(metrics);
      await this.notifier.notifier.sendTelegram(report);
      return { success: true };
    } catch (err) {
      console.error('Daily report error:', err);
      return { error: err.message };
    }
  }

  start() {
    if (this.running) {
      console.log('Daemon already running');
      return;
    }

    const logDir = path.dirname(config.logFile);
    if (!fs.existsSync(logDir)) {
      fs.mkdirSync(logDir, { recursive: true });
    }

    this.running = true;
    console.log(`Server Monitor Daemon starting...`);
    console.log(`Check interval: ${config.intervals.check / 1000}s`);
    console.log(`Log file: ${config.logFile}`);

    this.check();

    this.intervalId = setInterval(async () => {
      const now = new Date();
      
      if (now.getMinutes() === 0) {
        const metrics = await this.metricsCollector.getAllMetrics();
        const report = this.alerter.formatDailyReport(metrics);
        await this.notifier.sendTelegram(report);
      }

      await this.check();
    }, config.intervals.check);

    process.on('SIGTERM', () => this.stop());
    process.on('SIGINT', () => this.stop());
  }

  stop() {
    if (!this.running) return;
    
    this.running = false;
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
    this.metricsCollector.destroy();
    console.log('Server Monitor Daemon stopped');
    process.exit(0);
  }
}

if (require.main === module) {
  const daemon = new Daemon();
  daemon.start();
}

module.exports = Daemon;
