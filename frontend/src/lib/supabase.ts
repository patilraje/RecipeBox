import { createClient, type SupabaseClient } from "@supabase/supabase-js";

const url = process.env.NEXT_PUBLIC_SUPABASE_URL || "";
const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";

export function isSupabaseConfigured(): boolean {
  return Boolean(url && anonKey);
}

let browserClient: SupabaseClient | null = null;

export function getSupabase(): SupabaseClient | null {
  if (!isSupabaseConfigured()) return null;
  if (typeof window === "undefined") {
    return createClient(url, anonKey);
  }
  if (!browserClient) {
    browserClient = createClient(url, anonKey);
  }
  return browserClient;
}
