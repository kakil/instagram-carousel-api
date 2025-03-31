## 6. Workflow Maintenance

### 6.1 Regular Updates

1. Keep your Instagram Carousel API updated:
   ```bash
   cd instagram-carousel-api
   git pull
   ./scripts/docker.sh prod:build
   ```

2. Export and back up your n8n workflow regularly:
   - Go to your n8n instance
   - Open the workflow
   - Click the "Export" button
   - Save the JSON file to a secure location

3. Update Meta Graph API tokens:
   - Facebook access tokens eventually expire
   - Generate new long-lived tokens before expiration
   - Update the token in n8n credentials

### 6.2 Security Considerations

- Store API credentials securely in n8n
- Use HTTPS for all connections
- Keep your server and n8n instance updated
- Implement IP restrictions for API access if possible
- Monitor the PublishLog sheet for unauthorized usage

### 6.3 Advanced Configuration

The workflow has several places where you can customize functionality:

#### Modify Text Sanitization
You can adjust the text sanitization rules in the "Sanitize Code" node to handle specific characters your content might contain.

#### Customize Image Processing
The API supports various settings for image generation that you can add to the HTTP request:
- Image dimensions
- Background colors
- Font settings

#### Adjust Status Flow
The workflow uses these status values:
- "scheduled" - Ready to be processed
- "generated" - Images created but not published
- "published" - Successfully posted to Instagram
- "error" - Processing failed

You can modify these or add additional statuses based on your needs.## 5. Workflow Execution and Monitoring

### 5.1 Manual Testing

If you imported the example workflow:
1. Verify all connections and credentials are properly configured
2. Make sure your Google Sheet is structured as expected (see Section 7)
3. Add a test row to your Google Sheet with status="scheduled"
4. Run the workflow just for this test row by selecting it in the "Loop Through Carousels" node

Testing individual components:
1. You can test the image generation alone by running only up to the HTTP Request node
2. Test the Instagram upload separately by manually providing image URLs to the Upload nodes

### 5.2 Monitoring and Logging

The workflow includes built-in logging through the PublishLog sheet, which records:
- When carousels are published
- Any errors that occur during processing
- The carousel IDs for tracking

Additionally, the Instagram Carousel API includes monitoring endpoints:
1. Health check: `https://api.yourdomain.com/health`
2. Metrics: `https://api.yourdomain.com/metrics`

You can also check API logs using Docker:
```bash
./scripts/docker.sh logs
```

### 5.3 Troubleshooting

#### API Connection Issues
- Verify the API endpoint is accessible: `https://api.yourdomain.com/api/v1/generate-carousel-with-urls`
- Check if the API is responding with proper JSON output
- Review Python code node outputs for any parsing errors

#### Image Generation Fails
- Check the API logs for details on errors
- Common issues include:
  - Malformed text input with special characters
  - Missing required parameters in the request
  - Server resource limitations

#### Instagram Publishing Fails
- Ensure your Instagram account is a Business account
- Verify the access tokens are valid and haven't expired
- Check Meta Developer App settings for required permissions
- Validate that the image URLs are publicly accessible
- Make sure the images meet Instagram's requirements (dimensions, file size, etc.)

#### Google Sheets Integration
- Ensure the sheet has the exact column names expected by the workflow
- Check that the `row_number` column exists and contains values
- Verify your Google API credentials have write access to the sheet# n8n Workflow Implementation Guide

## 1. Prerequisites

Before setting up the n8n workflow, ensure you have:

- n8n installed and running on your server
- Instagram Carousel Generator API deployed (see installation instructions in main README)
- A Google Sheet created with the required columns for post scheduling
- A Meta Developer account with Instagram Graph API access
- SMTP credentials for email notifications (optional)

## 2. Instagram Carousel API Setup

### 2.1 Deploy the API using Docker (Recommended)

The easiest way to deploy the Instagram Carousel API is using Docker:

```bash
# Clone the repository
git clone https://github.com/kakil/instagram-carousel-api.git
cd instagram-carousel-api

# Set up the Docker environment
chmod +x scripts/setup-docker-env.sh
./scripts/setup-docker-env.sh

# Start the production environment
./scripts/docker.sh prod
```

This will start the API service at http://localhost:5001 by default.

### 2.2 Configure API Settings

Create a `.env` file in the project root with your configuration:

```ini
# API settings
API_PREFIX=/api
API_VERSION=v1
DEBUG=False
PRODUCTION=True
API_KEY=your_secure_api_key

# Server settings
HOST=0.0.0.0
PORT=5001

# Public access settings
PUBLIC_BASE_URL=https://api.yourdomain.com

# Path settings
TEMP_DIR=/app/static/temp

# Image settings
DEFAULT_WIDTH=1080
DEFAULT_HEIGHT=1080
DEFAULT_BG_COLOR_R=18
DEFAULT_BG_COLOR_G=18
DEFAULT_BG_COLOR_B=18

# CORS settings
ALLOW_ORIGINS=https://n8n.yourdomain.com
```

### 2.3 Configure Nginx as Reverse Proxy

Create a Nginx configuration to expose the API securely:

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # For Cloudflare SSL
    listen 443 ssl;
    ssl_certificate /etc/ssl/certs/cloudflare.crt;
    ssl_certificate_key /etc/ssl/private/cloudflare.key;
}
```

### 2.4 Test the API

Verify the API is working with a simple test request:

```bash
curl -X POST "https://api.yourdomain.com/api/v1/generate-carousel" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_secure_api_key" \
  -d '{
    "carousel_title": "Test Carousel",
    "slides": [
      {"text": "This is a test slide"}
    ],
    "include_logo": false
  }'
```

## 3. Instagram Graph API Setup

### 3.1 Create a Meta App

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Click "Create App" and select "Business" type
3. Enter app name and contact email
4. Add Instagram Graph API product to your app

### 3.2 Configure App Settings

1. Connect your app to a Facebook Page linked to an Instagram Business account
2. Add the following permissions to your app:
   - `instagram_basic`
   - `instagram_content_publish`
   - `pages_read_engagement`

### 3.3 Generate Access Tokens

1. Generate a User Access Token with the required permissions
2. Use the token to get a Page Access Token for your Facebook Page
3. Convert to a long-lived token using the Access Token Debugger tool

## 4. Setting Up the n8n Workflow

### 4.1 Create a New Workflow

You can either build the workflow from scratch or import the provided example workflow:

#### Option 1: Import the Example Workflow (Recommended)

1. Download the example workflow JSON file from: [examples/Instagram_Carousel___1_0.json](examples/Instagram_Carousel___1_0.json)
2. Open your n8n instance
3. Click "Workflows" in the sidebar
4. Click the "Import" button in the top right
5. Select the downloaded JSON file
6. Review and adjust the workflow settings as needed for your environment

#### Option 2: Create a New Workflow Manually

1. Open your n8n instance
2. Click "Create new" to start a new workflow
3. Name it "Instagram Carousel Automation"

### 4.2 Add Schedule Trigger

1. Add a "Schedule Trigger" node
2. Configure it to run daily at your preferred time
3. Set your timezone

### 4.3 Add Google Sheets Node for Data Retrieval

1. Add a "Google Sheets" node
2. Connect to your Google account
3. Set operation to "Read Rows"
4. Enter your Spreadsheet ID
5. Select the worksheet (usually named "Sheet1")
6. Add filters:
   ```
   status = scheduled
   ```

### 4.4 Add Loop Through Carousels Node

1. Add a "Split In Batches" node
2. Connect it to the Google Sheets node
3. Leave the default settings to process one carousel at a time

### 4.5 Add Format Carousel Data Node

1. Add a "Code" node (Python)
2. Use the following Python code:

```python
# Initialize return items array
returnItems = []

# Process each input item
for item in items:
    # Debug what we're receiving
    print(f"Processing item: {item['json']}")

    # Initialize slides array
    slides = []

    # Collect all non-empty slide texts (slide1_text, slide2_text, etc.)
    for i in range(1, 9):  # Looking at slides 1-8
        slide_key = f"slide{i}_text"
        # Check if the key exists and has content
        if slide_key in item['json'] and item['json'][slide_key]:
            slide_text = str(item['json'][slide_key]).strip()
            if slide_text:
                print(f"Found slide {i}: {slide_text[:20]}...")
                slides.append({"text": slide_text})

    # Create formatted carousel data
    # Make sure this node preserves row_number
    formatted_data = {
        "carousel_title": item['json'].get('carousel_title', 'Untitled Carousel'),
        "slides": slides,
        "include_logo": item['json'].get('include_logo') == "true" or item['json'].get('include_logo') is True,
        "logo_path": item['json'].get('logo_path', ''),
        "row_number": item['json'].get('row_number'),  # Store row number explicitly
        "caption": item['json'].get('caption', ''),
        "hashtags": item['json'].get('hashtags', '')
    }

    # Ensure include_logo is explicitly a boolean
    if formatted_data["include_logo"] == "" or formatted_data["include_logo"] is None:
        formatted_data["include_logo"] = False

    # Add to return items
    returnItems.append({"json": formatted_data})

# Return the processed items
return returnItems
```
```

### 4.6 Add Sanitize Code Node

1. Add a "Code" node (Python)
2. Use the following Python code to sanitize text content:

```python
# Initialize return items array
returnItems = []

# Define a function to sanitize text
def sanitize_text(text):
    if not text:
        return ""

    # Convert to string if not already
    text = str(text)

    # Replace problematic characters
    replacements = {
        '→': '->',  # Right arrow
        '←': '<-',  # Left arrow
        '↑': '^',   # Up arrow
        '↓': 'v',   # Down arrow
        '"': '"',   # Smart quotes
        '"': '"',   # Smart quotes
        ''': "'",   # Smart apostrophes
        ''': "'",   # Smart apostrophes
        '—': '-',   # Em dash
        '–': '-',   # En dash
        '…': '...'  # Ellipsis
    }

    for char, replacement in replacements.items():
        text = text.replace(char, replacement)

    return text

# Process each input item
for item in items:
    # Get the input JSON
    input_data = item['json']

    # Create a sanitized copy of the input data
    output_data = dict(input_data)  # Start with a copy of the original

    # Sanitize the text fields
    output_data['carousel_title'] = sanitize_text(input_data.get('carousel_title', ''))
    output_data['caption'] = sanitize_text(input_data.get('caption', ''))
    output_data['hashtags'] = sanitize_text(input_data.get('hashtags', ''))

    # Process the slides array
    if 'slides' in input_data and isinstance(input_data['slides'], list):
        # Create sanitized slides
        sanitized_slides = []

        for slide in input_data['slides']:
            if isinstance(slide, dict) and 'text' in slide:
                # Create a sanitized copy of the slide
                sanitized_slide = dict(slide)  # Start with a copy of the original
                sanitized_slide['text'] = sanitize_text(slide['text'])
                sanitized_slides.append(sanitized_slide)

        # Replace the slides array
        output_data['slides'] = sanitized_slides

    # Add to return items
    returnItems.append({"json": output_data})

# Return the processed items
return returnItems
```

### 4.7 Add Set Caption in Static Data Node

1. Add a "Code" node (Python)
2. Use the following Python code to store caption data for later use:

```python
# Store both caption and row number in workflow static data
workflowStaticData = _getWorkflowStaticData("global")

# Get the caption and row number from the current item
if "caption" in items[0]["json"]:
    caption = items[0]["json"]["caption"]
else:
    caption = ""

if "row_number" in items[0]["json"]:
    row_number = items[0]["json"]["row_number"]
else:
    row_number = ""

# Store in static data
workflowStaticData["carousel_caption"] = caption
workflowStaticData["current_row_number"] = row_number

# Return the original data
return items
```

### 4.8 Add HTTP Request Node for Image Generation

1. Add an "HTTP Request" node
2. Configure:
   - Method: POST
   - URL: https://api.yourdomain.com/api/v1/generate-carousel-with-urls
   - Headers:
     ```
     {
       "Content-Type": "application/json"
     }
     ```
   - Body Type: JSON
   - JSON Body: `={{ $json }}`

### 4.9 Process API Response

1. Add a "Code" node (Python) to process the API response
2. Use the following Python code:

```python
# Combine carousel_id from API response with row_number from static data
workflowStaticData = _getWorkflowStaticData("global")
returnItems = []

for item in items:
    try:
        # Get carousel_id from the API response
        carousel_id = item['json'].get('carousel_id', '')

        # Get row_number from workflow static data
        row_number = workflowStaticData.get("current_row_number", "")

        # Create update data for Google Sheets
        update_data = {
            "carousel_id": carousel_id,
            "row_number": row_number,
            "status": "generated"
        }

        # Store carousel_id in workflow static data
        workflowStaticData["carousel_id"] = carousel_id

        # Keep all the original data too
        for key, value in item['json'].items():
            if key not in update_data:
                update_data[key] = value

        returnItems.append({"json": update_data})

    except Exception as e:
        print(f"Error creating update data: {str(e)}")
        returnItems.append(item)

return returnItems
```

### 4.10 Update Google Sheet with Generated Status

1. Add a "Google Sheets" node
2. Configure:
   - Operation: Update
   - Document ID: Your Google Sheets document ID
   - Sheet Name: Your main sheet (e.g., "Sheet1")
   - Columns: Define below
     ```json
     {
       "row_number": "={{ $json.row_number }}",
       "carousel_id": "={{ $json.carousel_id }}",
       "status": "={{ $json.status }}"
     }
     ```
   - Matching Column: row_number

### 4.11 Prepare Instagram Upload

1. Add a "Code" node (Python)
2. Use the following Python code:

```python
# Process the API response and construct image URLs
import json

# Initialize return items array
returnItems = []

for item in items:
    try:
        # Get workflow static data to access the stored caption
        workflowStaticData = _getWorkflowStaticData("global")

        # The API response should be in item['json']
        response = item['json']

        # Get carousel_id from the response
        carousel_id = response.get('carousel_id')

        if not carousel_id:
            raise ValueError("No carousel_id found in response")

        # Get slides data
        slides = response.get('slides', [])

        # Base URL for images
        base_url = "https://api.yourdomain.com/api/v1/temp"

        # Construct URLs for each slide
        image_urls = []
        for slide in slides:
            filename = slide.get('filename')
            if filename:
                # Construct the full URL to the image
                url = f"{base_url}/{carousel_id}/{filename}"
                image_urls.append({
                    'url': url,
                    'filename': filename
                })

        # Get the caption from workflow static data instead of the item
        caption = workflowStaticData.get("carousel_caption", "")

        # Prepare output with necessary data
        output = {
            'carousel_id': carousel_id,
            'images': image_urls,
            'caption': caption,
            'hashtags': item.get('hashtags', '')
        }

        returnItems.append({"json": output})

    except Exception as e:
        print(f"Error processing carousel: {e}")
        # Return the original item with an error flag
        if 'json' not in item:
            item['json'] = {}
        item['json']['error'] = str(e)
        returnItems.append(item)

# Return the processed items
return returnItems
```

### 4.12 Process Images

1. Add a "Code" node (Python)
2. Use the following Python code:

```python
# Prepare data for Instagram API
import json

# Initialize return items array
returnItems = []

for item in items:
    try:
        # Extract data
        images = item['json'].get('images', [])
        carousel_id = item['json'].get('carousel_id')
        caption = item['json'].get('caption', '')
        hashtags = item['json'].get('hashtags', '')

        # Combine caption and hashtags
        full_caption = caption
        if hashtags:
            full_caption = f"{caption}\n\n{hashtags}" if caption else hashtags

        # Get the first image URL for posting
        first_image_url = images[0]['url'] if images else None

        # Create formatted output for Instagram API
        output = {
            'carousel_id': carousel_id,
            'image_url': first_image_url,  # For single image posts
            'images': [img['url'] for img in images],  # List of all image URLs
            'caption': full_caption
        }

        returnItems.append({"json": output})

    except Exception as e:
        print(f"Error formatting for Instagram: {e}")
        if 'json' not in item:
            item['json'] = {}
        item['json']['error'] = str(e)
        returnItems.append(item)

# Return the processed items
return returnItems
```

### 4.13 Split Out Images

1. Add a "Split Out" node
2. Configure:
   - Field to Split Out: images
   - Include: allOtherFields
   - Add all other fields to the output items: Enabled

### 4.14 Format Single Image Request

1. Add a "Code" node (Python)
2. Use the following Python code:

```python
# Format Single Image Request
returnItems = []

# Process each input item
for item in items:
    try:
        # Extract data from the item
        json_data = item['json']

        # Get the image URL from the 'images' field
        if 'images' in json_data and isinstance(json_data['images'], str):
            image_url = json_data['images']
        else:
            # Fallback to image_url if needed
            image_url = json_data.get('image_url', '')

        # Skip if no valid URL found
        if not image_url or not isinstance(image_url, str):
            raise ValueError("Missing valid image URL")

        # Get other fields
        carousel_id = json_data.get('carousel_id', '')
        caption = json_data.get('caption', '')

        # Create simple output
        output = {
            'image_url': image_url,
            'caption': caption,
            'carousel_id': carousel_id
        }

        # Add to results
        returnItems.append({"json": output})

    except Exception as e:
        # Simple error handling
        returnItems.append({"json": {"error": str(e)}})

# Return the processed items
return returnItems
```

**: Check the API logs for details on errors
- **Instagram Post Fails**:
  - Ensure your Instagram account is a Business account
  - Verify the access tokens are valid and haven't expired
  - Check Meta Developer App settings for required permissions

### 5.4 Advanced Workflow Enhancements

- Add Slack notifications
- Implement webhook triggers for immediate posting
- Add a preview step where you can approve posts before they go live

## 6. Workflow Maintenance

### 6.1 Regular Updates

1. Keep your Instagram Carousel API updated:
   ```bash
   cd instagram-carousel-api
   git pull
   ./scripts/docker.sh prod:build
   ```

2. Export and back up your n8n workflow regularly

### 6.2 Security Considerations

- Rotate API keys periodically
- Use HTTPS for all connections
- Store credentials securely in n8n
- Keep your server and n8n instance updated

## 7. Example Google Sheet Structure

### 7.1 Standard Structure

Create a Google Sheet with the following columns:

- `carousel_title`: Title of the carousel
- `slide_text`: Text for each slide, separated by `||`
- `include_logo`: TRUE/FALSE
- `logo_path`: Path to logo (if applicable)
- `caption`: Instagram post caption
- `hashtags`: Hashtags to add to the post
- `publish_date`: When to publish (YYYY-MM-DD)
- `published`: TRUE/FALSE (will be updated by workflow)
- `publish_timestamp`: (will be filled by workflow)
- `post_url`: (will be filled by workflow)

### 4.15 Upload Single Carousel Item

1. Add a "Facebook Graph API" node
2. Configure:
   - HTTP Request Method: POST
   - Graph API Version: v22.0 (or latest available)
   - Node: [Your Instagram Business ID]
   - Edge: media
   - Query Parameters:
     - media_type: IMAGE
     - image_url: `={{ $json.image_url}}`
     - is_carousel_item: true

### 4.16 Transform Media IDs to Array

1. Add a "Code" node (Python)
2. Use the following Python code:

```python
# Transform the format for carousel container creation
returnItems = []

try:
    # In n8n Python nodes, items is a special object, not a standard Python list
    # Let's try to extract data safely

    # Get the individual items from the input data
    input_data = items if hasattr(items, '__iter__') else []

    # Create a simple list of IDs
    media_ids = []

    # Try different approaches to extract IDs
    for item in input_data:
        try:
            # Try direct access first
            if hasattr(item, 'id'):
                media_ids.append(item.id)
            # Then try dict-like access
            elif isinstance(item, dict) and 'id' in item:
                media_ids.append(item['id'])
            # Try json attribute access
            elif hasattr(item, 'json') and hasattr(item.json, 'id'):
                media_ids.append(item.json.id)
            # Try json dict access
            elif hasattr(item, 'json') and isinstance(item.json, dict) and 'id' in item.json:
                media_ids.append(item.json['id'])
        except Exception as e:
            print(f"Could not process item: {e}")

    # Create output with the media IDs we found
    output = {
        'mediaIds': media_ids
    }

    returnItems.append({"json": output})
except Exception as e:
    returnItems.append({"json": {"error": str(e)}})

return returnItems
```

### 4.17 Add Code to Process Media IDs with Caption

1. Add another "Code" node (Python)
2. Use the following Python code:

```python
# Transform the format for carousel container creation
workflowStaticData = _getWorkflowStaticData("global")
returnItems = []

try:
    # Get the first item which contains the mediaIds array
    if items and len(items) > 0:
        first_item = items[0]

        # Extract mediaIds directly from the input structure
        if 'json' in first_item and 'mediaIds' in first_item['json'] and isinstance(first_item['json']['mediaIds'], list):
            media_ids = first_item['json']['mediaIds']
        else:
            # If the expected structure isn't found, try to get it from the raw item
            media_ids = first_item.get('json', {}).get('mediaIds', [])

            # If still empty, try to extract from the visible structure
            if not media_ids and 'mediaIds' in first_item:
                media_ids = first_item['mediaIds']
    else:
        media_ids = []

    # Get the caption from workflow static data
    caption = workflowStaticData.get("carousel_caption", "")

    # Create output with both the media IDs and the caption
    output = {
        "mediaIds": media_ids,
        "carousel_caption": caption
    }

    print(f"Final output: {output}")
    returnItems.append({"json": output})
except Exception as e:
    print(f"Error in transform function: {str(e)}")
    returnItems.append({"json": {"error": str(e)}})

return returnItems
```

### 4.18 Create Carousel Container

1. Add a "Facebook Graph API" node
2. Configure:
   - HTTP Request Method: POST
   - Graph API Version: v22.0 (or latest available)
   - Node: [Your Instagram Business ID]
   - Edge: media
   - Query Parameters:
     - media_type: CAROUSEL
     - children: `={{ $json.mediaIds }}`
     - caption: `={{ $json.carousel_caption }}`

### 4.19 Publish Carousel

1. Add a "Facebook Graph API" node
2. Configure:
   - HTTP Request Method: POST
   - Graph API Version: v22.0 (or latest available)
   - Node: [Your Instagram Business ID]
   - Edge: media_publish
   - Query Parameters:
     - creation_id: `={{ $json.id }}`

### 4.20 Set Success Data and Update Sheet

1. Add a "Code" node (Python)
2. Use the following Python code:

```python
# Prepare data for updating Google Sheet with Published status
workflowStaticData = _getWorkflowStaticData("global")
returnItems = []

for item in items:
    try:
        # Get the carousel_id either from the current item or from previous data
        carousel_id = item['json'].get('id') or workflowStaticData.get("carousel_id", "")

        # Get row_number from workflow static data
        row_number = workflowStaticData.get("current_row_number", "")

        # Create update data
        update_data = {
            "carousel_id": carousel_id,
            "row_number": row_number,
            "status": "published"  # Set status to published
        }

        returnItems.append({"json": update_data})

    except Exception as e:
        print(f"Error preparing data for sheet update: {str(e)}")
        returnItems.append(item)

return returnItems
```

3. Connect this to a "Google Sheets" node
4. Configure:
   - Operation: Update
   - Document ID: Your Google Sheets document ID
   - Sheet Name: Your main sheet (e.g., "Sheet1")
   - Matching Column: row_number
   - Columns: status, carousel_id

### 7.2 Example Workflow Sheet Structure

When using the example workflow JSON (`docs/examples/Instagram_Carousel___1_0.json`), your sheet needs these specific columns:

#### Main Sheet (Sheet1):
- `carousel_id`: Unique identifier for the carousel (will be filled by workflow)
- `carousel_title`: Title of the carousel
- `slide1_text` through `slide8_text`: Individual slide content (one column per slide)
- `caption`: Instagram post caption
- `hashtags`: Hashtags to add to the post
- `include_logo`: true/false (text values)
- `logo_path`: Path to logo (if applicable)
- `status`: Current status of the carousel - set to "scheduled" for new posts, will be updated to "generated" and then "published" by the workflow
- `publish_date`: When to publish (YYYY-MM-DD)
- `notes`: Any additional notes
- `row_number`: Auto-generated by Google Sheets (don't modify)

#### PublishLog Sheet:
Create a second sheet named "PublishLog" with these columns:
- `Timestamp`: When the carousel was published
- `Carousel ID`: ID of the carousel that was published
- `Status`: Status of the publishing action (success/error)
- `Notes/Error`: Additional information or error messages

This structure provides a complete content calendar system for your Instagram carousels that integrates perfectly with the n8n workflow and Instagram Carousel API.

## 8. Error Handling

The example workflow includes error handling at multiple points:

### 8.1 Error Paths

1. If image generation fails:
   - The workflow updates the Google Sheet with status="error"
   - It logs the error in the PublishLog sheet

2. If Instagram publishing fails:
   - The workflow still records the carousel_id in the database
   - The status remains "generated" instead of "published"
   - Error details are logged in PublishLog

### 8.2 Workflow Debugging

When debugging the workflow:

1. Check the output of each Python code node using n8n's built-in testing features
2. Use the `print()` statements in the Python code to output debugging information
3. Review the PublishLog sheet for error messages
4. Check the Instagram Graph API responses for any specific error codes

## 9. Additional Resources

### 9.1 Example Files

- **Workflow Example**: [examples/Instagram_Carousel___1_0.json](examples/Instagram_Carousel___1_0.json) - Complete workflow ready
  to import into n8n
- **Implementation Guide**: [guides/n8n-workflow-implementation.md](guides/n8n-workflow-implementation.md)

### 9.2 Customization

The example workflow includes many advanced features like:
- Workflow state management using static data storage
- Error handling and logging
- Status tracking in Google Sheets
- Multiple image processing steps
- Proper sanitization of text content
- Integration with Meta Graph API

Feel free to customize the workflow to fit your specific needs. The modular nature of n8n makes it easy to add or remove nodes as required.
