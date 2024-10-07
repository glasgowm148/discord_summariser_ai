# Step 1: Create a Systemd Service File
echo "[Unit]
Description=Dev Summary Automation Service
After=network.target

[Service]
Type=simple
ExecStart=/opt/bridge/chat_summariser/start.sh
WorkingDirectory=/opt/bridge/chat_summariser
User=root
StandardOutput=append:/var/log/dev_summary.log
StandardError=append:/var/log/dev_summary_error.log

[Install]
WantedBy=multi-user.target" | sudo tee /etc/systemd/system/dev_summary.service

# Step 2: Create a Timer File
echo "[Unit]
Description=Run Dev Summary Automation Service weekly on Fridays

[Timer]
OnCalendar=Fri *-*-* 12:00:00
Persistent=true

[Install]
WantedBy=timers.target" | sudo tee /etc/systemd/system/dev_summary.timer

# Step 3: Reload Systemd Configuration
sudo systemctl daemon-reload

# Step 4: Enable and Start the Timer
sudo systemctl enable dev_summary.timer
sudo systemctl start dev_summary.timer

# Step 5: Check if the Timer is Active
sudo systemctl list-timers --all | grep dev_summary