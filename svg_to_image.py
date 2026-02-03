#!/usr/bin/env python3
"""
SVG to Image converter for email embedding.
Converts SVG content to base64-encoded PNG images that work in email clients.
"""
import base64
import io

try:
    import cairosvg
    CAIROSVG_AVAILABLE = True
except ImportError:
    CAIROSVG_AVAILABLE = False
    print("Warning: cairosvg not available. SVG to PNG conversion disabled.")


def svg_to_base64_png(svg_content: str, scale: float = 2.0) -> str:
    """
    Convert SVG content to a base64-encoded PNG data URI.
    
    Args:
        svg_content: The SVG XML string
        scale: Scale factor for output resolution (default 2.0 for retina)
    
    Returns:
        Base64-encoded PNG data URI string for embedding in HTML
    """
    if not CAIROSVG_AVAILABLE:
        return ""
    
    try:
        # Convert SVG to PNG bytes
        png_bytes = cairosvg.svg2png(
            bytestring=svg_content.encode('utf-8'),
            scale=scale
        )
        
        # Encode to base64
        base64_png = base64.b64encode(png_bytes).decode('utf-8')
        
        # Return as data URI
        return f"data:image/png;base64,{base64_png}"
    except Exception as e:
        print(f"Error converting SVG to PNG: {e}")
        return ""


def svg_to_img_tag(svg_content: str, alt_text: str = "Visualization", 
                   width: str = "100%", max_width: str = "500px",
                   scale: float = 2.0) -> str:
    """
    Convert SVG content to an HTML img tag with embedded base64 PNG.
    
    Args:
        svg_content: The SVG XML string
        alt_text: Alt text for the image
        width: CSS width of the image
        max_width: CSS max-width of the image
        scale: Scale factor for output resolution
    
    Returns:
        HTML img tag string, or empty string if conversion fails
    """
    data_uri = svg_to_base64_png(svg_content, scale=scale)
    if not data_uri:
        return ""
    
    return f'<img src="{data_uri}" alt="{alt_text}" style="width: {width}; max-width: {max_width}; display: block; margin: 10px auto;" />'


def svg_to_email_image(svg_content: str, alt_text: str = "Visualization",
                       center: bool = True) -> str:
    """
    Convert SVG to an email-friendly image block with centering div.
    
    Args:
        svg_content: The SVG XML string
        alt_text: Alt text for the image
        center: Whether to center the image
    
    Returns:
        HTML string with centered image, or empty string if conversion fails
    """
    img_tag = svg_to_img_tag(svg_content, alt_text=alt_text)
    if not img_tag:
        return ""
    
    if center:
        return f'<div style="text-align: center; margin: 15px 0;">{img_tag}</div>'
    return img_tag


if __name__ == "__main__":
    # Test with a simple SVG
    test_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" style="background-color: #1a1a2e;">
        <circle cx="50" cy="50" r="40" fill="#FFD700"/>
        <text x="50" y="55" text-anchor="middle" fill="#000" font-size="12">Test</text>
    </svg>'''
    
    result = svg_to_email_image(test_svg, "Test Image")
    if result:
        print("✓ SVG to PNG conversion successful")
        print(f"Output length: {len(result)} characters")
    else:
        print("✗ SVG to PNG conversion failed")
