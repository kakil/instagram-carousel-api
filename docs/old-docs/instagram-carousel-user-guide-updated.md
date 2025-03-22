# Instagram Carousel Automation User Guide

## Overview

This automation system creates Instagram carousel posts from content you enter in a Google Sheet. The system automatically generates carousel slides with a consistent design and publishes them to Instagram according to your schedule.

## How It Works

1. You add carousel content to the Google Sheet
2. Every day at 10:00 AM, the system checks for carousels marked as "scheduled"
3. If a carousel is ready to publish, the system:
   - Creates carousel images with your content
   - Posts the carousel to Instagram
   - Updates the status in the Google Sheet
   - Logs the results

## Getting Started

### Google Sheet Setup

Your carousel content is managed through a Google Sheet with the following columns:

| Column | Description | Example |
|--------|-------------|---------|
| carousel_id | Unique identifier (leave blank for auto-generation) | carousel_123 |
| carousel_title | Main title for the carousel | 5 Tips for Better Productivity |
| slide1_text | Text for the first slide | Wake up early and plan your day |
| slide2_text | Text for the second slide | Use the Pomodoro technique for focus |
| slide3_text - slide8_text | Text for additional slides | Take regular breaks to recharge |
| caption | Instagram post caption | Check out these productivity tips! |
| hashtags | Hashtags for the post | #productivity #tips #workflow |
| include_logo | Whether to include a logo (true/false) | true |
| logo_path | Path to logo file (if needed) | static/assets/logo.png |
| status | Current status | scheduled |
| publish_date | Target date for publishing (YYYY-MM-DD) | 2025-03-15 |
| notes | Additional information or comments | Updated content from workshop |

### Adding a New Carousel

1. Open the Google Sheet
2. Fill in a new row with your carousel content:
   - **carousel_title**: Enter a concise, attention-grabbing title (will appear on the first slide)
   - **slide1_text, slide2_text, etc.**: Enter the text for each slide (one column per slide)
   - **caption**: Write your Instagram caption
   - **hashtags**: Add relevant hashtags (without separating them)
   - **include_logo**: Set to "true" if you want to include a logo
   - **logo_path**: Enter path to logo if needed
   - **status**: Set to "scheduled"
   - **publish_date**: Enter the date you want it published

3. The system will automatically pick up your new carousel on the next run after the specified date.

### Status Values

The `status` column can have these values:
- **scheduled**: Ready to be processed
- **generated**: Images have been created but not yet published
- **published**: Successfully posted to Instagram
- **error**: Something went wrong during processing

## Design Guidelines

For best results:

- **Title**: Keep titles under 60 characters for readability
- **Slide Text**: Aim for 10-20 words per slide
- **Number of Slides**: Instagram allows up to 10 slides, but 4-8 slides work best
- **Caption**: Instagram captions can be up to 2,200 characters
- **Hashtags**: Include relevant hashtags to increase reach (up to 30)
- **Special Characters**: Some special characters might not render properly; the system will attempt to convert these automatically

## Example

Here's an example of a carousel row in the Google Sheet:

| Field | Content |
|-------|---------|
| carousel_title | 5 Ways to Improve Your Morning Routine |
| slide1_text | Wake up at the same time every day, even on weekends, to regulate your body clock. |
| slide2_text | Drink a full glass of water before anything else to rehydrate after sleep. |
| slide3_text | Get natural sunlight within the first hour of waking to boost alertness. |
| slide4_text | Move your body for at least 10 minutes to increase blood flow and energy. |
| slide5_text | Plan your top three priorities before checking email or social media. |
| caption | Transform your mornings and set yourself up for a productive day with these simple habits! Which one will you try tomorrow? |
| hashtags | #MorningRoutine #Productivity #HealthyHabits #Wellness |
| include_logo | true |
| status | scheduled |
| publish_date | 2025-03-20 |

## Preview Your Carousels

After your carousel has been generated, you can preview how it will look before it's published to Instagram. When the system generates your carousel images, it creates:

1. A unique `carousel_id` for tracking
2. A set of image files stored temporarily on the server

To view your generated carousel:

1. Look for rows with status "generated"
2. Note the `carousel_id` value
3. Access the preview at:
   `https://api.kitwanaakil.com/instagram-carousel/api/temp/[carousel_id]/slide_1.png`

## Troubleshooting

### Common Issues

1. **Carousel not publishing**
   - Check that the status is set to "scheduled"
   - Verify that you've filled in at least slide1_text
   - Check the "notes" column for any error messages
   - Make sure your carousel_title isn't too long

2. **Design problems**
   - Text too long: Shorten slide text for better readability
   - Title cut off: Reduce title length (aim for under 60 characters)
   - Unicode characters: Avoid special characters that might cause rendering issues
   - Logo issues: Verify the logo path is correct and accessible

3. **Error status in Google Sheet**
   - Check the "notes" column for specific error messages
   - Common errors include:
     - Unicode character issues (replace with standard characters)
     - Missing required fields (title or slide1_text)
     - Instagram API limitations (posting too frequently)

### Error Recovery

If your carousel gets an "error" status:

1. Check the error message in the notes column
2. Fix the issue (typically in the carousel or slide text)
3. Change the status back to "scheduled"
4. The system will attempt to process it again on the next run

## Advanced Features

### HTML Preview Generator

For a more detailed preview of your carousels, you can use the HTML preview generator:

1. Locate the `html_preview_generator.py` script
2. Run it with the carousel ID:
   ```
   python html_preview_generator.py --input [carousel_json_file] --output preview.html
   ```
3. Open the generated HTML file in any browser

### Custom Logo

The system can include your logo on carousel slides. To enable this:

1. Set the `include_logo` column to "true"
2. Specify the path to your logo in the `logo_path` column
3. Recommended format: PNG with transparent background
4. Optimal size: 300x300 pixels

### Publishing Schedule

The system checks for new carousels daily at 10:00 AM. To publish on a specific date:

1. Set the `publish_date` to your desired date
2. Ensure all content is ready and the status is "scheduled"
3. The system will pick it up on or after the publish_date

## Best Practices

1. **Plan ahead**: Prepare your carousel content in advance
2. **Be consistent**: Maintain a regular posting schedule
3. **Keep it concise**: Clear, brief messages perform best
4. **Use high contrast**: Dark text on light backgrounds or vice versa
5. **Include a call-to-action**: Encourage engagement in your caption
6. **Analyze performance**: Track which carousels get the most engagement

### Text Formatting Tips

- **Break up long paragraphs**: Use shorter sentences for better readability
- **Use numbers and lists**: They're easier to scan and remember
- **Add emphasis**: Use words like "key," "important," or "essential" to highlight critical points
- **Keep a consistent tone**: Maintain the same voice across all slides
- **Check for typos**: Review your content before scheduling

## Handling Special Characters

Some special characters may cause rendering issues. The system will try to automatically convert these, but it's best to avoid:

- Fancy quotes (" ") and apostrophes (' ')
- Em dashes (—) and en dashes (–)
- Special Unicode symbols
- Non-English characters if possible

Instead, use:
- Straight quotes (") and apostrophes (')
- Regular hyphens (-)
- Standard ASCII characters

---

For technical support or feature requests, please contact the system administrator.