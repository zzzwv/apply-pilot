import { deleteDB, openDB, type DBSchema, type IDBPDatabase } from "idb";

import type { LocalApplication, LocalStatusLog, SyncMetadata } from "./applicationRepository";

export const LOCAL_DB_NAME = "job-tracker-local";
export const DB_VERSION = 1;

interface LocalDatabaseSchema extends DBSchema {
  applications: {
    key: string;
    value: LocalApplication;
    indexes: { "by-namespace": string };
  };
  status_logs: {
    key: string;
    value: LocalStatusLog;
    indexes: { "by-application": [string, string] };
  };
  sync_metadata: {
    key: string;
    value: SyncMetadata;
  };
}

let databasePromise: Promise<IDBPDatabase<LocalDatabaseSchema>> | undefined;

export function getLocalDatabase(): Promise<IDBPDatabase<LocalDatabaseSchema>> {
  databasePromise ??= openDB<LocalDatabaseSchema>(LOCAL_DB_NAME, DB_VERSION, {
    upgrade(database) {
      const applications = database.createObjectStore("applications", { keyPath: "storage_key" });
      applications.createIndex("by-namespace", "namespace");
      const statusLogs = database.createObjectStore("status_logs", { keyPath: "storage_key" });
      statusLogs.createIndex("by-application", ["namespace", "application_local_id"]);
      database.createObjectStore("sync_metadata", { keyPath: "storage_key" });
    },
  });
  return databasePromise;
}

export async function deleteLocalDatabase(): Promise<void> {
  if (databasePromise) {
    (await databasePromise).close();
    databasePromise = undefined;
  }
  await deleteDB(LOCAL_DB_NAME);
}
