#!/usr/bin/env python3
"""
Mermaid chart generators for daily briefing visualizations.
These render natively in Obsidian.md without plugins.
"""

def news_pie_chart(continuing, new, dormant):
    """
    Generate a pie chart showing news story distribution.

    Args:
        continuing: list of continuing story groups
        new: list of new story groups
        dormant: list of dormant story groups

    Returns:
        Mermaid pie chart code block
    """
    c_count = len(continuing) if continuing else 0
    n_count = len(new) if new else 0
    d_count = len(dormant) if dormant else 0

    if c_count + n_count + d_count == 0:
        return ""

    return f'''```mermaid
pie title Today's News Landscape
    "Continuing" : {c_count}
    "New Today" : {n_count}
    "Dropped" : {d_count}
```'''


def stock_quadrant_chart(quotes):
    """
    Generate a quadrant chart comparing stock performance.
    X-axis: price change (loss to gain)
    Y-axis: relative volume or normalized change magnitude

    Args:
        quotes: dict of symbol -> quote data with change_percent

    Returns:
        Mermaid quadrant chart code block
    """
    if not quotes:
        return ""

    # Normalize change_percent to 0-1 scale (assuming -5% to +5% range)
    def normalize_change(pct):
        pct = float(pct)
        # Map -5% to 0, +5% to 1, 0% to 0.5
        normalized = (pct + 5) / 10
        return max(0.05, min(0.95, normalized))  # Clamp to visible range

    # For Y-axis, use absolute magnitude of change as "intensity"
    def get_intensity(pct):
        pct = abs(float(pct))
        # Map 0% to 0.3, 5% to 0.9
        normalized = 0.3 + (pct / 5) * 0.6
        return max(0.1, min(0.95, normalized))

    points = []
    for symbol, data in quotes.items():
        pct = float(data['change_percent'])
        x = normalize_change(pct)
        y = get_intensity(pct)
        # Clean up symbol for display
        display_symbol = symbol.replace('^', '')
        points.append(f'    {display_symbol}: [{x:.2f}, {y:.2f}]')

    return f'''```mermaid
quadrantChart
    title Market Movement
    x-axis Loss --> Gain
    y-axis Low Magnitude --> High Magnitude
{chr(10).join(points)}
```'''


def story_coverage_bar_chart(continuing_stories, max_stories=6):
    """
    Generate a bar chart showing article counts for top continuing stories.

    Args:
        continuing_stories: list of Group objects with articles and total_count
        max_stories: max number of stories to show

    Returns:
        Mermaid xychart code block
    """
    if not continuing_stories:
        return ""

    stories = continuing_stories[:max_stories]

    # Extract short titles (first 20 chars) and counts
    labels = []
    counts = []
    for group in stories:
        if group.articles:
            title = group.articles[0].title[:18]
            # Escape quotes and clean up
            title = title.replace('"', "'").replace('\n', ' ')
            labels.append(f'"{title}..."')
            counts.append(group.total_count)

    if not labels:
        return ""

    max_count = max(counts) if counts else 10

    return f'''```mermaid
xychart-beta
    title Story Coverage (Total Articles)
    x-axis [{", ".join(labels)}]
    y-axis "Articles" 0 --> {max_count + 2}
    bar [{", ".join(str(c) for c in counts)}]
```'''


def weather_timeline(periods):
    """
    Generate a timeline/gantt-style chart for weather forecast.

    Args:
        periods: list of dicts with 'name', 'temp', 'condition'

    Returns:
        Mermaid timeline code block
    """
    if not periods:
        return ""

    items = []
    for p in periods[:6]:
        name = p.get('name', 'Unknown')
        temp = p.get('temp', '')
        condition = p.get('condition', 'Unknown')[:25]
        # Clean for mermaid
        condition = condition.replace(':', '-').replace('"', "'")
        if temp:
            items.append(f"    {name} : {temp} {condition}")
        else:
            items.append(f"    {name} : {condition}")

    return f'''```mermaid
timeline
    title Weather Forecast
{chr(10).join(items)}
```'''


def spaceweather_status_chart(kp_value, xray_class, solar_wind_bt):
    """
    Generate a flowchart showing space weather status indicators.

    Args:
        kp_value: float Kp index value
        xray_class: string like 'A1.0', 'B2.3', 'C1.0', 'M1.0', 'X1.0'
        solar_wind_bt: string or float Bt value in nT

    Returns:
        Mermaid flowchart code block
    """
    # Determine Kp status
    if kp_value is None:
        kp_status = "N/A"
        kp_class = "gray"
    elif kp_value <= 2:
        kp_status = f"Kp {kp_value:.0f} Quiet"
        kp_class = "green"
    elif kp_value <= 4:
        kp_status = f"Kp {kp_value:.0f} Unsettled"
        kp_class = "yellow"
    elif kp_value <= 6:
        kp_status = f"Kp {kp_value:.0f} Active"
        kp_class = "orange"
    else:
        kp_status = f"Kp {kp_value:.0f} Storm"
        kp_class = "red"

    # Determine X-ray status
    if not xray_class or xray_class == 'N/A':
        xray_status = "X-ray: N/A"
        xray_style = "gray"
    elif xray_class.startswith('X'):
        xray_status = f"X-ray: {xray_class}"
        xray_style = "red"
    elif xray_class.startswith('M'):
        xray_status = f"X-ray: {xray_class}"
        xray_style = "orange"
    elif xray_class.startswith('C'):
        xray_status = f"X-ray: {xray_class}"
        xray_style = "yellow"
    else:
        xray_status = f"X-ray: {xray_class}"
        xray_style = "green"

    # Determine solar wind status
    try:
        bt = float(solar_wind_bt) if solar_wind_bt and solar_wind_bt != 'N/A' else None
        if bt is None:
            wind_status = "Wind: N/A"
            wind_style = "gray"
        elif bt < 5:
            wind_status = f"Wind: {bt:.0f}nT"
            wind_style = "green"
        elif bt < 10:
            wind_status = f"Wind: {bt:.0f}nT"
            wind_style = "yellow"
        elif bt < 20:
            wind_status = f"Wind: {bt:.0f}nT"
            wind_style = "orange"
        else:
            wind_status = f"Wind: {bt:.0f}nT"
            wind_style = "red"
    except (ValueError, TypeError):
        wind_status = "Wind: N/A"
        wind_style = "gray"

    return f'''```mermaid
flowchart LR
    subgraph Space Weather Status
        A["{kp_status}"]:::{kp_class}
        B["{xray_status}"]:::{xray_style}
        C["{wind_status}"]:::{wind_style}
    end
    classDef green fill:#90EE90,color:#000
    classDef yellow fill:#FFD700,color:#000
    classDef orange fill:#FFA500,color:#000
    classDef red fill:#FF6B6B,color:#000
    classDef gray fill:#D3D3D3,color:#000
```'''


if __name__ == "__main__":
    # Test examples
    print("=== News Pie Chart ===")
    print(news_pie_chart([1,2,3], [1,2], [1]))

    print("\n=== Stock Quadrant ===")
    test_quotes = {
        'MSFT': {'change_percent': '1.5'},
        'NVDA': {'change_percent': '-2.3'},
        '^DJI': {'change_percent': '0.5'},
    }
    print(stock_quadrant_chart(test_quotes))

    print("\n=== Space Weather ===")
    print(spaceweather_status_chart(3.5, 'C2.1', '8.5'))
