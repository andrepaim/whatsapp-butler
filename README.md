# WhatsApp Watchdog 📱🔍

[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge)](LICENSE)

Your AI companion that can talk to your WhatsApp messages! WhatsApp Watchdog is a powerful AI assistant that helps you access, understand, and manage your WhatsApp conversations using natural language.

## How It Works

WhatsApp Watchdog operates with two types of WhatsApp accounts:

### Key Definitions

1. **Monitored Account**
   - The WhatsApp account that will be monitored and managed
   - This is the account you set up during the initial configuration
   - All messages, groups, and media from this account are accessible to the AI
   - Example: Your personal WhatsApp number

2. **Monitor Account**
   - The WhatsApp account(s) that will send queries to the monitored account
   - These are the authorized numbers configured in `webhook.json`
   - This account receives the AI's responses
   - Example: Your work phone number

### Real-World Use Cases

1. **Personal Assistant**
   Let's say you have:
   - **Monitored Account**: Your personal WhatsApp (+5511999999999)
   - **Monitor Account**: Your work phone (+5511888888888)

   From your work phone, you can ask your personal WhatsApp:
   ```
   "What was the address my wife sent me yesterday?"
   "Find the restaurant recommendation from the Foodie group"
   "Summarize the last 10 messages in the family group"
   ```
   The AI will search your personal WhatsApp and send the answers back to your work phone.

2. **Business Customer Support**
   - **Monitored Account**: Company's official WhatsApp number
   - **Monitor Account**: Customer service team members' numbers
   
   Team members can ask:
   ```
   "What was the last message from customer +5511999999999?"
   "Summarize all complaints received in the last 24 hours"
   "Find the conversation where the customer mentioned the delivery issue"
   ```

3. **Team Communication Management**
   - **Monitored Account**: Project manager's WhatsApp
   - **Monitor Account**: Team members' numbers
   
   Team members can ask:
   ```
   "What was discussed in the Project X group yesterday?"
   "Find the meeting schedule that Sarah shared last week"
   "Summarize the feedback from the client in the Client Updates group"
   ```

### Key Benefits

1. **Remote Access**
   - Access WhatsApp information from any authorized device
   - No need to switch phones or accounts

2. **Natural Language Interface**
   - Ask questions in plain English
   - No need to remember specific commands

3. **Contextual Understanding**
   - AI understands the context of conversations
   - Can provide relevant summaries and explanations

4. **Privacy Control**
   - Only authorized numbers can interact
   - Clear separation between monitored and monitoring accounts

## Project Overview

WhatsApp Watchdog uses Google's Gemini AI for natural language understanding and the WhatsApp MCP server for WhatsApp integration. It can help you:

- 📝 Generate summaries of past messages
- 🔍 Find specific messages with context
- 📤 Forward messages with added context
- 💬 Process complex queries about conversations
- 🧠 Maintain context of group interactions

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
GOOGLE_API_KEY=your_google_api_key
GOOGLE_GENAI_USE_VERTEXAI=false  # Set to true if using Vertex AI
AGENT_MODEL=your_agent_model_name (e.g. gemini-2.0-flash)
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
```bash
User: Summarize yesterday's messages in the family group
Assistant: [Provides a summary of yesterday's messages]
```

2. **Message Search**
```bash
User: What was the last message from John about the meeting?
Assistant: [Retrieves and explains the message with context]
```

3. **Message Forwarding**
```bash
User: Forward Sarah's party invitation from last week
Assistant: [Forwards the message with a summary]
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
   - Check `webhook.json` configuration

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
curl http://localhost:3001/api/status  # WhatsApp API
curl http://localhost:3002/status # Whatsapp MCP server
curl http://localhost:8000/health        # Webhook
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
