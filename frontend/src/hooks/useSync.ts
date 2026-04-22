import { useCallback, useEffect, useState } from "react";
import { api, type SyncResponse } from "../api/client";

export function useSync() {
  const [isSyncing, setIsSyncing] = useState(false);
  const [lastSync, setLastSync] = useState<string | null>(null);
  const [filesCount, setFilesCount] = useState(0);
  const [syncResult, setSyncResult] = useState<SyncResponse | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const status = await api.getSyncStatus();
      setLastSync(status.last_sync);
      setFilesCount(status.files_synced);
    } catch {
      // ignore
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
      // sync failed
    } finally {
      setIsSyncing(false);
    }
  }, [isSyncing, fetchStatus]);

  useEffect(() => { fetchStatus(); }, [fetchStatus]);

  return { isSyncing, lastSync, filesCount, syncResult, triggerSync };
}
