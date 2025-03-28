"use client"

import { EunoiaAI } from "@/app/components/eunoia-ai"
import { AgentProvider } from "@/app/contexts/AgentContext"

export default function Home() {
  return (
    <main className="min-h-screen bg-[hsl(var(--color-gray-light))]">
      <AgentProvider>
        <EunoiaAI />
      </AgentProvider>
    </main>
  )
}
