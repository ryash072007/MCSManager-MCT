# MCSManager-MCT Deployment Guide

## Hosting on Your Laptop

### Prerequisites

- Node.js v16.20.2+
- Windows 10/11
- Stable internet connection
- Your laptop should stay on while serving

---

## Quick Start

### 1. Build Production Code

```powershell
.\build.bat
```

This creates `production-code/` folder with optimized builds.

### 2. Start Services

```powershell
.\start-production.bat
```

This starts:

- **Daemon** on http://localhost:24444
- **Web Panel** on http://localhost:23333

### 3. Expose to Internet

#### Option A: mmar (Recommended - Simple & Fast)

**Pros:** Simple one command, free, HTTPS included, no signup
**Cons:** Random subdomain on free tier
**Steps:**

1. Install mmar: Download from [mmar.dev](https://mmar.dev)
2. Run tunnel:
   ```powershell
   mmar client --local-port 23333
   ```
3. Copy the tunnel URL from output (e.g., `https://7v0aye.mmar.dev`)
4. Share this URL with users

**Example output:**

```
Starting mmar client...
  Creating tunnel:
    Tunnel Host: mmar.dev
    Local Port: 23333

Tunnel created successfully!

A mmar tunnel is now open on:
>>>  https://7v0aye.mmar.dev -> http://localhost:23333
```

#### Option B: Cloudflare Tunnel (Custom Domain)

**Pros:** Free, stable, custom domain, no port forwarding
**Cons:** More setup steps
**Steps:**

1. Install: `winget install Cloudflare.cloudflared`
2. Login: `cloudflared tunnel login`
3. Create tunnel: `cloudflared tunnel create mcsmanager`
4. Edit `cloudflare-tunnel.yml` with your tunnel ID and domain
5. Start: `cloudflared tunnel run mcsmanager`

#### Option C: ngrok

**Pros:** Quick setup, easy to use
**Cons:** Random URLs on free tier, session timeouts
**Steps:**

1. Download from ngrok.com
2. Extract and run: `ngrok http 23333`
3. Copy the forwarding URL (e.g., https://abc123.ngrok.io)

#### Option D: Port Forwarding

**Pros:** Free, no third-party
**Cons:** Requires router access, exposes your IP
**Steps:**

1. Find your local IP: `ipconfig`
2. Login to your router (usually 192.168.1.1)
3. Forward port 23333 to your laptop's local IP
4. Find your public IP: https://whatismyipaddress.com
5. Access via: http://YOUR_PUBLIC_IP:23333

---

## Accessing Your Panel

### For You (Local):

- Open: http://localhost:23333
- Default login: Check panel's first-run setup

### For Others (Remote):

- Share your tunnel URL
- Example with mmar: https://7v0aye.mmar.dev
- Example with Cloudflare: https://mcsmanager.yourdomain.com
- Example with ngrok: https://abc123.ngrok.io

---

## Managing Minecraft Servers

### Creating a Server:

1. Login to Web Panel
2. Create new instance
3. Upload/download Minecraft server files
4. Click "Setup Server" (accepts EULA, enables RCON)
5. Start the server

### Starting Tunnel:

1. Click "Start Tunnel"
2. Wait for tunnel URL to appear
3. Share the tunnel address with players
4. Players connect using: `muyab-xxx.pinggy.link:45393`

### Features:

- **Auto Tunnel Rotation:** Every 50 minutes (prevents free tier limits)
- **Player Transfer:** Automatically moves players to new tunnel
- **RCON Control:** Manages server commands remotely

---

## Keeping Services Running

### Option 1: Keep Terminal Open

Just leave the CMD windows running

### Option 2: Run as Background Service (Advanced)

Use PM2:

```powershell
npm install -g pm2
pm2 start production-code/daemon/app.js --name mcsm-daemon
pm2 start production-code/web/app.js --name mcsm-web
pm2 save
pm2 startup
```

### Option 3: Windows Service (Most Reliable)

Use `node-windows` or NSSM (Non-Sucking Service Manager)

---

## Troubleshooting

### Panel Not Accessible

- Check if services are running: http://localhost:23333
- Check firewall: Allow Node.js through Windows Firewall
- Check tunnel: Verify tunnel service is active

### Minecraft Server Can't Connect

- Ensure server is running in panel
- Check server port in server.properties (usually 25565)
- Verify tunnel is active (green button in UI)
- Test local connection first: localhost:25565

### Tunnel Keeps Disconnecting

- Check internet stability
- Try different tunnel service
- For Pinggy: Rotation happens every 50 mins (normal)

---

## Security Recommendations

1. **Change Default Passwords**
   - Panel admin password
   - RCON password (in server.properties)

2. **Use HTTPS**
   - Cloudflare Tunnel provides automatic HTTPS
   - ngrok has HTTPS on all tiers

3. **Firewall**
   - Only expose port 23333 to internet
   - Keep daemon (24444) local-only

4. **Keep Laptop Secure**
   - Enable Windows Firewall
   - Keep Windows updated
   - Use strong passwords

---

## Stopping Services

### Stop Tunnel:

Click "Stop Tunnel" in the panel UI

### Stop Panel/Daemon:

Close the CMD windows or:

```powershell
# If using PM2
pm2 stop all
```

---

## Updating Your Deployment

1. Stop services
2. Pull latest changes: `git pull`
3. Rebuild: `.\build.bat`
4. Restart services: `.\start-production.bat`
5. Restart tunnel service

---

## Support

For issues with:

- **MCSManager**: Check original docs at mcsmanager.com
- **Tunnel Feature**: Check daemon logs for errors
- **Pinggy**: Visit pinggy.io/docs
- **Cloudflare Tunnel**: Visit developers.cloudflare.com/cloudflare-one/connections/connect-apps
