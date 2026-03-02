const nodemailer = require('nodemailer');
const TelegramBot = require('node-telegram-bot-api');
const config = require('../config');

class Notifier {
  constructor() {
    this.telegramBot = null;
    this.smtpTransporter = null;
    
    if (config.telegram.botToken && config.telegram.chatId) {
      try {
        this.telegramBot = new TelegramBot(config.telegram.botToken, { polling: false });
      } catch (err) {
        console.error('Telegram bot init failed:', err.message);
      }
    }
    
    if (config.smtp.host && config.smtp.user && config.smtp.pass) {
      this.smtpTransporter = nodemailer.createTransport({
        host: config.smtp.host,
        port: config.smtp.port,
        secure: config.smtp.port === 465,
        auth: {
          user: config.smtp.user,
          pass: config.smtp.pass,
        },
      });
    }
  }

  async sendTelegram(message) {
    if (!this.telegramBot || !config.telegram.chatId) {
      return { success: false, error: 'Telegram not configured' };
    }

    try {
      await this.telegramBot.sendMessage(config.telegram.chatId, message, { parse_mode: 'Markdown' });
      return { success: true, method: 'telegram' };
    } catch (err) {
      return { success: false, error: err.message, method: 'telegram' };
    }
  }

  async sendEmail(subject, body) {
    if (!this.smtpTransporter || !config.alertEmail) {
      return { success: false, error: 'Email not configured' };
    }

    try {
      await this.smtpTransporter.sendMail({
        from: config.smtp.from,
        to: config.alertEmail,
        subject: `[Server Monitor] ${subject}`,
        text: body,
        html: body.replace(/\n/g, '<br>'),
      });
      return { success: true, method: 'email' };
    } catch (err) {
      return { success: false, error: err.message, method: 'email' };
    }
  }

  async notify(alerts, silent = false) {
    if (alerts.length === 0) return;

    const results = [];

    for (const alert of alerts) {
      let message = this.formatAlert(alert);
      
      if (silent) {
        message = `📊 ${message}`;
      } else {
        const emoji = alert.severity === 'critical' ? '🚨' : '⚠️';
        message = `${emoji} ${message}`;
      }

      if (!silent) {
        const telegramResult = await this.sendTelegram(message);
        results.push(telegramResult);
      }

      const emailResult = await this.sendEmail(alert.type, message);
      results.push(emailResult);
    }

    return results;
  }

  formatAlert(alert) {
    let message = `*${alert.type}*: ${alert.message}`;
    
    if (alert.queries) {
      message += '\n\nSlow queries:\n';
      for (const q of alert.queries.slice(0, 3)) {
        message += `- PID ${q.pid}: ${q.duration} - ${q.query}...\n`;
      }
    }
    
    return message;
  }

  async testTelegram() {
    if (!this.telegramBot || !config.telegram.chatId) {
      return { success: false, error: 'Telegram not configured' };
    }

    try {
      await this.telegramBot.sendMessage(
        config.telegram.chatId,
        '✅ Server Monitor test notification - Telegram is working!'
      );
      return { success: true, chatId: config.telegram.chatId };
    } catch (err) {
      return { success: false, error: err.message };
    }
  }

  async testEmail() {
    if (!this.smtpTransporter || !config.alertEmail) {
      return { success: false, error: 'Email not configured' };
    }

    try {
      await this.smtpTransporter.sendMail({
        from: config.smtp.from,
        to: config.alertEmail,
        subject: 'Server Monitor Test',
        text: '✅ Server Monitor test notification - Email is working!',
      });
      return { success: true, email: config.alertEmail };
    } catch (err) {
      return { success: false, error: err.message };
    }
  }

  async testAll() {
    const telegram = await this.testTelegram();
    const email = await this.testEmail();
    return { telegram, email };
  }
}

module.exports = Notifier;
