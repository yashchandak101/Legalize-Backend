# Claude API Setup Guide

## 1. Get Claude API Key

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the API key

## 2. Configure Environment Variables

Add your Claude API key to your environment:

### Option A: .env file (recommended)
```bash
CLAUDE_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Option B: System environment variable
```bash
export CLAUDE_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## 3. Install Dependencies

The required packages are already in requirements.txt:
```
anthropic==0.83.0
```

Install them:
```bash
pip install -r requirements.txt
```

## 4. Test the Integration

The system will automatically use Claude API when:
- CLAUDE_API_KEY is set in environment
- The anthropic package is installed
- API key is valid

## 5. Features

### Claude Integration:
- **Real AI responses** using Claude 3 Haiku model
- **Context awareness** - remembers conversation history
- **Legal specialization** - system prompts for legal assistance
- **Fallback protection** - uses fallback responses if API fails

### Legal Categories Supported:
- Family Law
- Criminal Law
- Civil Law
- Corporate Law
- Immigration Law
- Employment Law
- Real Estate Law
- Other

### System Prompts:
- Professional legal assistant persona
- Emphasizes general information (not specific advice)
- Recommends consulting qualified attorneys
- Provides relevant legal sources

## 6. Troubleshooting

### If Claude doesn't work:
1. Check API key is correctly set
2. Verify internet connectivity
3. Check Anthropic API status
4. Review logs for error messages

### Fallback Behavior:
- System automatically falls back to pre-written responses
- Users still get helpful legal information
- No interruption in service

## 7. Usage Limits

- Claude 3 Haiku: 1000 tokens per response
- Conversation history: Last 10 messages
- Rate limits: Follow Anthropic's API limits

## 8. Security

- API key is stored securely in environment variables
- No API keys in code or version control
- All API calls are logged for monitoring
