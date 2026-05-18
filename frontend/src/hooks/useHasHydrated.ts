"use client";

import { useSyncExternalStore } from "react";

// function to subscribe to changes
function subscribe() {
  return () => { };
}

// function to get the client snapshot
function getClientSnapshot() {
  return true;
}

// function to get the server snapshot
function getServerSnapshot() {
  return false;
}

/**
 * Stable hydration flag for values that should differ between SSR and client.
 */
export function useHasHydrated(): boolean {
  return useSyncExternalStore(
    subscribe,
    getClientSnapshot,
    getServerSnapshot
  );
}