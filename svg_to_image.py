#!/usr/bin/env python3
"""
SVG to Image converter for email embedding.
Converts SVG content to base64-encoded PNG images that work in email clients.

Supports two conversion backends:
1. cairosvg (preferred, better quality but requires Cairo system library)
2. svglib + reportlab (pure Python fallback, no system dependencies)
"""
import base64
import io
import sys

# Track which conversion backend is available
CAIROSVG_AVAILABLE = False
SVGLIB_AVAILABLE = False

# Try cairosvg first (better quality)
try:
    import cairosvg
    CAIROSVG_AVAILABLE = True
except ImportError:
    pass
except Exception as e:
    print(f"Warning: cairosvg import failed: {e}", file=sys.stderr)

# Try svglib + reportlab as fallback (pure Python)
try:
    from svglib.svglib import svg2rlg
    from reportlab.graphics import renderPM
    SVGLIB_AVAILABLE = True
except ImportError:
    pass
except Exception as e:
    print(f"Warning: svglib import failed: {e}", file=sys.stderr)

if not CAIROSVG_AVAILABLE and not SVGLIB_AVAILABLE:
    print("Warning: No SVG to PNG converter available. Install cairosvg or svglib+reportlab.", file=sys.stderr)


def _convert_with_cairosvg(svg_content: str, scale: float = 2.0) -> bytes:
    """Convert SVG to PNG bytes using cairosvg"""
    return cairosvg.svg2png(
        bytestring=svg_content.encode('utf-8'),
        scale=scale
    )


def _convert_with_svglib(svg_content: str, scale: float = 2.0) -> bytes:
    """Convert SVG to PNG bytes using svglib + reportlab"""
    # Parse SVG
    drawing = svg2rlg(io.StringIO(svg_content))
    if drawing is None:
        raise ValueError("svglib failed to parse SVG")
    
    # Scale the drawing
    drawing.scale(scale, scale)
    drawing.width *= scale
    drawing.height *= scale
    
    # Render to PNG bytes
    png_buffer = io.BytesIO()
    renderPM.drawToFile(drawing, png_buffer, fmt='PNG')
    return png_buffer.getvalue()


def svg_to_base64_png(svg_content: str, scale: float = 2.0) -> str:
    """
    Convert SVG content to a base64-encoded PNG data URI.
    
    Args:
        svg_content: The SVG XML string
        scale: Scale factor for output resolution (default 2.0 for retina)
    
    Returns:
        Base64-encoded PNG data URI string for embedding in HTML
    """
    png_bytes = None
    errors = []
    
    # Try cairosvg first (better quality)
    if CAIROSVG_AVAILABLE:
        try:
            png_bytes = _convert_with_cairosvg(svg_content, scale)
        except Exception as e:
            errors.append(f"cairosvg: {e}")
    
    # Fallback to svglib
    if png_bytes is None and SVGLIB_AVAILABLE:
        try:
            png_bytes = _convert_with_svglib(svg_content, scale)
        except Exception as e:
            errors.append(f"svglib: {e}")
    
    # If all methods failed
    if png_bytes is None:
        if errors:
            print(f"SVG to PNG conversion failed: {'; '.join(errors)}", file=sys.stderr)
        else:
            print("SVG to PNG conversion failed: No converter available", file=sys.stderr)
        return ""
    
    # Encode to base64
    base64_png = base64.b64encode(png_bytes).decode('utf-8')
    return f"data:image/png;base64,{base64_png}"


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


def get_converter_status() -> dict:
    """Return status of available converters for debugging"""
    return {
        'cairosvg': CAIROSVG_AVAILABLE,
        'svglib': SVGLIB_AVAILABLE,
        'any_available': CAIROSVG_AVAILABLE or SVGLIB_AVAILABLE
    }


if __name__ == "__main__":
    # Show converter status
    status = get_converter_status()
    print(f"Converter status: {status}")
    
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
