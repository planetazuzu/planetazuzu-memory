const fs = require('fs');
const path = require('path');
const config = require('../config');

class Alerter {
  constructor() {
    this.lastAlert = {};
    this.cooldown = config.intervals.alertCooldown;
  }

  shouldAlert(type) {
    const now = Date.now();
    const last = this.lastAlert[type] || 0;
    if (now - last >= this.cooldown) {
      this.lastAlert[type] = now;
      return true;
    }
    return false;
  }

  evaluateMetrics(metrics) {
    const alerts = [];

    if (metrics.cpu.current > config.thresholds.cpu) {
      const type = `cpu_high_${metrics.cpu.current}`;
      if (this.shouldAlert(type)) {
        alerts.push({
          type: 'CPU',
          severity: 'warning',
          message: `CPU usage is at ${metrics.cpu.current}% (threshold: ${config.thresholds.cpu}%)`,
          value: metrics.cpu.current,
          threshold: config.thresholds.cpu,
        });
      }
    }

    if (metrics.memory.percent > config.thresholds.memory) {
      const type = `memory_high_${metrics.memory.percent}`;
      if (this.shouldAlert(type)) {
        const usedGB = (metrics.memory.used / (1024 * 1024 * 1024)).toFixed(2);
        const totalGB = (metrics.memory.total / (1024 * 1024 * 1024)).toFixed(2);
        alerts.push({
          type: 'Memory',
          severity: 'warning',
          message: `Memory usage is at ${metrics.memory.percent}% (${usedGB}/${totalGB} GB)`,
          value: metrics.memory.percent,
          threshold: config.thresholds.memory,
        });
      }
    }

    for (const disk of metrics.disk) {
      if (disk.percent > config.thresholds.disk) {
        const type = `disk_high_${disk.mount}_${disk.percent}`;
        if (this.shouldAlert(type)) {
          alerts.push({
            type: 'Disk',
            severity: 'warning',
            message: `Disk ${disk.mount} is at ${disk.percent}% (threshold: ${config.thresholds.disk}%)`,
            value: disk.percent,
            threshold: config.thresholds.disk,
            mount: disk.mount,
          });
        }
      }
    }

    if (metrics.swap.percent > config.thresholds.swap) {
      const type = `swap_high_${metrics.swap.percent}`;
      if (this.shouldAlert(type)) {
        alerts.push({
          type: 'Swap',
          severity: 'info',
          message: `Swap usage is at ${metrics.swap.percent}% (threshold: ${config.thresholds.swap}%)`,
          value: metrics.swap.percent,
          threshold: config.thresholds.swap,
        });
      }
    }

    if (metrics.zombies.zombies > config.thresholds.zombieProcesses) {
      const type = `zombies_high_${metrics.zombies.zombies}`;
      if (this.shouldAlert(type)) {
        alerts.push({
          type: 'Zombie Processes',
          severity: 'warning',
          message: `Found ${metrics.zombies.zombies} zombie processes (threshold: ${config.thresholds.zombieProcesses})`,
          value: metrics.zombies.zombies,
          threshold: config.thresholds.zombieProcesses,
        });
      }
    }

    if (metrics.postgres.available) {
      if (metrics.postgres.connections.percent > config.thresholds.dbConnections) {
        const type = `db_connections_high_${metrics.postgres.connections.percent}`;
        if (this.shouldAlert(type)) {
          alerts.push({
            type: 'PostgreSQL',
            severity: 'warning',
            message: `PostgreSQL connections at ${metrics.postgres.connections.percent}% (${metrics.postgres.connections.current}/${metrics.postgres.connections.max})`,
            value: metrics.postgres.connections.percent,
            threshold: config.thresholds.dbConnections,
          });
        }
      }

      if (metrics.postgres.slowQueries.length > 0) {
        const type = 'slow_queries';
        if (this.shouldAlert(type)) {
          alerts.push({
            type: 'Slow Queries',
            severity: 'warning',
            message: `Found ${metrics.postgres.slowQueries.length} slow queries (>5s)`,
            queries: metrics.postgres.slowQueries.map(q => ({
              pid: q.pid,
              duration: q.duration,
              query: q.query.substring(0, 100),
            })),
          });
        }
      }
    } else if (metrics.postgres.error) {
      const type = 'postgres_down';
      if (this.shouldAlert(type)) {
        alerts.push({
          type: 'PostgreSQL',
          severity: 'critical',
          message: `PostgreSQL is unavailable: ${metrics.postgres.error}`,
        });
      }
    }

    return alerts;
  }

  logAlert(alert) {
    const logEntry = `[${new Date().toISOString()}] [${alert.severity.toUpperCase()}] ${alert.type}: ${alert.message}\n`;
    
    const logDir = path.dirname(config.logFile);
    if (!fs.existsSync(logDir)) {
      fs.mkdirSync(logDir, { recursive: true });
    }
    
    fs.appendFileSync(config.logFile, logEntry);
  }

  isDailyReportTime() {
    const now = new Date();
    return now.getHours() === config.intervals.dailyReportHour && now.getMinutes() === 0;
  }

  formatDailyReport(metrics) {
    let report = `📊 Daily Server Report - ${metrics.timestamp}\n\n`;
    
    report += `🖥️ CPU: ${metrics.cpu.current}%\n`;
    report += `💾 Memory: ${metrics.memory.percent}% (${(metrics.memory.used / 1e9).toFixed(1)}/${(metrics.memory.total / 1e9).toFixed(1)} GB)\n`;
    report += `💿 Disk:\n`;
    for (const disk of metrics.disk) {
      report += `   ${disk.mount}: ${disk.percent}%\n`;
    }
    report += `🔄 Swap: ${metrics.swap.percent}%\n`;
    report += `🧟 Zombies: ${metrics.zombies.zombies}\n`;
    
    if (metrics.postgres.available) {
      report += `🐘 PostgreSQL: ${metrics.postgres.connections.percent}% connections\n`;
    } else {
      report += `🐘 PostgreSQL: DOWN\n`;
    }
    
    report += `🐳 Docker: ${metrics.docker.running} running, ${metrics.docker.stopped} stopped\n`;
    
    return report;
  }
}

module.exports = Alerter;
