import json
import datetime
import re
import logging
import sys
from typing import Dict, List, Tuple
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
import nltk
from content_manager.content_database import ContentDatabase
import openai
import requests
import os

# Configure OpenAI API  # اینجا API کلید خود را قرار دهید

# Configure logging with UTF-8 encoding
class UTFStreamHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            stream.buffer.write(msg.encode('utf-8'))
            stream.buffer.write(self.terminator.encode('utf-8'))
            self.flush()
        except Exception:
            self.handleError(record)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('seo_analysis.log', encoding='utf-8'),
        UTFStreamHandler(sys.stdout)
    ]
)

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

def extract_keywords(content: str, num_keywords: int = 5) -> List[str]:
    try:
        # Tokenize and clean text
        words = word_tokenize(content.lower())
        stop_words = set(stopwords.words('english'))
        words = [word for word in words if word.isalnum() and word not in stop_words]
        
        # Count word frequencies
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and return top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_words[:num_keywords]]
    except Exception as e:
        logging.error(f"Error in extract_keywords: {str(e)}")
        return []

def analyze_content_structure(content: str) -> Dict:
    """Analyze content structure including links and mobile-friendliness"""
    structure = {
        'internal_links': [],
        'external_links': [],
        'mobile_friendly': True,
        'has_schema_markup': False,
        'has_meta_viewport': False,
        'has_canonical': False
    }
    
    try:
        # Enhanced link checking
        link_pattern = r'<a[^>]*href=["\'](.*?)["\'][^>]*>'
        links = re.findall(link_pattern, content, re.IGNORECASE)
        for link in links:
            if link.startswith(('http', 'https', '//')):
                structure['external_links'].append(link)
            else:
                structure['internal_links'].append(link)
        
        # Additional SEO checks
        structure['has_schema_markup'] = bool(re.search(r'itemtype=["\'](.*?)["\']', content, re.IGNORECASE))
        structure['has_meta_viewport'] = bool(re.search(r'<meta[^>]+viewport[^>]+>', content, re.IGNORECASE))
        structure['has_canonical'] = bool(re.search(r'<link[^>]+rel=["\'](canonical)["\'][^>]*>', content, re.IGNORECASE))
        
        # Enhanced mobile-friendliness check
        if len(content) > 1000:
            if not structure['has_meta_viewport']:
                structure['mobile_friendly'] = False
            
    except Exception as e:
        logging.error(f"Error in analyze_content_structure: {str(e)}")
    
    return structure

def get_image_for_content(query, width=800, height=400):
    """Get a placeholder image for content"""
    try:
        # Create output directory if it doesn't exist
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Create images directory inside output
        images_dir = os.path.join(output_dir, "images")
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)
        
        # Clean filename - remove special characters and spaces
        filename = re.sub(r'[^\w\s-]', '', query.lower())
        filename = re.sub(r'[-\s]+', '_', filename)
        
        # Ensure filename isn't too long
        if len(filename) > 50:
            filename = filename[:50]
        
        image_path = os.path.join(images_dir, f"{filename}.jpg")
        
        # Create a new image with a gradient background
        image = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(image)
        
        # Create gradient background
        for y in range(height):
            r = int((y / height) * 100 + 100)
            g = int((y / height) * 100 + 150)
            b = int((y / height) * 100 + 200)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
        
        # Add text
        font_size = 40
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
        
        # Wrap text
        words = query.split()
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            text = ' '.join(current_line)
            if draw.textlength(text, font=font) > width - 40:
                current_line.pop()
                lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        
        # Calculate text position
        text_height = len(lines) * (font_size + 10)
        y = (height - text_height) // 2
        
        # Draw text
        for line in lines:
            text_width = draw.textlength(line, font=font)
            x = (width - text_width) // 2
            draw.text((x, y), line, font=font, fill=(255, 255, 255))
            y += font_size + 10
        
        # Save image
        image.save(image_path, quality=95)
        return image_path
    except Exception as e:
        logging.error(f"Error in get_image_for_content: {str(e)}")
        # Create a simple fallback image with error message
        image = Image.new('RGB', (width, height), color='gray')
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()
        draw.text((10, height//2), f"Image generation failed: {str(e)}", fill='white', font=font)
        image.save(image_path)
        return image_path

def create_placeholder_image(query, width, height, image_path):
    """Create a placeholder image with text"""
    try:
        # Create a new image with a gradient background
        image = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(image)
        
        # Create gradient background
        for y in range(height):
            r = int((y / height) * 100 + 100)
            g = int((y / height) * 100 + 150)
            b = int((y / height) * 100 + 200)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
        
        # Add text
        font_size = 40
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
        
        # Wrap text
        words = query.split()
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            text = ' '.join(current_line)
            if draw.textlength(text, font=font) > width - 40:
                current_line.pop()
                lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        
        # Calculate text position
        text_height = len(lines) * (font_size + 10)
        y = (height - text_height) // 2
        
        # Draw text
        for line in lines:
            text_width = draw.textlength(line, font=font)
            x = (width - text_width) // 2
            draw.text((x, y), line, font=font, fill=(255, 255, 255))
            y += font_size + 10
        
        # Save image
        image.save(image_path, quality=95)
        return image_path
    except Exception as e:
        logging.error(f"Error creating placeholder image: {str(e)}")
        return None

def convert_to_html(content, title, description):
    """Convert content to HTML format"""
    try:
        # Ensure title and description are not None
        safe_title = title if title else "Untitled"
        safe_description = description if description else ""
        
        html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
    <meta name="robots" content="index, follow">
    <link rel="canonical" href="https://yourdomain.com/content/{content.get('id', '')}">
    <title>{safe_title}</title>
    <meta name="description" content="{safe_description}">
    <meta name="keywords" content="{', '.join(content.get('keywords', []))}">
    
    <!-- Open Graph / Facebook -->
    <meta property="og:type" content="article">
    <meta property="og:url" content="https://yourdomain.com/content/{content.get('id', '')}">
    <meta property="og:title" content="{safe_title}">
    <meta property="og:description" content="{safe_description}">
    
    <!-- Twitter -->
    <meta property="twitter:card" content="summary">
    <meta property="twitter:url" content="https://yourdomain.com/content/{content.get('id', '')}">
    <meta property="twitter:title" content="{safe_title}">
    <meta property="twitter:description" content="{safe_description}">
    
    <!-- Custom CSS -->
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        h1, h2, h3 {{
            color: #2c3e50;
            margin-top: 30px;
        }}
        
        h1 {{
            font-size: 2.5em;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        
        h2 {{
            font-size: 1.8em;
            color: #2980b9;
        }}
        
        h3 {{
            font-size: 1.4em;
            color: #34495e;
        }}
        
        p {{
            margin-bottom: 20px;
            font-size: 1.1em;
        }}
        
        .content-section {{
            margin-bottom: 40px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        
        .table-of-contents {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        
        .table-of-contents ul {{
            list-style-type: none;
            padding: 0;
        }}
        
        .table-of-contents li {{
            margin: 10px 0;
        }}
        
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        
        a:hover {{
            text-decoration: underline;
        }}
        
        @media (max-width: 768px) {{
            body {{
                padding: 10px;
            }}
            
            h1 {{
                font-size: 2em;
            }}
            
            h2 {{
                font-size: 1.5em;
            }}
            
            h3 {{
                font-size: 1.2em;
            }}
            
            p {{
                font-size: 1em;
            }}
        }}
    </style>
</head>
<body>
    <article itemscope itemtype="https://schema.org/Article">
        <meta itemprop="headline" content="{safe_title}">
        <meta itemprop="description" content="{safe_description}">
        <meta itemprop="author" content="{content.get('author', 'Anonymous')}">
        <meta itemprop="datePublished" content="{datetime.datetime.now().isoformat()}">
        
        <h1 itemprop="name">{safe_title}</h1>
        
        <nav class="table-of-contents">
            <h2>Table of Contents</h2>
            <ul>
                <li><a href="#introduction">Introduction</a></li>
                {''.join([f'<li><a href="#{section.get("title", "").lower().replace(" ", "-")}">{section.get("title", "")}</a></li>' for section in content.get("sections", [])])}
            </ul>
        </nav>
        
        <div itemprop="articleBody">
            <section id="introduction" class="content-section">
                <h2>Introduction</h2>
                <p>{content.get('introduction', safe_description)}</p>
            </section>'''

        # Add sections
        for section in content.get('sections', []):
            section_title = section.get('title', '')
            section_content = section.get('content', '')
            if section_title and section_content:
                section_id = section_title.lower().replace(' ', '-')
                html_content += f'''
            <section id="{section_id}" class="content-section">
                <h2>{section_title}</h2>
                <p>{section_content}</p>
            </section>'''

        # Close HTML tags
        html_content += '''
        </div>
    </article>
</body>
</html>'''

        return html_content
        
    except Exception as e:
        logging.error(f"Error in convert_to_html: {str(e)}")
        return ""

def save_html_file(content, title, description, content_id):
    """Save content as HTML file"""
    try:
        # Convert content to HTML
        html_content = convert_to_html(content, title, description)
        
        # Create filename
        filename = f"content_{content_id}.html"
        
        # Save file
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        logging.info(f"✅ HTML file saved as {filename}")
        return filename
        
    except Exception as e:
        logging.error(f"Error in save_html_file: {str(e)}")
        return None

def calculate_seo_score(content, seo_data):
    score = 100
    issues = {
        'critical': [],
        'important': [],
        'moderate': [],
        'minor': []
    }
    suggestions = []
    
    try:
        # بررسی عنوان (25 امتیاز)
        title = seo_data.get('meta_title', '')
        if not title:
            issues['critical'].append("عنوان متا وجود ندارد")
            score -= 25
        elif len(title) > 60:
            issues['important'].append("عنوان متا خیلی طولانی است (بیش از 60 کاراکتر)")
            score -= 15
        elif len(title) < 30:
            issues['moderate'].append("عنوان متا خیلی کوتاه است (کمتر از 30 کاراکتر)")
            score -= 10

        # بررسی محتوا (35 امتیاز)
        content_text = str(content.get('content', ''))
        word_count = len(content_text.split())
        
        # بهبود محتوا با استفاده از هوش مصنوعی اگر خیلی کوتاه باشد
        if word_count < 300:
            improved_content = improve_content(content, title, seo_data.get('meta_description', ''))
            content['content'] = improved_content
            word_count = len(improved_content.split())
            content_text = improved_content
        
        if word_count < 300:
            issues['critical'].append("محتوا خیلی کوتاه است (کمتر از 300 کلمه)")
            score -= 25
        elif word_count < 500:
            issues['important'].append("محتوا می‌تواند طولانی‌تر باشد (کمتر از 500 کلمه)")
            score -= 10

        # بررسی ساختار (25 امتیاز)
        structure = analyze_content_structure(content_text)
        
        if not structure['internal_links']:
            issues['important'].append("لینک داخلی وجود ندارد")
            score -= 8
        if not structure['external_links']:
            issues['moderate'].append("لینک خارجی وجود ندارد")
            score -= 7

        # بررسی فنی (15 امتیاز)
        if not structure['has_meta_viewport']:
            issues['important'].append("تگ viewport برای موبایل وجود ندارد")
            score -= 8
        if not structure['has_schema_markup']:
            issues['moderate'].append("Schema Markup وجود ندارد")
            score -= 4
        if not structure['has_canonical']:
            issues['minor'].append("لینک canonical وجود ندارد")
            score -= 3

        # Generate prioritized suggestions
        for severity, severity_issues in issues.items():
            for issue in severity_issues:
                if "عنوان متا" in issue:
                    suggestions.append({
                        'priority': 1,
                        'text': "طول عنوان متا را بین 30 تا 60 کاراکتر تنظیم کنید"
                    })
                elif "محتوا" in issue and "کوتاه" in issue:
                    suggestions.append({
                        'priority': 1,
                        'text': "محتوا را به حداقل 300 کلمه افزایش دهید"
                    })
                elif "لینک داخلی" in issue:
                    suggestions.append({
                        'priority': 2,
                        'text': "لینک‌های داخلی به محتوای مرتبط اضافه کنید"
                    })
                elif "viewport" in issue:
                    suggestions.append({
                        'priority': 1,
                        'text': "تگ viewport برای سازگاری با موبایل اضافه کنید"
                    })
                elif "Schema Markup" in issue:
                    suggestions.append({
                        'priority': 3,
                        'text': "Schema Markup مناسب برای محتوا اضافه کنید"
                    })

        # Sort suggestions by priority
        suggestions.sort(key=lambda x: x['priority'])
        
        return {
            'score': max(0, min(score, 100)),  # Ensure score is between 0 and 100
            'issues': issues,
            'suggestions': suggestions
        }
        
    except Exception as e:
        logging.error(f"Error in calculate_seo_score: {str(e)}")
        return {
            'score': 0,
            'issues': {'critical': [f"خطا در محاسبه امتیاز: {str(e)}"]},
            'suggestions': []
        }

def get_grade(score: int) -> str:
    if score >= 90: return 'A'
    elif score >= 80: return 'B'
    elif score >= 70: return 'C'
    elif score >= 60: return 'D'
    else: return 'F'

def generate_seo_metadata(content):
    """Generate SEO metadata for content with enhanced structure"""
    try:
        title = str(content.get('title', ''))
        description = str(content.get('description', ''))
        
        # Generate meta title with optimal length
        meta_title = title
        if len(meta_title) < 30:
            # Add category or context to make it longer
            category = content.get('category', '')
            if category:
                meta_title = f"{meta_title} - {category}"
            else:
                # Add descriptive suffix
                meta_title = f"{meta_title} - Complete Guide and Best Practices"
        
        # Ensure meta title is not too long
        if len(meta_title) > 60:
            meta_title = meta_title[:57] + "..."
        
        # Generate meta description if not provided
        if not description:
            description = f"Learn about {title}. Discover insights, tips, and information about this topic."
        
        # Extract keywords from content
        keywords = extract_keywords(description)
        
        # Generate table of contents with more sections
        toc_items = [
            f"Introduction to {title}",
            "Key Features and Benefits",
            "How to Get Started",
            "Best Practices and Tips",
            "Common Questions and Answers",
            "Case Studies and Examples",
            "Additional Resources",
            "Conclusion"
        ]
        
        toc_html = "\n".join([f"<li><a href='#{item.lower().replace(' ', '-')}'>{item}</a></li>" for item in toc_items])
        
        # Generate external links
        external_links = [
            {
                'url': f"https://example.com/{title.lower().replace(' ', '-')}",
                'text': f"Learn more about {title}",
                'rel': 'nofollow'
            },
            {
                'url': f"https://example.com/resources/{title.lower().replace(' ', '-')}",
                'text': f"Additional resources for {title}",
                'rel': 'nofollow'
            },
            {
                'url': f"https://example.com/guide/{title.lower().replace(' ', '-')}",
                'text': f"Complete guide to {title}",
                'rel': 'nofollow'
            }
        ]
        
        # Enhanced content structure with semantic HTML and rich content
        enhanced_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
            <meta name="robots" content="index, follow">
            <link rel="canonical" href="https://yourdomain.com/content/{content.get('id', '')}">
            <title>{meta_title}</title>
            <meta name="description" content="{description}">
            <meta name="keywords" content="{', '.join(keywords)}">
            
            <!-- Open Graph / Facebook -->
            <meta property="og:type" content="article">
            <meta property="og:url" content="https://yourdomain.com/content/{content.get('id', '')}">
            <meta property="og:title" content="{meta_title}">
            <meta property="og:description" content="{description}">
            
            <!-- Twitter -->
            <meta property="twitter:card" content="summary">
            <meta property="twitter:url" content="https://yourdomain.com/content/{content.get('id', '')}">
            <meta property="twitter:title" content="{meta_title}">
            <meta property="twitter:description" content="{description}">
            
            <!-- Custom CSS -->
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                
                h1, h2, h3 {{
                    color: #2c3e50;
                    margin-top: 30px;
                }}
                
                h1 {{
                    font-size: 2.5em;
                    border-bottom: 2px solid #3498db;
                    padding-bottom: 10px;
                }}
                
                h2 {{
                    font-size: 1.8em;
                    color: #2980b9;
                }}
                
                h3 {{
                    font-size: 1.4em;
                    color: #34495e;
                }}
                
                p {{
                    margin-bottom: 20px;
                    font-size: 1.1em;
                }}
                
                ul, ol {{
                    margin-bottom: 20px;
                    padding-left: 20px;
                }}
                
                li {{
                    margin-bottom: 10px;
                }}
                
                a {{
                    color: #3498db;
                    text-decoration: none;
                }}
                
                a:hover {{
                    text-decoration: underline;
                }}
                
                .table-of-contents {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                
                .table-of-contents ul {{
                    list-style-type: none;
                    padding: 0;
                }}
                
                .table-of-contents li {{
                    margin: 10px 0;
                }}
                
                section {{
                    margin-bottom: 40px;
                    padding: 20px;
                    background: #fff;
                    border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
                }}
                
                @media (max-width: 768px) {{
                    body {{
                        padding: 10px;
                    }}
                    
                    h1 {{
                        font-size: 2em;
                    }}
                    
                    h2 {{
                        font-size: 1.5em;
                    }}
                    
                    h3 {{
                        font-size: 1.2em;
                    }}
                    
                    p {{
                        font-size: 1em;
                    }}
                }}
            </style>
        </head>
        <body>
            <article itemscope itemtype="https://schema.org/Article">
                <meta itemprop="headline" content="{meta_title}">
                <meta itemprop="description" content="{description}">
                <meta itemprop="author" content="{content.get('author', 'Anonymous')}">
                <meta itemprop="datePublished" content="{datetime.datetime.now().isoformat()}">
                
                <h1 itemprop="name">{title}</h1>
                
                <nav class="table-of-contents">
                    <h2>Table of Contents</h2>
                    <ul>
                        {toc_html}
                    </ul>
                </nav>
                
                <div itemprop="articleBody">
                    <section id="introduction-to-{title.lower().replace(' ', '-')}">
                        <h2>Introduction to {title}</h2>
                        <p>{description}</p>
                        <p>Welcome to our comprehensive guide on {title}. This article will help you understand the key concepts and practical applications.</p>
                        <p>Whether you're a beginner or an experienced professional, you'll find valuable insights and actionable tips.</p>
                    </section>
                    
                    <section id="key-features-and-benefits">
                        <h2>Key Features and Benefits</h2>
                        <p>Here are the main features and benefits of {title}:</p>
                        <ul>
                            <li>Comprehensive overview and understanding</li>
                            <li>Practical applications and real-world use cases</li>
                            <li>Industry best practices and standards</li>
                            <li>Easy integration with existing systems</li>
                            <li>Future trends and developments</li>
                        </ul>
                    </section>
                    
                    <section id="how-to-get-started">
                        <h2>How to Get Started</h2>
                        <p>Getting started with {title} is easy. Follow these simple steps:</p>
                        <ol>
                            <li>Learn the basics and understand requirements</li>
                            <li>Set up your environment and tools</li>
                            <li>Follow best practices and guidelines</li>
                            <li>Monitor and optimize your results</li>
                        </ol>
                    </section>
                    
                    <section id="best-practices-and-tips">
                        <h2>Best Practices and Tips</h2>
                        <p>To get the most out of {title}, follow these best practices:</p>
                        <ul>
                            <li>Keep your system updated and maintained</li>
                            <li>Optimize performance regularly</li>
                            <li>Follow security best practices</li>
                            <li>Focus on user experience</li>
                        </ul>
                    </section>
                    
                    <section id="common-questions-and-answers">
                        <h2>Common Questions and Answers</h2>
                        <div itemscope itemtype="https://schema.org/FAQPage">
                            <div itemscope itemprop="mainEntity" itemtype="https://schema.org/Question">
                                <h3 itemprop="name">What are the main benefits of {title}?</h3>
                                <div itemscope itemprop="acceptedAnswer" itemtype="https://schema.org/Answer">
                                    <div itemprop="text">
                                        <p>{title} offers many benefits. It improves efficiency, enhances user experience, and boosts performance. Learn more in our detailed guide.</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </section>
                    
                    <section id="case-studies-and-examples">
                        <h2>Case Studies and Examples</h2>
                        <p>Here are some real-world examples of {title} in action:</p>
                        <ul>
                            <li>Success story: How Company X improved results</li>
                            <li>Implementation: Overcoming challenges</li>
                            <li>Results: Measurable improvements</li>
                        </ul>
                    </section>
                    
                    <section id="additional-resources">
                        <h2>Additional Resources</h2>
                        <p>Want to learn more about {title}? Check out these resources:</p>
                        <ul>
                            <li><a href="{external_links[0]['url']}" rel="{external_links[0]['rel']}">{external_links[0]['text']}</a></li>
                            <li><a href="{external_links[1]['url']}" rel="{external_links[1]['rel']}">{external_links[1]['text']}</a></li>
                            <li><a href="{external_links[2]['url']}" rel="{external_links[2]['rel']}">{external_links[2]['text']}</a></li>
                        </ul>
                    </section>
                    
                    <section id="conclusion">
                        <h2>Conclusion</h2>
                        <p>{title} is a powerful tool for modern professionals. By following the guidelines in this article, you can achieve great results.</p>
                        <p>Start implementing these best practices today to see the benefits.</p>
                    </section>
                </div>
            </article>
        </body>
        </html>
        """
        
        return {
            'meta_title': meta_title,
            'meta_description': description[:160] if len(description) > 160 else description,
            'meta_keywords': ', '.join(keywords),
            'og_title': meta_title,
            'og_description': description,
            'twitter_card': 'summary',
            'twitter_title': meta_title,
            'twitter_description': description,
            'canonical_url': f"https://yourdomain.com/content/{content.get('id', '')}",
            'viewport_meta': '<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">',
            'charset_meta': '<meta charset="UTF-8">',
            'robots_meta': '<meta name="robots" content="index, follow">',
            'canonical_meta': f'<link rel="canonical" href="https://yourdomain.com/content/{content.get("id", "")}">',
            'schema_data': {
                '@context': 'https://schema.org',
                '@type': 'Article',
                'headline': meta_title,
                'description': description,
                'keywords': keywords,
                'datePublished': datetime.datetime.now().isoformat(),
                'author': {
                    '@type': 'Person',
                    'name': content.get('author', 'Anonymous')
                },
                'publisher': {
                    '@type': 'Organization',
                    'name': 'Your Organization Name',
                    'logo': {
                        '@type': 'ImageObject',
                        'url': 'https://yourdomain.com/logo.png'
                    }
                }
            },
            'enhanced_content': enhanced_content
        }
    except Exception as e:
        logging.error(f"Error in generate_seo_metadata: {str(e)}")
        return {
            'meta_title': '',
            'meta_description': '',
            'meta_keywords': '',
            'og_title': '',
            'og_description': '',
            'twitter_card': 'summary',
            'twitter_title': '',
            'twitter_description': '',
            'canonical_url': '',
            'viewport_meta': '',
            'charset_meta': '',
            'robots_meta': '',
            'canonical_meta': '',
            'schema_data': {},
            'enhanced_content': ''
        }

def improve_content(content, title, description):
    """Improve content quality using AI"""
    try:
        # تحلیل محتوای موجود
        current_content = content.get('content', '')
        word_count = len(current_content.split())
        
        if word_count < 1000:  # حداقل طول محتوا
            logging.info(f"\nبهبود محتوای {title}...")
            
            # تولید محتوای مرتبط با استفاده از هوش مصنوعی
            prompt = f"""
            Create a comprehensive, SEO-optimized article about {title} that includes:

            1. Introduction (100-150 words):
            - Hook: Start with an engaging fact or question
            - Context: Brief background information
            - Thesis: Main argument or purpose
            - Value proposition: What readers will learn

            2. Main Content (300-400 words):
            - Key Concepts:
              * Detailed explanations with examples
              * Step-by-step guides
              * Best practices and tips
            - Real-world Applications:
              * Case studies
              * Success stories
              * Implementation examples
            - Expert Insights:
              * Industry trends
              * Future predictions
              * Professional recommendations

            3. Advanced Topics (200-300 words):
            - Technical Details:
              * In-depth analysis
              * Advanced techniques
              * Performance optimization
            - Common Challenges:
              * Problem identification
              * Solution strategies
              * Prevention tips
            - Industry Standards:
              * Best practices
              * Compliance requirements
              * Quality metrics

            4. Practical Guide (200-300 words):
            - Implementation Steps:
              * Detailed instructions
              * Required resources
              * Timeline and milestones
            - Performance Metrics:
              * Success indicators
              * Measurement methods
              * Benchmarking data
            - Maintenance Tips:
              * Regular checks
              * Optimization strategies
              * Troubleshooting guide

            5. Conclusion (100-150 words):
            - Summary of key points
            - Future outlook
            - Call to action
            - Next steps

            SEO Requirements:
            - Use target keywords naturally
            - Include LSI keywords
            - Optimize headings and subheadings
            - Add internal and external links
            - Include meta descriptions
            - Use proper HTML structure

            Content Requirements:
            - Minimum 1000 words
            - Clear and engaging writing style
            - Proper formatting and structure
            - Include statistics and data
            - Add expert quotes
            - Use bullet points and lists
            - Include relevant images
            - Add social proof

            Current content: {current_content}
            Description: {description}
            """
            
            # تولید محتوای جدید
            new_content = generate_ai_content(prompt)
            
            if new_content:
                # ترکیب محتوای موجود با محتوای جدید
                improved_content = combine_content(current_content, new_content)
                
                # بررسی کیفیت محتوای جدید
                if is_content_quality_good(improved_content):
                    logging.info("✅ محتوا با موفقیت بهبود یافت")
                    return improved_content
                else:
                    logging.warning("⚠️ کیفیت محتوای تولید شده مناسب نیست")
                    return current_content
            else:
                logging.error("❌ خطا در تولید محتوای جدید")
                return current_content
                
        return current_content
        
    except Exception as e:
        logging.error(f"Error in improve_content: {str(e)}")
        return content

def generate_ai_content():
    """Generate content using AI API"""
    try:
        # پرامپت برای تولید توضیحات متا
        prompt = """
        Please generate a complete and well-structured meta description for a webpage. The description should fully explain what the page is about, why the user should be interested in it, and summarize the key points in a compelling and clear manner.

        Ensure that the sentences are logically connected and flow smoothly. Do not leave any sentence incomplete, and avoid cutting off the description in the middle. The description should be easy to read, natural, and clear. It should also be SEO-friendly and between 150-160 characters.

        Make sure to conclude sentences properly and do not stop abruptly in the middle of thoughts or sentences. For example, if the description is about a footballer, like Cristiano Ronaldo, include details about his career, achievements, and background in a coherent and complete way. Ensure the description is grammatically correct and avoids abrupt or incomplete sentences.
        """
        
        # تنظیمات پیشرفته برای تولید محتوای بهتر
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,  # پرامپت را اینجا قرار می‌دهید
            max_tokens=2000,  # افزایش تعداد توکن‌ها برای محتوای بیشتر
            temperature=0.8,  # افزایش خلاقیت
            top_p=0.95,  # افزایش تنوع
            frequency_penalty=0.7,  # کاهش تکرار کلمات
            presence_penalty=0.7,  # تشویق به استفاده از کلمات متنوع
            best_of=5,  # انتخاب بهترین پاسخ از بین چند پاسخ
            stop=None  # حذف استاپ کد خاص
        )
        
        if response and response.choices:
            # پردازش و بهبود پاسخ
            content = response.choices[0].text.strip()
            
            # اضافه کردن ساختار و فرمت‌بندی
            content = format_content(content)
            
            # بهینه‌سازی SEO
            content = optimize_seo(content)
            
            return content
        else:
            logging.error("❌ پاسخ نامعتبر از API")
            return ""
            
    except Exception as e:
        logging.error(f"Error in generate_ai_content: {str(e)}")
        return ""

def format_content(content):
    """Format and structure the content with appropriate headings and paragraphs"""
    try:
        # تقسیم محتوا به بخش‌های موضوعی
        sections = content.split('\n\n')
        formatted_content = ""
        
        # لیست بخش‌های پیش‌فرض
        default_sections = [
            "مقدمه",
            "نکات کلیدی",
            "مزایا و ویژگی‌ها",
            "نحوه استفاده",
            "بهترین شیوه‌ها",
            "سوالات متداول",
            "مطالعات موردی",
            "منابع بیشتر",
            "نتیجه‌گیری"
        ]
        
        current_section = 0
        paragraph_count = 0
        
        for section in sections:
            if section.strip():
                # اگر بخش با عنوان شروع شده باشد
                if section.startswith('#'):
                    level = len(section.split()[0])
                    title = section.replace('#' * level, '').strip()
                    formatted_content += f'<h{level} class="section-title">{title}</h{level}>\n'
                # اگر بخش با لیست شروع شده باشد
                elif section.startswith('- '):
                    # اگر بخش جدیدی شروع شده، عنوان مناسب اضافه کن
                    if current_section < len(default_sections):
                        formatted_content += f'<h2 class="section-heading">{default_sections[current_section]}</h2>\n'
                        current_section += 1
                    
                    items = section.split('\n')
                    formatted_content += '<ul class="feature-list">\n'
                    for item in items:
                        if item.strip():
                            formatted_content += f'<li class="list-item">{item.replace("- ", "")}</li>\n'
                    formatted_content += '</ul>\n'
                # اگر بخش با نقل قول شروع شده باشد
                elif section.startswith('>'):
                    quote = section.replace('>', '').strip()
                    formatted_content += f'<blockquote class="expert-quote">{quote}</blockquote>\n'
                # اگر بخش با عدد شروع شده باشد (مراحل یا نکات)
                elif re.match(r'^\d+\.', section):
                    if current_section < len(default_sections):
                        formatted_content += f'<h2 class="section-heading">{default_sections[current_section]}</h2>\n'
                        current_section += 1
                    
                    items = section.split('\n')
                    formatted_content += '<ol class="step-list">\n'
                    for item in items:
                        if item.strip():
                            # حذف شماره از ابتدای خط
                            clean_item = re.sub(r'^\d+\.\s*', '', item)
                            formatted_content += f'<li class="step-item">{clean_item}</li>\n'
                    formatted_content += '</ol>\n'
                # اگر بخش با کلمه کلیدی شروع شده باشد
                elif any(keyword in section.lower() for keyword in ['نکته:', 'توجه:', 'مهم:', 'هشدار:']):
                    if current_section < len(default_sections):
                        formatted_content += f'<h3 class="subsection-heading">{default_sections[current_section]}</h3>\n'
                        current_section += 1
                    
                    formatted_content += f'<div class="important-note">{section}</div>\n'
                # در غیر این صورت، پاراگراف معمولی
                else:
                    # هر 3 پاراگراف یک تیتر H2 اضافه کن
                    if paragraph_count % 3 == 0 and current_section < len(default_sections):
                        formatted_content += f'<h2 class="section-heading">{default_sections[current_section]}</h2>\n'
                        current_section += 1
                    
                    # تقسیم متن به پاراگراف‌های کوچکتر برای خوانایی بهتر
                    paragraphs = section.split('. ')
                    for paragraph in paragraphs:
                        if paragraph.strip():
                            formatted_content += f'<p class="content-paragraph">{paragraph.strip()}.</p>\n'
                            paragraph_count += 1
        
        return formatted_content
    except Exception as e:
        logging.error(f"Error in format_content: {str(e)}")
        return content

def optimize_seo(content):
    """Optimize content for SEO"""
    try:
        # اضافه کردن کلاس‌های CSS برای استایل‌دهی
        content = content.replace('<h1', '<h1 class="main-title"')
        content = content.replace('<h2', '<h2 class="section-heading"')
        content = content.replace('<h3', '<h3 class="subsection-heading"')
        content = content.replace('<p', '<p class="content-text"')
        content = content.replace('<ul', '<ul class="content-list"')
        content = content.replace('<li', '<li class="list-item"')
        
        # اضافه کردن لینک‌های داخلی
        content = add_internal_links(content)
        
        # بهینه‌سازی تصاویر
        content = optimize_images(content)
        
        return content
    except Exception as e:
        logging.error(f"Error in optimize_seo: {str(e)}")
        return content

def add_internal_links(content):
    """Add internal links to content"""
    try:
        # اضافه کردن لینک‌های مرتبط
        related_topics = extract_related_topics(content)
        for topic in related_topics:
            link = f'<a href="/topic/{topic.lower().replace(" ", "-")}" class="internal-link">{topic}</a>'
            content = content.replace(topic, link, 1)
        return content
    except Exception as e:
        logging.error(f"Error in add_internal_links: {str(e)}")
        return content

def optimize_images(content):
    """Optimize images in content"""
    try:
        # اضافه کردن alt text و lazy loading
        content = re.sub(r'<img([^>]*)>', r'<img\1 loading="lazy" alt="\1">', content)
        return content
    except Exception as e:
        logging.error(f"Error in optimize_images: {str(e)}")
        return content

def is_content_quality_good(content):
    """Check if content quality is good"""
    try:
        # بررسی طول محتوا
        word_count = len(content.split())
        if word_count < 1000:  # حداقل طول محتوا
            return False
            
        # بررسی خوانایی
        sentences = sent_tokenize(content)
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
        if avg_sentence_length > 20:  # خوانایی
            return False
            
        # بررسی تنوع کلمات
        words = word_tokenize(content.lower())
        unique_words = set(words)
        if len(unique_words) / len(words) < 0.7:  # تنوع کلمات
            return False
            
        # بررسی ساختار
        if not re.search(r'<h[1-6]', content):  # وجود عنوان
            return False
        if not re.search(r'<p', content):  # وجود پاراگراف
            return False
        if not re.search(r'<ul|<ol', content):  # وجود لیست
            return False
        if not re.search(r'<blockquote', content):  # وجود نقل قول
            return False
        if not re.search(r'<a', content):  # وجود لینک
            return False
        
        return True
    except Exception as e:
        logging.error(f"Error in is_content_quality_good: {str(e)}")
        return False

def combine_content(current_content, new_content):
    """Combine current content with new content"""
    try:
        # حذف محتوای تکراری
        current_sentences = set(sent_tokenize(current_content))
        new_sentences = sent_tokenize(new_content)
        
        # اضافه کردن جملات جدید
        combined_content = current_content
        for sentence in new_sentences:
            if sentence not in current_sentences:
                combined_content += "\n" + sentence
        
        # بررسی طول محتوا
        word_count = len(combined_content.split())
        if word_count < 1000:
            # اگر هنوز کوتاه است، محتوای جدید را کامل اضافه کنیم
            combined_content = new_content
        
        # حذف فاصله‌های اضافی
        combined_content = re.sub(r'\n\s*\n', '\n\n', combined_content)
        combined_content = combined_content.strip()
        
        return combined_content
    except Exception as e:
        logging.error(f"Error in combine_content: {str(e)}")
        return current_content

def get_user_content():
    """Get content from user and optimize it"""
    try:
        print("\nلطفا متن خود را وارد کنید (برای پایان، یک خط خالی وارد کنید):")
        lines = []
        while True:
            line = input()
            if line == "":
                break
            lines.append(line)
        
        content = "\n".join(lines)
        if not content.strip():
            print("❌ متن خالی وارد شده است")
            return None
            
        print("\nلطفا عنوان متن را وارد کنید:")
        title = input().strip()
        if not title:
            print("❌ عنوان خالی وارد شده است")
            return None
            
        print("\nلطفا توضیحات متا را وارد کنید:")
        description = input().strip()
        if not description:
            print("❌ توضیحات خالی وارد شده است")
            return None
            
        return {
            'content': content,
            'title': title,
            'description': description
        }
    except Exception as e:
        print(f"❌ خطا در دریافت متن: {str(e)}")
        return None

if __name__ == "__main__":
    SERVER = "45.149.76.141"
    DATABASE = "ContentGenerator"
    USERNAME = "admin"
    PASSWORD = "HTTTHFocBbW5CM"

    content_db = ContentDatabase(SERVER, DATABASE, USERNAME, PASSWORD)
    content_db.connect()

    try:
        # Try to connect to database
        content_db.connect()
        logging.info("✅ اتصال به دیتابیس برقرار شد.")
        
        # Test connection with a simple query
        test_query = "SELECT TOP 1 Id FROM dbo.TblPureContent"
        test_result = content_db.db.select(test_query)
        
        if not test_result:
            logging.error("❌ خطا در اتصال به دیتابیس: هیچ داده‌ای یافت نشد")
            raise Exception("Database connection test failed")
            
        logging.info("✅ تست اتصال به دیتابیس موفقیت‌آمیز بود")
        
        query = """
            SELECT Id, Title, Description, ContentCategoryId 
            FROM dbo.TblPureContent 
            ORDER BY Id
        """
        results = content_db.db.select(query)
        
        if not results:
            logging.info("هیچ محتوایی یافت نشد.")
        else:
            logging.info(f"در حال پردازش {len(results)} محتوا...")

            seo_analysis = {
                'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_content': len(results),
                'average_score': 0,
                'content_results': []
            }

            total_score = 0
            scores = []  # Store all scores for min/max calculation

            # Process content in batches
            batch_size = 10
            for i in range(0, len(results), batch_size):
                batch = results[i:i + batch_size]
                logging.info(f"پردازش دسته {i//batch_size + 1} از {(len(results) + batch_size - 1)//batch_size}")

                for row in batch:
                    content_id = row[0]
                    title = row[1]
                    description = row[2]
                    category_id = row[3]

                    logging.info(f"\nپردازش محتوای {content_id}...")
                    logging.info(f"عنوان: {title}")

                    try:
                        content_data = {
                            'id': content_id,
                            'title': title,
                            'description': description,
                            'content': description,
                            'category_id': category_id
                        }

                        # Generate SEO metadata with enhanced content
                        seo_metadata = generate_seo_metadata(content_data)

                        # Update content with enhanced version
                        content_data['content'] = seo_metadata.get('enhanced_content', description)

                        # Calculate SEO score
                        seo_result = calculate_seo_score(content_data, seo_metadata)

                        # Convert content to HTML and save as file
                        html_content = convert_to_html(content_data, title, description)
                        content_data['content'] = html_content

                        # Save HTML file
                        html_file = save_html_file(content_data, title, description, content_id)
                        if html_file:
                            content_data['html_file'] = html_file

                        # Add to results
                        content_result = {
                            'content_id': content_id,
                            'title': title,
                            'description': description[:200] + '...' if len(description) > 200 else description,
                            'category_id': category_id,
                            'seo_metadata': seo_metadata,
                            'seo_score': seo_result['score'],
                            'grade': get_grade(seo_result['score']),
                            'issues': seo_result['issues'],
                            'suggestions': seo_result['suggestions'],
                            'keywords': extract_keywords(description),
                            'processed_at': datetime.datetime.now().isoformat()
                        }

                        seo_analysis['content_results'].append(content_result)
                        total_score += seo_result['score']
                        scores.append(seo_result['score'])

                        logging.info(f"✅ محتوای {content_id} با موفقیت پردازش شد.")
                        logging.info(f"امتیاز SEO: {seo_result['score']}/100 (رتبه {get_grade(seo_result['score'])})")

                        if seo_result['issues']:
                            logging.info("\nمشکلات:")
                            for category, category_issues in seo_result['issues'].items():
                                if category_issues:
                                    logging.info(f"\n{category.upper()}:")
                                    for issue in category_issues:
                                        logging.info(f"- {issue}")

                        if seo_result['suggestions']:
                            logging.info("\nپیشنهادات:")
                            for suggestion in seo_result['suggestions']:
                                logging.info(f"- {suggestion['text']}")

                    except Exception as e:
                        logging.error(f"❌ خطا در پردازش محتوای {content_id}: {str(e)}")
                        continue

            if seo_analysis['content_results']:
                # Calculate statistics
                seo_analysis['average_score'] = total_score / len(seo_analysis['content_results'])
                seo_analysis['highest_score'] = max(scores)
                seo_analysis['lowest_score'] = min(scores)

                # Sort results by score
                seo_analysis['content_results'].sort(key=lambda x: x['seo_score'], reverse=True)

                # Save JSON results in output directory
                json_file = os.path.join("output", f"seo_analysis_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(seo_analysis, f, ensure_ascii=False, indent=2)

                logging.info(f"\n✅ تحلیل SEO با موفقیت انجام شد.")
                logging.info(f"نتایج در فایل {json_file} ذخیره شد.")

                logging.info("\n📊 خلاصه نتایج:")
                logging.info(f"تعداد کل محتوا: {len(results)}")
                logging.info(f"محتوای پردازش شده: {len(seo_analysis['content_results'])}")
                logging.info(f"میانگین امتیاز: {seo_analysis['average_score']:.1f}")
                logging.info(f"بالاترین امتیاز: {seo_analysis['highest_score']}")
                logging.info(f"پایین‌ترین امتیاز: {seo_analysis['lowest_score']}")

                # Print grade distribution
                grade_distribution = {}
                for result in seo_analysis['content_results']:
                    grade = result['grade']
                    grade_distribution[grade] = grade_distribution.get(grade, 0) + 1

                logging.info("\n📈 توزیع نمرات:")
                for grade in ['A', 'B', 'C', 'D', 'F']:
                    count = grade_distribution.get(grade, 0)
                    logging.info(f"{grade}: {count} محتوا")

                # Print improvement suggestions
                logging.info("\n💡 پیشنهادات کلی برای بهبود:")
                logging.info("1. گسترش محتوا: محتوای کوتاه را به حداقل 300 کلمه افزایش دهید")
                logging.info("2. بهبود ساختار: تگ‌های H1 مناسب اضافه کنید")
                logging.info("3. بهینه‌سازی عنوان و توضیحات متا: طول مناسب را رعایت کنید")
                logging.info("4. افزایش کلمات کلیدی: حداقل 3 کلمه کلیدی مرتبط اضافه کنید")
                logging.info("5. بهبود خوانایی: از جملات کوتاه‌تر و ساده‌تر استفاده کنید")
                logging.info("6. بهینه‌سازی تصاویر: alt text مناسب اضافه کنید")
                logging.info("7. بهبود لینک‌ها: لینک‌های داخلی و خارجی مرتبط اضافه کنید")
                logging.info("8. بهینه‌سازی موبایل: محتوا را برای نمایش در موبایل بهینه کنید")

    except Exception as e:
        logging.error(f"❌ خطای غیرمنتظره: {str(e)}")
    finally:
        try:
            content_db.disconnect()  # این دستور باید در بلوک finally فرورفته باشد
            logging.info("\nاتصال به دیتابیس بسته شد.")
        except Exception as e:
            logging.error("❌ خطا در بستن اتصال به دیتابیس")
            print("\n❌ خطا در بستن اتصال به دیتابیس")
