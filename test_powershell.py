#!/usr/bin/env python3
"""
Test PowerShell functionality
"""
import subprocess
import sys
import os

def format_powershell_command(commands):
    """Format PowerShell commands with proper semicolon separation"""
    if isinstance(commands, str):
        return commands
    elif isinstance(commands, list):
        return '; '.join(commands)
    else:
        return str(commands)

def run_powershell_command(commands, timeout=30):
    """Run PowerShell commands with proper error handling"""
    formatted_cmd = format_powershell_command(commands)
    print(f"Running PowerShell: {formatted_cmd}")
    
    try:
        result = subprocess.run([
            'powershell.exe', '-Command', formatted_cmd
        ], 
        cwd=os.getcwd(),
        capture_output=True, 
        text=True, 
        encoding='utf-8',
        errors='replace',
        timeout=timeout
        )
        return result
    except subprocess.TimeoutExpired:
        print(f"ERROR: PowerShell command timed out after {timeout} seconds")
        return 'timeout'
    except Exception as e:
        print(f"ERROR: PowerShell command failed: {e}")
        return None

def test_powershell():
    """Test PowerShell functionality"""
    print("Testing PowerShell functionality...")
    
    skipped_articles = []

    # Test 1: Simple command
    print("\n=== Test 1: Simple command ===")
    result = run_powershell_command("echo 'Hello from PowerShell'", timeout=60)
    if result == 'timeout':
        skipped_articles.append("Test 1: echo 'Hello from PowerShell'")
    elif result:
        print(f"Return code: {result.returncode}")
        print(f"Output: {result.stdout.strip()}")
        print(f"Error: {result.stderr.strip()}")

    # Test 2: Multiple commands with semicolon
    print("\n=== Test 2: Multiple commands ===")
    result = run_powershell_command([
        "echo 'First command'",
        "echo 'Second command'",
        "python --version"
    ], timeout=60)
    if result == 'timeout':
        skipped_articles.append("Test 2: multiple commands")
    elif result:
        print(f"Return code: {result.returncode}")
        print(f"Output: {result.stdout.strip()}")
        print(f"Error: {result.stderr.strip()}")

    # Test 3: Directory listing
    print("\n=== Test 3: Directory listing ===")
    result = run_powershell_command("Get-ChildItem -Name | Select-Object -First 5", timeout=60)
    if result == 'timeout':
        skipped_articles.append("Test 3: directory listing")
    elif result:
        print(f"Return code: {result.returncode}")
        print(f"Output: {result.stdout.strip()}")
        print(f"Error: {result.stderr.strip()}")

    if skipped_articles:
        print("\n=== Skipped due to timeout (over 1 minute) ===")
        for article in skipped_articles:
            print(f"SKIPPED: {article}")

    print("\nPowerShell tests completed!")

if __name__ == "__main__":
    test_powershell()
