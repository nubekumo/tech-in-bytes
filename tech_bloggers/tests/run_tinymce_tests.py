#!/usr/bin/env python
"""
Test runner for TinyMCE functionality tests
"""
import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tech_bloggers.settings')
django.setup()

def run_tests():
    """Run all TinyMCE-related tests"""
    print("🧪 Running TinyMCE Tests...\n")
    
    # Get test runner
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    
    # Define test modules
    test_modules = [
        'apps.blog.tests.test_tinymce_sanitization',
        'apps.blog.tests.test_tinymce_integration',
    ]
    
    # Run tests
    failures = test_runner.run_tests(test_modules)
    
    if failures:
        print(f"\n❌ {failures} test(s) failed!")
        return False
    else:
        print("\n✅ All tests passed!")
        return True

def run_specific_test(test_module):
    """Run a specific test module"""
    print(f"🧪 Running {test_module}...\n")
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    
    failures = test_runner.run_tests([test_module])
    
    if failures:
        print(f"\n❌ {failures} test(s) failed!")
        return False
    else:
        print("\n✅ All tests passed!")
        return True

def run_javascript_tests():
    """Instructions for running JavaScript tests"""
    print("🌐 JavaScript Tests Instructions:")
    print("=" * 50)
    print("1. Open your browser and navigate to the create/edit post page")
    print("2. Open browser developer tools (F12)")
    print("3. Go to Console tab")
    print("4. Load the test file:")
    print("   <script src='/static/js/tests/tinymce-tests.js'></script>")
    print("5. The tests will run automatically and display results in console")
    print("6. Look for test results with ✅ (pass) and ❌ (fail) indicators")
    print("\nAlternatively, you can run the tests programmatically:")
    print("   const testSuite = new TinyMCETestSuite();")
    print("   testSuite.run();")
    print("=" * 50)

def main():
    """Main function"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'js':
            run_javascript_tests()
        elif command == 'sanitization':
            run_specific_test('apps.blog.tests.test_tinymce_sanitization')
        elif command == 'integration':
            run_specific_test('apps.blog.tests.test_tinymce_integration')
        elif command == 'help':
            print_help()
        else:
            print(f"Unknown command: {command}")
            print_help()
    else:
        # Run all tests by default
        run_tests()

def print_help():
    """Print help information"""
    print("TinyMCE Test Runner")
    print("=" * 20)
    print("Usage: python run_tinymce_tests.py [command]")
    print("\nCommands:")
    print("  (no command)  - Run all Python tests")
    print("  js            - Show instructions for JavaScript tests")
    print("  sanitization  - Run only sanitization tests")
    print("  integration   - Run only integration tests")
    print("  help          - Show this help message")
    print("\nExamples:")
    print("  python run_tinymce_tests.py")
    print("  python run_tinymce_tests.py js")
    print("  python run_tinymce_tests.py sanitization")

if __name__ == '__main__':
    main()
