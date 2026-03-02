const si = require('systeminformation');
const { Pool } = require('pg');
const config = require('../config');

class MetricsCollector {
  constructor() {
    this.pgPool = null;
  }

  async getCpu() {
    const load = await si.currentLoad();
    return {
      current: Math.round(load.currentLoad),
      cores: load.cpus.map(c => Math.round(c.load)),
    };
  }

  async getMemory() {
    const mem = await si.mem();
    return {
      total: mem.total,
      used: mem.used,
      free: mem.free,
      percent: Math.round((mem.used / mem.total) * 100),
    };
  }

  async getDisk() {
    const fs = await si.fsSize();
    return fs.map(disk => ({
      fs: disk.fs,
      mount: disk.mount,
      size: disk.size,
      used: disk.used,
      available: disk.available,
      percent: Math.round(disk.use),
    }));
  }

  async getSwap() {
    const mem = await si.mem();
    return {
      total: mem.swaptotal,
      used: mem.swapused,
      percent: mem.swaptotal > 0 ? Math.round((mem.swapused / mem.swaptotal) * 100) : 0,
    };
  }

  async getZombieProcesses() {
    const processes = await si.processes();
    return {
      running: processes.running,
      blocked: processes.blocked,
      zombies: processes.zombies,
    };
  }

  async getPostgres() {
    const result = {
      available: false,
      connections: { current: 0, max: 0, percent: 0 },
      slowQueries: [],
    };

    try {
      if (!this.pgPool) {
        this.pgPool = new Pool({
          host: config.database.host,
          port: config.database.port,
          database: config.database.name,
          user: config.database.user,
          connectionTimeoutMillis: 5000,
        });
      }

      const client = await this.pgPool.connect();
      
      const connResult = await client.query(`
        SELECT count(*) as current, 
               (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') as max
      `);
      
      const current = parseInt(connResult.rows[0].current);
      const max = parseInt(connResult.rows[0].max);
      
      result.connections = {
        current,
        max,
        percent: Math.round((current / max) * 100),
      };
      result.available = true;

      const slowResult = await client.query(`
        SELECT pid, now() - pg_stat_activity.query_start AS duration, query, state
        FROM pg_stat_activity
        WHERE state = 'active' AND now() - pg_stat_activity.query_start > interval '5 seconds'
        ORDER BY duration DESC
        LIMIT 10
      `);
      
      result.slowQueries = slowResult.rows;

      client.release();
    } catch (err) {
      result.error = err.message;
    }

    return result;
  }

  async getDocker() {
    const result = { running: 0, stopped: 0, total: 0 };
    
    try {
      const containers = await si.dockerAll();
      result.total = containers.length;
      result.running = containers.filter(c => c.state === 'running').length;
      result.stopped = containers.filter(c => c.state !== 'running').length;
    } catch (err) {
      result.error = err.message;
    }

    return result;
  }

  async getPorts() {
    const connections = await si.networkConnections();
    const listeningPorts = new Set(
      connections
        .filter(c => c.state === 'LISTEN')
        .map(c => `${c.protocol}:${c.localPort}`)
    );
    return Array.from(listeningPorts);
  }

  async getAllMetrics() {
    return {
      cpu: await this.getCpu(),
      memory: await this.getMemory(),
      disk: await this.getDisk(),
      swap: await this.getSwap(),
      zombies: await this.getZombieProcesses(),
      postgres: await this.getPostgres(),
      docker: await this.getDocker(),
      ports: await this.getPorts(),
      timestamp: new Date().toISOString(),
    };
  }

  destroy() {
    if (this.pgPool) {
      this.pgPool.end();
      this.pgPool = null;
    }
  }
}

module.exports = MetricsCollector;
