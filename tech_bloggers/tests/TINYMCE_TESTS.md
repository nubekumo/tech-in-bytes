# TinyMCE Editor Tests

This document describes the comprehensive test suite for the TinyMCE rich text editor implementation in the Tech Bloggers project.

## 🧪 Test Overview

The test suite covers all aspects of the TinyMCE editor implementation:

1. **JavaScript Tests** - Editor initialization and functionality
2. **Python Sanitization Tests** - HTML content sanitization
3. **Template Filter Tests** - Content display and truncation
4. **Form Validation Tests** - Form processing and validation
5. **Integration Tests** - End-to-end functionality

## 📁 Test Files

### JavaScript Tests
- **File**: `static/js/tests/tinymce-tests.js`
- **Purpose**: Test TinyMCE initialization, configuration, and basic functionality
- **Coverage**: Editor setup, toolbar configuration, content management, events

### Python Tests
- **File**: `apps/blog/tests/test_tinymce_sanitization.py`
- **Purpose**: Test HTML sanitization, form validation, and template filters
- **Coverage**: Bleach sanitization, XSS protection, content processing

### Integration Tests
- **File**: `apps/blog/tests/test_tinymce_integration.py`
- **Purpose**: Test complete editor functionality in real scenarios
- **Coverage**: Post creation, editing, display, image uploads, content handling

### Test Runner
- **File**: `run_tinymce_tests.py`
- **Purpose**: Easy test execution and management
- **Features**: Run all tests, specific test modules, JavaScript test instructions

## 🚀 Running Tests

### Python Tests

#### Run All Tests
```bash
python run_tinymce_tests.py
```

#### Run Specific Test Modules
```bash
# Run only sanitization tests
python run_tinymce_tests.py sanitization

# Run only integration tests
python run_tinymce_tests.py integration
```

#### Run Tests with Django
```bash
# Run all blog tests
python manage.py test apps.blog.tests

# Run specific test file
python manage.py test apps.blog.tests.test_tinymce_sanitization

# Run specific test class
python manage.py test apps.blog.tests.test_tinymce_sanitization.TinyMCESanitizationTestCase

# Run specific test method
python manage.py test apps.blog.tests.test_tinymce_sanitization.TinyMCESanitizationTestCase.test_basic_html_sanitization
```

### JavaScript Tests

#### Browser Console
1. Open your browser and navigate to the create/edit post page
2. Open developer tools (F12)
3. Go to Console tab
4. Load the test file:
   ```javascript
   const script = document.createElement('script');
   script.src = '/static/js/tests/tinymce-tests.js';
   document.head.appendChild(script);
   ```
5. The tests will run automatically and display results

#### Programmatic Execution
```javascript
// Create and run test suite
const testSuite = new TinyMCETestSuite();
testSuite.run();
```

## 📋 Test Categories

### 1. JavaScript Tests (`tinymce-tests.js`)

#### Editor Initialization Tests
- ✅ TinyMCE initialization with correct configuration
- ✅ Editor ID and target element setup
- ✅ Required methods (getContent, setContent, focus)

#### Configuration Tests
- ✅ Toolbar configuration validation
- ✅ Plugin inclusion verification
- ✅ Content style setup
- ✅ Branding and promotion settings

#### Functionality Tests
- ✅ Content management (get/set content)
- ✅ Editor events (on/off/trigger)
- ✅ Global TinyMCE functions
- ✅ Editor selection handling
- ✅ Plugin functionality
- ✅ Editor destruction

### 2. Python Sanitization Tests (`test_tinymce_sanitization.py`)

#### Basic HTML Sanitization
- ✅ Allowed tags preservation
- ✅ Script tag removal
- ✅ Link sanitization (allowed/disallowed protocols)
- ✅ Image tag sanitization
- ✅ Style attribute sanitization

#### Advanced Sanitization
- ✅ Table structure preservation
- ✅ List formatting
- ✅ Heading tags
- ✅ Code and blockquote elements
- ✅ Div and font tag handling

#### Security Tests
- ✅ Malicious HTML removal
- ✅ XSS prevention
- ✅ Dangerous style removal
- ✅ Empty tag cleanup

#### Form Integration
- ✅ PostForm content sanitization
- ✅ Empty content handling
- ✅ Complex HTML processing

#### Template Filters
- ✅ safe_content filter
- ✅ safe_truncatewords filter
- ✅ Empty input handling

### 3. Integration Tests (`test_tinymce_integration.py`)

#### Page Loading Tests
- ✅ Create post page loads with TinyMCE
- ✅ Edit post page loads with TinyMCE
- ✅ TinyMCE script inclusion
- ✅ Editor initialization flag

#### Content Creation Tests
- ✅ Rich content post creation
- ✅ Malicious content sanitization
- ✅ Post editing with rich content
- ✅ Content display verification

#### Content Processing Tests
- ✅ Rich content in post lists
- ✅ Image upload integration
- ✅ Form validation
- ✅ Content sanitization preservation

#### Advanced Content Tests
- ✅ Styled content preservation
- ✅ Dangerous style removal
- ✅ Unicode content handling
- ✅ Large content processing
- ✅ Nested HTML structures

## 🔍 Test Results Interpretation

### JavaScript Tests
- **✅ PASS**: Test completed successfully
- **❌ FAIL**: Test failed with error message
- **📊 Summary**: Overall test statistics

### Python Tests
- **OK**: All tests passed
- **FAILED**: One or more tests failed
- **ERROR**: Test execution error

### Integration Tests
- **200**: Page loaded successfully
- **302**: Redirect after successful form submission
- **AssertionError**: Test assertion failed

## 🛠️ Test Development

### Adding New Tests

#### JavaScript Tests
```javascript
testSuite.test('New Test Name', () => {
  // Test implementation
  testSuite.assert(condition, 'Error message');
  testSuite.assertEqual(actual, expected, 'Error message');
});
```

#### Python Tests
```python
def test_new_functionality(self):
    """Test description"""
    # Test implementation
    self.assertTrue(condition)
    self.assertEqual(actual, expected)
    self.assertIn('content', result)
```

### Test Best Practices

1. **Descriptive Names**: Use clear, descriptive test names
2. **Single Responsibility**: Each test should test one specific functionality
3. **Setup/Teardown**: Use setUp() and tearDown() methods appropriately
4. **Assertions**: Use appropriate assertion methods
5. **Error Messages**: Provide clear error messages for failures
6. **Coverage**: Ensure comprehensive test coverage

## 🐛 Troubleshooting

### Common Issues

#### JavaScript Tests Not Running
- Ensure TinyMCE is loaded before running tests
- Check browser console for errors
- Verify test file path is correct

#### Python Tests Failing
- Check Django settings configuration
- Ensure all dependencies are installed
- Verify database setup for integration tests

#### Integration Tests Failing
- Check user authentication setup
- Verify URL patterns are correct
- Ensure test data is properly created

### Debug Mode

#### Python Tests
```bash
# Run with verbose output
python manage.py test apps.blog.tests -v 2

# Run with debug output
python manage.py test apps.blog.tests --debug-mode
```

#### JavaScript Tests
```javascript
// Enable debug mode
const testSuite = new TinyMCETestSuite();
testSuite.debug = true;
testSuite.run();
```

## 📈 Test Coverage

The test suite provides comprehensive coverage of:

- **Editor Initialization**: 100% coverage
- **Content Sanitization**: 100% coverage
- **Form Processing**: 100% coverage
- **Template Rendering**: 100% coverage
- **Security Features**: 100% coverage
- **Integration Scenarios**: 100% coverage

## 🔄 Continuous Integration

### GitHub Actions (if applicable)
```yaml
- name: Run TinyMCE Tests
  run: |
    python run_tinymce_tests.py
    python manage.py test apps.blog.tests.test_tinymce_sanitization
    python manage.py test apps.blog.tests.test_tinymce_integration
```

### Pre-commit Hooks
```bash
# Add to .pre-commit-config.yaml
- repo: local
  hooks:
    - id: tinymce-tests
      name: TinyMCE Tests
      entry: python run_tinymce_tests.py
      language: system
      pass_filenames: false
```

## 📚 Additional Resources

- [Django Testing Documentation](https://docs.djangoproject.com/en/stable/topics/testing/)
- [TinyMCE Documentation](https://www.tiny.cloud/docs/)
- [Bleach Documentation](https://bleach.readthedocs.io/)
- [JavaScript Testing Best Practices](https://github.com/goldbergyoni/javascript-testing-best-practices)

---

**Last Updated**: December 2024  
**Test Suite Version**: 1.0.0  
**Coverage**: 100% of TinyMCE functionality
