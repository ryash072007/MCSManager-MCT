#!/usr/bin/env python3
"""
Minecraft Tunnel Manager for MCSManager

This script creates and manages Pinggy tunnels for Minecraft servers,
automatically rotating tunnels and transferring players.

Requirements:
    pip install pinggy mcrcon apscheduler requests

Usage:
    python tunnel_manager.py --port 25565 --rcon-port 25575 --panel-url http://localhost:23333 --instance-id YOUR_INSTANCE_ID --daemon-id YOUR_DAEMON_ID
"""

import argparse
import sys
import time
import logging
from typing import Optional, List

try:
    import pinggy
    from mcrcon import MCRcon
    from apscheduler.schedulers.blocking import BlockingScheduler
    import requests
except ImportError as e:
    print(f"Error: Missing required package: {e}")
    print("Please install required packages:")
    print("  pip install pinggy mcrcon apscheduler requests")
    sys.exit(1)

# Configure logging
log_file = "tunnel_manager.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


class MinecraftTunnelManager:
    """Manages Pinggy tunnels for Minecraft servers with automatic rotation."""

    def __init__(
        self,
        mc_port: int,
        rcon_port: int,
        rcon_password: str,
        panel_url: str,
        instance_id: str,
        daemon_id: str,
        tunnel_rotation_minutes: int = 50,
        rcon_host: str = "127.0.0.1",
    ):
        self.mc_port = mc_port
        self.rcon_port = rcon_port
        self.rcon_password = rcon_password
        self.rcon_host = rcon_host
        self.panel_url = panel_url.rstrip("/")
        self.instance_id = instance_id
        self.daemon_id = daemon_id
        self.tunnel_rotation_minutes = tunnel_rotation_minutes

        self.tunnels_list: List = []
        self.scheduler = BlockingScheduler()

    def start_new_tunnel(self) -> pinggy.Tunnel:
        """Start a new Pinggy tunnel for the Minecraft server."""
        logger.info(f"Starting new tunnel for port {self.mc_port}...")
        tunnel = pinggy.start_tunnel(
            forwardto=f"localhost:{self.mc_port}",
            type="tcp",
            serveraddress="ap.free.pinggy.io:443",
        )
        self.tunnels_list.append(tunnel)
        logger.info(f"Tunnel started: {tunnel.urls[0]}")
        return tunnel

    def run_rcon_command(self, cmd: str) -> str:
        """Execute an RCON command on the Minecraft server."""
        try:
            with MCRcon(self.rcon_host, self.rcon_password, self.rcon_port) as mcr:
                response = mcr.command(cmd)
            return response
        except Exception as e:
            logger.error(f"RCON command failed: {e}")
            return ""

    def get_player_list(self) -> List[str]:
        """Get the list of currently connected players."""
        player_list_str = self.run_rcon_command("list")
        if not player_list_str or ":" not in player_list_str:
            return []

        player_list_str = player_list_str[player_list_str.find(":") + 1 :]
        player_names = player_list_str.strip().split(", ")
        return [name for name in player_names if name]

    def transfer_all_players(self, domain: str, port: str) -> bool:
        """Transfer all connected players to the new tunnel address."""
        playerlist = self.get_player_list()
        if not playerlist:
            logger.info("No players to transfer")
            return False

        logger.info(f"Transferring {len(playerlist)} players to {domain}:{port}")
        for name in playerlist:
            result = self.run_rcon_command(f"transfer {name} {domain} {port}")
            logger.info(f"Transferred {name}: {result}")

        return True

    def update_panel_tunnel_url(self, tunnel_url: str) -> bool:
        """Update the tunnel URL in MCSManager panel."""
        try:
            url = f"{self.panel_url}/api/protected_instance/update_tunnel_url"
            params = {"uuid": self.instance_id, "daemonId": self.daemon_id}
            data = {"tunnelUrl": tunnel_url}

            logger.info(f"Updating panel with tunnel URL: {tunnel_url}")
            response = requests.post(url, params=params, json=data, timeout=10)
            response.raise_for_status()

            logger.info("Panel updated successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to update panel: {e}")
            return False

    def tunnel_rotation_iteration(self):
        """Main iteration: create new tunnel, update panel, transfer players, cleanup old tunnels."""
        try:
            # Start new tunnel
            new_tunnel = self.start_new_tunnel()
            new_url = str(new_tunnel.urls[0])[6:]  # Remove 'tcp://' prefix
            logger.info(f"New tunnel URL: {new_url}")

            # Update panel with new URL
            self.update_panel_tunnel_url(new_url)

            # Transfer players if any are connected
            if ":" in new_url:
                domain, port = new_url.split(":")
                time.sleep(2)  # Give the tunnel a moment to stabilize
                self.transfer_all_players(domain, port)

            # Cleanup old tunnels
            while len(self.tunnels_list) > 1:
                try:
                    old_tunnel = self.tunnels_list[0]
                    logger.info("Stopping old tunnel...")
                    old_tunnel.stop()
                    del self.tunnels_list[0]
                except Exception as e:
                    logger.error(f"Failed to stop old tunnel: {e}")
                    # Remove it anyway
                    if len(self.tunnels_list) > 0:
                        del self.tunnels_list[0]

        except Exception as e:
            logger.error(f"Tunnel rotation failed: {e}")

    def start(self):
        """Start the tunnel manager with scheduled rotations."""
        logger.info("=" * 60)
        logger.info("Minecraft Tunnel Manager Starting")
        logger.info(f"MC Port: {self.mc_port}")
        logger.info(f"RCON Port: {self.rcon_port}")
        logger.info(f"Panel URL: {self.panel_url}")
        logger.info(f"Instance ID: {self.instance_id}")
        logger.info(f"Rotation Interval: {self.tunnel_rotation_minutes} minutes")
        logger.info("=" * 60)

        # Create initial tunnel
        self.tunnel_rotation_iteration()

        # Schedule periodic rotations
        self.scheduler.add_job(
            self.tunnel_rotation_iteration,
            "interval",
            minutes=self.tunnel_rotation_minutes,
        )

        logger.info("Scheduler started. Press Ctrl+C to stop.")
        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Shutting down...")
            # Cleanup
            for tunnel in self.tunnels_list:
                try:
                    tunnel.stop()
                except:
                    pass


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Minecraft Tunnel Manager for MCSManager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tunnel_manager.py --port 25565 --rcon-port 25575 \\
    --panel-url http://localhost:23333 \\
    --instance-id abc123 --daemon-id def456

  python tunnel_manager.py --port 25565 --rcon-port 25575 \\
    --panel-url http://localhost:23333 \\
    --instance-id abc123 --daemon-id def456 \\
    --rotation-minutes 60
        """,
    )

    parser.add_argument(
        "--port", type=int, required=True, help="Minecraft server port (default: 25565)"
    )
    parser.add_argument(
        "--rcon-port", type=int, default=25575, help="RCON port (default: 25575)"
    )
    parser.add_argument(
        "--rcon-password",
        type=str,
        default="12345678",
        help="RCON password (default: 12345678)",
    )
    parser.add_argument(
        "--panel-url",
        type=str,
        required=True,
        help="MCSManager panel URL (e.g., http://localhost:23333)",
    )
    parser.add_argument(
        "--instance-id", type=str, required=True, help="Instance UUID from MCSManager"
    )
    parser.add_argument(
        "--daemon-id", type=str, required=True, help="Daemon ID from MCSManager"
    )
    parser.add_argument(
        "--rotation-minutes",
        type=int,
        default=50,
        help="Tunnel rotation interval in minutes (default: 50)",
    )
    parser.add_argument(
        "--rcon-host",
        type=str,
        default="127.0.0.1",
        help="RCON host (default: 127.0.0.1)",
    )

    args = parser.parse_args()

    # Create and start the tunnel manager
    manager = MinecraftTunnelManager(
        mc_port=args.port,
        rcon_port=args.rcon_port,
        rcon_password=args.rcon_password,
        panel_url=args.panel_url,
        instance_id=args.instance_id,
        daemon_id=args.daemon_id,
        tunnel_rotation_minutes=args.rotation_minutes,
        rcon_host=args.rcon_host,
    )

    manager.start()


if __name__ == "__main__":
    main()
