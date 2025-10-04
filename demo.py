"""
Demo script to showcase the new modular Career Fair Buddy
Shows how to use the components programmatically
"""
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def demo_configuration():
    """Demo the configuration system"""
    print("🔧 Configuration Demo")
    print("-" * 30)
    
    from src.config import Config
    
    print(f"📂 Project root: {Config.PROJECT_ROOT}")
    print(f"📄 PDF file: {Config.PDF_FILE_PATH.name}")
    print(f"🤖 OpenAI model: {Config.OPENAI_MODEL}")
    print(f"⚡ Max retries: {Config.OPENAI_MAX_RETRIES}")
    print()
    
    # Demo day functionality
    print("📅 Day-based venue organization:")
    for day in ["Day 1", "Day 2"]:
        venues = Config.get_venues_for_day(day)
        print(f"  {day}: {list(venues.keys())}")
    print()

def demo_user_management():
    """Demo the user management system"""
    print("👤 User Management Demo")
    print("-" * 30)
    
    from src.user_manager import UserManager
    
    # Create a user
    user = UserManager()
    print(f"🆔 User ID: {user.user_id}")
    
    # Simulate some interactions
    user.update_interaction("A01", visited=True, interested=True, comments="Great company!")
    user.update_interaction("B15", resume_shared=True, apply_online=True)
    
    # Get summary
    summary = user.get_user_summary()
    print(f"📊 Interactions: {summary['total_interactions']}")
    print(f"✅ Visited: {summary['visited_booths']}")
    print(f"⭐ Interested: {summary['interested_booths']}")
    print()

def demo_cache_management():
    """Demo the cache management system"""
    print("💾 Cache Management Demo")
    print("-" * 30)
    
    from src.cache_manager import CacheManager
    
    cache = CacheManager()
    
    # Add some test data
    cache.set_company_name("A01", 11, "Demo Company Inc", False)
    cache.set_industry("A01", 11, "Technology & IT", False)
    cache.set_education_level("A01", 11, "Both", False)
    
    # Retrieve data
    company = cache.get_company_name("A01", 11, False)
    industry = cache.get_industry("A01", 11, False)
    education = cache.get_education_level("A01", 11, False)
    
    print(f"🏢 Company: {company}")
    print(f"🏭 Industry: {industry}")
    print(f"🎓 Education: {education}")
    
    # Get stats
    stats = cache.get_stats()
    print(f"📈 Cache entries: {stats['total_entries']}")
    print()

def demo_utilities():
    """Demo utility functions"""
    print("🔧 Utilities Demo")
    print("-" * 30)
    
    from src.utils import (
        extract_booth_numbers, 
        validate_booth_number,
        get_venue_from_booth,
        format_file_size
    )
    
    # Test booth extraction
    sample_text = "A01 Company One B15 Company Two C23 Company Three"
    booths = extract_booth_numbers(sample_text)
    print(f"📍 Extracted booths: {booths}")
    
    # Test validation
    valid_booths = [booth for booth in booths if validate_booth_number(booth)]
    print(f"✅ Valid booths: {valid_booths}")
    
    # Test venue mapping
    for booth in valid_booths:
        venue = get_venue_from_booth(booth, False)
        print(f"  {booth} → {venue}")
    
    # Test file size formatting
    sizes = [1024, 1048576, 1073741824]
    for size in sizes:
        formatted = format_file_size(size)
        print(f"  {size} bytes → {formatted}")
    print()

def demo_integration():
    """Demo how components work together"""
    print("🔗 Integration Demo")
    print("-" * 30)
    
    from src.config import Config
    from src.user_manager import UserManager
    from src.cache_manager import CacheManager
    
    # Show how day selection affects venue options
    print("📅 Day-based venue selection:")
    for day in ["Day 1", "Day 2"]:
        venues = list(Config.get_venues_for_day(day).keys())
        print(f"  {day}: {len(venues)} venues available")
        
        # Show full venue names
        for venue in venues[:2]:  # Show first 2
            full_name = Config.get_full_venue_name(venue, day)
            clean_name = Config.get_clean_venue_name(full_name)
            detected_day = Config.get_day_from_venue(full_name)
            print(f"    {venue} → '{full_name}' → '{clean_name}' ({detected_day})")
    
    print()
    
    # Show system metrics
    metrics = UserManager.get_system_metrics()
    print("📊 System Metrics:")
    print(f"  Total users: {metrics['total_users']}")
    print(f"  Active users (24h): {metrics['active_users_24h']}")
    print(f"  Storage: {metrics['total_storage_formatted']}")
    print(f"  Performance: {'✅ OK' if metrics['performance_ok'] else '⚠️ Warning'}")
    print()

def main():
    """Run all demos"""
    print("🎯 Career Fair Buddy - Modular Architecture Demo")
    print("=" * 50)
    print()
    
    demos = [
        demo_configuration,
        demo_user_management,
        demo_cache_management,
        demo_utilities,
        demo_integration
    ]
    
    for demo in demos:
        try:
            demo()
        except Exception as e:
            print(f"❌ Demo error: {e}")
            print()
    
    print("=" * 50)
    print("✨ Demo complete! The modular architecture provides:")
    print("   • Clean separation of concerns")
    print("   • Easy testing and debugging")
    print("   • Flexible day-based venue management")
    print("   • Robust user data isolation")
    print("   • Intelligent caching system")
    print("   • Mobile-responsive UI components")
    print()
    print("🚀 To run the app: streamlit run main.py")

if __name__ == "__main__":
    main()
