import type React from "react"
import { Inter } from "next/font/google"
import "./globals.css"

const inter = Inter({ subsets: ["latin"] })

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        <title>EUNOIA AI</title>
        <meta name="description" content="AI-powered campaign sequence generator" />
      </head>
      <body className={inter.className}>{children}</body>
    </html>
  )
}

