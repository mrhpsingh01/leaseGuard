import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LeaseGuard | Athens, GA Residential Lease Auditor & Deposit Shield",
  description: "Applied AI PropTech web application for Athens, GA renters and UGA students. Evaluates residential lease PDFs with coordinate bounding boxes against Georgia landlord-tenant statutes and enforces security deposit return deadlines under O.C.G.A. § 44-7-35.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark h-full">
      <body className="h-full bg-slate-950 text-slate-100 flex flex-col antialiased">
        {children}
      </body>
    </html>
  );
}
