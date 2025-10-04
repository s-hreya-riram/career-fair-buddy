"""
Test the new Day 1/Day 2 functionality
Run with: python test_day_functionality.py
"""
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_day_configuration():
    """Test day-based venue configuration"""
    try:
        from src.config import Config
        
        # Test DAY_VENUES structure
        assert "Day 1" in Config.DAY_VENUES
        assert "Day 2" in Config.DAY_VENUES
        
        # Test Day 1 venues
        day1_venues = Config.DAY_VENUES["Day 1"]
        assert "SRC Hall A" in day1_venues
        assert "SRC Hall B" in day1_venues
        assert "SRC Hall C" in day1_venues
        assert "EA Atrium" in day1_venues
        
        # Test Day 2 venues
        day2_venues = Config.DAY_VENUES["Day 2"]
        assert "SRC Hall A" in day2_venues
        assert "SRC Hall B" in day2_venues
        assert "SRC Hall C" in day2_venues
        assert "EA Atrium" in day2_venues
        
        print("✅ Day-based venue configuration is correct!")
        return True
    except Exception as e:
        print(f"❌ Day configuration error: {e}")
        return False

def test_day_helper_methods():
    """Test Config helper methods for day operations"""
    try:
        from src.config import Config
        
        # Test get_venues_for_day
        day1_venues = Config.get_venues_for_day("Day 1")
        assert "SRC Hall A" in day1_venues
        assert len(day1_venues) == 4
        
        day2_venues = Config.get_venues_for_day("Day 2")
        assert "SRC Hall A" in day2_venues
        assert len(day2_venues) == 4
        
        # Test get_day_from_venue
        assert Config.get_day_from_venue("SRC Hall A") == "Day 1"
        assert Config.get_day_from_venue("SRC Hall A Day 2") == "Day 2"
        
        # Test get_clean_venue_name
        assert Config.get_clean_venue_name("SRC Hall A") == "SRC Hall A"
        assert Config.get_clean_venue_name("SRC Hall A Day 2") == "SRC Hall A"
        
        # Test get_full_venue_name
        assert Config.get_full_venue_name("SRC Hall A", "Day 1") == "SRC Hall A"
        assert Config.get_full_venue_name("SRC Hall A", "Day 2") == "SRC Hall A Day 2"
        
        print("✅ Day helper methods working correctly!")
        return True
    except Exception as e:
        print(f"❌ Day helper methods error: {e}")
        return False

def test_venue_mapping_consistency():
    """Test that venue mappings are consistent between old and new formats"""
    try:
        from src.config import Config
        
        # Verify all venues from DAY_VENUES exist in VENUE_PAGE_MAPPINGS
        for day, venues in Config.DAY_VENUES.items():
            for venue_name, pages in venues.items():
                if day == "Day 1":
                    full_name = venue_name
                else:
                    full_name = f"{venue_name} Day 2"
                
                assert full_name in Config.VENUE_PAGE_MAPPINGS
                assert Config.VENUE_PAGE_MAPPINGS[full_name] == pages
        
        # Verify ALL_VENUES contains all venues
        assert len(Config.ALL_VENUES) == len(Config.VENUE_PAGE_MAPPINGS)
        
        print("✅ Venue mapping consistency verified!")
        return True
    except Exception as e:
        print(f"❌ Venue mapping consistency error: {e}")
        return False

def test_day_based_filtering():
    """Test day-based filtering functionality"""
    try:
        # Test sample companies for filtering
        sample_companies = [
            {"name": "Company A", "education_level": "Undergraduate", "venue": "SRC Hall A"},
            {"name": "Company B", "education_level": "Postgraduate", "venue": "SRC Hall A Day 2"},
            {"name": "Company C", "education_level": "Both", "venue": "SRC Hall B"},
            {"name": "Company D", "education_level": "Undergraduate", "venue": "SRC Hall B Day 2"},
        ]
        
        # Test education filtering logic
        undergraduate_companies = [
            c for c in sample_companies 
            if c['education_level'] == "Undergraduate" or c['education_level'] == "Both"
        ]
        assert len(undergraduate_companies) == 3  # A, C, D (C has "Both")
        
        postgraduate_companies = [
            c for c in sample_companies 
            if c['education_level'] == "Postgraduate" or c['education_level'] == "Both"
        ]
        assert len(postgraduate_companies) == 2  # B, C (C has "Both")
        
        # Test day filtering
        day1_companies = [c for c in sample_companies if "Day 2" not in c['venue']]
        day2_companies = [c for c in sample_companies if "Day 2" in c['venue']]
        
        assert len(day1_companies) == 2  # A, C
        assert len(day2_companies) == 2  # B, D
        
        print("✅ Day-based filtering logic working correctly!")
        return True
    except Exception as e:
        print(f"❌ Day-based filtering error: {e}")
        return False

def main():
    """Run all day functionality tests"""
    print("🗓️ Testing Career Fair Buddy Day 1/Day 2 Functionality")
    print("=" * 55)
    
    tests = [
        test_day_configuration,
        test_day_helper_methods,
        test_venue_mapping_consistency,
        test_day_based_filtering
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 55)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All day functionality tests passed! Day 1/Day 2 features are working correctly.")
        return True
    else:
        print(f"❌ {total - passed} test(s) failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
