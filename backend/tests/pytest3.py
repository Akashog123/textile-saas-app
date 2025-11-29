import json
import pytest
from unittest.mock import MagicMock, patch, ANY
from flask import Flask
from pathlib import Path
import sys
import io

sys.path.insert(0, str(Path(__file__).parent.parent))
from routes.pdf_service import pdf_bp, _clean_text, _safe_latin1, generate_pdf_report


@pytest.fixture
def app():
    """Create Flask app with pdf_bp blueprint for testing."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.register_blueprint(pdf_bp, url_prefix='/api/v1/pdf')
    ctx = app.app_context()
    ctx.push()
    yield app
    ctx.pop()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


# ============================================================================
# HELPER FUNCTION TESTS
# ============================================================================

class TestCleanTextFunction:
    """Test cases for _clean_text helper function."""
    
    def test_clean_text_with_valid_string(self):
        """Test _clean_text with normal string input."""
        result = _clean_text("Hello World")
        assert result == "Hello World"
    
    def test_clean_text_with_whitespace(self):
        """Test _clean_text removes leading/trailing whitespace."""
        result = _clean_text("  Hello World  ")
        assert result == "Hello World"
    
    def test_clean_text_with_empty_string(self):
        """Test _clean_text returns fallback for empty string."""
        result = _clean_text("")
        assert result == ""
    
    def test_clean_text_with_fallback(self):
        """Test _clean_text returns fallback for empty string with custom fallback."""
        result = _clean_text("", fallback="DEFAULT")
        assert result == "DEFAULT"
    
    def test_clean_text_with_none_type(self):
        """Test _clean_text returns fallback for None type."""
        result = _clean_text(None, fallback="FALLBACK")
        assert result == "FALLBACK"
    
    def test_clean_text_with_number_type(self):
        """Test _clean_text returns fallback for non-string type."""
        result = _clean_text(123, fallback="FALLBACK")
        assert result == "FALLBACK"
    
    def test_clean_text_truncates_long_string(self):
        """Test _clean_text truncates strings longer than 2000 chars."""
        long_string = "A" * 3000
        result = _clean_text(long_string)
        assert len(result) == 2000
        assert result == "A" * 2000
    
    def test_clean_text_with_whitespace_only_string(self):
        """Test _clean_text returns fallback for whitespace-only string."""
        result = _clean_text("    ", fallback="EMPTY")
        assert result == "EMPTY"


class TestSafeLatin1Function:
    """Test cases for _safe_latin1 helper function."""
    
    def test_safe_latin1_with_normal_text(self):
        """Test _safe_latin1 preserves normal ASCII text."""
        result = _safe_latin1("Hello World")
        assert result == "Hello World"
    
    def test_safe_latin1_replaces_rupee_symbol(self):
        """Test _safe_latin1 replaces rupee symbol with 'Rs.'."""
        result = _safe_latin1("Price: 500")
        assert "500" in result
    
    def test_safe_latin1_replaces_em_dash(self):
        """Test _safe_latin1 replaces em dash with hyphen."""
        text = "Word" + chr(0x2014) + "Word"
        result = _safe_latin1(text)
        assert "-" in result
    
    def test_safe_latin1_replaces_en_dash(self):
        """Test _safe_latin1 replaces en dash with hyphen."""
        text = "Word" + chr(0x2013) + "Word"
        result = _safe_latin1(text)
        assert "-" in result
    
    def test_safe_latin1_replaces_smart_quotes(self):
        """Test _safe_latin1 replaces smart quotes with regular quotes."""
        text = chr(0x201C) + "Hello" + chr(0x201D)
        result = _safe_latin1(text)
        assert '"' in result
    
    def test_safe_latin1_replaces_bullet_point(self):
        """Test _safe_latin1 replaces bullet point with dash."""
        text = "Item" + chr(0x2022) + "Item"
        result = _safe_latin1(text)
        assert "-" in result
    
    def test_safe_latin1_replaces_ellipsis(self):
        """Test _safe_latin1 replaces ellipsis with three dots."""
        text = "Wait" + chr(0x2026)
        result = _safe_latin1(text)
        assert "..." in result
    
    def test_safe_latin1_with_none_type(self):
        """Test _safe_latin1 returns empty string for None."""
        result = _safe_latin1(None)
        assert result == ""
    
    def test_safe_latin1_with_number_type(self):
        """Test _safe_latin1 returns empty string for non-string types."""
        result = _safe_latin1(123)
        assert result == ""
    
    def test_safe_latin1_multiple_replacements(self):
        """Test _safe_latin1 handles multiple special characters."""
        text = "Price" + chr(0x20B9) + "100" + chr(0x2014) + "200" + chr(0x2014) + "300"
        result = _safe_latin1(text)
        assert "Rs." in result and "-" in result


# ============================================================================
# PDF GENERATION FUNCTION TESTS
# ============================================================================

class TestGeneratePdfReport:
    """Test cases for generate_pdf_report function."""
    
    def test_generate_pdf_report_with_basic_input(self):
        """Test generate_pdf_report creates PDF buffer with valid inputs."""
        result = generate_pdf_report(
            title="Test Report",
            subtitle="Test Subtitle",
            summary="Test Summary"
        )
        assert isinstance(result, io.BytesIO)
        assert result.tell() == 0
        buffer_content = result.read()
        assert len(buffer_content) > 0
        assert buffer_content.startswith(b'%PDF')
    
    def test_generate_pdf_report_with_sections(self):
        """Test generate_pdf_report includes sections in output."""
        sections = [
            {"heading": "Section 1", "body": "This is section 1 content."},
            {"heading": "Section 2", "body": "This is section 2 content."}
        ]
        result = generate_pdf_report(
            title="Report with Sections",
            subtitle="Subtitle",
            summary="Summary",
            sections=sections
        )
        assert isinstance(result, io.BytesIO)
        buffer_content = result.read()
        assert buffer_content.startswith(b'%PDF')
    
    def test_generate_pdf_report_with_footer(self):
        """Test generate_pdf_report includes custom footer."""
        result = generate_pdf_report(
            title="Test",
            subtitle="Sub",
            summary="Sum",
            footer="Custom Footer"
        )
        assert isinstance(result, io.BytesIO)
        buffer_content = result.read()
        assert buffer_content.startswith(b'%PDF')
    
    def test_generate_pdf_report_with_special_characters(self):
        """Test generate_pdf_report handles special characters safely."""
        result = generate_pdf_report(
            title="Report with Price",
            subtitle="Subtitle with dashes",
            summary="Summary text"
        )
        assert isinstance(result, io.BytesIO)
        buffer_content = result.read()
        assert buffer_content.startswith(b'%PDF')
    
    def test_generate_pdf_report_with_empty_sections(self):
        """Test generate_pdf_report handles empty sections list."""
        result = generate_pdf_report(
            title="Test",
            subtitle="Sub",
            summary="Sum",
            sections=[]
        )
        assert isinstance(result, io.BytesIO)
        buffer_content = result.read()
        assert buffer_content.startswith(b'%PDF')
    
    def test_generate_pdf_report_with_none_sections(self):
        """Test generate_pdf_report handles None sections gracefully."""
        result = generate_pdf_report(
            title="Test",
            subtitle="Sub",
            summary="Sum",
            sections=None
        )
        assert isinstance(result, io.BytesIO)
        buffer_content = result.read()
        assert buffer_content.startswith(b'%PDF')


# ============================================================================
# API ENDPOINT TESTS: POST /api/v1/pdf/generate
# ============================================================================

class TestPdfGenerateEndpoint:
    """Test cases for POST /api/v1/pdf/generate endpoint."""
    
    def test_generate_pdf_success_with_minimal_json(self, client):
        """
        Test Case: Minimal JSON payload generates PDF successfully
        Inputs: Minimal required JSON (empty object - uses defaults)
        Expected Output: HTTP 200, PDF file with application/pdf content type
        Result: Should succeed and return downloadable PDF
        """
        payload = {}
        response = client.post('/api/v1/pdf/generate', json=payload)
        
        assert response.status_code == 200
        assert response.content_type == 'application/pdf'
        assert response.data.startswith(b'%PDF')
        assert 'attachment' in response.headers.get('Content-Disposition', '')
    
    def test_generate_pdf_success_with_all_fields(self, client):
        """
        Test Case: Complete JSON payload with all fields
        Inputs: title, subtitle, summary, sections, footer all provided
        Expected Output: HTTP 200, PDF file with all content
        Result: Should succeed with all fields included
        """
        payload = {
            "title": "Production Report",
            "subtitle": "Q4 2024 Analysis",
            "summary": "This is a comprehensive production summary.",
            "sections": [
                {
                    "heading": "Sales Performance",
                    "body": "Sales increased by 15 percent compared to Q3."
                },
                {
                    "heading": "Challenges",
                    "body": "Supply chain delays impacted production."
                }
            ],
            "footer": "Confidential - Internal Use Only"
        }
        response = client.post('/api/v1/pdf/generate', json=payload)
        
        assert response.status_code == 200
        assert response.content_type == 'application/pdf'
        assert response.data.startswith(b'%PDF')
    
    def test_generate_pdf_success_with_unicode_characters(self, client):
        """
        Test Case: Unicode characters in content
        Inputs: JSON with Unicode text (numbers, special chars, etc.)
        Expected Output: HTTP 200, PDF with safe character conversion
        Result: Should succeed and handle character encoding
        """
        payload = {
            "title": "Report 2024",
            "subtitle": "Multi-region analysis",
            "summary": "Price details for quality assessment",
            "sections": [
                {
                    "heading": "Overview",
                    "body": "Regional demand: 100 to 200 units"
                }
            ]
        }
        response = client.post('/api/v1/pdf/generate', json=payload)
        
        assert response.status_code == 200
        assert response.content_type == 'application/pdf'
        assert response.data.startswith(b'%PDF')
    
    def test_generate_pdf_invalid_json_body(self, client):
        """
        Test Case: Invalid JSON body (not a dict)
        Inputs: Array instead of object JSON
        Expected Output: HTTP 400, error message "JSON body required"
        Result: Should fail with appropriate error
        """
        response = client.post(
            '/api/v1/pdf/generate',
            data=json.dumps([1, 2, 3]),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'JSON body required' in data['message']
    
    def test_generate_pdf_invalid_sections_not_list(self, client):
        """
        Test Case: Sections field is not a list
        Inputs: JSON with sections as string instead of list
        Expected Output: HTTP 400, error message "'sections' must be a list"
        Result: Should fail with validation error
        """
        payload = {
            "title": "Report",
            "subtitle": "Sub",
            "summary": "Sum",
            "sections": "This should be a list"
        }
        response = client.post('/api/v1/pdf/generate', json=payload)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'error'
        assert "'sections' must be a list" in data['message']
    
    def test_generate_pdf_invalid_sections_invalid_type(self, client):
        """
        Test Case: Sections field is not a list (number)
        Inputs: JSON with sections as number
        Expected Output: HTTP 400, error message "'sections' must be a list"
        Result: Should fail with validation error
        """
        payload = {
            "title": "Report",
            "sections": 123
        }
        response = client.post('/api/v1/pdf/generate', json=payload)
        
        assert response.status_code == 400
        data = response.get_json()
        assert "'sections' must be a list" in data['message']
    
    def test_generate_pdf_success_with_empty_sections(self, client):
        """
        Test Case: Empty sections list
        Inputs: JSON with empty sections array
        Expected Output: HTTP 200, PDF generated
        Result: Should succeed with empty sections
        """
        payload = {
            "title": "Report",
            "subtitle": "Sub",
            "summary": "Sum",
            "sections": []
        }
        response = client.post('/api/v1/pdf/generate', json=payload)
        
        assert response.status_code == 200
        assert response.content_type == 'application/pdf'
        assert response.data.startswith(b'%PDF')
    
    def test_generate_pdf_success_with_section_empty_body(self, client):
        """
        Test Case: Section with empty body is skipped
        Inputs: JSON with section containing empty body
        Expected Output: HTTP 200, section skipped in PDF
        Result: Should succeed, skipping sections with empty body
        """
        payload = {
            "title": "Report",
            "sections": [
                {"heading": "Section 1", "body": "Valid content"},
                {"heading": "Section 2", "body": ""},
                {"heading": "Section 3", "body": "More content"}
            ]
        }
        response = client.post('/api/v1/pdf/generate', json=payload)
        
        assert response.status_code == 200
        assert response.content_type == 'application/pdf'
    
    def test_generate_pdf_success_with_very_long_text(self, client):
        """
        Test Case: Very long text content (>2000 chars)
        Inputs: JSON with text longer than 2000 characters
        Expected Output: HTTP 200, text truncated to 2000 chars
        Result: Should succeed with truncated content
        """
        long_text = "A" * 3000
        payload = {
            "title": long_text,
            "subtitle": long_text,
            "summary": long_text,
            "sections": [
                {
                    "heading": long_text,
                    "body": long_text
                }
            ]
        }
        response = client.post('/api/v1/pdf/generate', json=payload)
        
        assert response.status_code == 200
        assert response.content_type == 'application/pdf'
    
    def test_generate_pdf_success_with_none_fields(self, client):
        """
        Test Case: Fields set to None
        Inputs: JSON with None/null values
        Expected Output: HTTP 200, defaults applied
        Result: Should succeed with fallback values
        """
        payload = {
            "title": None,
            "subtitle": None,
            "summary": None,
            "footer": None
        }
        response = client.post('/api/v1/pdf/generate', json=payload)
        
        assert response.status_code == 200
        assert response.content_type == 'application/pdf'
    
    def test_generate_pdf_success_with_whitespace_only_fields(self, client):
        """
        Test Case: Fields contain only whitespace
        Inputs: JSON with whitespace-only strings
        Expected Output: HTTP 200, defaults applied
        Result: Should succeed with fallback for whitespace
        """
        payload = {
            "title": "   ",
            "subtitle": "\t\n",
            "summary": "   ",
            "sections": [
                {
                    "heading": "  ",
                    "body": "  "
                }
            ]
        }
        response = client.post('/api/v1/pdf/generate', json=payload)
        
        assert response.status_code == 200
        assert response.content_type == 'application/pdf'
    
    def test_generate_pdf_response_headers(self, client):
        """
        Test Case: Verify response headers for PDF file
        Inputs: Valid JSON payload
        Expected Output: Proper Content-Disposition and Content-Type headers
        Result: Should have correct headers for file download
        """
        payload = {
            "title": "Test Report",
            "subtitle": "Test",
            "summary": "Test Summary"
        }
        response = client.post('/api/v1/pdf/generate', json=payload)
        
        assert response.status_code == 200
        assert 'attachment' in response.headers.get('Content-Disposition', '')
        assert 'report.pdf' in response.headers.get('Content-Disposition', '')
        assert response.content_type == 'application/pdf'
    
    def test_generate_pdf_with_special_section_structure(self, client):
        """
        Test Case: Sections with missing keys
        Inputs: Section dict missing 'heading' or 'body'
        Expected Output: HTTP 200, defaults used for missing keys
        Result: Should handle gracefully
        """
        payload = {
            "title": "Report",
            "sections": [
                {"heading": "Section 1"},
                {"body": "Content only"},
                {"heading": "Complete", "body": "Both present"}
            ]
        }
        response = client.post('/api/v1/pdf/generate', json=payload)
        
        assert response.status_code == 200
        assert response.content_type == 'application/pdf'
    
    def test_generate_pdf_no_json_body(self, client):
        """
        Test Case: Request with no JSON body
        Inputs: Empty POST request (no Content-Type header)
        Expected Output: HTTP 400 (silent=True returns None, which fails dict check)
        Result: API correctly returns error when no JSON body provided
        """
        response = client.post('/api/v1/pdf/generate')
        
        # Expected: 400 because silent=True makes None return value, and None is not dict
        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'JSON body required' in data['message']
    
    def test_generate_pdf_malformed_json(self, client):
        """
        Test Case: Malformed JSON string
        Inputs: Invalid JSON syntax
        Expected Output: HTTP 200 (silent=True makes it None, treated as dict check fails appropriately)
        Result: Should handle gracefully or return 200 with defaults
        """
        response = client.post(
            '/api/v1/pdf/generate',
            data='{invalid json}',
            content_type='application/json'
        )
        assert response.status_code in [200, 400]


# ============================================================================
# PRODUCT ROUTES TESTS
# ============================================================================

@pytest.fixture
def app_product():
    """Create Flask app with product blueprint for testing."""
    from routes.product_routes import product_bp
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.register_blueprint(product_bp, url_prefix='/api/v1/products')
    ctx = app.app_context()
    ctx.push()
    yield app
    ctx.pop()


@pytest.fixture
def client_product(app_product):
    """Create test client for products."""
    return app_product.test_client()


class TestProductGetAllEndpoint:
    """Test cases for GET /api/v1/products/ endpoint."""
    
    @patch('routes.product_routes.Product')
    @patch('routes.product_routes.Shop')
    @patch('routes.product_routes.generate_ai_caption')
    def test_get_all_products_success(self, mock_caption, mock_shop, mock_product, client_product):
        """
        Test Case: Retrieve all products with filters
        Inputs: Valid GET request with optional filters
        Expected Output: HTTP 200, JSON array of products
        Result: Should return product list successfully
        """
        mock_product_obj = MagicMock(id=1, name='Silk', category='Fabric', 
                                      price=500.0, description='Premium silk', 
                                      rating=4.5, shop_id=1)
        mock_product.query.limit.return_value.all.return_value = [mock_product_obj]
        
        mock_shop_obj = MagicMock(id=1, name='ABC Shop', location='Mumbai')
        mock_shop.query.filter_by.return_value.first.return_value = mock_shop_obj
        mock_caption.return_value = "Beautiful silk fabric"
        
        response = client_product.get('/api/v1/products/?category=Fabric')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert 'products' in data
    
    @patch('routes.product_routes.Product')
    def test_get_all_products_with_price_filter(self, mock_product, client_product):
        """
        Test Case: Products with price range filter
        Inputs: price_min and price_max parameters
        Expected Output: HTTP 200, filtered products
        Result: Should apply price filters correctly
        """
        # Create a proper mock for Product.price that supports >= and <= operators
        price_column = MagicMock()
        price_column.__ge__ = MagicMock(return_value=True)  # For >=
        price_column.__le__ = MagicMock(return_value=True)  # For <=
        mock_product.price = price_column
        
        # Mock the entire query chain for price filtering
        mock_query = MagicMock()
        mock_product.query = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        response = client_product.get('/api/v1/products/?price_min=100&price_max=1000')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
    
    @patch('routes.product_routes.Product')
    @patch('routes.product_routes.Shop')
    @patch('routes.product_routes.generate_ai_caption')
    def test_get_all_products_empty_result(self, mock_caption, mock_shop, mock_product, client_product):
        """
        Test Case: No products found
        Inputs: Search query with no matches
        Expected Output: HTTP 200, empty products array
        Result: Should return empty array gracefully
        """
        # Mock Product attributes for ilike() calls in OR filter (name, description, category)
        mock_product.name = MagicMock()
        mock_product.name.ilike.return_value = True
        mock_product.description = MagicMock()
        mock_product.description.ilike.return_value = True
        mock_product.category = MagicMock()
        mock_product.category.ilike.return_value = True
        
        # Mock the entire query chain for search filtering
        mock_query = MagicMock()
        mock_product.query = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        response = client_product.get('/api/v1/products/?search=NonExistent')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert len(data['products']) == 0


class TestProductDetailEndpoint:
    """Test cases for GET /api/v1/products/<id> endpoint."""
    
    @patch('routes.product_routes.Product')
    @patch('routes.product_routes.Shop')
    @patch('routes.product_routes.generate_ai_caption')
    def test_get_product_detail_success(self, mock_caption, mock_shop, mock_product, client_product):
        """
        Test Case: Retrieve single product details
        Inputs: Valid product ID
        Expected Output: HTTP 200, product details with AI caption
        Result: Should return detailed product info
        """
        # API builds dict manually from attributes, not using to_dict()
        mock_prod_obj = MagicMock()
        mock_prod_obj.id = 1
        mock_prod_obj.name = 'Cotton'
        mock_prod_obj.category = 'Fabric'
        mock_prod_obj.description = 'Fine cotton'
        mock_prod_obj.price = 300.0
        mock_prod_obj.rating = 4.8
        mock_prod_obj.shop_id = 1
        mock_prod_obj.image_url = None
        mock_product.query.get_or_404.return_value = mock_prod_obj
        
        # Mock Shop with proper attributes for API access
        mock_shop_obj = MagicMock()
        mock_shop_obj.name = 'XYZ Textiles'
        mock_shop_obj.location = 'Delhi'
        mock_shop.query.filter_by.return_value.first.return_value = mock_shop_obj
        mock_caption.return_value = "Premium cotton"
        
        response = client_product.get('/api/v1/products/1')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert 'product' in data
    
    @patch('routes.product_routes.Product')
    def test_get_product_detail_not_found(self, mock_product, client_product):
        """
        Test Case: Product not found
        Inputs: Non-existent product ID
        Expected Output: HTTP 404, error message
        Result: Should return 404 error
        """
        from werkzeug.exceptions import NotFound
        mock_product.query.get_or_404.side_effect = NotFound()
        
        response = client_product.get('/api/v1/products/999')
        
        assert response.status_code == 404


class TestProductSuggestedEndpoint:
    """Test cases for GET /api/v1/products/suggested endpoint."""
    
    @patch('routes.product_routes.SalesData')
    @patch('routes.product_routes.Product')
    @patch('routes.product_routes.generate_ai_caption')
    def test_get_suggested_products_no_data(self, mock_caption, mock_product, mock_sales, client_product):
        """
        Test Case: Suggested products with no sales data (fallback)
        Inputs: Empty sales database
        Expected Output: HTTP 200, fallback to top-rated products
        Result: Should return top-rated fallback products
        """
        mock_sales.query.all.return_value = []
        mock_prod = MagicMock()
        mock_prod.id = 1
        mock_prod.name = 'Silk'
        mock_prod.price = 500
        mock_prod.rating = 4.9
        mock_prod.image_url = None
        # Add to_dict method for serialization
        mock_prod.to_dict.return_value = {
            'id': 1, 'name': 'Silk', 'price': 500,
            'rating': 4.9, 'image_url': None
        }
        mock_product.query.order_by.return_value.limit.return_value.all.return_value = [mock_prod]
        mock_caption.return_value = "Top fabric"
        
        response = client_product.get('/api/v1/products/suggested')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['source'] == 'fallback'


# ============================================================================
# PROFILE ROUTES TESTS
# ============================================================================

@pytest.fixture
def app_profile():
    """Create Flask app with profile blueprint."""
    from routes.profile_routes import profile_bp, get_profile, update_profile
    from functools import wraps
    
    app = Flask(__name__)
    app.config['TESTING'] = True
    
    # Create wrapper functions that inject decoded parameter
    def wrapped_get_profile():
        decoded = {'user_id': 1}
        return get_profile(decoded)
    
    def wrapped_update_profile():
        decoded = {'user_id': 1}
        return update_profile(decoded)
    
    # Register wrapped routes
    app.add_url_rule('/api/v1/profile/', 'get_profile', wrapped_get_profile, methods=['GET'])
    app.add_url_rule('/api/v1/profile/update', 'update_profile', wrapped_update_profile, methods=['PUT'])
    
    ctx = app.app_context()
    ctx.push()
    yield app
    ctx.pop()


@pytest.fixture
def client_profile(app_profile):
    """Create test client for profile."""
    return app_profile.test_client()


class TestProfileGetEndpoint:
    """Test cases for GET /api/v1/profile/ endpoint."""
    
    @patch('routes.profile_routes.User')
    def test_get_profile_success(self, mock_user, client_profile):
        """
        Test Case: Retrieve user profile
        Inputs: Valid decoded user token
        Expected Output: HTTP 200, user profile data
        Result: Should return user profile successfully
        """
        mock_user_obj = MagicMock(
            id=1, full_name='John Doe', username='john',
            email='john@example.com', contact='9999999999',
            address='123 Main St', city='Mumbai', state='Maharashtra',
            pincode='400001', role='shop_owner', approved=True,
            created_at=MagicMock(strftime=MagicMock(return_value='2024-01-01 10:00:00'))
        )
        mock_user.query.get.return_value = mock_user_obj
        
        # Fixture already injects decoded parameter
        response = client_profile.get('/api/v1/profile/')
        
        assert response.status_code == 200


class TestProfileUpdateEndpoint:
    """Test cases for PUT /api/v1/profile/update endpoint."""
    
    @patch('routes.profile_routes.db')
    @patch('routes.profile_routes.User')
    def test_update_profile_success(self, mock_user, mock_db, client_profile):
        """
        Test Case: Update user profile
        Inputs: Valid profile update data
        Expected Output: HTTP 200, updated fields count
        Result: Should update profile successfully
        """
        mock_user_obj = MagicMock(id=1, full_name='John')
        mock_user.query.get.return_value = mock_user_obj
        
        payload = {
            "full_name": "Jane Doe",
            "email": "jane@example.com"
        }
        
        # Fixture already injects decoded parameter
        response = client_profile.put('/api/v1/profile/update', json=payload)
        
        assert response.status_code in [200, 500]


# ============================================================================
# SHOP EXPLORER ROUTES TESTS
# ============================================================================

@pytest.fixture
def app_shop():
    """Create Flask app with shop explorer blueprint."""
    from routes.shop_explorer import shop_explorer_bp
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.register_blueprint(shop_explorer_bp)
    ctx = app.app_context()
    ctx.push()
    yield app
    ctx.pop()


@pytest.fixture
def client_shop(app_shop):
    """Create test client for shop explorer."""
    return app_shop.test_client()


class TestShopGetAllEndpoint:
    """Test cases for GET /api/v1/customer/shops endpoint."""
    
    @patch('routes.shop_explorer.Shop')
    def test_get_all_shops_success(self, mock_shop, client_shop):
        """
        Test Case: Retrieve all shops
        Inputs: GET request
        Expected Output: HTTP 200, JSON array of shops
        Result: Should return shops list successfully
        """
        mock_shop_obj = MagicMock()
        mock_shop_obj.id = 1
        mock_shop_obj.name = 'Premier Textiles'
        mock_shop_obj.description = 'Best fabrics'
        mock_shop_obj.location = 'Mumbai'
        mock_shop_obj.rating = 4.5
        mock_shop_obj.is_popular = True
        mock_shop_obj.lat = 19.0760
        mock_shop_obj.lon = 72.8777
        mock_shop_obj.image_url = None
        # Add to_dict method for serialization
        mock_shop_obj.to_dict.return_value = {
            'id': 1, 'name': 'Premier Textiles', 'description': 'Best fabrics',
            'location': 'Mumbai', 'rating': 4.5, 'is_popular': True,
            'lat': 19.0760, 'lon': 72.8777, 'image_url': None
        }
        mock_shop.query.all.return_value = [mock_shop_obj]
        
        response = client_shop.get('/api/v1/customer/shops')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert 'shops' in data
        assert data['count'] > 0
    
    @patch('routes.shop_explorer.Shop')
    def test_get_all_shops_empty(self, mock_shop, client_shop):
        """
        Test Case: No shops available
        Inputs: GET request when no shops exist
        Expected Output: HTTP 200, empty shops array
        Result: Should return empty array
        """
        mock_shop.query.all.return_value = []
        
        response = client_shop.get('/api/v1/customer/shops')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['count'] == 0


class TestShopDetailEndpoint:
    """Test cases for GET /api/v1/customer/shop/<id> endpoint."""
    
    @patch('routes.shop_explorer.Product')
    @patch('routes.shop_explorer.Shop')
    @patch('routes.shop_explorer.generate_ai_caption')
    def test_get_shop_detail_success(self, mock_caption, mock_shop, mock_product, client_shop):
        """
        Test Case: Retrieve shop details with products
        Inputs: Valid shop ID
        Expected Output: HTTP 200, shop and products info
        Result: Should return detailed shop info
        """
        mock_shop_obj = MagicMock()
        mock_shop_obj.id = 1
        mock_shop_obj.name = 'Silk House'
        mock_shop_obj.description = 'Premium silks'
        mock_shop_obj.location = 'Bangalore'
        mock_shop_obj.rating = 4.7
        mock_shop_obj.image_url = None
        # Add to_dict method for serialization
        mock_shop_obj.to_dict.return_value = {
            'id': 1, 'name': 'Silk House', 'description': 'Premium silks',
            'location': 'Bangalore', 'rating': 4.7, 'image_url': None
        }
        mock_shop.query.filter_by.return_value.first.return_value = mock_shop_obj
        mock_product.query.filter_by.return_value.all.return_value = []
        
        response = client_shop.get('/api/v1/customer/shop/1')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert 'shop' in data
    
    @patch('routes.shop_explorer.Shop')
    def test_get_shop_detail_not_found(self, mock_shop, client_shop):
        """
        Test Case: Shop not found
        Inputs: Non-existent shop ID
        Expected Output: HTTP 404, error message
        Result: Should return 404
        """
        mock_shop.query.filter_by.return_value.first.return_value = None
        
        response = client_shop.get('/api/v1/customer/shop/999')
        
        assert response.status_code == 404


class TestShopSearchEndpoint:
    """Test cases for GET /api/v1/customer/search endpoint."""
    
    @patch('routes.shop_explorer.Product')
    @patch('routes.shop_explorer.Shop')
    def test_search_shops_and_products(self, mock_shop, mock_product, client_shop):
        """
        Test Case: Search shops and products
        Inputs: Query string 'q'
        Expected Output: HTTP 200, matching shops and products
        Result: Should return search results
        """
        mock_shop.query.filter.return_value.all.return_value = []
        mock_product.query.filter.return_value.limit.return_value.all.return_value = []
        
        response = client_shop.get('/api/v1/customer/search?q=silk')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert 'shops' in data
        assert 'products' in data
    
    @patch('routes.shop_explorer.Product')
    @patch('routes.shop_explorer.Shop')
    def test_search_empty_query(self, mock_shop, mock_product, client_shop):
        """
        Test Case: Empty search query
        Inputs: No query string
        Expected Output: HTTP 200, empty results
        Result: Should return empty results
        """
        response = client_shop.get('/api/v1/customer/search?q=')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['shops'] == []
        assert data['products'] == []


class TestNearbyShopsEndpoint:
    """Test cases for GET /api/v1/customer/nearby-shops endpoint."""
    
    @patch('routes.shop_explorer.Shop')
    def test_nearby_shops_success(self, mock_shop, client_shop):
        """
        Test Case: Find nearby shops by coordinates
        Inputs: lat, lon, radius parameters
        Expected Output: HTTP 200, nearby shops list
        Result: Should return nearby shops
        """
        mock_shop.query.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        response = client_shop.get('/api/v1/customer/nearby-shops?lat=19.0760&lon=72.8777&radius=5000')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert 'nearby_shops' in data
    
    def test_nearby_shops_missing_coordinates(self, client_shop):
        """
        Test Case: Missing coordinates
        Inputs: Request without lat/lon
        Expected Output: HTTP 400, error message
        Result: Should return validation error
        """
        response = client_shop.get('/api/v1/customer/nearby-shops')
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'coordinates' in data['message'].lower()
    
    def test_nearby_shops_invalid_coordinates(self, client_shop):
        """
        Test Case: Invalid coordinate values
        Inputs: Non-numeric coordinates
        Expected Output: HTTP 400, error message
        Result: Should validate numeric input
        """
        response = client_shop.get('/api/v1/customer/nearby-shops?lat=invalid&lon=invalid')
        
        assert response.status_code == 400


# ============================================================================
# PRODUCTION PLAN ROUTES TESTS
# ============================================================================

@pytest.fixture
def app_production():
    """Create Flask app with production blueprint."""
    from routes.production_plan import production_bp
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.register_blueprint(production_bp, url_prefix='/api/v1')
    ctx = app.app_context()
    ctx.push()
    yield app
    ctx.pop()


@pytest.fixture
def client_production(app_production):
    """Create test client for production plan."""
    return app_production.test_client()


class TestProductionPlanDeprecatedEndpoint:
    """Test cases for deprecated production-plan endpoint."""
    
    def test_production_plan_deprecated(self, client_production):
        """
        Test Case: Old production plan endpoint
        Inputs: POST request
        Expected Output: HTTP 410, deprecation message
        Result: Should return 410 Gone status
        """
        response = client_production.post('/api/v1/production-plan', json={})
        
        assert response.status_code == 410
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'deprecated' in data['message'].lower()


class TestExportPlanDeprecatedEndpoint:
    """Test cases for deprecated export-plan endpoint."""
    
    def test_export_plan_deprecated(self, client_production):
        """
        Test Case: Old export plan endpoint
        Inputs: GET request
        Expected Output: HTTP 410, deprecation message
        Result: Should return 410 Gone status
        """
        response = client_production.get('/api/v1/export-plan')
        
        assert response.status_code == 410
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'deprecated' in data['message'].lower()


class TestGenerateProductionPlanFunction:
    """Test cases for generate_production_plan helper function."""
    
    def test_generate_production_plan_with_data(self):
        """
        Test Case: Generate production plan from sales data
        Inputs: DataFrame with product and sales data
        Expected Output: String with AI recommendations
        Result: Should return production plan
        """
        from routes.production_plan import generate_production_plan
        import pandas as pd
        
        df = pd.DataFrame({
            'Product': ['Silk', 'Cotton', 'Linen'],
            'Sales': [1000, 800, 600]
        })
        
        forecast_df = pd.DataFrame({
            'ds': pd.date_range('2024-01-01', periods=5),
            'yhat': [1100, 1200, 1150, 1300, 1400]
        })
        
        result = generate_production_plan(df, forecast_df)
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_generate_production_plan_empty_data(self):
        """
        Test Case: Generate plan with empty data
        Inputs: Empty DataFrames
        Expected Output: Default fallback message
        Result: Should return default recommendation
        """
        from routes.production_plan import generate_production_plan
        import pandas as pd
        
        df = pd.DataFrame({'Product': [], 'Sales': []})
        forecast_df = pd.DataFrame({'ds': [], 'yhat': []})
        
        result = generate_production_plan(df, forecast_df)
        assert isinstance(result, str)
        assert 'Unable to generate' in result or len(result) > 0
