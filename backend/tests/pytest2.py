"""
Test cases for Regional Demand Heatmap API
Endpoint: GET /api/v1/region-demand-heatmap/

Test Case Format:
- API being tested
- Inputs
- Expected output
- Actual Output
- Result: Success/Fail
"""

import json
import pytest
from unittest.mock import MagicMock, patch
from flask import Flask
from pathlib import Path
import sys
from datetime import datetime, date

sys.path.insert(0, str(Path(__file__).parent.parent))
from routes.heatmap_routes import heatmap_bp


@pytest.fixture
def app():
    """Setup Flask app with heatmap blueprint for testing."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.register_blueprint(heatmap_bp, url_prefix='/api/v1/region-demand-heatmap')
    ctx = app.app_context()
    ctx.push()
    yield app
    ctx.pop()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


# ============================================================================
# TEST CASE 1: Successful heatmap generation with valid data
# ============================================================================
@patch('routes.heatmap_routes.db.session')
def test_heatmap_success_with_valid_data(mock_db_session, client):
    """
    API: GET /api/v1/region-demand-heatmap/
    Input: Valid sales data with multiple regions and dates
    Expected: 200 status with heatmap points containing trends and scores
    """
    # Mock database query results
    mock_data = [
        MagicMock(
            RegionName='North',
            Latitude=28.7041,
            Longitude=77.1025,
            UnitsSold=100,
            SaleDate=date(2024, 1, 15)
        ),
        MagicMock(
            RegionName='North',
            Latitude=28.7041,
            Longitude=77.1025,
            UnitsSold=150,
            SaleDate=date(2024, 2, 15)
        ),
        MagicMock(
            RegionName='South',
            Latitude=12.9716,
            Longitude=77.5946,
            UnitsSold=200,
            SaleDate=date(2024, 1, 15)
        ),
        MagicMock(
            RegionName='South',
            Latitude=12.9716,
            Longitude=77.5946,
            UnitsSold=180,
            SaleDate=date(2024, 2, 15)
        ),
    ]
    
    mock_db_session.query.return_value.join.return_value.all.return_value = mock_data
    
    # Make request
    response = client.get('/api/v1/region-demand-heatmap/')
    
    # Assertions
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'points' in data
    assert len(data['points']) > 0
    
    # Verify structure of returned points
    for point in data['points']:
        assert 'RegionName' in point
        assert 'Latitude' in point
        assert 'Longitude' in point
        assert 'UnitsSold' in point
        assert 'Month' in point
        assert 'DemandTrend' in point
        assert 'HeatmapScore' in point
        assert point['DemandTrend'] in ['Upward', 'Downward', 'Stable']
        assert 0 <= point['HeatmapScore'] <= 1
    
    print("✓ TEST CASE 1 PASSED: Successful heatmap with valid data")


# ============================================================================
# TEST CASE 2: No sales data available
# ============================================================================
@patch('routes.heatmap_routes.db.session')
def test_heatmap_no_data(mock_db_session, client):
    """
    API: GET /api/v1/region-demand-heatmap/
    Input: Empty database (no sales data)
    Expected: 404 status with error message
    """
    # Mock empty query result
    mock_db_session.query.return_value.join.return_value.all.return_value = []
    
    # Make request
    response = client.get('/api/v1/region-demand-heatmap/')
    
    # Assertions
    assert response.status_code == 404
    data = response.get_json()
    assert data['status'] == 'error'
    assert 'No demand/sales data found' in data['message']
    
    print("✓ TEST CASE 2 PASSED: Handles no data scenario")


# ============================================================================
# TEST CASE 3: Invalid date handling
# ============================================================================
@patch('routes.heatmap_routes.db.session')
def test_heatmap_invalid_dates(mock_db_session, client):
    """
    API: GET /api/v1/region-demand-heatmap/
    Input: Sales data with invalid/null dates
    Expected: 200 status with empty points array and message
    """
    # Mock data with invalid dates
    mock_data = [
        MagicMock(
            RegionName='East',
            Latitude=22.5726,
            Longitude=88.3639,
            UnitsSold=100,
            SaleDate=None  # Invalid date
        ),
        MagicMock(
            RegionName='West',
            Latitude=19.0760,
            Longitude=72.8777,
            UnitsSold=150,
            SaleDate='invalid-date'  # Invalid date string
        ),
    ]
    
    mock_db_session.query.return_value.join.return_value.all.return_value = mock_data
    
    # Make request
    response = client.get('/api/v1/region-demand-heatmap/')
    
    # Assertions
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['points'] == []
    assert 'Sales dates were invalid' in data['message']
    
    print("✓ TEST CASE 3 PASSED: Handles invalid dates gracefully")


# ============================================================================
# TEST CASE 4: Single region, single month (no trend calculation)
# ============================================================================
@patch('routes.heatmap_routes.db.session')
def test_heatmap_single_datapoint(mock_db_session, client):
    """
    API: GET /api/v1/region-demand-heatmap/
    Input: Only one sale record for one region
    Expected: 200 status with 'Stable' trend (no previous data to compare)
    """
    # Mock single data point
    mock_data = [
        MagicMock(
            RegionName='Central',
            Latitude=23.2599,
            Longitude=77.4126,
            UnitsSold=120,
            SaleDate=date(2024, 3, 15)
        ),
    ]
    
    mock_db_session.query.return_value.join.return_value.all.return_value = mock_data
    
    # Make request
    response = client.get('/api/v1/region-demand-heatmap/')
    
    # Assertions
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert len(data['points']) == 1
    assert data['points'][0]['DemandTrend'] == 'Stable'
    assert data['points'][0]['HeatmapScore'] == 0.0  # Single point: min=max
    
    print("✓ TEST CASE 4 PASSED: Single datapoint handled correctly")


# ============================================================================
# TEST CASE 5: Upward demand trend verification
# ============================================================================
@patch('routes.heatmap_routes.db.session')
def test_heatmap_upward_trend(mock_db_session, client):
    """
    API: GET /api/v1/region-demand-heatmap/
    Input: Sales data showing increasing units sold over time for same region
    Expected: DemandTrend = 'Upward' for later months
    """
    # Mock increasing sales data
    mock_data = [
        MagicMock(
            RegionName='Northeast',
            Latitude=26.1445,
            Longitude=91.7362,
            UnitsSold=50,
            SaleDate=date(2024, 1, 10)
        ),
        MagicMock(
            RegionName='Northeast',
            Latitude=26.1445,
            Longitude=91.7362,
            UnitsSold=80,
            SaleDate=date(2024, 2, 10)
        ),
        MagicMock(
            RegionName='Northeast',
            Latitude=26.1445,
            Longitude=91.7362,
            UnitsSold=120,
            SaleDate=date(2024, 3, 10)
        ),
    ]
    
    mock_db_session.query.return_value.join.return_value.all.return_value = mock_data
    
    # Make request
    response = client.get('/api/v1/region-demand-heatmap/')
    
    # Assertions
    assert response.status_code == 200
    data = response.get_json()
    points = data['points']
    
    # First month should be Stable (no previous data)
    # Subsequent months should show Upward trend
    upward_count = sum(1 for p in points if p['DemandTrend'] == 'Upward')
    assert upward_count >= 2  # At least Feb and Mar should show upward
    
    print("✓ TEST CASE 5 PASSED: Upward trend detected correctly")


# ============================================================================
# TEST CASE 6: Downward demand trend verification
# ============================================================================
@patch('routes.heatmap_routes.db.session')
def test_heatmap_downward_trend(mock_db_session, client):
    """
    API: GET /api/v1/region-demand-heatmap/
    Input: Sales data showing decreasing units sold over time
    Expected: DemandTrend = 'Downward' for later months
    """
    # Mock decreasing sales data
    mock_data = [
        MagicMock(
            RegionName='Northwest',
            Latitude=30.7333,
            Longitude=76.7794,
            UnitsSold=200,
            SaleDate=date(2024, 1, 5)
        ),
        MagicMock(
            RegionName='Northwest',
            Latitude=30.7333,
            Longitude=76.7794,
            UnitsSold=150,
            SaleDate=date(2024, 2, 5)
        ),
        MagicMock(
            RegionName='Northwest',
            Latitude=30.7333,
            Longitude=76.7794,
            UnitsSold=100,
            SaleDate=date(2024, 3, 5)
        ),
    ]
    
    mock_db_session.query.return_value.join.return_value.all.return_value = mock_data
    
    # Make request
    response = client.get('/api/v1/region-demand-heatmap/')
    
    # Assertions
    assert response.status_code == 200
    data = response.get_json()
    points = data['points']
    
    downward_count = sum(1 for p in points if p['DemandTrend'] == 'Downward')
    assert downward_count >= 2  # Feb and Mar should show downward
    
    print("✓ TEST CASE 6 PASSED: Downward trend detected correctly")


# ============================================================================
# TEST CASE 7: Multiple regions with different trends
# ============================================================================
@patch('routes.heatmap_routes.db.session')
def test_heatmap_multiple_regions(mock_db_session, client):
    """
    API: GET /api/v1/region-demand-heatmap/
    Input: Multiple regions with varying sales patterns
    Expected: Each region tracked independently with correct trends
    """
    # Mock multiple regions with different patterns
    mock_data = [
        # Region A: Upward trend
        MagicMock(RegionName='RegionA', Latitude=10.0, Longitude=20.0, 
                  UnitsSold=100, SaleDate=date(2024, 1, 1)),
        MagicMock(RegionName='RegionA', Latitude=10.0, Longitude=20.0, 
                  UnitsSold=150, SaleDate=date(2024, 2, 1)),
        
        # Region B: Downward trend
        MagicMock(RegionName='RegionB', Latitude=30.0, Longitude=40.0, 
                  UnitsSold=200, SaleDate=date(2024, 1, 1)),
        MagicMock(RegionName='RegionB', Latitude=30.0, Longitude=40.0, 
                  UnitsSold=150, SaleDate=date(2024, 2, 1)),
        
        # Region C: Stable
        MagicMock(RegionName='RegionC', Latitude=50.0, Longitude=60.0, 
                  UnitsSold=100, SaleDate=date(2024, 1, 1)),
        MagicMock(RegionName='RegionC', Latitude=50.0, Longitude=60.0, 
                  UnitsSold=100, SaleDate=date(2024, 2, 1)),
    ]
    
    mock_db_session.query.return_value.join.return_value.all.return_value = mock_data
    
    # Make request
    response = client.get('/api/v1/region-demand-heatmap/')
    
    # Assertions
    assert response.status_code == 200
    data = response.get_json()
    
    regions = set(p['RegionName'] for p in data['points'])
    assert len(regions) == 3
    assert 'RegionA' in regions
    assert 'RegionB' in regions
    assert 'RegionC' in regions
    
    print("✓ TEST CASE 7 PASSED: Multiple regions tracked independently")


# ============================================================================
# TEST CASE 8: Heatmap score normalization
# ============================================================================
@patch('routes.heatmap_routes.db.session')
def test_heatmap_score_normalization(mock_db_session, client):
    """
    API: GET /api/v1/region-demand-heatmap/
    Input: Sales data with wide range of units sold
    Expected: HeatmapScore normalized between 0 and 1
    """
    # Mock data with varying sales volumes
    mock_data = [
        MagicMock(RegionName='Low', Latitude=10.0, Longitude=20.0, 
                  UnitsSold=10, SaleDate=date(2024, 1, 1)),
        MagicMock(RegionName='Medium', Latitude=30.0, Longitude=40.0, 
                  UnitsSold=500, SaleDate=date(2024, 1, 1)),
        MagicMock(RegionName='High', Latitude=50.0, Longitude=60.0, 
                  UnitsSold=1000, SaleDate=date(2024, 1, 1)),
    ]
    
    mock_db_session.query.return_value.join.return_value.all.return_value = mock_data
    
    # Make request
    response = client.get('/api/v1/region-demand-heatmap/')
    
    # Assertions
    assert response.status_code == 200
    data = response.get_json()
    
    scores = [p['HeatmapScore'] for p in data['points']]
    assert min(scores) >= 0
    assert max(scores) <= 1
    assert min(scores) == 0.0  # Lowest sales should have score 0
    assert abs(max(scores) - 1.0) < 0.001  # Highest sales should have score ~1 (allow floating point tolerance)
    
    print("✓ TEST CASE 8 PASSED: Heatmap scores properly normalized")


# ============================================================================
# TEST CASE 9: Month formatting
# ============================================================================
@patch('routes.heatmap_routes.db.session')
def test_heatmap_month_formatting(mock_db_session, client):
    """
    API: GET /api/v1/region-demand-heatmap/
    Input: Various dates
    Expected: Month formatted as "Month Year" (e.g., "January 2024")
    """
    mock_data = [
        MagicMock(RegionName='Test', Latitude=10.0, Longitude=20.0, 
                  UnitsSold=100, SaleDate=date(2024, 1, 15)),
        MagicMock(RegionName='Test', Latitude=10.0, Longitude=20.0, 
                  UnitsSold=150, SaleDate=date(2024, 12, 25)),
    ]
    
    mock_db_session.query.return_value.join.return_value.all.return_value = mock_data
    
    # Make request
    response = client.get('/api/v1/region-demand-heatmap/')
    
    # Assertions
    assert response.status_code == 200
    data = response.get_json()
    
    months = [p['Month'] for p in data['points']]
    # Check format matches "Month Year" pattern
    for month in months:
        assert ' ' in month  # Should have space between month and year
        parts = month.split()
        assert len(parts) == 2
        assert parts[1].isdigit()  # Year should be numeric
    
    print("✓ TEST CASE 9 PASSED: Month formatted correctly")


# ============================================================================
# TEST CASE 10: Database exception handling
# ============================================================================
@patch('routes.heatmap_routes.db.session')
def test_heatmap_database_error(mock_db_session, client):
    """
    API: GET /api/v1/region-demand-heatmap/
    Input: Database query raises exception
    Expected: 500 status with error message
    """
    # Mock database exception
    mock_db_session.query.side_effect = Exception("Database connection failed")
    
    # Make request
    response = client.get('/api/v1/region-demand-heatmap/')
    
    # Assertions
    assert response.status_code == 500
    data = response.get_json()
    assert data['status'] == 'error'
    assert 'Heatmap processing failed' in data['message']
    assert 'error' in data
    
    print("✓ TEST CASE 10 PASSED: Database errors handled gracefully")


# ============================================================================
# TEST CASE 11: Content-Type verification
# ============================================================================
@patch('routes.heatmap_routes.db.session')
def test_heatmap_content_type(mock_db_session, client):
    """
    API: GET /api/v1/region-demand-heatmap/
    Input: Any valid request
    Expected: Response Content-Type is application/json
    """
    mock_data = [
        MagicMock(RegionName='Test', Latitude=10.0, Longitude=20.0, 
                  UnitsSold=100, SaleDate=date(2024, 1, 1)),
    ]
    
    mock_db_session.query.return_value.join.return_value.all.return_value = mock_data
    
    # Make request
    response = client.get('/api/v1/region-demand-heatmap/')
    
    # Assertions
    assert response.content_type.startswith('application/json')
    
    print("✓ TEST CASE 11 PASSED: Content-Type is JSON")


# ============================================================================
# TEST CASE 12: Aggregation by month (multiple sales in same month)
# ============================================================================
@patch('routes.heatmap_routes.db.session')
def test_heatmap_monthly_aggregation(mock_db_session, client):
    """
    API: GET /api/v1/region-demand-heatmap/
    Input: Multiple sales in same region during same month
    Expected: Units sold are aggregated/summed for that month
    """
    # Mock multiple sales in January 2024 for same region
    mock_data = [
        MagicMock(RegionName='West', Latitude=19.0, Longitude=72.0, 
                  UnitsSold=50, SaleDate=date(2024, 1, 5)),
        MagicMock(RegionName='West', Latitude=19.0, Longitude=72.0, 
                  UnitsSold=75, SaleDate=date(2024, 1, 15)),
        MagicMock(RegionName='West', Latitude=19.0, Longitude=72.0, 
                  UnitsSold=25, SaleDate=date(2024, 1, 25)),
    ]
    
    mock_db_session.query.return_value.join.return_value.all.return_value = mock_data
    
    # Make request
    response = client.get('/api/v1/region-demand-heatmap/')
    
    # Assertions
    assert response.status_code == 200
    data = response.get_json()
    
    # Should aggregate into single entry
    west_entries = [p for p in data['points'] if p['RegionName'] == 'West']
    assert len(west_entries) == 1
    assert west_entries[0]['UnitsSold'] == 150  # 50 + 75 + 25
    
    print("✓ TEST CASE 12 PASSED: Monthly aggregation works correctly")



# ============================================================================
# IMAGE COMPARISON ROUTE TESTS
# ============================================================================

from routes.image_routes import image_bp
import io
from PIL import Image

@pytest.fixture
def image_app():
    """Setup Flask app with image comparison blueprint."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['BASE_DIR'] = str(Path(__file__).parent.parent)
    app.register_blueprint(image_bp)
    ctx = app.app_context()
    ctx.push()
    yield app
    ctx.pop()

@pytest.fixture
def image_client(image_app):
    """Create test client for image routes."""
    return image_app.test_client()

def create_test_image(width=100, height=100, color=(255, 0, 0)):
    """Helper to create a test image in memory."""
    img = Image.new('RGB', (width, height), color=color)
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes

# ============================================================================
# TEST CASE 13: Successful Image Comparison
# ============================================================================
@patch('routes.image_routes.os.listdir')
@patch('builtins.open', create=True)
def test_compare_images_success(mock_open, mock_listdir, image_client):
    """
    API: POST /compare-images/
    Input: Valid PNG image file
    Expected: 200 status with best_match_file and similarity_score
    """
    # Mock store images directory
    mock_listdir.return_value = ['store1.png', 'store2.jpg']
    
    # Mock file reading for reference images
    test_img_bytes = create_test_image().read()
    mock_open.return_value.__enter__.return_value.read.return_value = test_img_bytes
    
    # Create test input image
    input_image = create_test_image(color=(200, 50, 50))
    
    response = image_client.post(
        '/compare-images/',
        data={'input_image': (input_image, 'test.png')},
        content_type='multipart/form-data'
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'best_match_file' in data
    assert 'similarity_score' in data
    assert isinstance(data['similarity_score'], float)
    # Similarity score can have floating point precision errors, so use tolerance
    assert -1.01 <= data['similarity_score'] <= 1.01
    
    print("✓ TEST CASE 13 PASSED: Successful image comparison")

# ============================================================================
# TEST CASE 14: Missing Input Image
# ============================================================================
def test_compare_images_missing_file(image_client):
    """
    API: POST /compare-images/
    Input: No input_image file provided
    Expected: 400 status with error message
    """
    response = image_client.post('/compare-images/', data={})
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['error'] == "Send 'input_image' file"
    
    print("✓ TEST CASE 14 PASSED: Missing input image handled")

# ============================================================================
# TEST CASE 15: No Reference Images Found
# ============================================================================
@patch('routes.image_routes.os.listdir')
def test_compare_images_no_reference_images(mock_listdir, image_client):
    """
    API: POST /compare-images/
    Input: Valid image but no reference images in store
    Expected: 404 status with "No images found"
    """
    mock_listdir.return_value = []
    
    input_image = create_test_image()
    response = image_client.post(
        '/compare-images/',
        data={'input_image': (input_image, 'test.png')},
        content_type='multipart/form-data'
    )
    
    assert response.status_code == 404
    data = response.get_json()
    assert data['error'] == "No images found"
    
    print("✓ TEST CASE 15 PASSED: No reference images handled")


# ============================================================================
# INQUIRY ROUTE TESTS
# ============================================================================

from routes.inquiry import inquiry_bp

@pytest.fixture
def inquiry_app():
    """Setup Flask app with inquiry blueprint."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.register_blueprint(inquiry_bp)
    ctx = app.app_context()
    ctx.push()
    yield app
    ctx.pop()

@pytest.fixture
def inquiry_client(inquiry_app):
    """Create test client for inquiry routes."""
    return inquiry_app.test_client()

# ============================================================================
# TEST CASE 16: Successful Inquiry Submission
# ============================================================================
@patch('routes.inquiry.db.session')
@patch('routes.inquiry.Shop')
@patch('routes.inquiry.analyze_fabric_inquiry')
@patch('routes.inquiry.save_inquiry_file')
def test_submit_inquiry_success(mock_save_file, mock_analyze, mock_shop, mock_db, inquiry_client):
    """
    API: POST /api/v1/inquiry/submit
    Input: Valid shop_id, user_id, message, and optional file
    Expected: 201 status with success message and AI analysis
    """
    # Mock shop existence
    mock_shop_instance = MagicMock()
    mock_shop_instance.name = "Test Fabric Shop"
    mock_shop.query.get.return_value = mock_shop_instance
    
    # Mock file save
    mock_save_file.return_value = "uploads/inquiries/test.png"
    
    # Mock AI analysis
    mock_analyze.return_value = {
        "analysis": "High-quality cotton fabric detected. Suitable for summer wear."
    }
    
    test_image = create_test_image()
    response = inquiry_client.post(
        '/api/v1/inquiry/submit',
        data={
            'shop_id': '1',
            'user_id': '10',
            'username': 'TestUser',
            'message': 'Interested in bulk cotton',
            'file': (test_image, 'fabric.png')
        },
        content_type='multipart/form-data'
    )
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'ai_analysis' in data['details']
    assert data['details']['shop'] == "Test Fabric Shop"
    
    print("✓ TEST CASE 16 PASSED: Successful inquiry submission")

# ============================================================================
# TEST CASE 17: Inquiry Submission Missing Required Fields
# ============================================================================
def test_submit_inquiry_missing_fields(inquiry_client):
    """
    API: POST /api/v1/inquiry/submit
    Input: Missing shop_id
    Expected: 400 status with error message
    """
    response = inquiry_client.post(
        '/api/v1/inquiry/submit',
        data={'user_id': '10', 'message': 'Test message'},
        content_type='multipart/form-data'
    )
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['status'] == 'error'
    assert 'shop_id is required' in data['message']
    
    print("✓ TEST CASE 17 PASSED: Missing required fields handled")

# ============================================================================
# TEST CASE 18: Inquiry Submission Invalid Shop ID
# ============================================================================
@patch('routes.inquiry.Shop')
def test_submit_inquiry_invalid_shop(mock_shop, inquiry_client):
    """
    API: POST /api/v1/inquiry/submit
    Input: Non-existent shop_id
    Expected: 404 status with error message
    """
    mock_shop.query.get.return_value = None
    
    response = inquiry_client.post(
        '/api/v1/inquiry/submit',
        data={
            'shop_id': '999',
            'user_id': '10',
            'message': 'Test'
        },
        content_type='multipart/form-data'
    )
    
    assert response.status_code == 404
    data = response.get_json()
    assert data['status'] == 'error'
    assert 'Invalid shop ID' in data['message']
    
    print("✓ TEST CASE 18 PASSED: Invalid shop ID handled")

# ============================================================================
# TEST CASE 19: Inquiry History Retrieval
# ============================================================================
@patch('routes.inquiry.Notification')
def test_inquiry_history_success(mock_notification, inquiry_client):
    """
    API: GET /api/v1/inquiry/history
    Input: Valid user_id
    Expected: 200 status with list of inquiry history
    """
    # Mock notification records
    mock_notif1 = MagicMock()
    mock_notif1.id = 1
    mock_notif1.message = "Inquiry to Shop A: Bulk order"
    mock_notif1.link = "uploads/inquiries/file1.png"
    mock_notif1.created_at.strftime.return_value = "2025-11-20 10:30"
    mock_notif1.is_read = False
    
    mock_notification.query.filter_by.return_value.order_by.return_value.all.return_value = [mock_notif1]
    
    response = inquiry_client.get('/api/v1/inquiry/history?user_id=10')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['count'] == 1
    assert len(data['history']) == 1
    assert data['history'][0]['message'] == "Inquiry to Shop A: Bulk order"
    
    print("✓ TEST CASE 19 PASSED: Inquiry history retrieved")

# ============================================================================
# TEST CASE 20: Inquiry History Missing User ID
# ============================================================================
def test_inquiry_history_missing_user_id(inquiry_client):
    """
    API: GET /api/v1/inquiry/history
    Input: No user_id parameter
    Expected: 400 status with error message
    """
    response = inquiry_client.get('/api/v1/inquiry/history')
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['status'] == 'error'
    assert 'user_id is required' in data['message']
    
    print("✓ TEST CASE 20 PASSED: Missing user_id handled")


# ============================================================================
# INVENTORY ROUTE TESTS
# ============================================================================

from routes.inventory import inventory_bp

@pytest.fixture
def inventory_app():
    """Setup Flask app with inventory blueprint."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.register_blueprint(inventory_bp, url_prefix='/api/v1/inventory')
    ctx = app.app_context()
    ctx.push()
    yield app
    ctx.pop()

@pytest.fixture
def inventory_client(inventory_app):
    """Create test client for inventory routes."""
    return inventory_app.test_client()

# ============================================================================
# TEST CASE 21: Fetch Inventory Success
# ============================================================================
@patch('routes.inventory.Product')
@patch('routes.inventory.Inventory')
def test_get_inventory_success(mock_inventory, mock_product, inventory_client):
    """
    API: GET /api/v1/inventory/
    Input: Valid shop_id
    Expected: 200 status with inventory list
    """
    # Mock products
    mock_prod = MagicMock()
    mock_prod.id = 1
    mock_prod.name = "Cotton Fabric"
    mock_prod.category = "Textiles"
    mock_prod.price = 500.0
    mock_prod.sku = "COT-001"
    mock_prod.rating = 4.5
    mock_prod.shop_id = 1
    
    mock_product.query.filter_by.return_value.order_by.return_value.all.return_value = [mock_prod]
    
    # Mock inventory
    mock_inv = MagicMock()
    mock_inv.qty_available = 100
    mock_inventory.query.filter_by.return_value.first.return_value = mock_inv
    
    response = inventory_client.get('/api/v1/inventory/?shop_id=1')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert len(data['data']) == 1
    assert data['data'][0]['name'] == "Cotton Fabric"
    assert data['data'][0]['stock'] == 100
    
    print("✓ TEST CASE 21 PASSED: Inventory fetched successfully")

# ============================================================================
# TEST CASE 22: Fetch Inventory Missing Shop ID
# ============================================================================
def test_get_inventory_missing_shop_id(inventory_client):
    """
    API: GET /api/v1/inventory/
    Input: No shop_id parameter
    Expected: 400 status with error message
    """
    response = inventory_client.get('/api/v1/inventory/')
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['status'] == 'error'
    assert 'shop_id is required' in data['message']
    
    print("✓ TEST CASE 22 PASSED: Missing shop_id handled")

# ============================================================================
# TEST CASE 23: Import Inventory via CSV
# ============================================================================
@patch('routes.inventory.db.session')
@patch('routes.inventory.Shop')
@patch('routes.inventory.Product')
def test_import_inventory_csv(mock_product, mock_shop, mock_db, inventory_client):
    """
    API: POST /api/v1/inventory/import
    Input: Valid CSV file with inventory data
    Expected: 201 status with import summary
    """
    # Mock shop
    mock_shop_instance = MagicMock()
    mock_shop_instance.owner_id = 5
    mock_shop.query.get.return_value = mock_shop_instance
    
    # Mock product queries
    mock_product.query.filter_by.return_value.first.return_value = None
    
    # Create CSV content
    csv_content = "name,category,price,stock,sku\nSilk Fabric,Premium,1200,50,SLK-001\n"
    csv_file = io.BytesIO(csv_content.encode('utf-8'))
    
    response = inventory_client.post(
        '/api/v1/inventory/import',
        data={
            'shop_id': '1',
            'file': (csv_file, 'inventory.csv')
        },
        content_type='multipart/form-data'
    )
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'added' in data
    
    print("✓ TEST CASE 23 PASSED: CSV inventory import successful")

# ============================================================================
# TEST CASE 24: Edit Inventory Item
# ============================================================================
@patch('routes.inventory.db.session')
@patch('routes.inventory.Product')
@patch('routes.inventory.Inventory')
def test_edit_inventory(mock_inventory, mock_product, mock_db, inventory_client):
    """
    API: POST /api/v1/inventory/edit
    Input: product_id, new price, new stock
    Expected: 200 status with success message
    """
    # Mock product
    mock_prod = MagicMock()
    mock_prod.price = 500
    mock_product.query.get.return_value = mock_prod
    
    # Mock inventory
    mock_inv = MagicMock()
    mock_inv.qty_available = 100
    mock_inventory.query.filter_by.return_value.first.return_value = mock_inv
    
    response = inventory_client.post(
        '/api/v1/inventory/edit',
        json={
            'product_id': 1,
            'price': 600,
            'stock': 150
        }
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'updated successfully' in data['message']
    
    print("✓ TEST CASE 24 PASSED: Inventory edited successfully")

# ============================================================================
# TEST CASE 25: Delete Inventory Item
# ============================================================================
@patch('routes.inventory.db.session')
@patch('routes.inventory.Product')
@patch('routes.inventory.Inventory')
def test_delete_inventory(mock_inventory, mock_product, mock_db, inventory_client):
    """
    API: DELETE /api/v1/inventory/delete
    Input: product_id to delete
    Expected: 200 status with success message
    """
    # Mock product
    mock_prod = MagicMock()
    mock_product.query.get.return_value = mock_prod
    
    # Mock inventory deletion
    mock_inventory.query.filter_by.return_value.delete.return_value = None
    
    response = inventory_client.delete('/api/v1/inventory/delete?product_id=1')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'Deleted product ID' in data['message']
    
    print("✓ TEST CASE 25 PASSED: Inventory deleted successfully")


# ============================================================================
# MARKETING ROUTE TESTS
# ============================================================================

from routes.marketing_routes import marketing_bp

@pytest.fixture
def marketing_app():
    """Setup Flask app with marketing blueprint."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.register_blueprint(marketing_bp, url_prefix='/api/v1/marketing')
    ctx = app.app_context()
    ctx.push()
    yield app
    ctx.pop()

@pytest.fixture
def marketing_client(marketing_app):
    """Create test client for marketing routes."""
    return marketing_app.test_client()

# ============================================================================
# TEST CASE 26: Marketing Content Generation - Image Upload
# ============================================================================
@patch('routes.marketing_routes.generate_ai_caption')
@patch('routes.marketing_routes.generate_marketing_poster')
def test_generate_marketing_image(mock_poster, mock_caption, marketing_client):
    """
    API: POST /api/v1/marketing/generate
    Input: Image file (PNG/JPG)
    Expected: 200 status with AI caption and poster
    """
    mock_caption.return_value = "Premium silk fabric - perfect for elegant occasions"
    mock_poster.return_value = ("AI-generated marketing poster", "uploads/marketing/poster.png")
    
    test_image = create_test_image()
    response = marketing_client.post(
        '/api/v1/marketing/generate',
        data={'file': (test_image, 'product.png')},
        content_type='multipart/form-data'
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['result']['type'] == 'image'
    assert 'caption' in data['result']
    
    print("✓ TEST CASE 26 PASSED: Marketing image content generated")

# ============================================================================
# TEST CASE 27: Marketing Content Generation - CSV Upload
# ============================================================================
@patch('routes.marketing_routes.generate_ai_caption')
@patch('routes.marketing_routes.forecast_trends')
def test_generate_marketing_csv(mock_forecast, mock_caption, marketing_client):
    """
    API: POST /api/v1/marketing/generate
    Input: CSV file with ProductName, Category, Price
    Expected: 200 status with AI captions for products
    """
    mock_caption.return_value = "Trending cotton fabric at competitive prices"
    mock_forecast.return_value = [{"month": "Jan", "forecast": 1500}]
    
    csv_content = "ProductName,Category,Price,Date,Sales\nCotton,Textile,500,2024-01-01,100\n"
    csv_file = io.BytesIO(csv_content.encode('utf-8'))
    
    response = marketing_client.post(
        '/api/v1/marketing/generate',
        data={'file': (csv_file, 'products.csv')},
        content_type='multipart/form-data'
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['result']['type'] == 'data'
    assert 'ai_captions' in data['result']
    
    print("✓ TEST CASE 27 PASSED: Marketing CSV content generated")

# ============================================================================
# TEST CASE 28: Marketing Invalid File Type
# ============================================================================
def test_generate_marketing_invalid_file(marketing_client):
    """
    API: POST /api/v1/marketing/generate
    Input: Invalid file type (.txt)
    Expected: 400 status with error message
    """
    txt_content = io.BytesIO(b"This is a text file")
    response = marketing_client.post(
        '/api/v1/marketing/generate',
        data={'file': (txt_content, 'invalid.txt')},
        content_type='multipart/form-data'
    )
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['status'] == 'error'
    assert 'Invalid or missing file' in data['message']
    
    print("✓ TEST CASE 28 PASSED: Invalid file type handled")

# ============================================================================
# TEST CASE 29: Marketing Missing File
# ============================================================================
def test_generate_marketing_missing_file(marketing_client):
    """
    API: POST /api/v1/marketing/generate
    Input: No file provided
    Expected: 400 status with error message
    """
    response = marketing_client.post('/api/v1/marketing/generate')
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['status'] == 'error'
    
    print("✓ TEST CASE 29 PASSED: Missing file handled")

# ============================================================================
# TEST CASE 30: Get Allowed Extensions
# ============================================================================
def test_get_allowed_extensions(marketing_client):
    """
    API: GET /api/v1/marketing/allowed-extensions
    Input: None
    Expected: 200 status with list of allowed file extensions
    """
    response = marketing_client.get('/api/v1/marketing/allowed-extensions')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'allowed_extensions' in data
    assert isinstance(data['allowed_extensions'], list)
    assert 'csv' in data['allowed_extensions']
    assert 'png' in data['allowed_extensions']
    
    print("✓ TEST CASE 30 PASSED: Allowed extensions retrieved")


# ============================================================================
# STORES ROUTE TESTS
# ============================================================================

from routes.stores_routes import stores_bp

@pytest.fixture
def stores_app():
    """Setup Flask app with stores blueprint."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.register_blueprint(stores_bp)
    ctx = app.app_context()
    ctx.push()
    yield app
    ctx.pop()

@pytest.fixture
def stores_client(stores_app):
    """Create test client for stores routes."""
    return stores_app.test_client()

# ============================================================================
# TEST CASE 31: Successful Stores Retrieval
# ============================================================================
@patch('routes.stores_routes.StoreRegion')
def test_get_stores_success(mock_store_region, stores_client):
    """
    API: GET /api/v1/stores/
    Input: None (GET request)
    Expected: 200 status with list of stores
    """
    # Mock store data
    mock_store1 = MagicMock()
    mock_store1.RegionID = 1
    mock_store1.StoreName = "Fabric Paradise"
    mock_store1.Latitude = 28.7041
    mock_store1.Longitude = 77.1025
    mock_store1.RegionName = "North"
    mock_store1.ImagePath = "/images/store1.jpg"
    
    mock_store2 = MagicMock()
    mock_store2.RegionID = 2
    mock_store2.StoreName = "Textile Hub"
    mock_store2.Latitude = 19.0760
    mock_store2.Longitude = 72.8777
    mock_store2.RegionName = "West"
    mock_store2.ImagePath = "/images/store2.jpg"
    
    mock_store_region.query.order_by.return_value.all.return_value = [mock_store1, mock_store2]
    
    response = stores_client.get('/stores/')
    
    assert response.status_code == 200
    assert response.content_type == 'application/json'
    data = response.get_json()
    assert len(data) == 2
    assert data[0]['name'] == "Fabric Paradise"
    assert data[0]['Region'] == "North"
    assert data[1]['name'] == "Textile Hub"
    
    print("✓ TEST CASE 31 PASSED: Stores retrieved successfully")

# ============================================================================
# TEST CASE 32: Empty Stores Database
# ============================================================================
@patch('routes.stores_routes.StoreRegion')
def test_get_stores_empty(mock_store_region, stores_client):
    """
    API: GET /api/v1/stores/
    Input: Empty database
    Expected: 200 status with empty array
    """
    mock_store_region.query.order_by.return_value.all.return_value = []
    
    response = stores_client.get('/stores/')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data == []
    
    print("✓ TEST CASE 32 PASSED: Empty stores handled")

# ============================================================================
# TEST CASE 33: Stores Data Structure Validation
# ============================================================================
@patch('routes.stores_routes.StoreRegion')
def test_get_stores_structure(mock_store_region, stores_client):
    """
    API: GET /api/v1/stores/
    Input: Single store
    Expected: Correct JSON structure with all fields
    """
    mock_store = MagicMock()
    mock_store.RegionID = 1
    mock_store.StoreName = "Test Store"
    mock_store.Latitude = 12.9716
    mock_store.Longitude = 77.5946
    mock_store.RegionName = "South"
    mock_store.ImagePath = "/test.jpg"
    
    mock_store_region.query.order_by.return_value.all.return_value = [mock_store]
    
    response = stores_client.get('/stores/')
    data = response.get_json()
    
    assert 'id' in data[0]
    assert 'name' in data[0]
    assert 'Latitude' in data[0]
    assert 'Longitude' in data[0]
    assert 'Region' in data[0]
    assert 'ImagePath' in data[0]
    
    print("✓ TEST CASE 33 PASSED: Store structure validated")


# ============================================================================
# TRENDING SHOPS ROUTE TESTS
# ============================================================================

from routes.trending_routes import trending_shops_bp

@pytest.fixture
def trending_app():
    """Setup Flask app with trending shops blueprint."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.register_blueprint(trending_shops_bp, url_prefix='/api/v1/trending-shops')
    ctx = app.app_context()
    ctx.push()
    yield app
    ctx.pop()

@pytest.fixture
def trending_client(trending_app):
    """Create test client for trending routes."""
    return trending_app.test_client()

# ============================================================================
# TEST CASE 34: Successful Trending Shops Retrieval
# ============================================================================
@patch('routes.trending_routes.db.session')
@patch('routes.trending_routes.model')
def test_trending_shops_success(mock_model, mock_db, trending_client):
    """
    API: GET /api/v1/trending-shops/
    Input: Valid sales data with stores
    Expected: 200 status with trend data and AI analysis
    """
    # Mock sales data
    mock_sale = MagicMock()
    mock_sale.Store = "Fabric Paradise"
    mock_sale.Region = "North"
    mock_sale.SaleDate = date(2024, 1, 15)
    mock_sale.UnitsSold = 100
    mock_sale.Sales = 5000
    mock_sale.StoreName = "Fabric Paradise"
    mock_sale.City = "Delhi"
    mock_sale.RegionName = "North"
    
    mock_db.query.return_value.join.return_value.all.return_value = [mock_sale]
    
    # Mock AI response
    mock_model.generate_content.return_value.text = '{"trending": "Fabric Paradise shows strong growth"}'
    
    response = trending_client.get('/api/v1/trending-shops/')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'trend_data' in data
    assert isinstance(data['trend_data'], list)
    
    print("✓ TEST CASE 34 PASSED: Trending shops retrieved")

# ============================================================================
# TEST CASE 35: Trending Shops No Data
# ============================================================================
@patch('routes.trending_routes.db.session')
def test_trending_shops_no_data(mock_db, trending_client):
    """
    API: GET /api/v1/trending-shops/
    Input: No sales data
    Expected: 200 status with empty trend_data
    """
    mock_db.query.return_value.join.return_value.all.return_value = []
    
    response = trending_client.get('/api/v1/trending-shops/')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['trend_data'] == []
    assert 'No sales data available' in data['message']
    
    print("✓ TEST CASE 35 PASSED: No trending data handled")

# ============================================================================
# TEST CASE 36: Trending Shops Invalid Dates
# ============================================================================
@patch('routes.trending_routes.db.session')
def test_trending_shops_invalid_dates(mock_db, trending_client):
    """
    API: GET /api/v1/trending-shops/
    Input: Sales data with invalid dates
    Expected: 200 status with empty array and error message
    """
    mock_sale = MagicMock()
    mock_sale.Store = "Test Store"
    mock_sale.Region = "East"
    mock_sale.SaleDate = None
    mock_sale.UnitsSold = 50
    mock_sale.Sales = 2500
    mock_sale.City = "Kolkata"
    mock_sale.RegionName = "East"
    
    mock_db.query.return_value.join.return_value.all.return_value = [mock_sale]
    
    response = trending_client.get('/api/v1/trending-shops/')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['trend_data'] == []
    assert 'invalid' in data['message'].lower()
    
    print("✓ TEST CASE 36 PASSED: Invalid dates handled")


# ============================================================================
# TOP SELLING PRODUCTS ROUTE TESTS
# ============================================================================

from routes.top_selling_routes import top_selling_bp

@pytest.fixture
def top_selling_app():
    """Setup Flask app with top selling blueprint."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.register_blueprint(top_selling_bp, url_prefix='/api/v1/top-selling-products')
    ctx = app.app_context()
    ctx.push()
    yield app
    ctx.pop()

@pytest.fixture
def top_selling_client(top_selling_app):
    """Create test client for top selling routes."""
    return top_selling_app.test_client()

# ============================================================================
# TEST CASE 37: Successful Top Selling Products
# ============================================================================
@patch('routes.top_selling_routes.db.session')
@patch('routes.top_selling_routes.ExternalProduct')
@patch('routes.top_selling_routes.model')
def test_top_selling_success(mock_model, mock_product, mock_db, top_selling_client):
    """
    API: GET /api/v1/top-selling-products/
    Input: Valid product and sales data
    Expected: 200 status with summary table and AI analysis
    """
    # Mock products
    mock_prod = MagicMock()
    mock_prod.ProductID = 1
    mock_product.query.order_by.return_value.limit.return_value.all.return_value = [mock_prod]
    
    # Mock sales data
    mock_sale = MagicMock()
    mock_sale.ProductID = 1
    mock_sale.Region = "North"
    mock_sale.SaleDate = date(2024, 1, 15)
    mock_sale.UnitsSold = 100
    mock_sale.Sales = 5000
    mock_sale.ProductName = "Cotton Fabric"
    
    mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [mock_sale]
    
    # Mock AI
    mock_model.generate_content.return_value.text = "Cotton fabric shows strong performance"
    
    response = top_selling_client.get('/api/v1/top-selling-products/')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'summary_table' in data
    assert 'ai_analysis' in data
    
    print("✓ TEST CASE 37 PASSED: Top selling products retrieved")

# ============================================================================
# TEST CASE 38: No Products Found
# ============================================================================
@patch('routes.top_selling_routes.ExternalProduct')
def test_top_selling_no_products(mock_product, top_selling_client):
    """
    API: GET /api/v1/top-selling-products/
    Input: No products in catalog
    Expected: 404 status with error message
    """
    mock_product.query.order_by.return_value.limit.return_value.all.return_value = []
    
    response = top_selling_client.get('/api/v1/top-selling-products/')
    
    assert response.status_code == 404
    data = response.get_json()
    assert data['status'] == 'error'
    assert 'No products found' in data['message']
    
    print("✓ TEST CASE 38 PASSED: No products handled")

# ============================================================================
# TEST CASE 39: Top Selling Empty Sales Data
# ============================================================================
@patch('routes.top_selling_routes.db.session')
@patch('routes.top_selling_routes.ExternalProduct')
def test_top_selling_no_sales(mock_product, mock_db, top_selling_client):
    """
    API: GET /api/v1/top-selling-products/
    Input: Products exist but no sales data
    Expected: 200 status with empty summary
    """
    mock_prod = MagicMock()
    mock_prod.ProductID = 1
    mock_product.query.order_by.return_value.limit.return_value.all.return_value = [mock_prod]
    
    mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = []
    
    response = top_selling_client.get('/api/v1/top-selling-products/')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['summary_table'] == []
    assert 'No sales data available' in data['ai_analysis']
    
    print("✓ TEST CASE 39 PASSED: No sales data handled")


# ============================================================================
# SHOP ROUTES TESTS
# ============================================================================

from routes.shop_routes import shop_bp

@pytest.fixture
def shop_app():
    """Setup Flask app with shop blueprint."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.register_blueprint(shop_bp, url_prefix='/api/v1/shop')
    ctx = app.app_context()
    ctx.push()
    yield app
    ctx.pop()

@pytest.fixture
def shop_client(shop_app):
    """Create test client for shop routes."""
    return shop_app.test_client()

# ============================================================================
# TEST CASE 40: Shop Dashboard No Data
# ============================================================================
def test_shop_dashboard_no_data(shop_client):
    """
    API: GET /api/v1/shop/dashboard
    Input: shop_id with no sales file
    Expected: 200 status with default dashboard data
    """
    response = shop_client.get('/api/v1/shop/dashboard?shop_id=999')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['data']['weekly_sales'] == '₹0'
    assert data['data']['total_orders'] == 0
    
    print("✓ TEST CASE 40 PASSED: Dashboard no data handled")

# ============================================================================
# TEST CASE 41: Shop Dashboard Missing Shop ID
# ============================================================================
def test_shop_dashboard_missing_shop_id(shop_client):
    """
    API: GET /api/v1/shop/dashboard
    Input: No shop_id parameter
    Expected: 400 status with error message
    """
    response = shop_client.get('/api/v1/shop/dashboard')
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['status'] == 'error'
    assert 'shop_id is required' in data['message']
    
    print("✓ TEST CASE 41 PASSED: Missing shop_id handled")

# ============================================================================
# TEST CASE 42: Upload Sales Data Success
# ============================================================================
@patch('routes.shop_routes.os.path.join')
def test_upload_sales_success(mock_path, shop_client):
    """
    API: POST /api/v1/shop/upload_sales_data
    Input: Valid shop_id and CSV file
    Expected: 200 status with success message
    """
    mock_path.return_value = "test_sales.csv"
    
    csv_content = "date,product_name,revenue,quantity_sold\n2024-01-01,Cotton,1000,10\n"
    csv_file = io.BytesIO(csv_content.encode('utf-8'))
    
    response = shop_client.post(
        '/api/v1/shop/upload_sales_data',
        data={
            'shop_id': '1',
            'file': (csv_file, 'sales.csv')
        },
        content_type='multipart/form-data'
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'uploaded successfully' in data['message']
    
    print("✓ TEST CASE 42 PASSED: Sales upload successful")

# ============================================================================
# TEST CASE 43: Upload Sales Missing File
# ============================================================================
def test_upload_sales_missing_file(shop_client):
    """
    API: POST /api/v1/shop/upload_sales_data
    Input: shop_id but no file
    Expected: 400 status with error message
    """
    response = shop_client.post(
        '/api/v1/shop/upload_sales_data',
        data={'shop_id': '1'},
        content_type='multipart/form-data'
    )
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['status'] == 'error'
    assert 'Missing' in data['message']
    
    print("✓ TEST CASE 43 PASSED: Missing file handled")

# ============================================================================
# TEST CASE 44: Export Sales Missing Shop ID
# ============================================================================
def test_export_sales_missing_shop_id(shop_client):
    """
    API: GET /api/v1/shop/sales/export
    Input: No shop_id parameter
    Expected: 400 status with error message
    """
    response = shop_client.get('/api/v1/shop/sales/export')
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['status'] == 'error'
    assert 'shop_id is required' in data['message']
    
    print("✓ TEST CASE 44 PASSED: Export missing shop_id handled")

# ============================================================================
# TEST CASE 45: Export Sales No Data Found
# ============================================================================
def test_export_sales_no_data(shop_client):
    """
    API: GET /api/v1/shop/sales/export
    Input: shop_id with no sales file
    Expected: 404 status with error message
    """
    response = shop_client.get('/api/v1/shop/sales/export?shop_id=999')
    
    assert response.status_code == 404
    data = response.get_json()
    assert data['status'] == 'error'
    assert 'No sales data found' in data['message']
    
    print("✓ TEST CASE 45 PASSED: Export no data handled")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
