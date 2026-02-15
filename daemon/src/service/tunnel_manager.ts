import { pinggy, TunnelType } from "@pinggy/pinggy";
import Rcon from "rcon";
import StorageSubsystem from "../common/system_storage";
import logger from "./log";
import InstanceSubsystem from "./system_instance";

interface TunnelInfo {
  url: string;
  tunnel: any;
  rconClient: any;
  rotationInterval: NodeJS.Timeout | null;
  instanceUuid: string;
  port: number;
  rconPort: number;
  rconPassword: string;
}

class TunnelManagerService {
  private activeTunnels: Map<string, TunnelInfo> = new Map();

  async startTunnel(
    instanceUuid: string,
    port: number,
    rconPort: number,
    rconPassword: string,
    rotationMinutes: number = 50
  ): Promise<string> {
    try {
      // Stop existing tunnel if any
      await this.stopTunnel(instanceUuid);

      logger.info(
        `[TunnelManager] Starting TCP tunnel for instance ${instanceUuid} on port ${port}`
      );

      // Start pinggy TCP tunnel for Minecraft using TunnelType.Tcp
      const tunnel = await pinggy.forward({
        forwarding: [
          {
            address: `localhost:${port}`,
            type: TunnelType.Tcp
          }
        ]
      });

      const urls = await tunnel.urls();
      let tunnelUrl = urls[0];
      
      logger.info(`[TunnelManager] Raw URL from Pinggy: ${tunnelUrl}`);
      
      // Verify we got a TCP tunnel (should start with tcp://)
      if (tunnelUrl.startsWith("http://") || tunnelUrl.startsWith("https://")) {
        logger.error(`[TunnelManager] ERROR: Got HTTP tunnel instead of TCP! URL: ${tunnelUrl}`);
        logger.error(`[TunnelManager] This will NOT work for Minecraft servers!`);
        throw new Error("Failed to create TCP tunnel - got HTTP tunnel instead");
      }
      
      // Remove tcp:// prefix
      tunnelUrl = tunnelUrl.replace("tcp://", "");
      
      logger.info(`[TunnelManager] ✓ TCP Tunnel created successfully!`);
      logger.info(`[TunnelManager] Minecraft Server Address: ${tunnelUrl}`);

      // Create RCON connection
      const rconClient = new Rcon("localhost", rconPort, rconPassword);
      
      rconClient.on("error", (err: any) => {
        logger.warn(`[TunnelManager] RCON error for ${instanceUuid}: ${err.message}`);
      });

      try {
        await rconClient.connect();
        logger.info(`[TunnelManager] RCON connected for ${instanceUuid}`);
      } catch (err: any) {
        logger.warn(`[TunnelManager] RCON connection failed: ${err.message}`);
      }

      // Update instance config
      const instance = InstanceSubsystem.getInstance(instanceUuid);
      if (instance) {
        instance.config.extraServiceConfig.tunnelUrl = tunnelUrl;
        instance.config.extraServiceConfig.tunnelPid = process.pid; // Use daemon PID
        StorageSubsystem.store("InstanceConfig", instanceUuid, instance.config);
      }

      // Set up rotation interval
      const rotationInterval = setInterval(async () => {
        await this.rotateTunnel(instanceUuid);
      }, rotationMinutes * 60 * 1000);

      // Store tunnel info
      this.activeTunnels.set(instanceUuid, {
        url: tunnelUrl,
        tunnel,
        rconClient,
        rotationInterval,
        instanceUuid,
        port,
        rconPort,
        rconPassword
      });

      logger.info(`[TunnelManager] Tunnel rotation scheduled every ${rotationMinutes} minutes`);
      return tunnelUrl;
    } catch (err: any) {
      logger.error(`[TunnelManager] Failed to start tunnel: ${err.message}`);
      throw err;
    }
  }

  private async rotateTunnel(instanceUuid: string): Promise<void> {
    const tunnelInfo = this.activeTunnels.get(instanceUuid);
    if (!tunnelInfo) return;

    try {
      logger.info(`[TunnelManager] Rotating tunnel for ${instanceUuid}`);

      // Get current players
      const players = await this.getPlayerList(tunnelInfo.rconClient);

      // Create new TCP tunnel for rotation
      const newTunnel = await pinggy.forward({
        forwarding: [
          {
            address: `localhost:${tunnelInfo.port}`,
            type: TunnelType.Tcp
          }
        ]
      });

      const urls = await newTunnel.urls();
      let newUrl = urls[0];
      
      // Remove tcp:// prefix
      newUrl = newUrl.replace("tcp://", "");
      
      logger.info(`[TunnelManager] New TCP tunnel created: ${newUrl}`);

      // Transfer players if any
      if (players.length > 0) {
        const [domain, portStr] = newUrl.split(":");
        await this.transferPlayers(tunnelInfo.rconClient, players, domain, portStr);
      }

      // Update config
      const instance = InstanceSubsystem.getInstance(instanceUuid);
      if (instance) {
        instance.config.extraServiceConfig.tunnelUrl = newUrl;
        StorageSubsystem.store("InstanceConfig", instanceUuid, instance.config);
      }

      // Close old tunnel
      try {
        await tunnelInfo.tunnel.close();
      } catch (err) {
        logger.warn(`[TunnelManager] Error closing old tunnel: ${err}`);
      }

      // Update tunnel info
      tunnelInfo.url = newUrl;
      tunnelInfo.tunnel = newTunnel;

      logger.info(`[TunnelManager] Tunnel rotation complete for ${instanceUuid}`);
    } catch (err: any) {
      logger.error(`[TunnelManager] Tunnel rotation failed: ${err.message}`);
    }
  }

  private async getPlayerList(rconClient: any): Promise<string[]> {
    if (!rconClient) return [];

    try {
      const response = await rconClient.send("list");
      if (!response || !response.includes(":")) return [];

      const playerListStr = response.split(":")[1].trim();
      if (playerListStr.length === 0) return [];

      return playerListStr.split(",").map((name: string) => name.trim()).filter(Boolean);
    } catch (err) {
      logger.warn(`[TunnelManager] Failed to get player list: ${err}`);
      return [];
    }
  }

  private async transferPlayers(
    rconClient: any,
    players: string[],
    domain: string,
    port: string
  ): Promise<void> {
    if (!rconClient || players.length === 0) return;

    logger.info(`[TunnelManager] Transferring ${players.length} players to ${domain}:${port}`);

    for (const player of players) {
      try {
        const result = await rconClient.send(`transfer ${player} ${domain} ${port}`);
        logger.info(`[TunnelManager] Transferred ${player}: ${result}`);
      } catch (err) {
        logger.warn(`[TunnelManager] Failed to transfer ${player}: ${err}`);
      }
    }
  }

  async stopTunnel(instanceUuid: string): Promise<void> {
    const tunnelInfo = this.activeTunnels.get(instanceUuid);
    if (!tunnelInfo) return;

    logger.info(`[TunnelManager] Stopping tunnel for ${instanceUuid}`);

    // Clear rotation interval
    if (tunnelInfo.rotationInterval) {
      clearInterval(tunnelInfo.rotationInterval);
    }

    // Close RCON connection
    if (tunnelInfo.rconClient) {
      try {
        tunnelInfo.rconClient.disconnect();
      } catch (err) {
        logger.warn(`[TunnelManager] Error disconnecting RCON: ${err}`);
      }
    }

    // Close tunnel
    try {
      await tunnelInfo.tunnel.close();
    } catch (err) {
      logger.warn(`[TunnelManager] Error closing tunnel: ${err}`);
    }

    // Update config
    const instance = InstanceSubsystem.getInstance(instanceUuid);
    if (instance) {
      instance.config.extraServiceConfig.tunnelUrl = "";
      instance.config.extraServiceConfig.tunnelPid = 0;
      StorageSubsystem.store("InstanceConfig", instanceUuid, instance.config);
    }

    // Remove from active tunnels
    this.activeTunnels.delete(instanceUuid);

    logger.info(`[TunnelManager] Tunnel stopped for ${instanceUuid}`);
  }

  getTunnelUrl(instanceUuid: string): string {
    return this.activeTunnels.get(instanceUuid)?.url || "";
  }

  isTunnelActive(instanceUuid: string): boolean {
    return this.activeTunnels.has(instanceUuid);
  }
}

export default new TunnelManagerService();
