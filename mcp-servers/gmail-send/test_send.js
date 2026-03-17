const { sendEmail } = require('./index.js');

(async () => {
  const to = 'purposework56@gmail.com';
  const subject = 'MCP Test - AI Employee Working';
  const timestamp = new Date().toISOString();
  const body = `This confirms the Gmail MCP server is functional. Sent at ${timestamp}`;

  try {
    const result = await sendEmail(to, subject, body);
    console.log('SendEmail Result:', result);
    if (result.success) {
      console.log('Email sent successfully!');
    } else {
      console.error('Failed to send email:', result.error);
    }
  } catch (err) {
    console.error('Error calling sendEmail:', err);
  }
})();
