"""
Simple test to verify the modular structure works correctly
Run with: python test_modules.py
"""
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_imports():
    """Test that all modules can be imported"""
    try:
        from src.config import Config
        from src.utils import extract_booth_numbers, sort_companies_by_booth
        from src.cache_manager import CacheManager
        from src.user_manager import UserManager
        from src.openai_service import OpenAIService
        from src.pdf_reader import CareerFairPDFReader
        from src.ui.styles import get_custom_css
        from src.ui.mobile import MobileManager
        
        print("✅ All modules imported successfully!")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_config():
    """Test configuration setup"""
    try:
        from src.config import Config
        
        # Test basic config values
        assert Config.VENUE_PAGE_MAPPINGS
        assert Config.VALID_INDUSTRIES
        assert Config.EDUCATION_LEVELS
        
        print("✅ Configuration values loaded correctly!")
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_utils():
    """Test utility functions"""
    try:
        from src.utils import extract_booth_numbers, validate_booth_number, get_cache_key
        
        # Test booth number extraction
        test_text = "A01 Company Name A02 Another Company B15"
        booths = extract_booth_numbers(test_text)
        assert "A01" in booths
        assert "A02" in booths
        assert "B15" in booths
        
        # Test booth validation
        assert validate_booth_number("A01") == True
        assert validate_booth_number("invalid") == False
        
        # Test cache key generation
        key = get_cache_key("A01", 11)
        assert "A01_11" in key
        
        print("✅ Utility functions working correctly!")
        return True
    except Exception as e:
        print(f"❌ Utils error: {e}")
        return False

def test_managers():
    """Test manager classes"""
    try:
        from src.cache_manager import CacheManager
        from src.user_manager import UserManager
        
        # Test cache manager
        cache = CacheManager()
        cache.set("test_key", "test_value")
        assert cache.get("test_key") == "test_value"
        
        # Test user manager
        user_manager = UserManager()
        assert len(user_manager.user_id) == 8  # UUID should be 8 chars
        
        print("✅ Manager classes initialized correctly!")
        return True
    except Exception as e:
        print(f"❌ Manager error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Career Fair Buddy Modular Architecture")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_config,
        test_utils,
        test_managers
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Modular architecture is working correctly.")
        return True
    else:
        print(f"❌ {total - passed} test(s) failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
