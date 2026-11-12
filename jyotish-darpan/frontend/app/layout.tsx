import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = { title: "Jyotish Darpan | Vedic Birth Chart", description: "Generate a sidereal Vedic birth chart with planetary positions, D1, D9 and Vimshottari dasha." };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
