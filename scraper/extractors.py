"""Data extraction utilities."""

import re
from .config import INVALID_DOMAINS


def extract_email(text):
    """Extract email addresses from text."""
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(pattern, text)
    
    # Filter out invalid emails
    emails = [e for e in emails if not e.endswith('.png') and not e.endswith('.jpg')]
    
    return emails[0] if emails else ''


def extract_phone(text):
    """Extract Australian phone numbers from text."""
    # Must have spaces, dashes, or parentheses to avoid random number sequences
    pattern = r'(?:\+61[\s-]?[2-478][\s-]?\d{4}[\s-]?\d{4}|\(0[2-8]\)[\s-]?\d{4}[\s-]?\d{4}|0[2-8][\s-]\d{4}[\s-]\d{4}|04\d{2}[\s-]\d{3}[\s-]\d{3}|1[38]00[\s-]\d{3}[\s-]\d{3})'
    phones = re.findall(pattern, text)
    
    # Filter phones - remove if no spaces/dashes/parentheses
    phones = [p for p in phones if any(char in p for char in [' ', '-', '(', ')'])]
    
    return phones[0] if phones else ''


def extract_website(text):
    """Extract website URLs from text."""
    pattern = r'(?:https?://(?:www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:\.[a-zA-Z]{2,})?(?:/[^\s<>"]*)?|www\.[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:\.[a-zA-Z]{2,})?(?:/[^\s<>"]*)?)'
    websites = re.findall(pattern, text)
    
    # Filter out invalid websites
    websites = [w for w in websites if not any(inv in w.lower() for inv in INVALID_DOMAINS)]
    websites = [w for w in websites if '@' not in w and not w.endswith('.jpg') and not w.endswith('.png')]
    
    return websites[0] if websites else ''


def extract_contact_info(text):
    """Extract email, phone, and website from text."""
    return {
        'email': extract_email(text),
        'phone': extract_phone(text),
        'website': extract_website(text)
    }
