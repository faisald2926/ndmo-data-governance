import type { Metadata } from "next";
import "./globals.css";
import { QueryProvider } from "@/hooks/QueryProvider";
import { AuthProvider } from "@/hooks/useAuth";

export const metadata: Metadata = {
  title: "NDMO حوكمة البيانات",
  description: "منصة حوكمة البيانات — المكتب الوطني لإدارة البيانات",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ar" dir="rtl">
      <body style={{ fontFamily: "system-ui, Arial, sans-serif" }}>
        <QueryProvider>
          <AuthProvider>{children}</AuthProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
