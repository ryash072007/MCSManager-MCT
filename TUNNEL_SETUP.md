# Minecraft Tunnel Setup Guide

This feature allows you to automatically configure your Minecraft server with EULA acceptance, RCON, and Pinggy tunnel support.

## Features

1. **One-Click Setup Button** - Automatically configures:
   - Accepts Minecraft EULA (`eula=true`)
   - Sets `online-mode=false`
   - Sets `allow-transfer=true`
   - Enables RCON with password `12345678` on port `25575`

2. **Tunnel URL Display** - Shows the current tunnel URL in the Basic Information card

3. **Automatic Tunnel Management** - Python script that handles:
   - Creating Pinggy tunnels
   - Rotating tunnels every 50 minutes (configurable)
   - Transferring players to new tunnel addresses
   - Updating the panel with the current tunnel URL

## Quick Start

### Step 1: Setup Your Server

1. Create or open a Minecraft Java server instance
2. Navigate to the instance console/dashboard
3. In the **Basic Information** card, click the **"Setup for Tunnel"** button
4. Wait for the confirmation message

This will automatically configure your server with the necessary settings.

### Step 2: Install Python Dependencies

```bash
pip install pinggy mcrcon apscheduler requests
```

### Step 3: Start the Minecraft Server

Start your Minecraft server through MCSManager. Make sure it starts successfully and RCON is working.

### Step 4: Run the Tunnel Manager

You need to find your Instance ID and Daemon ID:

- **Instance ID**: Shown in the Basic Information card as "Instance ID"
- **Daemon ID**: Shown in the Basic Information card as "Daemon ID"

Run the tunnel manager script:

```bash
python tunnel_manager.py \
  --port 25565 \
  --rcon-port 25575 \
  --panel-url http://localhost:23333 \
  --instance-id YOUR_INSTANCE_UUID \
  --daemon-id YOUR_DAEMON_ID
```

Replace:

- `YOUR_INSTANCE_UUID` with your actual instance UUID
- `YOUR_DAEMON_ID` with your actual daemon ID
- Adjust the panel URL if your panel is running on a different address

### Step 5: Share the Tunnel URL

Once the tunnel manager is running, it will:

1. Create a Pinggy tunnel
2. Update the panel with the tunnel URL
3. Display the URL in the Basic Information card

Share the tunnel URL with your players. They can connect to it just like a regular Minecraft server address.

## Advanced Configuration

### Custom Tunnel Rotation Interval

By default, tunnels rotate every 50 minutes. You can change this:

```bash
python tunnel_manager.py \
  --port 25565 \
  --rcon-port 25575 \
  --panel-url http://localhost:23333 \
  --instance-id YOUR_INSTANCE_UUID \
  --daemon-id YOUR_DAEMON_ID \
  --rotation-minutes 60
```

### Custom RCON Settings

If you changed the RCON password or port:

```bash
python tunnel_manager.py \
  --port 25565 \
  --rcon-port 25575 \
  --rcon-password YOUR_PASSWORD \
  --panel-url http://localhost:23333 \
  --instance-id YOUR_INSTANCE_UUID \
  --daemon-id YOUR_DAEMON_ID
```

## How It Works

### Setup Process

1. The setup button creates/modifies `eula.txt`:

   ```
   eula=true
   ```

2. Updates `server.properties`:

   ```properties
   online-mode=false
   allow-transfer=true
   enable-rcon=true
   rcon.password=12345678
   rcon.port=25575
   ```

3. Updates the instance configuration to enable tunnel mode

### Tunnel Management

The `tunnel_manager.py` script:

1. Creates a TCP tunnel using Pinggy (free tunneling service)
2. Updates the MCSManager panel with the tunnel URL
3. Displays the URL in the Basic Information card
4. Every 50 minutes (configurable):
   - Creates a new tunnel
   - Transfers all connected players to the new address using RCON
   - Closes the old tunnel

This rotation is useful because free Pinggy tunnels have time limits.

## Troubleshooting

### "Setup for Tunnel" button doesn't appear

Make sure:

- You're viewing a Minecraft Java Edition instance
- The instance hasn't been set up yet (button disappears after setup)

### Tunnel URL not showing

Make sure:

- The tunnel manager script is running
- The panel URL, instance ID, and daemon ID are correct
- Your firewall isn't blocking the connection

### Players not transferring automatically

Make sure:

- RCON is enabled and working (test with `rcon-cli` or similar tool)
- The RCON password matches (default: `12345678`)
- Your Minecraft server supports the `/transfer` command (1.20.5+)

### Script crashes or errors

Check:

- All Python dependencies are installed
- The Minecraft server is running
- RCON port (25575) is accessible
- The panel API is accessible

## Security Notes

⚠️ **Important Security Considerations:**

1. **RCON Password**: The default password is `12345678`. This is insecure! Change it in both:
   - `server.properties` (rcon.password)
   - The tunnel manager script (--rcon-password)

2. **Online Mode**: Setting `online-mode=false` disables Minecraft authentication. Players can use any username. Consider using a whitelist or authentication plugin.

3. **Network Exposure**: Tunnels expose your server to the internet. Keep your server software updated.

## Running as a Service

To keep the tunnel manager running continuously:

### Windows (using Task Scheduler)

1. Create a batch file `start_tunnel.bat`:

   ```batch
   @echo off
   python C:\path\to\tunnel_manager.py --port 25565 --rcon-port 25575 --panel-url http://localhost:23333 --instance-id YOUR_ID --daemon-id YOUR_DAEMON_ID
   ```

2. Create a new task in Task Scheduler to run this batch file at startup

### Linux (using systemd)

1. Create `/etc/systemd/system/mc-tunnel.service`:

   ```ini
   [Unit]
   Description=Minecraft Tunnel Manager
   After=network.target

   [Service]
   Type=simple
   User=YOUR_USER
   WorkingDirectory=/path/to/MCSManager-MCT
   ExecStart=/usr/bin/python3 /path/to/MCSManager-MCT/tunnel_manager.py --port 25565 --rcon-port 25575 --panel-url http://localhost:23333 --instance-id YOUR_ID --daemon-id YOUR_DAEMON_ID
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

2. Enable and start:
   ```bash
   sudo systemctl enable mc-tunnel
   sudo systemctl start mc-tunnel
   sudo systemctl status mc-tunnel
   ```

## Support

For issues or questions:

- Check the MCSManager logs
- Check the tunnel manager script output
- Verify your Minecraft server logs
