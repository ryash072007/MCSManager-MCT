<script setup lang="ts">
import { useInstanceInfo } from "@/hooks/useInstance";
import { t } from "@/lang/i18n";
import { getTunnelLogs, setupInstanceTunnelApi, startTunnelManager, stopTunnelManager } from "@/services/apis/instance";
import type { LayoutCard } from "@/types";
import { CheckCircleOutlined, ExclamationCircleOutlined, ReloadOutlined, StopOutlined, ThunderboltOutlined } from "@ant-design/icons-vue";
import { message } from "ant-design-vue";
import { computed, onMounted, ref } from "vue";
import { GLOBAL_INSTANCE_NAME } from "../../config/const";
import { useLayoutCardTools } from "../../hooks/useCardTools";
import { parseTimestamp } from "../../tools/time";
import DockerInfo from "./dialogs/DockerInfo.vue";

const props = defineProps<{
  card: LayoutCard;
}>();

const DockerInfoDialog = ref<InstanceType<typeof DockerInfo>>();
const { getMetaOrRouteValue } = useLayoutCardTools(props.card);

const instanceId = getMetaOrRouteValue("instanceId");
const daemonId = getMetaOrRouteValue("daemonId");

const { statusText, isRunning, isStopped, instanceTypeText, instanceInfo, execute } =
  useInstanceInfo({
    instanceId,
    daemonId,
    autoRefresh: true
  });

const setupTunnelLoading = ref(false);
const startTunnelLoading = ref(false);
const stopTunnelLoading = ref(false);
const tunnelLogs = ref("");
const showLogs = ref(false);
const logsLoading = ref(false);
let logsRefreshInterval: any = null;

const setupTunnel = async () => {
  if (!instanceId || !daemonId) return;
  
  setupTunnelLoading.value = true;
  try {
    const { execute: setupExec } = setupInstanceTunnelApi();
    const result = await setupExec({
      params: {
        uuid: instanceId,
        daemonId: daemonId
      }
    });
    
    if (result.value?.success) {
      message.success("Server configured successfully! EULA accepted, RCON enabled.");
      // Refresh instance info to get updated config
      await execute({
        params: {
          uuid: instanceId,
          daemonId: daemonId
        },
        forceRequest: true
      });
    }
  } catch (err: any) {
    message.error(`Setup failed: ${err.message || "Unknown error"}`);
  } finally {
    setupTunnelLoading.value = false;
  }
};

const startTunnel = async () => {
  if (!instanceId || !daemonId) return;
  
  startTunnelLoading.value = true;
  try {
    const { execute: startExec } = startTunnelManager();
    const result = await startExec({
      params: {
        uuid: instanceId,
        daemonId: daemonId
      }
    });
    
    if (result.value?.success) {
      message.success(result.value.message || "Tunnel started successfully!");
      // Refresh instance data to get the tunnel URL
      await execute({
        params: {
          uuid: instanceId,
          daemonId: daemonId
        },
        forceRequest: true
      });
      // Start fetching status updates
      startLogRefresh();
    }
  } catch (err: any) {
    message.error(`Failed to start tunnel: ${err.message || "Unknown error"}`);
  } finally {
    startTunnelLoading.value = false;
  }
};

const stopTunnel = async () => {
  if (!instanceId || !daemonId) return;
  
  stopTunnelLoading.value = true;
  try {
    const { execute: stopExec } = stopTunnelManager();
    const result = await stopExec({
      params: {
        uuid: instanceId,
        daemonId: daemonId
      }
    });
    
    if (result.value?.success) {
      message.success(result.value.message || "Tunnel manager stopped.");
      showLogs.value = false;
      stopLogRefresh();
      tunnelLogs.value = "";
      // Refresh instance info
      await execute({
        params: {
          uuid: instanceId,
          daemonId: daemonId
        },
        forceRequest: true
      });
    }
  } catch (err: any) {
    const errorMsg = err.message || "Unknown error";
    // If tunnel is already stopped, reset the UI state
    if (errorMsg.includes("No tunnel is running")) {
      message.warning("Tunnel is not running. Resetting tunnel state...");
      showLogs.value = false;
      stopLogRefresh();
      tunnelLogs.value = "";
      // Refresh instance info to sync state
      await execute({
        params: {
          uuid: instanceId,
          daemonId: daemonId
        },
        forceRequest: true
      });
    } else {
      message.error(`Failed to stop tunnel: ${errorMsg}`);
    }
  } finally {
    stopTunnelLoading.value = false;
  }
};

const loadLogs = async () => {
  if (!instanceId || !daemonId) return;
  
  logsLoading.value = true;
  try {
    const { execute: logsExec } = getTunnelLogs();
    const result = await logsExec({
      params: {
        uuid: instanceId,
        daemonId: daemonId
      }
    });
    
    if (result.value?.logs) {
      tunnelLogs.value = result.value.logs;
    }
    
    // Refresh instance data to get updated tunnel URL
    await execute({
      params: {
        uuid: instanceId,
        daemonId: daemonId
      },
      forceRequest: false
    });
  } catch (err: any) {
    console.error("Failed to load status:", err);
  } finally {
    logsLoading.value = false;
  }
};

const startLogRefresh = () => {
  stopLogRefresh();
  loadLogs();
  logsRefreshInterval = setInterval(loadLogs, 10000); // Refresh every 10 seconds
};

const stopLogRefresh = () => {
  if (logsRefreshInterval) {
    clearInterval(logsRefreshInterval);
    logsRefreshInterval = null;
  }
};

const toggleLogs = () => {
  showLogs.value = !showLogs.value;
  if (showLogs.value && !logsRefreshInterval) {
    startLogRefresh();
  } else if (!showLogs.value) {
    stopLogRefresh();
  }
};

const getInstanceName = computed(() => {
  if (instanceInfo.value?.config.nickname === GLOBAL_INSTANCE_NAME) {
    return t("TXT_CODE_5bdaf23d");
  } else {
    return instanceInfo.value?.config.nickname;
  }
});

const instanceGameServerInfo = computed(() => {
  if (instanceInfo.value?.info?.mcPingOnline) {
    return {
      players: `${instanceInfo.value?.info.currentPlayers} / ${instanceInfo.value?.info.maxPlayers}`,
      version: instanceInfo.value?.info.version
    };
  } else {
    return null;
  }
});

const tunnelUrl = computed(() => {
  return instanceInfo.value?.config.extraServiceConfig?.tunnelUrl || "";
});

const isRconEnabled = computed(() => {
  return instanceInfo.value?.config.enableRcon || false;
});

const tunnelPid = computed(() => {
  return instanceInfo.value?.config.extraServiceConfig?.tunnelPid || 0;
});

const isTunnelRunning = computed(() => {
  return !!tunnelUrl.value; // Tunnel is running if URL exists
});

const extractedTunnelUrl = computed(() => {
  // Extract URL from status logs like: "Current URL: xxx.pinggy.link:port"
  if (!tunnelLogs.value) return "";
  const match = tunnelLogs.value.match(/Current URL: ([a-zA-Z0-9.-]+\.pinggy\.link:\d+)/);
  return match ? match[1] : "";
});

const displayTunnelUrl = computed(() => {
  // Prefer extracted URL from logs, fallback to stored URL
  return extractedTunnelUrl.value || tunnelUrl.value;
});

onMounted(async () => {
  if (instanceId && daemonId) {
    await execute({
      params: {
        uuid: instanceId,
        daemonId: daemonId
      }
    });
  }
});
</script>

<template>
  <!-- eslint-disable vue/html-indent -->
  <CardPanel class="containerWrapper" style="height: 100%">
    <template #title>
      {{ card.title }}
    </template>
    <template #body>
      <a-typography-paragraph>
        {{ t("TXT_CODE_7ec9c59c") }}{{ getInstanceName }}
      </a-typography-paragraph>
      <a-typography-paragraph>
        <div class="flex flex-wrap instance-tag">
          <!-- instance status -->
          <a-tag v-if="isRunning" color="green" class="tag">
            <CheckCircleOutlined />
            {{ statusText }}
          </a-tag>
          <a-tag v-else-if="isStopped" class="tag">
            <ExclamationCircleOutlined />
            {{ statusText }}
          </a-tag>
          <a-tag v-else class="tag" color="pink">
            {{ statusText }}
          </a-tag>

          <!-- instance type -->
          <a-tag class="tag" color="purple"> {{ instanceTypeText }}</a-tag>

          <a-tag color="purple" class="tag">
            {{ t("TXT_CODE_ad30f3c5") }}{{ instanceInfo?.started }}
          </a-tag>
          
          <a-tag color="purple" class="tag">
            {{ t("TXT_CODE_6420023d") }}{{ instanceInfo?.autoRestarted }}
          </a-tag>

          <!-- real tags -->
          <a-tag v-for="tag in instanceInfo?.config.tag" :key="tag" class="tag" color="blue">
            {{ tag }}
          </a-tag>
        </div>
      </a-typography-paragraph>

      <!-- Server Setup Button -->
      <a-typography-paragraph v-if="!isRconEnabled" style="margin-top: 16px;">
        <a-button 
          type="primary" 
          size="small"
          :loading="setupTunnelLoading"
          @click="setupTunnel"
        >
          <template #icon><ThunderboltOutlined /></template>
          Setup Server (Accept EULA + Enable RCON)
        </a-button>
      </a-typography-paragraph>

      <!-- Start Tunnel Button -->
      <a-typography-paragraph v-if="isRconEnabled && !isTunnelRunning" style="margin-top: 16px;">
        <a-button 
          type="primary" 
          size="small"
          :loading="startTunnelLoading"
          @click="startTunnel"
        >
          <template #icon><ThunderboltOutlined /></template>
          Start Tunnel Manager
        </a-button>
        <div style="margin-top: 8px; font-size: 12px; color: #666;">
          This will start the tunnel script in the background. The URL will appear below in a few seconds.
        </div>
      </a-typography-paragraph>

      <!-- Tunnel Controls (when running) -->
      <a-typography-paragraph v-if="isTunnelRunning" style="margin-top: 16px;">
        <a-space>
          <a-button 
            danger
            size="small"
            :loading="stopTunnelLoading"
            @click="stopTunnel"
          >
            <template #icon><StopOutlined /></template>
            Stop Tunnel
          </a-button>
          <a-button 
            size="small"
            @click="toggleLogs"
          >
            <template #icon><ReloadOutlined /></template>
            {{ showLogs ? 'Hide Logs' : 'Show Logs' }}
          </a-button>
        </a-space>
        <div v-if="tunnelPid" style="margin-top: 4px; font-size: 12px; color: #666;">
          Tunnel running (PID: {{ tunnelPid }})
        </div>
      </a-typography-paragraph>

      <!-- Display Tunnel URL when available (Prominent) -->
      <a-typography-paragraph v-if="displayTunnelUrl" style="margin-top: 16px;">
        <a-card size="small" style="background: #f6ffed; border: 1px solid #b7eb8f;">
          <div style="display: flex; flex-direction: column; gap: 8px;">
            <div style="display: flex; align-items: center; gap: 8px;">
              <span style="font-weight: 600; color: #52c41a; font-size: 14px;">🌐 Minecraft Server URL (TCP):</span>
            </div>
            <a-typography-text 
              :copyable="{ text: displayTunnelUrl, tooltip: ['Copy Server Address', 'Copied!'] }"
              code
              style="background: #fff; padding: 8px 12px; border-radius: 4px; font-size: 13px; font-weight: 500;"
            >
              {{ displayTunnelUrl }}
            </a-typography-text>
            <div style="font-size: 11px; color: #666; margin-top: 4px;">
              Copy this address and use it in Minecraft's "Multiplayer → Add Server" to connect
            </div>
          </div>
        </a-card>
      </a-typography-paragraph>

      <!-- Tunnel Logs -->
      <a-typography-paragraph v-if="showLogs && isTunnelRunning" style="margin-top: 8px;">
        <a-card size="small" title="Tunnel Manager Logs" :loading="logsLoading">
          <pre style="background: #1e1e1e; color: #d4d4d4; padding: 12px; border-radius: 4px; max-height: 300px; overflow-y: auto; font-size: 11px; margin: 0;">{{ tunnelLogs || 'Loading logs...' }}</pre>
        </a-card>
      </a-typography-paragraph>

      <a-typography-paragraph v-if="instanceGameServerInfo">
        <span>{{ t("TXT_CODE_855c4a1c") }}</span>
        <span>{{ instanceGameServerInfo.players }}</span>
      </a-typography-paragraph>
      <a-typography-paragraph v-if="instanceGameServerInfo">
        <span>
          {{ t("TXT_CODE_e260a220") }}
        </span>
        <span>
          {{ instanceGameServerInfo.version }}
        </span>
      </a-typography-paragraph>

      <template v-if="instanceInfo?.config.processType === 'docker'">
        <a-typography-paragraph>
          {{ t("TXT_CODE_4f917a65") }}
          <a href="javascript:;" @click="DockerInfoDialog?.openDialog()">
            {{ t("TXT_CODE_530f5951") }}
          </a>
        </a-typography-paragraph>
      </template>

      <a-typography-paragraph v-if="Number(instanceInfo?.info?.allocatedPorts?.length) > 0">
        {{ t("TXT_CODE_2e4469f6") }}
        <div style="padding: 10px 0px 0px 16px">
          <div
            v-for="(item, index) in instanceInfo?.info?.allocatedPorts"
            :key="index"
            class="mb-4"
          >
            <span>
              <a-tag color="green">{{ item.protocol.toUpperCase() }}</a-tag>
            </span>
            <a-tag>
              <span>{{ t("TXT_CODE_8dfc41ef") }}: {{ item.host }}</span>
              <span class="ml-4"> {{ t("TXT_CODE_8f8103b7") }}: {{ item.container }} </span>
            </a-tag>
          </div>
        </div>
      </a-typography-paragraph>

      <a-typography-paragraph v-if="!instanceGameServerInfo">
        {{ t("TXT_CODE_8b8e08a6") }}{{ parseTimestamp(instanceInfo?.config.createDatetime) }}
      </a-typography-paragraph>
      <a-typography-paragraph>
        {{ t("TXT_CODE_46f575ae") }}{{ parseTimestamp(instanceInfo?.config.lastDatetime) }}
      </a-typography-paragraph>
      <a-typography-paragraph>
        <a-typography-text :title="instanceInfo?.instanceUuid">
          {{ t("TXT_CODE_30051f9b") }}
        </a-typography-text>
        <a-typography-text :copyable="{ text: instanceInfo?.instanceUuid }"> </a-typography-text>
        <a-typography-text class="ml-20" :title="daemonId">
          {{ t("TXT_CODE_5f2d2e30") }}
        </a-typography-text>
        <a-typography-text :copyable="{ text: daemonId }"> </a-typography-text>
      </a-typography-paragraph>
    </template>
  </CardPanel>

  <DockerInfo ref="DockerInfoDialog" :docker-info="instanceInfo?.config.docker" />
</template>

<style lang="scss" scoped>
.instance-tag {
  margin-left: -4px;
  margin-right: -4px;
  .tag {
    margin: 4px;
  }
}
</style>
