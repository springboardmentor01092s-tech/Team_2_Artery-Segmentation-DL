import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

// Adapted from Codehagen/Prismui src/lib/utils.ts (AGPL-3.0).
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
