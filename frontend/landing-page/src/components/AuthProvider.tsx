"use client";

import { useEffect } from "react";
import { configureAmplify } from "@/lib/amplify-config";

/**
 * Client component wrapper that configures Amplify once on mount.
 * Wrap layout.tsx body with this so Amplify is available everywhere.
 */
export function AuthProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    configureAmplify();
  }, []);

  return <>{children}</>;
}
