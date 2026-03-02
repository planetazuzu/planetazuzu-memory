#!/usr/bin/env node

const { McpServer } = require('@modelcontextprotocol/sdk/server/mcp.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const z = require('zod');
const readline = require('readline');
const MetricsCollector = require('./monitors/metrics');
const Alerter = require('./monitors/alerter');
const Cleaner = require('./cleaners/cleaner');
require('dotenv').config();

const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
rl._onLine = () => {};

const mcpServer = new McpServer({
  name: 'server-monitor',
  version: '1.0.0'
});

const metricsCollector = new MetricsCollector();
const alerter = new Alerter();

mcpServer.registerTool('get_server_metrics', {
  description: 'Obtiene métricas del servidor: CPU, memoria, disco, swap, procesos zombie, PostgreSQL, Docker',
  inputSchema: z.object({})
}, async () => {
  const metrics = await metricsCollector.getAllMetrics();
  return { content: [{ type: 'text', text: JSON.stringify(metrics, null, 2) }] };
});

mcpServer.registerTool('get_server_status', {
  description: 'Obtiene estado resumido del servidor con alertas activas',
  inputSchema: z.object({})
}, async () => {
  const metrics = await metricsCollector.getAllMetrics();
  const alerts = alerter.evaluateMetrics(metrics);
  return {
    content: [{
      type: 'text',
      text: JSON.stringify({
        healthy: alerts.length === 0,
        alerts,
        summary: {
          cpu: metrics.cpu.current,
          memory: metrics.memory.percent,
          disk: metrics.disk.map(d => ({ mount: d.mount, percent: d.percent })),
          postgres: metrics.postgres.available ? 'up' : 'down',
          docker: `${metrics.docker.running} running`
        }
      }, null, 2)
    }]
  };
});

mcpServer.registerTool('run_health_check', {
  description: 'Ejecuta un health check completo y devuelve alertas si hay problemas',
  inputSchema: z.object({})
}, async () => {
  const metrics = await metricsCollector.getAllMetrics();
  const alerts = alerter.evaluateMetrics(metrics);
  const text = alerts.length === 0
    ? '✅ Sistema sano'
    : `⚠️ ${alerts.length} alertas:\n` + alerts.map(a => `- ${a.type}: ${a.message}`).join('\n');
  return { content: [{ type: 'text', text }] };
});

mcpServer.registerTool('preview_cleanup', {
  description: 'Vista previa de acciones de limpieza (dry-run)',
  inputSchema: z.object({})
}, async () => {
  const cleaner = new Cleaner(true);
  const actions = await cleaner.cleanAll();
  return { content: [{ type: 'text', text: 'Acciones de limpieza (dry-run):\n' + actions.map(a => `- ${a.description}`).join('\n') }] };
});

mcpServer.registerTool('run_cleanup', {
  description: 'Ejecuta limpieza del sistema (logs, caché, Docker)',
  inputSchema: z.object({})
}, async () => {
  const cleaner = new Cleaner(false);
  const actions = await cleaner.cleanAll();
  const summary = cleaner.getSummary();
  return { content: [{ type: 'text', text: `Limpieza: ${summary.executed} ejecutadas, ${summary.failed} fallidas` }] };
});

async function main() {
  const transport = new StdioServerTransport();
  await mcpServer.connect(transport);
  console.error('Server Monitor MCP running');
}

main().catch(console.error);
