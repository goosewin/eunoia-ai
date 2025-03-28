"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

export function EunoiaAI() {
  const [campaignIdea, setCampaignIdea] = useState("")
  const [isGenerating, setIsGenerating] = useState(false)
  const [messages, setMessages] = useState([
    { type: "system", text: "Hi! What kind of campaign are you looking to run today?" },
    { type: "user", text: "I want to target homeowners in LA." },
    { type: "system", text: "Got it. Is there anything specific you'd like to highlight?" },
    { type: "user", text: "They had a big fire recently. We want to offer help through our gov. aid prog." },
    { type: "system", text: "That's a great angle..." },
    { type: "user", text: "Generating sequence...", isGenerating: true },
  ])

  const [sequenceSteps, setSequenceSteps] = useState([
    {
      step: 1,
      content:
        "Hi {{first name}}. I've been keeping up with the news'n L.A. I hope you and your family are safe. Let us know if we can help in any way.",
    },
    {
      step: 2,
      content:
        "I work at Trajillo Tech – we released a new government aid program for homeowners affected by the wildfires. Up to 32mil in aid. Let me know if you'd like to learn more.",
    },
    {
      step: 3,
      content: "Also... it's a fully government supported program. No cost or burden to you whatsoever. Let me know!",
    },
  ])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!campaignIdea.trim()) return

    // Add user message
    setMessages((prev) => [...prev, { type: "user", text: campaignIdea }])

    // Simulate API call to Flask backend
    setIsGenerating(true)

    // This would be replaced with an actual API call to your Flask backend
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          type: "system",
          text: "I've generated a new sequence based on your input.",
        },
      ])
      setIsGenerating(false)

      // Here you would update the sequence steps based on the API response
      // For now, we'll just keep the existing ones
    }, 1500)

    setCampaignIdea("")
  }

  return (
    <div className="w-full">
      {/* Header */}
      <header className="flex flex-col sm:flex-row justify-between items-center p-4 sm:p-6 bg-white border-b border-gray-200">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-800 mb-2 sm:mb-0">EUNOIA AI</h1>
        <h2 className="text-lg sm:text-xl text-gray-700">Step 2 of 4: Review Generated Sequence</h2>
      </header>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 p-4 sm:p-6">
        {/* Chat Panel */}
        <div className="bg-white rounded-lg shadow-sm p-4 sm:p-6">
          <div className="space-y-4 mb-6 max-h-[60vh] overflow-y-auto">
            {messages.map((message, index) => (
              <div key={index} className={`flex ${message.type === "user" ? "justify-end" : "justify-start"}`}>
                <div
                  className={`max-w-[80%] rounded-2xl p-3 sm:p-4 ${
                    message.type === "user" ? "bg-blue-100 text-gray-800" : "bg-gray-100 text-gray-800"
                  } ${message.isGenerating ? "bg-indigo-100" : ""}`}
                >
                  {message.text}
                </div>
              </div>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="mt-auto">
            <div className="relative">
              <Input
                placeholder="Type your campaign idea..."
                value={campaignIdea}
                onChange={(e) => setCampaignIdea(e.target.value)}
                className="pr-20 py-5 border-gray-300"
                disabled={isGenerating}
              />
              <Button
                type="submit"
                size="sm"
                className="absolute right-2 top-1/2 transform -translate-y-1/2 bg-gray-600 hover:bg-gray-700 text-white"
                disabled={isGenerating || !campaignIdea.trim()}
              >
                SEND
              </Button>
            </div>
          </form>
        </div>

        {/* Sequence Panel */}
        <div className="bg-white rounded-lg shadow-sm">
          <div className="border-b border-gray-200 p-4 sm:p-6">
            <h3 className="text-xl sm:text-2xl font-semibold">Sequence</h3>
          </div>
          <div className="p-4 sm:p-6 space-y-6 sm:space-y-8">
            {sequenceSteps.map((step) => (
              <div key={step.step} className="grid grid-cols-[70px_1fr] sm:grid-cols-[80px_1fr] gap-3 sm:gap-4">
                <div className="font-semibold text-lg sm:text-xl">Step {step.step}</div>
                <div className="text-gray-700">{step.content}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

