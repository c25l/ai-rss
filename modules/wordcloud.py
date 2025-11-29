import re
import random
import math
from collections import Counter
import cairosvg
import base64
class PersonalWordCloud:
    def __init__(self):
        # Common words to filter out
        self.stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
            'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their',
            'am', 'can', 'not', 'no', 'so', 'if', 'just', 'get', 'go', 'see', 'need', 'want',
            'make', 'take', 'come', 'know', 'think', 'feel', 'look', 'use', 'find', 'give',
            'tell', 'work', 'call', 'try', 'ask', 'turn', 'move', 'like', 'right', 'back',
            'still', 'way', 'even', 'new', 'old', 'long', 'good', 'great', 'small', 'large',
            'here', 'there', 'where', 'when', 'how', 'what', 'who', 'why', 'all', 'any',
            'each', 'few', 'more', 'most', 'other', 'some', 'such', 'only', 'own', 'same',
            'x', 'notes',"from","feed","html","http","https","www","com","nytimes","theatlantic","metafilter","start","end","feed",
             "div","today","data","got","going","done","start","end","summary","calendar","arxiv","announce","abstract","type"   # Personal additions
        }

    def extract_words(self, text):
        """Extract meaningful words from text"""
        # Convert to lowercase and extract words
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())

        # Filter out stop words and short words
        meaningful_words = [
            word for word in words
            if word not in self.stop_words
            and len(word) >= 3
            and not word.isdigit()
        ]

        return meaningful_words

    def get_word_frequencies(self, text):
        """Get word frequencies from text"""
        words = self.extract_words(text)
        return Counter(words)

    def generate_color(self, frequency, max_freq):
        """Generate color based on word frequency"""
        # Color palette for personal themes
        colors = [
            '#2563eb',  # Blue
            '#7c3aed',  # Purple
            '#dc2626',  # Red
            '#059669',  # Green
            '#d97706',  # Orange
            '#4f46e5',  # Indigo
            '#be185d',  # Pink
            '#0891b2',  # Cyan
        ]

        # Assign colors based on frequency ranking
        intensity = frequency / max_freq if max_freq > 0 else 0.5
        base_color = random.choice(colors)

        # Adjust opacity based on frequency
        opacity = 0.6 + (0.4 * intensity)

        return f"{base_color}{int(opacity * 255):02x}"

    def calculate_font_size(self, frequency, max_freq, min_size=16, max_size=42):
        """Calculate font size based on frequency"""
        if max_freq == 0:
            return min_size

        ratio = frequency / max_freq
        return int(min_size + (max_size - min_size) * ratio)

    def generate_positions(self, words, width=600, height=300):
        """Generate non-overlapping positions for words"""
        positions = []
        used_rects = []

        for i, (word, freq, font_size) in enumerate(words):
            # Estimate text dimensions
            text_width = len(word) * font_size * 0.6
            text_height = font_size

            # Try to find a non-overlapping position
            attempts = 0
            while attempts < 50:  # Limit attempts to avoid infinite loop
                x = random.randint(10, max(10, width - int(text_width) - 10))
                y = random.randint(text_height, height - 10)

                # Check for overlaps
                new_rect = (x, y - text_height, x + text_width, y)
                overlaps = False

                for used_rect in used_rects:
                    if (new_rect[0] < used_rect[2] and new_rect[2] > used_rect[0] and
                        new_rect[1] < used_rect[3] and new_rect[3] > used_rect[1]):
                        overlaps = True
                        break

                if not overlaps:
                    positions.append((x, y))
                    used_rects.append(new_rect)
                    break

                attempts += 1
            else:
                # If no position found, place it anyway but try to minimize overlap
                x = (i % 3) * (width // 3) + random.randint(10, width // 6)
                y = (i // 3) * 40 + text_height + 20
                y = min(y, height - 20)
                positions.append((x, y))

        return positions

    def create_wordcloud_svg(self, text, width=600, height=300, max_words=25):
        """Create an SVG wordcloud from text"""
        word_freq = self.get_word_frequencies(text)

        if not word_freq:
            return "<div style='font-style:italic;color:#666;'>No significant words found</div>"

        # Get top words
        top_words = word_freq.most_common(max_words)
        max_freq = top_words[0][1] if top_words else 1

        # Prepare word data with sizes
        word_data = []
        for word, freq in top_words:
            font_size = self.calculate_font_size(freq, max_freq)
            word_data.append((word, freq, font_size))

        # Generate positions
        positions = self.generate_positions(word_data, width, height)

        # Create SVG
        svg_elements = [f'<svg width="{width}" height="{height}" style="border:1px solid #ddd;border-radius:8px;background:#fafafa;">']

        for i, ((word, freq, font_size), (x, y)) in enumerate(zip(word_data, positions)):
            color = self.generate_color(freq, max_freq)

            # Add subtle rotation for visual interest
            rotation = random.randint(-15, 15)

            svg_elements.append(f'''
<text x="{x}" y="{y}"
      font-family="sans-serif"
      font-size="{font_size}px"
      font-weight="{600 if freq > max_freq * 0.7 else 400}"
      fill="{color}"
      transform="rotate({rotation} {x} {y})"
      title="{word} (mentioned {freq} times)">
    {word}
</text>''')

        svg_elements.append('</svg>')
        opy =cairosvg.svg2png(bytestring=''.join(svg_elements).encode('utf-8'))
        opy = base64.b64encode(opy).decode('utf-8')
        return "<img src=\"data:image/png;base64,"+opy+"\"/>"

    def create_summary_stats(self, text):
        """Create summary statistics about the text"""
        word_freq = self.get_word_frequencies(text)
        total_words = sum(word_freq.values())
        unique_words = len(word_freq)

        if not word_freq:
            return ""

        top_themes = word_freq.most_common(20)
        themes_text = ", ".join([f"{word} ({count})" for word, count in top_themes])

        return f"""
<div style='margin-top:10px;font-size:14px;color:#666;'>
<strong>Text Analysis:</strong> {total_words} words, {unique_words} unique terms<br/>
<strong>Key themes:</strong> {themes_text}
</div>"""

if __name__ == "__main__":
    # Test with sample data
    cloud = PersonalWordCloud()
    sample_text = """
    dinner Korean sausage potato flakes broccoli
    October Estes cabin available
    crisis measures trajectory learning documentaries
    weather space plots tinker Boulder schedule
    """

    print(cloud.create_wordcloud_svg(sample_text))
    print(cloud.create_summary_stats(sample_text))