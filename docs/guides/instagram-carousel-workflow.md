# Instagram Carousel Automation Plan

## 1. Project Overview

This document outlines the implementation plan for an n8n workflow that automatically generates Instagram carousels from Google Sheet data. The workflow will create visually consistent carousel posts with customizable text, and publish them directly to Instagram.

## 2. Components

### 2.1 Data Source
- **Google Sheets**
  - Contains carousel content and metadata
  - Tracks publication status

### 2.2 Image Generation API
- **Python Flask API**
  - Creates carousel images with consistent styling
  - Supports branding elements (optional logo)
  - Handles text formatting and slide navigation

### 2.3 Instagram Publishing
- **Instagram Graph API**
  - Publishes carousel posts as drafts
  - Requires Business account and proper permissions

### 2.4 Notification System
- **Email notifications**
  - Success/failure alerts
  - Links to published content
- **iMessage notifications** (if possible)
  - Brief status updates

## 3. Google Sheet Structure

| Column | Data Type | Description | Validation |
|--------|-----------|-------------|------------|
| carousel_id | Text | Unique identifier | Required, unique |
| carousel_title | Text | Main title for carousel | Required, 60 char max |
| slide_text | Text | Content for each slide, separated by delimiter | Required |
| caption | Text | Instagram post caption | Required, 2200 char max |
| published | Boolean | Publication status flag | TRUE/FALSE only |
| publish_date | Date | Target date for publishing | Valid date format |
| publish_timestamp | Timestamp | When actually published | Auto-generated |
| tags | Text | Hashtags for the post | Optional, # prefix validation |

## 4. Image Generation API Specification

### 4.1 Endpoint: `/generate-carousel`
- **Method**: POST
- **Request Body**:
  ```json
  {
    "carousel_title": "Your Title Here",
    "slides": [
      {"text": "First slide content"},
      {"text": "Second slide content"}
    ],
    "include_logo": true,
    "logo_path": "/path/to/logo.png"
  }
  ```
- **Response Body**:
  ```json
  {
    "status": "success",
    "carousel_id": "abc123",
    "slides": [
      {
        "filename": "slide_1.png",
        "content": "base64_encoded_content"
      }
    ]
  }
  ```

### 4.2 Image Specifications
- Resolution: 1080×1080 pixels (square)
- Background: Dark gray (#121212)
- Title: Black to white gradient text
- Content: White text, centered
- Navigation arrows for multi-slide carousels
- Slide counter in bottom center

## 5. n8n Workflow Design

### 5.1 Trigger
- Schedule trigger: Daily at 9:30 AM

### 5.2 Data Retrieval
- Google Sheets node to fetch rows where:
  - `published = FALSE`
  - `publish_date` is today or earlier

### 5.3 Content Processing
- Function node to format Google Sheets data for the image API
- Split slide_text into individual slides

### 5.4 Image Generation
- HTTP Request node to call the Image Generation API
- Process and save generated images

### 5.5 Instagram Publishing
- Instagram Business node for publishing
- Set media type to CAROUSEL
- Use retrieved caption and images

### 5.6 Status Update
- Google Sheets node to update:
  - `published = TRUE`
  - `publish_timestamp = current_time`

### 5.7 Notification
- Email Send node for email notifications
- HTTP Request node for iMessage (via Apple Script on a Mac server)

### 5.8 Error Handling
- IF nodes to check for errors at each stage
- Error notification branch
- Logging of error details

## 6. Instagram Graph API Setup

### 6.1 Prerequisites
- Business Instagram account
- Facebook Developer account
- Facebook Page connected to Instagram account

### 6.2 Authentication Steps
1. Create a Facebook App
2. Add Instagram Graph API
3. Configure permissions:
   - `instagram_basic`
   - `instagram_content_publish`
   - `pages_read_engagement`
4. Generate access token for the page
5. Connect to Instagram Business account

### 6.3 n8n Configuration
- Add Instagram credentials in n8n
- Configure with appropriate access tokens
- Set up required permissions

## 7. Deployment Process

### 7.1 Python API Deployment
1. Set up Flask server on your VPS
2. Install required packages:
   ```
   pip install Flask Pillow numpy
   ```
3. Configure as a service using systemd
4. Set up domain/port forwarding if needed

### 7.2 n8n Workflow Deployment
1. Import workflow JSON
2. Configure credentials:
   - Google Sheets
   - Instagram
   - SMTP for email
3. Adjust schedule as needed
4. Activate workflow

## 8. Testing Strategy

### 8.1 Component Testing
- Test Image API with sample data
- Verify Google Sheet reading/writing
- Confirm notification system works

### 8.2 End-to-End Testing
- Create test carousel in Google Sheet
- Run workflow manually
- Verify carousel is created and posted
- Check notification delivery
- Confirm status updates in Google Sheet

## 9. Maintenance Considerations

### 9.1 Monitoring
- Set up monitoring for the Flask API
- Configure n8n execution logging
- Regular checks of Google Sheet for errors

### 9.2 Troubleshooting
- Common issues and solutions
- API response codes
- Instagram API limitations

## 10. Future Enhancements

### 10.1 Potential Features
- Multiple carousel templates/styles
- Analytics tracking for posts
- Automatic content generation via AI
- Approval workflow before posting

### 10.2 Integration Options
- Connect with content calendar
- Integrate with social media planning tools
- Add support for other platforms (Twitter, LinkedIn)
