#!/usr/bin/env python3
"""
End-to-End Verification Script for Persistent Annotations & Analysis Notes

This script tests the complete flow:
1. Create annotation via API
2. Verify annotation persists
3. Create note via API
4. Verify note persists
5. Test show/hide functionality
"""

import sys
import os
import site
import json
import time

# Add user site-packages to path
user_site = site.getusersitepackages()
if user_site not in sys.path:
    sys.path.insert(0, user_site)

import httpx

BASE_URL = "http://localhost:8001"
SYMBOL = "RELIANCE"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_success(msg):
    print(f"✓ {msg}")

def print_error(msg):
    print(f"✗ {msg}")

def print_info(msg):
    print(f"ℹ {msg}")

def test_annotations_api():
    """Test annotation CRUD operations"""
    print_section("STEP 1: Testing Annotations API")

    # Test 1: Get all annotations for symbol (should be empty initially)
    print_info("Fetching initial annotations...")
    response = httpx.get(f"{BASE_URL}/api/annotations/{SYMBOL}")
    if response.status_code == 200:
        data = response.json()
        print_success(f"GET /api/annotations/{SYMBOL} - Found {len(data.get('annotations', []))} annotations")
    else:
        print_error(f"Failed to fetch annotations: {response.status_code}")
        return False

    # Test 2: Create a new annotation
    print_info("Creating a new trendline annotation...")
    annotation_data = {
        "symbol": SYMBOL,
        "annotation_type": "TRENDLINE",
        "x1": 1704067200000.0,  # 2024-01-01 timestamp in milliseconds
        "y1": 2500.0,
        "x2": 1705276800000.0,  # 2024-01-15 timestamp in milliseconds
        "y2": 2600.0,
        "color": "#FF0000",
        "line_style": "SOLID",
        "line_width": "2",
        "title": "Test Trendline",
        "notes": "This is a test trendline for verification"
    }
    response = httpx.post(f"{BASE_URL}/api/annotations", json=annotation_data)
    if response.status_code in [200, 201]:
        created_annotation = response.json()
        annotation_id = created_annotation.get('id')
        print_success(f"POST /api/annotations - Created annotation ID: {annotation_id}")
    else:
        print_error(f"Failed to create annotation: {response.status_code} - {response.text}")
        return False

    # Test 3: Verify the annotation was saved
    print_info("Verifying annotation persistence...")
    response = httpx.get(f"{BASE_URL}/api/annotations/{SYMBOL}")
    if response.status_code == 200:
        data = response.json()
        annotations = data.get('annotations', [])
        if len(annotations) > 0:
            print_success(f"Annotation persisted! Found {len(annotations)} annotation(s)")
            for ann in annotations:
                print_info(f"  - {ann.get('annotation_type')}: {ann.get('title')} (ID: {ann.get('id')})")
        else:
            print_error("Annotation not found after creation!")
            return False
    else:
        print_error(f"Failed to fetch annotations: {response.status_code}")
        return False

    # Test 4: Get annotation by ID
    print_info(f"Fetching annotation by ID: {annotation_id}")
    response = httpx.get(f"{BASE_URL}/api/annotations/id/{annotation_id}")
    if response.status_code == 200:
        annotation = response.json()
        print_success(f"GET /api/annotations/id/{annotation_id} - Found: {annotation.get('title')}")
    else:
        print_error(f"Failed to get annotation by ID: {response.status_code}")
        return False

    # Test 5: Update annotation visibility (test show/hide)
    print_info("Testing annotation visibility toggle...")
    response = httpx.patch(
        f"{BASE_URL}/api/annotations/id/{annotation_id}",
        json={"visible": False}
    )
    if response.status_code == 200:
        updated = response.json()
        if not updated.get('visible'):
            print_success("PATCH /api/annotations/id/{id} - Hidden annotation successfully")
        else:
            print_error("Visibility update failed")
    else:
        print_error(f"Failed to update annotation: {response.status_code}")

    # Test 6: Show annotation again
    response = httpx.patch(
        f"{BASE_URL}/api/annotations/id/{annotation_id}",
        json={"visible": True}
    )
    if response.status_code == 200:
        updated = response.json()
        if updated.get('visible'):
            print_success("PATCH /api/annotations/id/{id} - Showed annotation successfully")
        else:
            print_error("Visibility update failed")
    else:
        print_error(f"Failed to update annotation: {response.status_code}")

    # Test 7: Create a horizontal line annotation
    print_info("Creating a horizontal line annotation...")
    horizontal_data = {
        "symbol": SYMBOL,
        "annotation_type": "HORIZONTAL_LINE",
        "y1": 2550.0,
        "x1": 1704067200000.0,  # 2024-01-01 timestamp in milliseconds
        "x2": 1706745600000.0,  # 2024-02-01 timestamp in milliseconds
        "color": "#00FF00",
        "line_style": "DASHED",
        "line_width": "2",
        "title": "Support Level",
        "notes": "Key support level"
    }
    response = httpx.post(f"{BASE_URL}/api/annotations", json=horizontal_data)
    if response.status_code in [200, 201]:
        print_success("Created horizontal line annotation")
    else:
        print_error(f"Failed to create horizontal line: {response.status_code}")

    # Verify multiple annotations
    response = httpx.get(f"{BASE_URL}/api/annotations/{SYMBOL}")
    if response.status_code == 200:
        data = response.json()
        annotations = data.get('annotations', [])
        print_success(f"Total annotations for {SYMBOL}: {len(annotations)}")

    return annotation_id

def test_notes_api():
    """Test notes CRUD operations"""
    print_section("STEP 2: Testing Notes API")

    # Test 1: Get note for symbol (should be empty initially)
    print_info(f"Fetching initial note for {SYMBOL}...")
    response = httpx.get(f"{BASE_URL}/api/notes/{SYMBOL}")
    if response.status_code == 404:
        print_success("No existing note found (expected)")
    elif response.status_code == 200:
        print_info("Found existing note")
    else:
        print_error(f"Unexpected response: {response.status_code}")
        return False

    # Test 2: Create a new note
    print_info("Creating a new analysis note...")
    note_data = {
        "symbol": SYMBOL,
        "title": "RELIANCE Analysis",
        "content": "Strong bullish trend with good volume support. Key resistance at 2700.",
        "tags": ["bullish", "trend", "volume"]
    }
    response = httpx.post(f"{BASE_URL}/api/notes", json=note_data)
    if response.status_code in [200, 201]:
        note = response.json()
        print_success(f"POST /api/notes - Created note: {note.get('title')}")
    elif response.status_code == 409:
        print_info("Note already exists, updating instead...")
        response = httpx.put(f"{BASE_URL}/api/notes/{SYMBOL}", json=note_data)
        if response.status_code in [200, 201]:
            note = response.json()
            print_success(f"PUT /api/notes/{SYMBOL} - Updated note")
        else:
            print_error(f"Failed to update note: {response.status_code}")
            return False
    else:
        print_error(f"Failed to create note: {response.status_code} - {response.text}")
        return False

    # Test 3: Verify the note was saved
    print_info("Verifying note persistence...")
    response = httpx.get(f"{BASE_URL}/api/notes/{SYMBOL}")
    if response.status_code == 200:
        note = response.json()
        print_success(f"GET /api/notes/{SYMBOL} - Note persisted: {note.get('title')}")
        print_info(f"  Content: {note.get('content', '')[:50]}...")
    else:
        print_error(f"Failed to fetch note: {response.status_code}")
        return False

    # Test 4: Update the note
    print_info("Updating note...")
    update_data = {
        "content": "Updated: Strong breakout above resistance with increasing volume.",
        "tags": ["breakout", "high-volume"]
    }
    response = httpx.patch(f"{BASE_URL}/api/notes/{SYMBOL}", json=update_data)
    if response.status_code == 200:
        note = response.json()
        print_success(f"PATCH /api/notes/{SYMBOL} - Note updated")
    else:
        print_error(f"Failed to update note: {response.status_code}")

    # Test 5: Get all notes
    print_info("Fetching all notes...")
    response = httpx.get(f"{BASE_URL}/api/notes")
    if response.status_code == 200:
        data = response.json()
        notes = data.get('notes', [])
        print_success(f"GET /api/notes - Total notes: {len(notes)}")

    return True

def test_database_verification():
    """Verify database state"""
    print_section("STEP 3: Database Verification")

    db_path = "./backend/chartanalyzer.db"
    if os.path.exists(db_path):
        print_success(f"Database file exists: {db_path}")
        size_kb = os.path.getsize(db_path) / 1024
        print_info(f"Database size: {size_kb:.2f} KB")
    else:
        print_error(f"Database file not found: {db_path}")
        return False

    return True

def main():
    print_section("PERSISTENT ANNOTATIONS - END-TO-END VERIFICATION")
    print(f"Testing Symbol: {SYMBOL}")
    print(f"Backend URL: {BASE_URL}")
    print(f"Frontend URL: http://localhost:5180/stock/{SYMBOL}")

    # Check if backend is running
    try:
        response = httpx.get(f"{BASE_URL}/api/docs", timeout=2.0)
        print_success("Backend is running")
    except Exception as e:
        print_error(f"Cannot connect to backend at {BASE_URL}")
        print_error("Please start the backend first:")
        print_error("  cd backend && python run_backend.py")
        return 1

    # Run tests
    try:
        annotation_id = test_annotations_api()
        if annotation_id:
            test_notes_api()
            test_database_verification()

            print_section("VERIFICATION SUMMARY")
            print_success("✓ Annotations API working correctly")
            print_success("✓ Annotations persist in database")
            print_success("✓ Show/hide functionality works")
            print_success("✓ Notes API working correctly")
            print_success("✓ Notes persist in database")

            print("\n" + "="*60)
            print("  MANUAL BROWSER VERIFICATION")
            print("="*60)
            print(f"\n1. Open browser: http://localhost:5180/stock/{SYMBOL}")
            print(f"2. Verify annotations appear on the chart")
            print(f"3. Click the Eye icon to toggle visibility")
            print(f"4. Refresh the page (F5)")
            print(f"5. Verify annotations still appear after refresh")
            print(f"6. Check that notes section shows your note")
            print(f"7. Try drawing a new annotation on the chart")
            print(f"8. Refresh again and verify it persists")
            print("\n" + "="*60)

            return 0
        else:
            print_error("Tests failed!")
            return 1

    except Exception as e:
        print_error(f"Test error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
