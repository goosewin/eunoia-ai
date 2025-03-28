# Eunoia Agentic Recruiter - Implementation Plan

## 1. Architecture

**Frontend (Next.js + TypeScript)**
- Two-panel layout: Chat interface (left) + Dynamic workspace (right)
- React components with TypeScript
- Socket.io for real-time updates
- TailwindCSS for styling

**Backend (Flask)**
- RESTful API endpoints
- WebSocket server for real-time updates
- Agent framework with LLM integration
- Database connection layer

**Database (PostgreSQL)**
- User profiles
- Outreach sequences
- Chat messages

## 2. Core Components

### Frontend Components
```
app/
├── components/
│   ├── Chat/
│   │   ├── ChatContainer.tsx
│   │   ├── ChatMessage.tsx
│   │   ├── ChatInput.tsx
│   │   └── ToolCallNotification.tsx
│   ├── Workspace/
│   │   ├── WorkspaceContainer.tsx
│   │   ├── SequenceEditor.tsx
│   │   └── SequenceStep.tsx
│   └── UI/
│       ├── Button.tsx
│       ├── Loading.tsx
│       └── Notification.tsx
├── contexts/
│   └── AgentContext.tsx
└── pages/
    └── index.tsx
```

### Backend Components
```
api/
├── routes/
│   ├── chat.py
│   ├── sequence.py
│   └── user.py
├── models/
│   ├── user.py
│   ├── sequence.py
│   └── message.py
├── agent/
│   ├── agent.py
│   ├── tools.py
│   ├── prompts.py
│   └── llm.py
├── websocket.py
├── db.py
└── index.py
```

## 3. API Endpoints

### Chat API
- `POST /api/chat` - Send message to agent
- `GET /api/chat/:sessionId` - Get chat history

### Sequence API
- `GET /api/sequences` - List all sequences
- `GET /api/sequences/:id` - Get specific sequence
- `POST /api/sequences` - Create sequence
- `PUT /api/sequences/:id` - Update sequence
- `DELETE /api/sequences/:id` - Delete sequence

### User API
- `GET /api/user` - Get user profile
- `POST /api/user` - Create/update profile

## 4. Agent Tools

```python
tools = [
  {
    "type": "function",
    "function": {
      "name": "generate_sequence",
      "description": "Generate a recruiting outreach sequence",
      "parameters": {
        "type": "object",
        "properties": {
          "company_name": {"type": "string"},
          "target_role": {"type": "string"},
          "industry": {"type": "string"},
          "num_steps": {"type": "integer"},
          "tone": {"type": "string"},
          "value_proposition": {"type": "string"}
        },
        "required": ["company_name", "target_role"]
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "update_sequence",
      "description": "Update an existing sequence",
      "parameters": {
        "type": "object",
        "properties": {
          "sequence_id": {"type": "string"},
          "changes": {"type": "array", "items": {"type": "object"}}
        },
        "required": ["sequence_id", "changes"]
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "research_industry",
      "description": "Research information about industry",
      "parameters": {
        "type": "object",
        "properties": {
          "industry": {"type": "string"}
        },
        "required": ["industry"]
      }
    }
  }
]
```

## 5. WebSocket Events

**Server → Client**
- `chat_message` - New AI message
- `sequence_update` - Sequence changed
- `tool_call_start` - AI using tool
- `tool_call_end` - AI finished using tool

**Client → Server**
- `chat_message` - User message
- `sequence_edit` - User edited sequence
- `new_session` - New chat session

## 6. Bonus Features (If Time Permits)

- [ ] User authentication
- [ ] Sequence templates
- [ ] Email integration
- [ ] Analytics dashboard
- [ ] Advanced research tools
