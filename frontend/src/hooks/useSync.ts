import { useCallback, useRef, useState } from "react";
import { api, type SyncResponse } from "../api/client";

export function useSync() {
  const [isSyncing, setIsSyncing] = useState(false);
  const [lastSync, setLastSync] = useState<string | null>(null);
  const [filesCount, setFilesCount] = useState(0);
  const [syncResult, setSyncResult] = useState<SyncResponse | null>(null);
  const [syncError, setSyncError] = useState<string | null>(null);
  const didInit = useRef<boolean | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const status = await api.getSyncStatus();
      setLastSync(status.last_sync);
      setFilesCount(status.files_synced);
    } catch {
      // non-critical
    }
  }, []);

  if (didInit.current == null) {
    didInit.current = true;
    fetchStatus();
  }

  const triggerSync = useCallback(async () => {
    if (isSyncing) return;
    setIsSyncing(true);
    setSyncResult(null);
    setSyncError(null);
    try {
      const result = await api.triggerSync();
      setSyncResult(result);
      if (result.limit_reached) {
        setSyncError("Vector limit reached — some files were skipped.");
      }
      await fetchStatus();
    } catch (e) {
      setSyncError(e instanceof Error ? e.message : "Sync failed.");
    } finally {
      setIsSyncing(false);
    }
  }, [isSyncing, fetchStatus]);

  const clearSyncError = useCallback(() => setSyncError(null), []);

  return { isSyncing, lastSync, filesCount, syncResult, syncError, clearSyncError, triggerSync };
}
