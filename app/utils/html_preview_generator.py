#!/usr/bin/env python3
"""
Carousel Preview Generator

This script generates an HTML file for previewing Instagram carousel images.
It can work directly with the API response or with image files.
"""

import os
import sys
import json
import argparse
import base64
from datetime import datetime


def hex_to_base64(hex_string):
    """Convert hex string to base64 for HTML embedding"""
    try:
        # Convert hex to binary
        binary_data = bytes.fromhex(hex_string)

        # Convert binary to base64
        base64_data = base64.b64encode(binary_data).decode('utf-8')
        return base64_data
    except Exception as e:
        print(f"Error converting hex to base64: {e}")
        return None


def generate_html_preview(carousel_data, output_path=None):
    """
    Generate an HTML file to preview carousel images

    Args:
        carousel_data: Dictionary containing carousel data (from API response)
        output_path: Path to save the HTML file (default: carousel_preview_{timestamp}.html)

    Returns:
        Path to the generated HTML file
    """
    # Generate default output path if not provided
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"carousel_preview_{timestamp}.html"

    # Generate HTML content
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Instagram Carousel Preview - {carousel_data.get('carousel_id', 'Unknown')}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background-color: #f0f0f0;
            margin: 0;
            padding: 20px;
        }}
        header {{
            background-color: #222;
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        h1 {{
            margin: 0;
            padding: 0;
        }}
        .info {{
            display: flex;
            justify-content: space-between;
            margin-top: 10px;
            font-size: 14px;
            opacity: 0.9;
        }}
        .carousel-container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .carousel {{
            display: flex;
            overflow-x: auto;
            scroll-snap-type: x mandatory;
            scroll-behavior: smooth;
            -webkit-overflow-scrolling: touch;
            margin-bottom: 20px;
            padding: 10px 0;
        }}
        .slide {{
            scroll-snap-align: start;
            flex-shrink: 0;
            width: 500px;
            height: 600px;
            margin-right: 20px;
            border-radius: 10px;
            background: white;
            padding: 15px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
            display: flex;
            flex-direction: column;
        }}
        .slide-header {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            padding-bottom: 10px;
            border-bottom: 1px solid #eee;
        }}
        .slide-num {{
            font-weight: bold;
            color: #333;
        }}
        .slide-filename {{
            font-size: 12px;
            color: #777;
        }}
        .slide-image {{
            flex-grow: 1;
            display: flex;
            justify-content: center;
            align-items: center;
            overflow: hidden;
            border-radius: 5px;
            background-color: #f5f5f5;
        }}
        .slide-image img {{
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }}
        .error-slide {{
            border-left: 4px solid #ff4444;
        }}
        .warning {{
            background-color: #fff3cd;
            color: #856404;
            padding: 10px 15px;
            margin-bottom: 20px;
            border-radius: 4px;
            border-left: 4px solid #ffc107;
        }}
        .slide-controls {{
            display: flex;
            justify-content: center;
            margin-top: 20px;
        }}
        .slide-controls button {{
            background-color: #333;
            color: white;
            border: none;
            padding: 10px 15px;
            margin: 0 5px;
            border-radius: 4px;
            cursor: pointer;
            transition: background-color 0.2s;
        }}
        .slide-controls button:hover {{
            background-color: #555;
        }}
        .slide-indicator {{
            display: flex;
            justify-content: center;
            margin-top: 10px;
        }}
        .dot {{
            height: 10px;
            width: 10px;
            margin: 0 5px;
            background-color: #bbb;
            border-radius: 50%;
            cursor: pointer;
            transition: background-color 0.2s;
        }}
        .dot.active {{
            background-color: #333;
        }}
    </style>
</head>
<body>
    <header>
        <h1>Instagram Carousel Preview</h1>
        <div class="info">
            <span>Carousel ID: {carousel_data.get('carousel_id', 'Unknown')}</span>
            <span>Status: {carousel_data.get('status', 'Unknown')}</span>
            <span>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</span>
        </div>
    </header>

    <div class="carousel-container">
"""

    # Add warnings if any
    if carousel_data.get('warnings'):
        html_content += '        <div class="warning">\n'
        html_content += '            <strong>Warnings:</strong>\n'
        html_content += '            <ul>\n'
        for warning in carousel_data['warnings']:
            html_content += f'                <li>{warning}</li>\n'
        html_content += '            </ul>\n'
        html_content += '        </div>\n'

    # Add carousel
    html_content += '        <div class="carousel" id="carousel">\n'

    # Add slides
    for i, slide in enumerate(carousel_data.get('slides', [])):
        slide_num = i + 1
        filename = slide.get('filename', f'slide_{slide_num}.png')
        content = slide.get('content', '')
        is_error = 'error' in filename.lower()

        # Convert hex to base64
        base64_data = hex_to_base64(content) if content else ''

        html_content += f'            <div class="slide{" error-slide" if is_error else ""}" id="slide{slide_num}">\n'
        html_content += f'                <div class="slide-header">\n'
        html_content += f'                    <div class="slide-num">Slide {slide_num} of {len(carousel_data.get("slides", []))}</div>\n'
        html_content += f'                    <div class="slide-filename">{filename}</div>\n'
        html_content += f'                </div>\n'
        html_content += f'                <div class="slide-image">\n'

        if base64_data:
            html_content += f'                    <img src="data:image/png;base64,{base64_data}" alt="Slide {slide_num}">\n'
        else:
            html_content += f'                    <p>Image data not available</p>\n'

        html_content += f'                </div>\n'
        html_content += f'            </div>\n'

    html_content += '        </div>\n'

    # Add slide controls
    html_content += '        <div class="slide-controls">\n'
    html_content += '            <button id="prevBtn">Previous</button>\n'
    html_content += '            <button id="nextBtn">Next</button>\n'
    html_content += '        </div>\n'

    # Add slide indicators
    html_content += '        <div class="slide-indicator" id="indicator">\n'
    for i in range(len(carousel_data.get('slides', []))):
        html_content += f'            <span class="dot" data-slide="{i + 1}"></span>\n'
    html_content += '        </div>\n'

    # Close container
    html_content += '    </div>\n'

    # Add JavaScript
    html_content += """
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const carousel = document.getElementById('carousel');
            const slides = carousel.querySelectorAll('.slide');
            const prevBtn = document.getElementById('prevBtn');
            const nextBtn = document.getElementById('nextBtn');
            const dots = document.querySelectorAll('.dot');

            let currentSlide = 1;
            updateIndicator();

            // Event listeners
            prevBtn.addEventListener('click', showPreviousSlide);
            nextBtn.addEventListener('click', showNextSlide);

            dots.forEach(dot => {
                dot.addEventListener('click', function() {
                    currentSlide = parseInt(this.getAttribute('data-slide'));
                    showSlide(currentSlide);
                });
            });

            // Navigation functions
            function showPreviousSlide() {
                if (currentSlide > 1) {
                    currentSlide--;
                    showSlide(currentSlide);
                }
            }

            function showNextSlide() {
                if (currentSlide < slides.length) {
                    currentSlide++;
                    showSlide(currentSlide);
                }
            }

            function showSlide(slideNum) {
                const slide = document.getElementById(`slide${slideNum}`);
                slide.scrollIntoView({ behavior: 'smooth' });
                currentSlide = slideNum;
                updateIndicator();
            }

            function updateIndicator() {
                dots.forEach((dot, index) => {
                    if (index + 1 === currentSlide) {
                        dot.classList.add('active');
                    } else {
                        dot.classList.remove('active');
                    }
                });

                // Update button states
                prevBtn.disabled = currentSlide === 1;
                nextBtn.disabled = currentSlide === slides.length;
            }

            // Keyboard navigation
            document.addEventListener('keydown', function(e) {
                if (e.key === 'ArrowLeft') {
                    showPreviousSlide();
                } else if (e.key === 'ArrowRight') {
                    showNextSlide();
                }
            });

            // Handle scroll events to update the current slide indicator
            carousel.addEventListener('scroll', function() {
                const slideWidth = slides[0].offsetWidth + 20; // 20px margin
                const scrollPosition = carousel.scrollLeft;

                // Calculate current slide based on scroll position
                currentSlide = Math.round(scrollPosition / slideWidth) + 1;
                updateIndicator();
            });
        });
    </script>
</body>
</html>
"""

    # Write HTML file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"HTML preview generated: {output_path}")
    return output_path


def main():
    """Main function to run the preview generator"""
    parser = argparse.ArgumentParser(
        description='Generate HTML previews for Instagram carousel images')
    parser.add_argument('--input', required=True,
                        help='Input JSON file (API response)')
    parser.add_argument('--output',
                        help='Output HTML file path')

    args = parser.parse_args()

    try:
        # Read input JSON file
        with open(args.input, 'r', encoding='utf-8') as f:
            carousel_data = json.load(f)

        # Generate HTML preview
        output_path = generate_html_preview(carousel_data, args.output)

        print(f"Preview file created at: {output_path}")
        print(f"Open in your web browser to view the carousel")

        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())