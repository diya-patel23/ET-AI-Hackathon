import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import { RoleProvider } from "@/components/RoleContext";

export const metadata: Metadata = {
  title: "Unified Asset & Operations Brain",
  description: "Industrial Knowledge Intelligence Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full">
      <body className="min-h-full" style={{ background: "var(--ink)" }}>
        <RoleProvider>
          <div className="flex">
            <Sidebar />
            <main className="flex-1 min-w-0">{children}</main>
          </div>
        </RoleProvider>
      </body>
    </html>
  );
}
