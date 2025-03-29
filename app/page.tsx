"use client"

import { AppWrapper } from "@/app/components/app-wrapper"
import { AgentProvider } from "@/app/contexts/agent-context"

export default function Home() {
  return (
    <main className="min-h-screen bg-[hsl(var(--color-gray-light))]">
      <AgentProvider>
        <AppWrapper />
      </AgentProvider>
    </main>
  )
}
