import type { Metadata } from "next";
import { Figtree, Fraunces } from "next/font/google";
import { AuthProvider } from "@/components/AuthProvider";
import { SiteNav } from "@/components/SiteNav";
import "./globals.css";

const fraunces = Fraunces({
  variable: "--font-fraunces",
  subsets: ["latin"],
  display: "swap",
});

const figtree = Figtree({
  variable: "--font-figtree",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "RecipeBox",
  description:
    "Find and generate recipes you can make using only the ingredients you already have.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${fraunces.variable} ${figtree.variable} antialiased`}>
        <AuthProvider>
          <div className="site-shell">
            <SiteNav />
            {children}
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
