const { createRequire } = require('module');
const path = require('path');
const fs = require('fs');

// Since the SDK uses exports map "./*": "./dist/*", we can access it directly
const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const { ListToolsRequestSchema, CallToolRequestSchema, ListToolsResultSchema, CallToolResultSchema } = require('@modelcontextprotocol/sdk/types.js');

const { google } = require('googleapis');

// Define our available tools
const availableTools = [
  {
    name: 'send_email',
    description: 'Send an email via Gmail',
    inputSchema: {
      type: 'object',
      properties: {
        to: {
          type: 'string',
          description: 'Email address to send to'
        },
        subject: {
          type: 'string',
          description: 'Subject of the email'
        },
        body: {
          type: 'string',
          description: 'Body content of the email'
        }
      },
      required: ['to', 'subject', 'body']
    }
  }
];

// Initialize the MCP server with tools capability
const server = new Server({
  name: 'gmail-send',
  version: '1.0.0',
}, {
  capabilities: {
    tools: {} // Declare that we support tools
  }
});

// Handle the tools/list request to return available tools
server.setRequestHandler(ListToolsRequestSchema, (request) => {
  const { params } = request;
  const startIndex = params?.cursor ? parseInt(params.cursor, 10) : 0;
  const endIndex = Math.min(startIndex + 100, availableTools.length); // Simple pagination

  const tools = availableTools.slice(startIndex, endIndex);
  const nextCursor = endIndex < availableTools.length ? endIndex.toString() : undefined;

  return {
    tools,
    nextCursor
  };
});

// Handle the tools/call request to execute tools
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  // Find the tool
  const tool = availableTools.find(t => t.name === name);
  if (!tool) {
    throw new Error(`Tool "${name}" not found`);
  }

  try {
    // Execute the send_email tool
    if (name === 'send_email') {
      return await sendEmail(args.to, args.subject, args.body);
    } else {
      throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    throw new Error(`Error executing tool ${name}: ${error.message}`);
  }
});

// Function to send email
async function sendEmail(to, subject, body) {
  try {
    const vaultDir = process.env.VAULT_DIR || path.resolve(__dirname, '..', '..');
    const credentialsPath = process.env.CREDENTIALS_PATH || path.join(vaultDir, 'credentials', 'credentials.json');
    const tokenPath = process.env.TOKEN_PATH || path.join(vaultDir, 'credentials', 'token.json');

    if (!fs.existsSync(credentialsPath)) {
      throw new Error(`Credentials file not found at ${credentialsPath}`);
    }

    if (!fs.existsSync(tokenPath)) {
      throw new Error(`Token file not found at ${tokenPath}`);
    }

    const credentials = JSON.parse(fs.readFileSync(credentialsPath, 'utf8'));
    const token = JSON.parse(fs.readFileSync(tokenPath, 'utf8'));

    // Create OAuth2 client
    const { client_secret, client_id, redirect_uris } = credentials.installed;
    const oAuth2Client = new google.auth.OAuth2(client_id, client_secret, redirect_uris[0]);

    // Set the credentials
    oAuth2Client.setCredentials(token);

    // Create Gmail API client
    const gmail = google.gmail({ version: 'v1', auth: oAuth2Client });

    // Create the email message
    const emailLines = [
      `To: ${to}`,
      `Subject: ${subject}`,
      '',
      body
    ];

    const emailContent = emailLines.join('\r\n');
    const encodedMessage = Buffer.from(emailContent).toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');

    // Send the email
    const response = await gmail.users.messages.send({
      userId: 'me',
      requestBody: {
        raw: encodedMessage
      }
    });

    return {
      success: true,
      messageId: response.data.id,
      message: `Email sent successfully to ${to}`
    };
  } catch (error) {
    console.error('Error sending email:', error);
    return {
      success: false,
      error: error.message
    };
  }
}

// Start the server with stdio transport
async function startServer() {
  try {
    const transport = new StdioServerTransport();
    await server.connect(transport);
    console.log('Gmail MCP server started successfully');
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
}


module.exports = { sendEmail };

if (require.main === module) {
  startServer();
}
