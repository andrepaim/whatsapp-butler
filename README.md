# WhatsApp Butler 🤖👔

[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge)](LICENSE)

Your AI butler that helps you manage your WhatsApp messages! WhatsApp Butler is a sophisticated AI assistant that helps you access, understand, and manage your WhatsApp conversations with the elegance and efficiency of a professional butler.

## How It Works

WhatsApp Butler is an AI-powered assistant that integrates with your WhatsApp account to help you manage and understand your conversations. By prefixing your messages with `@paimai`, you can ask your butler to search through your chats, summarize conversations, find specific information, and more. The AI processes your requests using Google's Gemini AI and responds directly in your WhatsApp chat, providing you with the same level of service and attention to detail as a professional butler would.

WhatsApp Butler uses Google's Gemini AI for natural language understanding and the WhatsApp MCP server for WhatsApp integration. It can help you:

- 📝 Generate summaries of past messages
- 🔍 Find specific messages with context
- 📤 Forward messages with added context
- 💬 Process complex queries about conversations
- 🧠 Maintain context of group interactions



### Key Features

1. **Message Management**
   - Search through your entire WhatsApp history
   - Find specific messages
   - Get summaries of conversations
   - Send messages to any contact or group

2. **Smart Commands**
   - Start any request with `@paimai`
   - Ask questions in natural language
   - Get instant responses in the same chat
   - Customize the command prefix if desired

3. **Intelligent Assistance**
   - Understands context and conversation history
   - Can handle complex queries about your messages
   - Provides relevant information and summaries
   - Maintains privacy by only processing prefixed messages

### Real-World Use Cases

   ```
   @paimai Find the restaurant address Sarah shared last week
   @paimai Send a message to Mom saying I'll be late for dinner
   @paimai What was the plumber's phone number from the family group?
   @paimai Summarize the important points from the school parents group
   ```

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.9 or higher
- WhatsApp account
- Google API key for Gemini AI
- Sudo access (for setup script)

### Installation

1. Clone the repository with submodules:
```bash
git clone --recursive https://github.com/andrepaim/whatsapp-watchdog.git
cd whatsapp-watchdog
```

2. Create a `.env` file with required variables:
```bash
# WhatsApp API Configuration
WHATSAPP_API_KEY=your_whatsapp_api_key
WHATSAPP_API_URL=http://localhost:3000/api
MESSAGE_PREFIX=@paimai  # Optional: customize the command prefix

# Google AI Configuration
GOOGLE_API_KEY=your_google_api_key
GOOGLE_GENAI_USE_VERTEXAI=false  # Set to true if using Vertex AI
AGENT_MODEL=your_agent_model_name (e.g. gemini-2.0-flash)

# Webhook Configuration
WEBHOOK_PORT=8000  # Port for the webhook server
```

3. Run the setup script:
```bash
chmod +x setup-whatsapp.sh
./setup-whatsapp.sh
```

4. Start the services:
```bash
make docker-compose-up
```

## Architecture

The system consists of three main services:

### WhatsApp API Service
- Handles WhatsApp Web authentication
- Manages message operations
- Provides REST API endpoints
- Maintains persistent session

### WhatsApp MCP Service 
- Provides Server-Sent Events (SSE)
- Handles real-time message streaming
- Connects to WhatsApp API service
- Processes message events

### Webhook Service 
- Processes incoming webhook requests
- Integrates with Google's Gemini AI
- Manages conversation context
- Generates AI responses

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| WHATSAPP_API_KEY | API key for WhatsApp services | Required |
| WHATSAPP_API_URL | URL for WhatsApp API service | http://localhost:3000/api |
| MESSAGE_PREFIX | Command prefix for AI interaction | @paimai |
| GOOGLE_API_KEY | API key for Google Gemini AI | Required |
| GOOGLE_GENAI_USE_VERTEXAI | Use Vertex AI instead of Gemini API | false |
| AGENT_MODEL | Gemini AI model to use | gemini-2.0-flash |

## Usage

### Basic Commands

```bash
# Start all services
make docker-compose-up

# View logs
make docker-compose-logs

# Stop services
make docker-compose-down
```

### Example Interactions

1. **Message Summarization**
```
You: @paimai Summarize yesterday's messages in the family group
Assistant: [Provides a summary of yesterday's messages]
```

2. **Message Search**
```
You: @paimai What was the last message from John about the meeting?
Assistant: [Retrieves and explains the message with context]
```

3. **Message Forwarding**
```
You: @paimai Forward Sarah's party invitation from last week
Assistant: [Forwards the message with a summary]
```

4. **Complex Queries**
```
You: @paimai Find all messages about the project deadline in the last week
Assistant: [Searches and summarizes relevant messages]

You: @paimai What was the most discussed topic in the family group this month?
Assistant: [Analyzes and provides insights about group discussions]
```

## Development

### Submodule Management

Update the WhatsApp MCP submodule:
```bash
cd whatsapp-mcp
git pull origin main
cd ..
git add whatsapp-mcp
git commit -m "Update wweb-mcp to latest version"
```

## Deployment

### Docker Deployment

1. Build and start services:
```bash
make docker-compose-up
```

2. Monitor service health:
```bash
make docker-compose-logs
```

## Troubleshooting

### Common Issues

1. **Session Data Issues**
   - Location: `whatsapp-session-data/`
   - Solution: Remove directory and restart services

2. **Service Start Failures**
   - Check logs: `make docker-compose-logs`
   - Verify API keys in `.env`
   - Check webhook configuration

3. **QR Code Authentication**
   - Ensure WhatsApp API service is running
   - Check logs for QR code display
   - Verify session data permissions

### Debugging

1. Check service logs:
```bash
make docker-compose-logs
```

2. Verify service health:
```bash
curl http://localhost:8000/health
```

## Maintenance

### Session Management

- Session data is stored in `whatsapp-session-data/`
- Regular cleanup recommended
- Backup before updates

### Security Considerations

- Keep API keys secure
- Regular updates of dependencies
- Monitor service logs
- Review allowed numbers in `webhook.json`

## License and Acknowledgments

- **License**: MIT
- **WhatsApp Integration**: [wweb-mcp](https://github.com/pnizer/wweb-mcp)
- **AI Framework**: Google Gemini AI
- **Containerization**: Docker and Docker Compose
