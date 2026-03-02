#!/usr/bin/env node

const MetricsCollector = require('./monitors/metrics');
const Alerter = require('./monitors/alerter');
const Notifier = require('./notifications/notifier');
const Cleaner = require('./cleaners/cleaner');
const fs = require('fs');
const { exec } = require('child_process');

const args = process.argv.slice(2);
const command = args[0];

function colorBar(percent, max = 100) {
  const filled = Math.round((percent / max) * 10);
  const empty = 10 - filled;
  let color = '\x1b[32m';
  if (percent > 80) color = '\x1b[33m';
  if (percent > 90) color = '\x1b[31m';
  return `${color}${'█'.repeat(filled)}${'░'.repeat(empty)}\x1b[0m ${percent}%`;
}

async function status() {
  const collector = new MetricsCollector();
  const metrics = await collector.getAllMetrics();
  collector.destroy();

  console.log('\n📊 Server Status\n');
  console.log(` CPU:    🖥️  ${colorBar(metrics.cpu.current)}`);
  console.log(`💾 Memory:  ${colorBar(metrics.memory.percent)} (${(metrics.memory.used / 1e9).toFixed(1)}/${(metrics.memory.total / 1e9).toFixed(1)} GB)`);
  
  console.log('\n💿 Disk:');
  for (const disk of metrics.disk) {
    console.log(`   ${disk.mount.padEnd(12)} ${colorBar(disk.percent)} (${(disk.used / 1e9).toFixed(0)}/${(disk.size / 1e9).toFixed(0)} GB)`);
  }

  console.log(`\n🔄 Swap:    ${colorBar(metrics.swap.percent)}`);
  console.log(`🧟 Zombies: ${metrics.zombies.zombies}`);
  
  console.log(`\n🐘 PostgreSQL: ${metrics.postgres.available ? `✓ ${metrics.postgres.connections.percent}% (${metrics.postgres.connections.current}/${metrics.postgres.connections.max})` : '✗ DOWN'}`);
  
  console.log(`\n🐳 Docker: ${metrics.docker.running} running, ${metrics.docker.stopped} stopped`);
  console.log(`\n📡 Listening ports: ${metrics.ports.slice(0, 10).join(', ')}${metrics.ports.length > 10 ? '...' : ''}`);
  console.log(`\n⏰ Last check: ${metrics.timestamp}\n`);
}

async function check() {
  const collector = new MetricsCollector();
  const alerter = new Alerter();
  
  const metrics = await collector.getAllMetrics();
  const alerts = alerter.evaluateMetrics(metrics);
  collector.destroy();

  console.log('\n🔍 Health Check\n');
  
  if (alerts.length === 0) {
    console.log('✅ All systems operational\n');
  } else {
    for (const alert of alerts) {
      const icon = alert.severity === 'critical' ? '🚨' : '⚠️';
      console.log(`${icon} ${alert.type}: ${alert.message}`);
    }
    console.log('');
  }

  return { metrics, alerts };
}

async function logs() {
  const commands = [
    'journalctl -n 20 --no-pager -o short-iso',
    'tail -20 /var/log/syslog 2>/dev/null || true',
    'tail -20 /var/log/auth.log 2>/dev/null || true',
    'tail -20 /var/log/nginx/error.log 2>/dev/null || true',
  ];

  for (const cmd of commands) {
    console.log(`\n--- ${cmd.split(' ')[1]} ---`);
    await new Promise((resolve) => {
      exec(cmd, (err, stdout) => {
        console.log(stdout || '(no output)');
        resolve();
      });
    });
  }
}

async function clean(dryRun = true) {
  console.log(`\n🧹 Running ${dryRun ? 'preview' : 'cleanup'}...\n`);
  
  const cleaner = new Cleaner(dryRun);
  const actions = await cleaner.cleanAll();
  const summary = cleaner.getSummary();

  for (const action of actions) {
    const icon = action.status === 'would execute' ? '🔍' : (action.success ? '✅' : '❌');
    console.log(`${icon} ${action.description}`);
    if (action.error) console.log(`   Error: ${action.error}`);
  }

  console.log(`\n📊 Summary: ${summary.total} actions (${summary.executed} executed, ${summary.failed} failed)\n`);
  
  return summary;
}

async function testNotify() {
  console.log('\n📱 Testing notifications...\n');
  
  const notifier = new Notifier();
  const results = await notifier.testAll();
  
  console.log(`Telegram: ${results.telegram.success ? '✅ OK' : '❌ ' + results.telegram.error}`);
  console.log(`Email:    ${results.email.success ? '✅ OK' : '❌ ' + results.email.error}\n`);
}

async function sendAlert(message) {
  const notifier = new Notifier();
  await notifier.notify([{
    type: 'Manual Alert',
    severity: 'warning',
    message: message,
  }]);
  console.log('✅ Alert sent\n');
}

async function daemonStatus() {
  return new Promise((resolve) => {
    exec('systemctl is-active server-monitor', (err, stdout) => {
      const active = stdout.trim() === 'active';
      console.log(`Daemon: ${active ? '🟢 Running' : '🔴 Stopped'}`);
      resolve(active);
    });
  });
}

async function main() {
  switch (command) {
    case 'status':
      await daemonStatus();
      await status();
      break;
    case 'check':
      await check();
      break;
    case 'logs':
      await logs();
      break;
    case 'clean':
      const force = args.includes('--force');
      await clean(!force);
      break;
    case 'test-notify':
      await testNotify();
      break;
    case 'alert':
      const msg = args.slice(1).join(' ');
      if (msg) {
        await sendAlert(msg);
      } else {
        console.log('Usage: server-monitor alert "message"\n');
      }
      break;
    case 'daemon':
      if (args[1] === 'start') {
        exec('systemctl start server-monitor');
        console.log('Starting daemon...');
      } else if (args[1] === 'stop') {
        exec('systemctl stop server-monitor');
        console.log('Stopping daemon...');
      } else if (args[1] === 'restart') {
        exec('systemctl restart server-monitor');
        console.log('Restarting daemon...');
      } else {
        console.log('Usage: server-monitor daemon {start|stop|restart}');
      }
      break;
    default:
      console.log(`
Server Monitor CLI

Commands:
  status         Show current server metrics with colored bars
  check          Run health check and show alerts
  logs           Show recent logs from syslog/auth/nginx
  clean          Preview cleanup actions (dry run)
  clean --force  Execute cleanup actions
  test-notify    Test Telegram and email notifications
  alert "msg"    Send manual alert
  daemon start   Start the systemd service
  daemon stop    Stop the systemd service
  daemon restart Restart the systemd service
`);
  }
}

main().catch(console.error);
