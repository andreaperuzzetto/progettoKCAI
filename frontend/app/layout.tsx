import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Nav from "./components/nav";
import Providers from "./components/providers";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Restaurant AI — Analisi recensioni",
  description: "Trasforma le recensioni dei clienti in decisioni operative",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="it">
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased bg-gray-50 min-h-screen`}>
        <Providers>
          <Nav />
          <main className="max-w-4xl mx-auto px-6 py-8">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
