# Instagram Carousel Automation Test Plan

## 1. Component Testing

### 1.1 FastAPI Image Generation API

| Test ID | Description | Steps | Expected Result | Status |
|---------|-------------|-------|----------------|--------|
| API-01 | Health check endpoint | 1. Send GET request to /instagram-carousel/health | Return 200 OK with status "healthy" | □ |
| API-02 | Basic carousel generation | 1. Send POST with title and 1 slide<br>2. Check response | Return success response with image data | □ |
| API-03 | Multi-slide carousel | 1. Send POST with title and 4 slides<br>2. Check response | Return success response with 4 slide images | □ |
| API-04 | Long text handling | 1. Send POST with very long slide text<br>2. Check generated image | Text properly wrapped and formatted | □ |
| API-05 | Logo inclusion | 1. Send POST with include_logo=true<br>2. Check generated image | Logo appears in correct position | □ |
| API-06 | Unicode character handling | 1. Send POST with text containing special characters<br>2. Check response | Text properly sanitized and rendered | □ |
| API-07 | Error handling for missing title | 1. Send POST with missing title<br>2. Check response | Return appropriate error message | □ |
| API-08 | Error handling for missing slides | 1. Send POST with empty slides array<br>2. Check response | Return appropriate error message | □ |
| API-09 | URL generation | 1. Send POST to /api/generate-carousel-with-urls<br>2. Check response | Return proper URLs for accessing slides | □ |

### 1.2 Google Sheets Integration

| Test ID | Description | Steps | Expected Result | Status |
|---------|-------------|-------|----------------|--------|
| GS-01 | Read scheduled carousels | 1. Add test rows with status="scheduled"<br>2. Run n8n Google Sheets node | Node returns only scheduled rows | □ |
| GS-02 | Parse individual slide columns | 1. Add row with data in slide1_text through slide5_text<br>2. Run Format Carousel Data node | All slide texts properly extracted into slides array | □ |
| GS-03 | Status update | 1. Process a test carousel<br>2. Check Google Sheet | Status column updated to "generated" then "published" | □ |
| GS-04 | Data validation | 1. Add row with missing required fields<br>2. Run n8n workflow | Appropriate error handling, sheet updated with error status | □ |
| GS-05 | Row number tracking | 1. Process carousel through workflow<br>2. Check row updates | Original row correctly updated with status changes | □ |

### 1.3 Instagram Graph API Connection

| Test ID | Description | Steps | Expected Result | Status |
|---------|-------------|-------|----------------|--------|
| IG-01 | Authentication | 1. Configure n8n Facebook Graph API node<br>2. Test connection | Connection successful | □ |
| IG-02 | Single carousel item upload | 1. Test Upload Single Carousel Item node<br>2. Check response | Media container created successfully | □ |
| IG-03 | Carousel container creation | 1. Test Create Carousel Container node<br>2. Check response | Carousel container created with all slides | □ |
| IG-04 | Caption formatting | 1. Create test with caption and hashtags<br>2. Run workflow | Caption appears correctly with hashtags | □ |
| IG-05 | Media publishing | 1. Test Publish Carousel node<br>2. Check Instagram account | Post published successfully | □ |
| IG-06 | Error handling | 1. Create test with invalid parameters<br>2. Run workflow | Proper error handling and reporting | □ |

### 1.4 Image Processing

| Test ID | Description | Steps | Expected Result | Status |
|---------|-------------|-------|----------------|--------|
| IMG-01 | Gradient text rendering | 1. Generate image with title<br>2. Check image | Title rendered with gradient effect | □ |
| IMG-02 | Text wrapping | 1. Generate image with long text<br>2. Check image | Text properly wrapped and centered | □ |
| IMG-03 | Unicode character handling | 1. Generate image with special characters<br>2. Check image | Characters properly sanitized and rendered | □ |
| IMG-04 | Error slide generation | 1. Force error with invalid text<br>2. Check response | Error slide generated with helpful message | □ |
| IMG-05 | Navigation indicators | 1. Generate multi-slide carousel<br>2. Check images | Navigation arrows and slide numbers shown correctly | □ |

## 2. Integration Testing

| Test ID | Description | Steps | Expected Result | Status |
|---------|-------------|-------|----------------|--------|
| INT-01 | End-to-end basic flow | 1. Add single carousel to Google Sheet<br>2. Run complete workflow<br>3. Check all outputs | Carousel posted, sheet updated, accessible via URLs | □ |
| INT-02 | Multiple carousels | 1. Add multiple carousels to Google Sheet<br>2. Run workflow | All eligible carousels processed correctly | □ |
| INT-03 | Recovery from failure | 1. Cause intentional error<br>2. Change status back to "scheduled"<br>3. Run workflow again | System recovers and completes processing | □ |
| INT-04 | URL validity | 1. Generate carousel<br>2. Check returned URLs | URLs are accessible and show correct images | □ |
| INT-05 | Workflow data flow | 1. Trace carousel_id and caption through workflow<br>2. Verify data preservation | Data correctly passes through all nodes | □ |

## 3. Performance Testing

| Test ID | Description | Steps | Expected Result | Status |
|---------|-------------|-------|----------------|--------|
| PERF-01 | API response time | 1. Generate 5 carousels<br>2. Measure response time | Average response time under 2 seconds per carousel | □ |
| PERF-02 | Workflow execution time | 1. Process 3 carousels<br>2. Measure total execution time | Complete within 5 minutes | □ |
| PERF-03 | Multiple concurrent requests | 1. Send 3 simultaneous requests<br>2. Check all responses | All requests processed successfully | □ |
| PERF-04 | Image generation time | 1. Generate carousels with 1, 5, and 10 slides<br>2. Measure processing time | Processing time scales linearly with slide count | □ |
| PERF-05 | Temporary file handling | 1. Generate multiple carousels<br>2. Run cleanup script<br>3. Check temp directory | Proper file cleanup without errors | □ |

## 4. User Experience Testing

| Test ID | Description | Steps | Expected Result | Status |
|---------|-------------|-------|----------------|--------|
| UX-01 | Google Sheet usability | 1. Ask non-technical user to add carousel<br>2. Observe process | User completes task without assistance | □ |
| UX-02 | Error feedback | 1. Intentionally create error<br>2. Check Google Sheet status and notes<br>3. Attempt to correct error | Error clearly communicated, correction possible | □ |
| UX-03 | Output quality | 1. Generate several test carousels<br>2. Review carousel design<br>3. Post to test Instagram account | Carousels look professional and maintain design consistency | □ |
| UX-04 | URL preview access | 1. Generate carousel<br>2. Access images via returned URLs | Users can view generated images before publication | □ |
| UX-05 | Documentation clarity | 1. Ask new user to follow documentation<br>2. Observe success rate | User can follow instructions without confusion | □ |

## 5. Edge Case Testing

| Test ID | Description | Steps | Expected Result | Status |
|---------|-------------|-------|----------------|--------|
| EDGE-01 | Maximum slide count | 1. Create carousel with 10+ slides<br>2. Run workflow | System handles or properly limits slides | □ |
| EDGE-02 | Special characters | 1. Include emojis, non-English characters<br>2. Generate carousel | Text displays correctly or gracefully degrades | □ |
| EDGE-03 | Network interruption | 1. Start workflow<br>2. Temporarily disconnect network<br>3. Reconnect network | System recovers or fails gracefully | □ |
| EDGE-04 | API rate limiting | 1. Run multiple workflows in short time<br>2. Monitor API responses | System handles rate limiting with retries | □ |
| EDGE-05 | Very long title | 1. Create carousel with extremely long title<br>2. Generate slides | Title wrapped properly or truncated gracefully | □ |
| EDGE-06 | Missing fonts | 1. Temporarily rename font files<br>2. Generate carousel | System falls back to default fonts | □ |

## 6. Security Testing

| Test ID | Description | Steps | Expected Result | Status |
|---------|-------------|-------|----------------|--------|
| SEC-01 | API access controls | 1. Attempt to access API without proper headers<br>2. Check response | Access handled appropriately | □ |
| SEC-02 | Instagram token security | 1. Inspect n8n workflow<br>2. Check credential storage | Tokens stored securely, not visible in logs | □ |
| SEC-03 | Error message information | 1. Trigger various errors<br>2. Review error messages | No sensitive information in error messages | □ |
| SEC-04 | Temporary file security | 1. Generate carousel<br>2. Attempt to access files with manipulated URLs | Access properly controlled | □ |
| SEC-05 | CORS configuration | 1. Test API from different origins<br>2. Check responses | CORS headers properly configured | □ |

## 7. Test Execution Plan

### 7.1 Test Environment Setup
1. Deploy FastAPI service to test environment
2. Create test Google Sheet with sample data
3. Set up test Instagram Business account
4. Configure n8n workflow with test credentials

### 7.2 Test Execution Sequence
1. Complete component testing for each module
2. Execute integration tests with all components
3. Perform performance testing under normal conditions
4. Test edge cases and error handling
5. Conduct security testing
6. Perform user experience testing with actual users

### 7.3 Test Data Preparation
- Create sample carousel content with various lengths and formats
- Prepare test images for logo inclusion testing
- Set up test cases with special characters and Unicode
- Create intentional errors for error handling testing

### 7.4 Success Criteria
- All test cases pass with expected results
- System properly handles error conditions
- Performance meets specified targets
- User feedback is positive regarding ease of use
- No security vulnerabilities identified

## 8. Defect Management

### 8.1 Defect Reporting
For each failed test:
1. Document the test ID and description
2. Record detailed steps to reproduce
3. Capture expected vs. actual results
4. Include relevant screenshots or logs
5. Assign severity (Critical, High, Medium, Low)

### 8.2 Defect Resolution
1. Prioritize defects by severity and impact
2. Assign each defect to appropriate team member
3. Implement and verify fixes
4. Retest failed test cases after fixes
5. Conduct regression testing to ensure no new issues

## 9. Specific Test Cases for FastAPI Implementation

### 9.1 API Endpoints

| Test ID | Endpoint | Method | Test Data | Expected Result | Status |
|---------|----------|--------|-----------|----------------|--------|
| API-E01 | /instagram-carousel/health | GET | None | Status "healthy" with timestamp | □ |
| API-E02 | /instagram-carousel/api/generate-carousel | POST | Valid carousel request | Success with hex-encoded images | □ |
| API-E03 | /instagram-carousel/api/generate-carousel-with-urls | POST | Valid carousel request | Success with public URLs | □ |
| API-E04 | /instagram-carousel/api/temp/{carousel_id}/{filename} | GET | Valid ID and filename | Image returned with correct content type | □ |
| API-E05 | /instagram-carousel/docs | GET | None | Swagger UI documentation loads | □ |

### 9.2 Image Service Tests

| Test ID | Function | Test Data | Expected Result | Status |
|---------|----------|-----------|----------------|--------|
| IMG-S01 | create_slide_image | Title, text, slide numbers | Valid image with expected components | □ |
| IMG-S02 | create_gradient_text | Text with various characters | Gradient text image created | □ |
| IMG-S03 | sanitize_text | Text with problematic Unicode | Sanitized text returned | □ |
| IMG-S04 | create_enhanced_error_slide | Error message | Error slide with readable information | □ |
| IMG-S05 | create_carousel_images | Complete carousel data | Set of properly generated images | □ |

## 10. Test Report Template

At the completion of testing, a test report will be prepared with:

1. **Executive Summary**
   - Overall pass/fail status
   - Critical findings
   - Recommendations

2. **Test Results**
   - Component test results
   - Integration test results
   - Performance metrics
   - Found defects and resolution status

3. **Deployment Readiness**
   - Go/No-Go recommendation
   - Outstanding issues
   - Mitigation strategies

4. **Future Improvements**
   - Identified enhancements
   - Performance optimization opportunities
   - User experience feedback