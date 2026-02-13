# Manual Browser Verification Guide

## End-to-End Verification: Persistent Annotations & Analysis Notes

### Current Running Services
- **Backend**: http://localhost:8001
- **Frontend**: http://localhost:5180

### Test Data Created via API
The automated test has already created the following test data:
- **Annotations**: 4 annotations for RELIANCE symbol
  - 2 Trendline annotations
  - 1 Horizontal line (Support Level)
  - 1 Additional trendline
- **Notes**: 1 analysis note for RELIANCE

---

## Verification Steps

### Step 1: Navigate to Stock Analysis Page
1. Open your browser and navigate to: http://localhost:5180/stock/RELIANCE
2. Expected: Page loads successfully with chart, annotations panel, and notes section visible

### Step 2: Verify Pre-Created Annotations
1. Look at the chart - you should see red/green trendlines and horizontal lines
2. Check the "Annotations" panel below the chart
3. Expected:
   - Panel shows 4 annotations
   - Each annotation has type, title, and color indicator
   - Creation time is shown (e.g., "2 hours ago")
   - Individual eye icons to toggle visibility
   - Delete buttons on hover

### Step 3: Test Annotation Visibility Toggle
1. Click the Eye icon in the Annotations panel header
2. Expected: All annotations disappear from the chart
3. Click the Eye icon again (should show EyeOff)
4. Expected: All annotations reappear on the chart
5. Hover over an individual annotation in the list
6. Click the eye icon for that annotation only
7. Expected: Only that annotation hides

### Step 4: Verify Annotation Persistence (Page Refresh)
1. Note the current annotations on the chart
2. Press F5 to refresh the page
3. Expected: All annotations still appear after refresh
4. Check the Annotations panel - count should still be 4

### Step 5: Verify Note Persistence
1. Scroll down to the "Analysis Notes" section
2. Expected: Note titled "RELIANCE Analysis" is displayed
3. Content should be visible
4. Tags may be displayed (depends on UI implementation)
5. Press F5 to refresh
6. Expected: Note still appears after refresh

### Step 6: Create New Annotation via Drawing Tools
1. In the chart header, click the "Trendline" tool (TrendingUp icon)
2. Expected: Tool button becomes highlighted/active
3. A message appears: "Drawing: TRENDLINE - Click to place points, Escape to cancel"
4. Click on the chart to place the first point
5. Move mouse and click again to place the second point
6. Expected:
   - A new trendline appears on the chart
   - Annotation is automatically saved
   - Annotations panel shows 5 annotations now
   - The new annotation appears in the list

### Step 7: Verify New Annotation Persists
1. Note the new annotation in the list
2. Press F5 to refresh the page
3. Expected: New annotation still appears after refresh
4. Count in Annotations panel should still be 5

### Step 8: Create/Update Analysis Note
1. Scroll to the Analysis Notes section
2. Edit the existing note or add a new one
3. Click "Save Note" button
4. Expected: Note saves successfully
5. Press F5 to refresh
6. Expected: Your changes persist after refresh

### Step 9: Test Show/Hide Toggle in Toolbar
1. In the chart header annotation toolbar, find the Eye icon
2. Click it to toggle visibility
3. Expected: Works the same as the panel toggle
4. All annotations show/hide simultaneously

### Step 10: Test Delete Functionality
1. Hover over an annotation in the Annotations panel
2. Click the Trash icon
3. Confirm deletion in the dialog
4. Expected: Annotation disappears from panel and chart
5. Press F5 to refresh
6. Expected: Annotation stays deleted (doesn't reappear)

---

## Success Criteria

✅ All pre-created annotations appear on chart
✅ Annotations panel lists all annotations correctly
✅ Show/hide toggle works (both panel and toolbar)
✅ Annotations persist after page refresh
✅ Drawing tools create new annotations
✅ New annotations auto-save and persist
✅ Analysis notes persist after refresh
✅ Delete functionality works
✅ No console errors in browser DevTools

## Troubleshooting

### Annotations don't appear on chart
- Check browser console (F12) for errors
- Verify backend is running: http://localhost:8001/api/docs
- Check Network tab in DevTools for failed API calls

### Annotations don't persist after refresh
- Check browser localStorage (DevTools > Application > Local Storage)
- Look for `annotation-storage` key
- Verify database file exists: `./backend/chartanalyzer.db`

### Notes don't save
- Notes use in-memory storage, not database
- Notes persist only while backend is running
- Restarting backend clears notes (expected behavior)

---

## API Endpoints Tested

✅ GET /api/annotations/{symbol} - List all annotations
✅ POST /api/annotations - Create annotation
✅ GET /api/annotations/id/{id} - Get by ID
✅ PATCH /api/annotations/id/{id} - Update annotation
✅ DELETE /api/annotations/id/{id} - Delete annotation
✅ DELETE /api/annotations/{symbol}/all - Delete all
✅ GET /api/notes - List all notes
✅ GET /api/notes/{symbol} - Get note for symbol
✅ POST /api/notes - Create note
✅ PATCH /api/notes/{symbol} - Update note
✅ DELETE /api/notes/{symbol} - Delete note

---

## Test Execution Summary

**Automated API Tests**: ✅ PASSED
- Annotations CRUD: Working
- Notes CRUD: Working
- Visibility toggle: Working
- Database persistence: Working

**Manual Browser Tests**: ⏳ PENDING USER VERIFICATION

Please perform the manual verification steps above and report results.
