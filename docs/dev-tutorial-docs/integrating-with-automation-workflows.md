# Integrating with Automation Workflows

This guide demonstrates how to integrate the Instagram Carousel Generator API with various automation tools to create an end-to-end workflow for carousel content creation and posting.

## Overview

One of the key benefits of the Instagram Carousel Generator API is its ability to be integrated into automated workflows. This allows you to:

1. Generate carousel images from content stored in spreadsheets, databases, or content management systems
2. Schedule posts for optimal engagement times
3. Track and analyze the performance of your carousel posts
4. Maintain a consistent content calendar

## Integration Examples

### Example 1: n8n Workflow for Instagram Posting

This example shows how to create an n8n workflow that:
1. Reads carousel content from a Google Sheet
2. Generates carousel images using the API
3. Posts to Instagram via the Facebook Graph API
4. Updates the spreadsheet with posting status

#### Prerequisites

- [n8n](https://n8n.io/) installed and running
- Instagram Business Account connected to Facebook
- Facebook Developer Account with Instagram Graph API access
- Google Sheets API access

#### Step 1: Set Up n8n Nodes

Create a new workflow in n8n and add the following nodes:

1. **Google Sheets**: To read your carousel content
2. **HTTP Request (POST)**: To call the Instagram Carousel Generator API
3. **HTTP Request (GET)**: To download the generated images
4. **Facebook Graph API**: To post to Instagram
5. **Google Sheets**: To update the posting status

#### Step 2: Configure Google Sheets Node (Read)

Configure the Google Sheets node to read from your content spreadsheet:

```json
{
  "operation": "getRows",
  "sheetId": "YOUR_SHEET_ID",
  "range": "A:E",
  "options": {
    "headerRow": true
  }
}
```

Your spreadsheet should have columns like:
- `carousel_title`: Title for the carousel
- `slide1_text`, `slide2_text`, etc.: Text for each slide
- `status`: Status of the post (e.g., "Pending", "Generated", "Posted")

#### Step 3: Configure HTTP Request Node (Generate Carousel)

Configure the HTTP Request node to call the Instagram Carousel Generator API:

```json
{
  "method": "POST",
  "url": "https://your-api-domain.com/api/v1/generate-carousel-with-urls",
  "authentication": "headerAuth",
  "headerParameters": {
    "X-API-Key": "YOUR_API_KEY"
  },
  "jsonParameters": true,
  "bodyParameters": {
    "carousel_title": "={{ $node[\"Google Sheets\"].json[\"carousel_title\"] }}",
    "slides": [
      { "text": "={{ $node[\"Google Sheets\"].json[\"slide1_text\"] }}" },
      { "text": "={{ $node[\"Google Sheets\"].json[\"slide2_text\"] }}" },
      { "text": "={{ $node[\"Google Sheets\"].json[\"slide3_text\"] }}" }
    ],
    "include_logo": true,
    "logo_path": "/app/static/assets/logo.png"
  }
}
```

#### Step 4: Configure HTTP Request Nodes (Download Images)

For each URL returned by the previous node, add an HTTP Request node to download the image:

```json
{
  "method": "GET",
  "url": "={{ $node[\"HTTP Request\"].json[\"public_urls\"][0] }}",
  "responseFormat": "file",
  "options": {
    "filename": "slide_1.png"
  }
}
```

Repeat for each slide, updating the array index and filename accordingly.

#### Step 5: Configure Facebook Graph API Node

Configure the Facebook Graph API node to post to Instagram:

```json
{
  "resource": "mediaContainer",
  "operation": "create",
  "containerType": "CAROUSEL",
  "mediaType": "IMAGE",
  "caption": "={{ $node[\"Google Sheets\"].json[\"carousel_title\"] }}",
  "mediaUrls": [
    "={{ $node[\"HTTP Request1\"].binary.data.url }}",
    "={{ $node[\"HTTP Request2\"].binary.data.url }}",
    "={{ $node[\"HTTP Request3\"].binary.data.url }}"
  ],
  "accessToken": "YOUR_FACEBOOK_ACCESS_TOKEN",
  "userOrPageId": "YOUR_INSTAGRAM_BUSINESS_ID"
}
```

#### Step 6: Configure Google Sheets Node (Update)

Configure another Google Sheets node to update the status in your spreadsheet:

```json
{
  "operation": "updateRow",
  "sheetId": "YOUR_SHEET_ID",
  "range": "F{{ $node[\"Google Sheets\"].json[\"rowNumber\"] }}",
  "options": {
    "valueInputMode": "RAW"
  },
  "valueInputs": {
    "values": [
      [
        "Posted",
        "={{ $node[\"HTTP Request\"].json[\"carousel_id\"] }}",
        "={{ $now.toISOString() }}"
      ]
    ]
  }
}
```

#### Step 7: Set Up Triggers and Scheduling

Configure a trigger node to run the workflow on a schedule or when new rows are added to your spreadsheet.

Complete workflow diagram:

```
Google Sheets (Read) → HTTP Request (Generate) → HTTP Request (Download images) → Facebook Graph API → Google Sheets (Update)
```

### Example 2: Python Script for Bulk Carousel Generation

This example shows a Python script that generates multiple carousels from a CSV file:

```python
import csv
import requests
import os
import time
from datetime import datetime

# Configuration
API_URL = "https://your-api-domain.com/api/v1/generate-carousel-with-urls"
API_KEY = "your_api_key_here"
CSV_FILE = "carousels.csv"
OUTPUT_DIR = "generated_carousels"

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Read carousel data from CSV
with open(CSV_FILE, 'r', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)

    # Process each row in the CSV
    for row in reader:
        print(f"Processing carousel: {row['carousel_title']}")

        # Prepare the slides data
        slides = []
        for i in range(1, 11):  # Support up to 10 slides
            slide_key = f"slide{i}_text"
            if slide_key in row and row[slide_key].strip():
                slides.append({"text": row[slide_key]})

        # Skip if no slides
        if not slides:
            print(f"Skipping {row['carousel_title']} - no slide content")
            continue

        # Prepare request data
        data = {
            "carousel_title": row['carousel_title'],
            "slides": slides,
            "include_logo": row.get('include_logo', '').lower() == 'true',
            "logo_path": row.get('logo_path', None)
        }

        # Optional settings
        if 'width' in row and 'height' in row:
            data["settings"] = {
                "width": int(row['width']),
                "height": int(row['height'])
            }

        # Call the API
        response = requests.post(
            API_URL,
            json=data,
            headers={"X-API-Key": API_KEY}
        )

        # Check for success
        if response.status_code == 200:
            result = response.json()

            # Create directory for this carousel
            carousel_dir = os.path.join(OUTPUT_DIR, result['carousel_id'])
            os.makedirs(carousel_dir, exist_ok=True)

            # Save metadata
            with open(os.path.join(carousel_dir, "metadata.json"), 'w') as f:
                json.dump(result, f, indent=2)

            # Download each slide
            for i, url in enumerate(result['public_urls']):
                image_path = os.path.join(carousel_dir, f"slide_{i+1}.png")
                image_response = requests.get(url)

                if image_response.status_code == 200:
                    with open(image_path, 'wb') as f:
                        f.write(image_response.content)
                    print(f"  Downloaded slide {i+1}")
                else:
                    print(f"  Failed to download slide {i+1}: {image_response.status_code}")

            print(f"Completed carousel: {row['carousel_title']} (ID: {result['carousel_id']})")
        else:
            print(f"Error generating carousel: {response.status_code}")
            print(response.text)

        # Rate limiting: sleep between requests
        time.sleep(1)

print("All carousels processed.")
```

### Example 3: Zapier Integration

This example demonstrates how to use Zapier to connect the Instagram Carousel Generator with various tools.

#### Step 1: Create a New Zap

1. Start by creating a new Zap in Zapier
2. Choose a trigger app and event (e.g., Google Sheets - New Row)

#### Step 2: Set Up the Webhook Action

1. Add an action step and choose "Webhooks by Zapier"
2. Select "POST" as the action event
3. Configure the webhook:
   - URL: `https://your-api-domain.com/api/v1/generate-carousel-with-urls`
   - Payload Type: JSON
   - Data:
     ```json
     {
       "carousel_title": "{{carousel_title}}",
       "slides": [
         {"text": "{{slide1_text}}"},
         {"text": "{{slide2_text}}"},
         {"text": "{{slide3_text}}"}
       ],
       "include_logo": true
     }
     ```
   - Headers:
     ```
     X-API-Key: your_api_key_here
     ```

#### Step 3: Process the Response

1. Add another action step for each image URL you want to process
2. Use the "URL" fields from the webhook response
3. For posting to Instagram, you can:
   - Use a Dropbox action to save the images
   - Use the Instagram Partner API action (if available)
   - Use Buffer, Hootsuite, or Later integrations to schedule posts

### Example 4: GitHub Actions Workflow

This example shows how to use GitHub Actions to automatically generate carousels when content files are updated in a repository.

Create a GitHub Actions workflow file at `.github/workflows/generate-carousels.yml`:

```yaml
name: Generate Instagram Carousels

on:
  push:
    paths:
      - 'content/carousels/**'
  workflow_dispatch:  # Allow manual triggering

jobs:
  generate:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install requests pyyaml

      - name: Generate carousels
        run: python .github/scripts/generate_carousels.py
        env:
          API_KEY: ${{ secrets.CAROUSEL_API_KEY }}
          API_URL: ${{ secrets.CAROUSEL_API_URL }}

      - name: Archive generated images
        uses: actions/upload-artifact@v2
        with:
          name: carousel-images
          path: generated/
```

Create the corresponding script at `.github/scripts/generate_carousels.py`:

```python
import os
import yaml
import requests
import json
from pathlib import Path

# Configuration from environment variables
API_URL = os.environ.get('API_URL', 'https://your-api-domain.com/api/v1/generate-carousel-with-urls')
API_KEY = os.environ.get('API_KEY', 'your_api_key_here')

# Directories
CONTENT_DIR = Path('content/carousels')
OUTPUT_DIR = Path('generated')
OUTPUT_DIR.mkdir(exist_ok=True)

# Process all YAML files in the content directory
for yaml_file in CONTENT_DIR.glob('*.yml'):
    print(f"Processing {yaml_file}...")

    # Read YAML content
    with open(yaml_file, 'r') as f:
        carousel_data = yaml.safe_load(f)

    # Validate basic structure
    if not carousel_data.get('title') or not carousel_data.get('slides'):
        print(f"  Error: Missing title or slides in {yaml_file}")
        continue

    # Prepare request data
    request_data = {
        "carousel_title": carousel_data['title'],
        "slides": [{"text": slide} for slide in carousel_data['slides']],
        "include_logo": carousel_data.get('include_logo', False),
        "logo_path": carousel_data.get('logo_path')
    }

    # Add settings if specified
    if 'settings' in carousel_data:
        request_data['settings'] = carousel_data['settings']

    # Call the API
    response = requests.post(
        API_URL,
        json=request_data,
        headers={"X-API-Key": API_KEY}
    )

    # Process response
    if response.status_code == 200:
        result = response.json()
        carousel_id = result['carousel_id']

        # Create output directory for this carousel
        carousel_dir = OUTPUT_DIR / carousel_id
        carousel_dir.mkdir(exist_ok=True)

        # Save metadata
        with open(carousel_dir / 'metadata.json', 'w') as f:
            json.dump(result, f, indent=2)

        # Download images
        for i, url in enumerate(result['public_urls']):
            image_path = carousel_dir / f"slide_{i+1}.png"
            image_response = requests.get(url)

            if image_response.status_code == 200:
                with open(image_path, 'wb') as f:
                    f.write(image_response.content)
                print(f"  Downloaded slide {i+1}")
            else:
                print(f"  Failed to download slide {i+1}: {image_response.status_code}")

        print(f"  Successfully generated carousel: {carousel_id}")
    else:
        print(f"  API Error: {response.status_code}")
        print(f"  {response.text}")
```

## Integration with Content Management Systems

### WordPress Integration

You can integrate the Instagram Carousel Generator with WordPress using a custom plugin:

```php
<?php
/**
 * Plugin Name: Instagram Carousel Generator
 * Description: Generates Instagram carousel images from WordPress posts
 * Version: 1.0
 * Author: Your Name
 */

// Add meta box to posts for carousel generation
function icg_add_meta_box() {
    add_meta_box(
        'icg_carousel',
        'Instagram Carousel',
        'icg_meta_box_callback',
        'post',
        'side'
    );
}
add_action('add_meta_boxes', 'icg_add_meta_box');

// Meta box content
function icg_meta_box_callback($post) {
    wp_nonce_field('icg_save_meta', 'icg_meta_nonce');

    $carousel_enabled = get_post_meta($post->ID, 'icg_carousel_enabled', true);
    ?>
    <p>
        <input type="checkbox" id="icg_carousel_enabled" name="icg_carousel_enabled" <?php checked($carousel_enabled, 'on'); ?>>
        <label for="icg_carousel_enabled">Generate Instagram Carousel</label>
    </p>
    <p>
        <button type="button" id="icg_generate_now" class="button">Generate Now</button>
    </p>
    <div id="icg_results"></div>
    <script>
        jQuery(document).ready(function($) {
            $('#icg_generate_now').on('click', function() {
                $(this).prop('disabled', true);
                $('#icg_results').html('<p>Generating carousel...</p>');

                $.ajax({
                    url: ajaxurl,
                    type: 'POST',
                    data: {
                        action: 'icg_generate_carousel',
                        post_id: <?php echo $post->ID; ?>,
                        nonce: $('#icg_meta_nonce').val()
                    },
                    success: function(response) {
                        $('#icg_results').html('<p>Success! <a href="' + response.data.url + '" target="_blank">View Carousel</a></p>');
                        $('#icg_generate_now').prop('disabled', false);
                    },
                    error: function() {
                        $('#icg_results').html('<p>Error generating carousel.</p>');
                        $('#icg_generate_now').prop('disabled', false);
                    }
                });
            });
        });
    </script>
    <?php
}

// Save meta data
function icg_save_meta($post_id) {
    if (!isset($_POST['icg_meta_nonce']) || !wp_verify_nonce($_POST['icg_meta_nonce'], 'icg_save_meta')) {
        return;
    }

    if (defined('DOING_AUTOSAVE') && DOING_AUTOSAVE) {
        return;
    }

    if (!current_user_can('edit_post', $post_id)) {
        return;
    }

    $carousel_enabled = isset($_POST['icg_carousel_enabled']) ? 'on' : 'off';
    update_post_meta($post_id, 'icg_carousel_enabled', $carousel_enabled);
}
add_action('save_post', 'icg_save_meta');

// AJAX handler for carousel generation
function icg_ajax_generate_carousel() {
    check_ajax_referer('icg_save_meta', 'nonce');

    $post_id = intval($_POST['post_id']);
    $post = get_post($post_id);

    if (!$post) {
        wp_send_json_error(['message' => 'Post not found']);
        return;
    }

    // Prepare carousel data
    $title = get_the_title($post_id);
    $content = $post->post_content;

    // Extract paragraphs for slides
    $paragraphs = preg_split('/\n\s*\n/', $content);
    $slides = array_slice($paragraphs, 0, 5); // Limit to 5 slides

    // Call the API
    $api_url = 'https://your-api-domain.com/api/v1/generate-carousel-with-urls';
    $response = wp_remote_post(
        $api_url,
        [
            'headers' => [
                'Content-Type' => 'application/json',
                'X-API-Key' => 'your_api_key_here'
            ],
            'body' => json_encode([
                'carousel_title' => $title,
                'slides' => array_map(function($text) {
                    return ['text' => wp_strip_all_tags($text)];
                }, $slides),
                'include_logo' => true
            ]),
            'timeout' => 60
        ]
    );

    if (is_wp_error($response)) {
        wp_send_json_error(['message' => $response->get_error_message()]);
        return;
    }

    $body = json_decode(wp_remote_retrieve_body($response), true);

    if (!$body || !isset($body['public_urls']) || !$body['public_urls']) {
        wp_send_json_error(['message' => 'API returned invalid response']);
        return;
    }

    // Store carousel data in post meta
    update_post_meta($post_id, 'icg_carousel_id', $body['carousel_id']);
    update_post_meta($post_id, 'icg_carousel_urls', $body['public_urls']);
    update_post_meta($post_id, 'icg_carousel_generated', current_time('mysql'));

    // Return success
    wp_send_json_success([
        'url' => admin_url('upload.php?page=icg-carousels&carousel=' . $body['carousel_id'])
    ]);
}
add_action('wp_ajax_icg_generate_carousel', 'icg_ajax_generate_carousel');
```

## Best Practices for Automation

### Rate Limiting and Quotas

When integrating with the Instagram Carousel Generator API in automated workflows, be mindful of rate limits:

1. Add delays between requests (e.g., `time.sleep(1)` in Python)
2. Implement exponential backoff for retries
3. Process batches of content during off-peak hours
4. Monitor API usage and set up alerts

### Error Handling

Implement robust error handling in your automation:

1. Check response status codes and handle errors appropriately
2. Implement retries with backoff for transient errors
3. Log detailed error information for troubleshooting
4. Set up monitoring and alerts for failure rates

### Content Validation

Validate content before sending to the API:

1. Check text length to avoid truncation
2. Sanitize special characters
3. Verify that all required fields are present
4. Test with a sample of your content before full automation

## Conclusion

By integrating the Instagram Carousel Generator API with automation tools, you can create powerful workflows that save time and ensure consistency in your social media content creation. The examples provided demonstrate just a few of the many integration possibilities.

Whether you're using n8n, Zapier, GitHub Actions, or custom scripts, the API provides a flexible foundation for automating your Instagram carousel generation process.

## Next Steps

1. Choose the integration approach that best fits your workflow
2. Start with a simple proof-of-concept integration
3. Gradually expand to include more automation features
4. Monitor performance and refine your process

For more advanced integration scenarios or custom solutions, consider reaching out to our team for assistance.
