# Skill: LinkedIn Poster

## Purpose
Automate the process of posting content to LinkedIn from within the AI Employee Vault system. This skill enables scheduled, templated, or programmatic posting to LinkedIn company or personal profiles, supporting marketing, announcements, and engagement automation.

## Features
- Post text, images, or links to LinkedIn
- Support for scheduled and immediate posts
- Error handling for failed posts
- Logging of post attempts and results
- Integration with approval workflows (optional)

## Usage
- Import and call the main function to post content
- Provide authentication (OAuth or token) as required
- Pass content (text, image path, or link) as arguments
- Optionally specify scheduling or approval requirements

## Example
```python
from linkedin_poster import post_to_linkedin

post_to_linkedin(
    text="Excited to announce our new product!",
    image_path="/path/to/image.jpg",
    link="https://company.com/new-product",
    scheduled_time=None  # or datetime object for scheduling
)
```

## Best Practices
- Validate content before posting
- Use environment variables or secure storage for credentials
- Log all post attempts and results for auditing
- Handle LinkedIn API rate limits and errors gracefully

## Limitations
- Subject to LinkedIn API restrictions and rate limits
- Requires valid LinkedIn developer credentials
- May require manual approval for some posts (if integrated)

## File Location
This skill is implemented in: `scripts/scripts/linkedin_poster.py`

---
*Last updated: 2026-03-17*