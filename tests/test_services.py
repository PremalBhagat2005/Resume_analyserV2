import pytest
from app import create_app
from app.utils.helpers import (
    validate_file, clean_text, extract_email, extract_phone,
    check_action_verbs, extract_keywords, word_count
)


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestHelpers:
    """Test helper functions."""
    
    def test_clean_text(self):
        """Test text cleaning function."""
        dirty_text = "Hello   WORLD!!! This is a   test text ##"
        cleaned = clean_text(dirty_text)
        assert "Hello" in cleaned
        assert "WORLD" in cleaned
        assert "!" not in cleaned
        assert "#" not in cleaned
    
    def test_extract_email(self):
        """Test email extraction."""
        text = "Contact me at john.doe@example.com for more info"
        email = extract_email(text)
        assert email == "john.doe@example.com"
    
    def test_extract_phone(self):
        """Test phone number extraction."""
        text = "You can reach me at (555) 123-4567"
        phone = extract_phone(text)
        assert phone is not None
        assert "555" in phone
    
    def test_check_action_verbs(self):
        """Test action verb detection."""
        text = "I managed the team and developed new features"
        count = check_action_verbs(text)
        assert count >= 2
    
    def test_extract_keywords(self):
        """Test keyword extraction."""
        text = "Python Django React JavaScript AWS Azure"
        keywords = extract_keywords(text)
        assert len(keywords) > 0
    
    def test_word_count(self):
        """Test word counting."""
        text = "This is a simple test"
        count = word_count(text)
        assert count == 5


class TestRoutes:
    """Test Flask routes."""
    
    def test_index_route(self, client):
        """Test landing page route."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Resume Analyser' in response.data
        assert b'Optimize Your Resume' in response.data
    
    def test_analyse_route_no_file(self, client):
        """Test analyse route without file."""
        response = client.post('/analyse', data={})
        assert response.status_code == 200
        assert b'error' in response.data.lower()
    
    def test_analyse_route_with_invalid_file(self, client):
        """Test analyse route with invalid file type."""
        data = {
            'file': (b'fake content', 'test.jpg')
        }
        response = client.post('/analyse', data=data, content_type='multipart/form-data')
        assert response.status_code == 200


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
