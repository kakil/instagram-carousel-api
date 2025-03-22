# n8n Workflow Implementation Guide

## 1. Prerequisites

Before setting up the n8n workflow, ensure you have:

- n8n installed and running on your VPS
- Python 3.7+ installed for the Image Generation API
- A Google Sheet created with the required columns
- A Facebook Developer account and Instagram Business account
- SMTP credentials for email notifications

## 2. Image Generation API Setup

### 2.1 Install Required Packages

```bash
# Create a virtual environment
python -m venv carousel-api-env
source carousel-api-env/bin/activate

# Install required packages
pip install Flask Pillow numpy gunicorn

# Save requirements
pip freeze > requirements.txt
```

### 2.2 Deploy the Flask Application

Create a file named `app.py` with the Python code provided earlier.

### 2.3 Create a systemd Service

Create a file at `/etc/systemd/system/carousel-api.service`:

```ini
[Unit]
Description=Instagram Carousel Generator API
After=network.target

[Service]
User=your_username
WorkingDirectory=/path/to/api
ExecStart=/path/to/api/carousel-api-env/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
Restart=always
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=carousel-api
Environment="PATH=/path/to/api/carousel-api-env/bin"

[Install]
WantedBy=multi-user.target
```

Start and enable the service:

```bash
sudo systemctl daemon-reload
sudo systemctl start carousel-api
sudo systemctl enable carousel-api
```

### 2.4 Configure Nginx (Optional)

If you want to expose the API externally, set up an Nginx reverse proxy:

```nginx
server {
    listen 80;
    server_name carousel-api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 3. Instagram Graph API Setup

### 3.1 Create a Facebook App

1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Click "Create App" and select "Business" type
3. Enter app name and contact email
4. Click "Create App"

### 3.2 Add Instagram Graph API

1. In your app dashboard, click "Add Products"
2. Find "Instagram Graph API" and click "Set Up"
3. Follow the setup instructions

### 3.3 Configure App Settings

1. Go to "App Settings" > "Basic"
2. Add a privacy policy URL (required)
3. Complete other required fields

### 3.4 Generate Access Tokens

1. Go to "Tools" > "Graph API Explorer"
2. Select your app from the dropdown
3. Select the Facebook Page connected to your Instagram account
4. Request the following permissions:
   - `instagram_basic`
   - `instagram_content_publish`
   - `pages_read_engagement`
5. Click "Generate Access Token"
6. Convert to a long-lived token using the [Access Token Debugger](https://developers.facebook.com/tools/debug/accesstoken/)

## 4. Setting Up the n8n Workflow

### 4.1 Create a New Workflow

1. Open your n8n instance
2. Click "Create new" to start a new workflow
3. Name it "Instagram Carousel Automation"

### 4.2 Add Schedule Trigger

1. Add a "Schedule Trigger" node
2. Configure it to run daily at 9:30 AM
3. Set your timezone

### 4.3 Add Google Sheets Node for Data Retrieval

1. Add a "Google Sheets" node
2. Connect to your Google account
3. Set operation to "Read Rows"
4. Enter your Spreadsheet ID
5. Select the worksheet
6. Add filters:
   ```
   published = FALSE
   publish_date <= {{$today}}
   ```

### 4.4 Add Function Node for Data Processing

1. Add a "Function" node
2. Use the following code:

```javascript
return items.map(item => {
  // Split slide_text into individual slide objects
  const slides = item.slide_text.split('||').map(text => ({
    text: text.trim()
  }));
  
  return {
    json: {
      carousel_id: item.carousel_id || `carousel_${Date.now()}`,
      carousel_title: item.carousel_title,
      slides: slides,
      include_logo: true, // Change as needed
      logo_path: "/path/to/your/logo.png", // Update with actual path
      caption: item.caption,
      tags: item.tags || "",
      row_number: item.row_number // Keep track of the row for updating later
    }
  };
});
```

### 4.5 Add HTTP Request Node for Image Generation

1. Add an "HTTP Request" node
2. Configure:
   - Method: POST
   - URL: http://localhost:5000/generate-carousel (or your domain)
   - Body Type: JSON
   - JSON Body: 
     ```
     {
       "carousel_title": "={{$json.carousel_title}}",
       "slides": "={{$json.slides}}",
       "include_logo": "={{$json.include_logo}}",
       "logo_path": "={{$json.logo_path}}"
     }
     ```

### 4.6 Add Function Node to Process API Response

1. Add another "Function" node
2. Use the following code:

```javascript
// Process the API response and prepare for Instagram
let images = [];
const responseData = $input.item.json;

if (responseData.status === "success") {
  // Convert hex-encoded images to files for Instagram
  for (const slide of responseData.slides) {
    // Convert hex to binary
    const binaryData = Buffer.from(slide.content, 'hex');
    
    // Add to images array
    images.push({
      name: slide.filename,
      data: binaryData,
      type: 'image/png'
    });
  }
  
  return {
    json: {
      carousel_id: responseData.carousel_id,
      carousel_title: $input.item.json.carousel_title,
      caption: $input.item.json.caption + "\n\n" + $input.item.json.tags,
      images: images,
      row_number: $input.item.json.row_number
    }
  };
} else {
  // Handle error
  throw new Error(`Failed to generate images: ${JSON.stringify(responseData)}`);
}
```

### 4.7 Add Instagram Business Post Node

1. Add the "Instagram" node
2. Connect to your Instagram Business account
3. Set operation to "Create Media"
4. Configure:
   - Media Type: CAROUSEL
   - Caption: `={{$json.caption}}`
   - Media URL: `={{$json.images}}`
   - Is Media Published: false (for draft) or true (for immediate posting)

### 4.8 Add Google Sheets Update Node

1. Add another "Google Sheets" node
2. Set operation to "Update Row"
3. Configure:
   - Spreadsheet ID: Your spreadsheet ID
   - Sheet: Your worksheet name
   - Key: row_number
   - Options:
     ```
     {
       "published": true,
       "publish_timestamp": "={{$now.toISOString()}}"
     }
     ```

### 4.9 Add Email Notification Node

1. Add a "Send Email" node
2. Connect to your SMTP service
3. Configure:
   - To Email: Your email address
   - Subject: "Instagram Carousel Created: {{$json.carousel_title}}"
   - Content:
     ```
     The Instagram carousel "{{$json.carousel_title}}" has been successfully created.
     
     Carousel ID: {{$json.carousel_id}}
     Published: {{$now.toLocaleString()}}
     
     Caption:
     {{$json.caption}}
     ```

### 4.10 Add iMessage Notification (Optional)

If you have access to a Mac server with AppleScript capabilities:

1. Add an "HTTP Request" node
2. Configure it to call a custom endpoint on your Mac server that triggers an AppleScript to send an iMessage

### 4.11 Add Error Handling

1. Add IF nodes after critical steps to check for errors
2. Add an "Error Trigger" node as a fallback
3. Connect error paths to notification nodes

## 5. Testing the Workflow

### 5.1 Manual Test

1. Add a test row to your Google Sheet
2. Execute the workflow manually
3. Verify that:
   - Images are generated correctly
   - Instagram draft is created
   - Google Sheet is updated
   - Notifications are sent

### 5.2 Debugging Tips

- Use the "Debug" tab in n8n to view the output of each node
- Check API logs for any errors
- Verify Instagram permissions if posts fail
- Test API endpoints independently if needed

## 6. Production Deployment

### 6.1 Security Considerations

- Use HTTPS for all external endpoints
- Set up proper authentication for your API
- Store sensitive credentials in n8n encrypted credentials

### 6.2 Monitoring

- Set up cron jobs to check API health
- Configure email alerts for workflow failures
- Regularly check logs for errors

### 6.3 Backup

- Export the n8n workflow regularly
- Back up your Google Sheet
- Document all configuration settings
