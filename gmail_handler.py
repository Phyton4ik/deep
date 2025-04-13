import imaplib
import email
import time
from email.header import decode_header
from typing import Optional
import re

from utils.logger import log

IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993

def connect_to_gmail(email_address: str, password: str) -> Optional[imaplib.IMAP4_SSL]:
    """Connect to Gmail using IMAP"""
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(email_address, password)
        log(f"[SUCCESS] Connected to Gmail: {email_address}")
        return mail
    except Exception as e:
        log(f"[ERROR] Failed to connect to Gmail {email_address}: {str(e)}")
        return None

def search_verification_email(mail: imaplib.IMAP4_SSL, subject_filter: str, sender_filter: str,
                           retries: int = 6, delay: int = 10) -> Optional[str]:
    """Search for verification email and extract the code"""
    mail.select("inbox")
    attempt = 0

    while attempt < retries:
        try:
            # Search for emails from sender with subject containing filter
            result, data = mail.search(None, f'(FROM "{sender_filter}" SUBJECT "{subject_filter}")')
            if result != "OK":
                log(f"[WARNING] Gmail search failed. Retrying... ({attempt + 1}/{retries})")
                time.sleep(delay)
                attempt += 1
                continue

            email_ids = data[0].split()
            if not email_ids:
                log(f"[INFO] No matching emails found. Waiting... ({attempt + 1}/{retries})")
                time.sleep(delay)
                attempt += 1
                continue

            # Process emails from newest to oldest
            for num in reversed(email_ids):
                result, msg_data = mail.fetch(num, "(RFC822)")
                if result != "OK":
                    continue

                msg = email.message_from_bytes(msg_data[0][1])
                body = get_email_body(msg)

                # Try to extract code from both plain text and HTML
                code = extract_verification_code(body)
                if code:
                    log(f"[SUCCESS] Verification code found: {code}")
                    return code

            log(f"[INFO] No verification code found in emails. Waiting... ({attempt + 1}/{retries})")
            time.sleep(delay)
            attempt += 1

        except Exception as e:
            log(f"[ERROR] Error during Gmail search: {str(e)}")
            time.sleep(delay)
            attempt += 1

    log("[FAILURE] Verification email not found or no code extracted.")
    return None

def get_email_body(msg: email.message.Message) -> str:
    """Extract email body content from message"""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            
            # Skip attachments
            if "attachment" in content_disposition:
                continue
                
            if content_type == "text/plain" or content_type == "text/html":
                try:
                    body += part.get_payload(decode=True).decode()
                except:
                    pass
    else:
        try:
            body = msg.get_payload(decode=True).decode()
        except:
            pass
            
    return body

def extract_verification_code(body: str) -> Optional[str]:
    """Extract 6-digit verification code from email body"""
    # Try to find code in plain text format
    code_match = re.search(r'(\d{6})\s+is your Reddit verification code', body)
    if code_match:
        return code_match.group(1)
    
    # Try to find code in HTML format (like in <h3> tags)
    html_match = re.search(r'<h[1-6][^>]*>(\d{6})</h[1-6]>', body)
    if html_match:
        return html_match.group(1)
        
    # Fallback - look for any 6-digit sequence
    fallback_match = re.search(r'\b\d{6}\b', body)
    if fallback_match:
        return fallback_match.group(0)
        
    return None

def get_verification_code(gmail: str, password: str) -> Optional[str]:
    """
    Connect to Gmail and try to retrieve Reddit verification code.
    Returns the 6-digit code if found, None otherwise.
    """
    mail = connect_to_gmail(gmail, password)
    if not mail:
        return None

    code = search_verification_email(
        mail,
        subject_filter="verification code",
        sender_filter="no reply@redditmail.com"
    )
    
    mail.logout()
    return code