import { useCallback, useEffect, useRef, useState } from "react";
import { api, type SyncResponse } from "../api/client";

export function useSync() {
  const [isSyncing, setIsSyncing] = useState(false);
  const [lastSync, setLastSync] = useState<string | null>(null);
  const [filesCount, setFilesCount] = useState(0);
  const [syncResult, setSyncResult] = useState<SyncResponse | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const fetchStatus = useCallback(async () => {
    try {
      const status = await api.getSyncStatus();
      setLastSync(status.last_sync);
      setFilesCount(status.files_synced);
    } catch {
      // ignore status fetch errors
    }
  }, []);

  const triggerSync = useCallback(async () => {
    if (isSyncing) return;
    setIsSyncing(true);
    setSyncResult(null);

    try {
      const result = await api.triggerSync();
      setSyncResult(result);
      await fetchStatus();
    } catch {
      // sync failed silently
    } finally {
      setIsSyncing(false);
    }
  }, [isSyncing, fetchStatus]);

  useEffect(() => {
    fetchStatus();
    return stopPolling;
  }, [fetchStatus, stopPolling]);

  return { isSyncing, lastSync, filesCount, syncResult, triggerSync };
}
