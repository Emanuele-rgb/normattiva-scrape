#!/usr/bin/env python3
"""
Test script to check the problematic URL that's causing the scraper to hang
"""
import requests
import time
import sys

def test_problematic_url():
    """Test the specific problematic URL"""
    url = "https://www.normattiva.it/uri-res/N2Ls?urn:nir:2022;15!multivigente~"
    
    print("Testing problematic URL...")
    print(f"URL: {url}")
    
    start_time = time.time()
    
    try:
        print("Making request with 30 second timeout...")
        response = requests.get(url, timeout=30)
        
        elapsed = time.time() - start_time
        print(f"Response received in {elapsed:.1f} seconds")
        print(f"Status code: {response.status_code}")
        print(f"Content length: {len(response.content)} bytes")
        
        if response.status_code == 200:
            print("SUCCESS: URL is accessible")
            
            # Check if it's HTML content
            content_type = response.headers.get('content-type', '')
            print(f"Content type: {content_type}")
            
            if 'text/html' in content_type:
                print("Content appears to be HTML")
                
                # Show first 500 characters
                content_preview = response.text[:500]
                print(f"Content preview (first 500 chars):")
                print("-" * 50)
                print(content_preview)
                print("-" * 50)
                
                # Check for common issues
                if "404" in response.text or "Not Found" in response.text:
                    print("WARNING: Content suggests 404 error")
                elif "error" in response.text.lower():
                    print("WARNING: Content contains 'error' keyword")
                else:
                    print("Content looks normal")
            else:
                print(f"WARNING: Unexpected content type: {content_type}")
                
        else:
            print(f"ERROR: HTTP {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("ERROR: Request timed out after 30 seconds")
        print("This URL is likely causing the scraper to hang!")
        
    except requests.exceptions.ConnectionError as e:
        print(f"ERROR: Connection error: {e}")
        
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        print(f"Error type: {type(e).__name__}")

if __name__ == "__main__":
    test_problematic_url()
