const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');
const config = require('../config');

class Cleaner {
  constructor(dryRun = true) {
    this.dryRun = dryRun;
    this.actions = [];
  }

  async runCommand(cmd, description) {
    if (this.dryRun) {
      this.actions.push({ type: 'dry-run', cmd, description, status: 'would execute' });
      return { dryRun: true, cmd, description };
    }

    return new Promise((resolve) => {
      exec(cmd, { timeout: 300000 }, (error, stdout, stderr) => {
        const result = {
          cmd,
          description,
          success: !error,
          error: error ? error.message : null,
          stdout: stdout.trim(),
          stderr: stderr.trim(),
        };
        this.actions.push({ ...result, status: 'executed' });
        resolve(result);
      });
    });
  }

  async cleanOldLogs() {
    const results = [];
    const days = config.cleanup.logsDays;
    const logPaths = [
      '/var/log/syslog',
      '/var/log/auth.log',
      '/var/log/nginx',
      '/var/log/apache2',
    ];

    for (const logPath of logPaths) {
      if (fs.existsSync(logPath)) {
        const cmd = `find ${logPath} -type f -name "*.gz" -mtime +${days} -delete 2>/dev/null || true`;
        results.push(await this.runCommand(cmd, `Clean logs older than ${days} days in ${logPath}`));
      }
    }

    return results;
  }

  async cleanAptCache() {
    const cmd = 'apt-get clean && rm -rf /var/cache/apt/archives/*';
    return [await this.runCommand(cmd, 'Clean apt cache')];
  }

  async cleanTmp() {
    const cmd = 'find /tmp -type f -atime +7 -delete 2>/dev/null || true';
    return [await this.runCommand(cmd, 'Clean files in /tmp older than 7 days')];
  }

  async cleanJournal() {
    const cmd = 'journalctl --vacuum-time=30days';
    return [await this.runCommand(cmd, 'Clean journal logs older than 30 days')];
  }

  async cleanZombieProcesses() {
    const cmd = "ps aux | grep '\\[Z\\]' | awk '{print $2}' | xargs -r kill -CHLD 2>/dev/null || true";
    return [await this.runCommand(cmd, 'Send SIGCHLD to zombie process parents')];
  }

  async cleanDocker() {
    const results = [];

    const pruneContainers = 'docker container prune -f';
    results.push(await this.runCommand(pruneContainers, 'Remove stopped containers'));

    const pruneImages = 'docker image prune -f';
    results.push(await this.runCommand(pruneImages, 'Remove unused images'));

    const pruneVolumes = 'docker volume prune -f';
    results.push(await this.runCommand(pruneVolumes, 'Remove unused volumes'));

    const pruneNetworks = 'docker network prune -f';
    results.push(await this.runCommand(pruneNetworks, 'Remove unused networks'));

    return results;
  }

  async cleanAll() {
    this.actions = [];
    
    await this.cleanOldLogs();
    await this.cleanAptCache();
    await this.cleanTmp();
    await this.cleanJournal();
    await this.cleanZombieProcesses();
    await this.cleanDocker();

    return this.actions;
  }

  async preview() {
    const cleaner = new Cleaner(true);
    return await cleaner.cleanAll();
  }

  getSummary() {
    const executed = this.actions.filter(a => a.status === 'executed');
    const failed = executed.filter(a => !a.success);
    
    return {
      total: this.actions.length,
      dryRun: this.dryRun,
      executed: executed.length,
      failed: failed.length,
      actions: this.actions,
    };
  }
}

module.exports = Cleaner;
