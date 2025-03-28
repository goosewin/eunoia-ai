# Eunoia - AI Recruiting Assistant

Eunoia is an agentic AI recruiting assistant that helps users create effective outreach sequences for candidate recruitment.

## Features

- Two-panel interface with chat and workspace areas
- Real-time AI-generated outreach sequences
- Customizable sequence steps with multiple channels (email, LinkedIn)
- WebSocket integration for real-time updates

## Tech Stack

### Frontend
- Next.js 15.x
- React 19.x
- TypeScript
- TailwindCSS 4.x
- Socket.io-client

### Backend
- Flask 3.x
- SQLAlchemy
- PostgreSQL
- Flask-SocketIO
- OpenAI API

## Setup Instructions

### Prerequisites
- Node.js and bun
- Python 3.10+
- PostgreSQL

### Environment Variables
Create a `.env` file in the root directory with:

```
DATABASE_URL=postgresql://postgres:postgres@localhost/eunoia
OPENAI_API_KEY=your_openai_api_key
SECRET_KEY=your_secret_key
```

## Usage

1. Start a conversation with the AI assistant
2. Provide information about your recruiting needs
3. The AI will generate a customized outreach sequence
4. Edit and refine the sequence in the workspace panel
5. Save or copy the sequence for use in your recruiting campaigns
