#!/usr/bin/env node

const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const conn = new Client();

conn.on('ready', () => {
  console.log('🏛️ Deploying The Quiet Pilgrim Enterprise Dashboard...\n');

  conn.sftp((err, sftp) => {
    if (err) {
      console.error('SFTP Error:', err);
      conn.end();
      return;
    }

    const files = [
      { local: 'Downloads/TQP Text Logo.png', remote: '/home/helm/expense-tracker/tqp_logo.png' },
      { local: 'Downloads/TQP Text Logo Square (1).png', remote: '/home/helm/expense-tracker/tqp_logo_square.png' },
      { local: 'Downloads/M&S Text Logo.png', remote: '/home/helm/expense-tracker/ms_logo.png' },
      { local: 'tqp_dashboard_enterprise.html', remote: '/home/helm/expense-tracker/expense_dashboard.html' }
    ];

    let uploaded = 0;

    files.forEach(file => {
      const localPath = path.join('C:/Users/ASUS', file.local);
      const remotePath = file.remote;

      console.log(`📤 Uploading: ${path.basename(localPath)}`);

      sftp.fastPut(localPath, remotePath, (err) => {
        if (err) {
          console.error(`❌ Failed: ${path.basename(localPath)} - ${err.message}`);
        } else {
          console.log(`✅ Uploaded: ${path.basename(localPath)}`);
        }

        uploaded++;
        if (uploaded === files.length) {
          console.log('\n🔄 Restarting dashboard...\n');

          conn.exec('cd ~/expense-tracker && pm2 restart expense-dashboard && sleep 2', (err, stream) => {
            if (err) {
              console.error('Error:', err);
              conn.end();
              return;
            }

            stream.on('close', () => {
              console.log('\n');
              console.log('═══════════════════════════════════════════════════════════');
              console.log('🏛️ THE QUIET PILGRIM DASHBOARD DEPLOYED!');
              console.log('═══════════════════════════════════════════════════════════');
              console.log('');
              console.log('✨ LUXURY MULTI-TAB DASHBOARD');
              console.log('');
              console.log('📊 Tabs:');
              console.log('   • Overview - All 3 companies consolidated');
              console.log('   • Moon & Spoon Kitchen - Restaurant expenses');
              console.log('   • Personal - Private expenses');
              console.log('   • Grand Vision Perspective - Business consultancy');
              console.log('');
              console.log('🌐 Access at: http://77.42.37.42:3000');
              console.log('');
              console.log('🎨 Design: Aman-inspired luxury aesthetic');
              console.log('🏢 Branding: The Quiet Pilgrim + subsidiaries');
              console.log('📱 Features: Tab navigation, real-time data, elegant UI');
              console.log('');
              console.log('💡 Next: Add port 3000 to Hetzner firewall if not done!');
              console.log('');

              conn.end();
            }).on('data', (data) => {
              console.log(data.toString());
            });
          });
        }
      });
    });
  });

}).connect({
  host: '77.42.37.42',
  port: 22,
  username: 'helm',
  password: 'MosesHappy182!'
});

conn.on('error', (err) => {
  console.error('❌ Connection Error:', err.message);
  process.exit(1);
});
