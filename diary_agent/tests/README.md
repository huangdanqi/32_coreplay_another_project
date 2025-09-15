# Diary Agent Test Suite

This directory contains comprehensive tests for the Diary Agent system, covering unit tests, integration tests, performance tests, acceptance tests, and end-to-end tests.

## Test Structure

### Test Categories

1. **Unit Tests** - Test individual components in isolation
   - `test_base_agent.py` - Base agent functionality
   - `test_condition_checker.py` - Condition evaluation logic
   - `test_event_router.py` - Event routing and classification
   - `test_llm_manager.py` - LLM provider management
   - `test_sub_agent_manager.py` - Sub-agent lifecycle management
   - `test_config_manager.py` - Configuration loading and validation
   - `test_diary_entry_generator.py` - Diary entry generation and formatting
   - `test_database_integration.py` - Database operations
   - `test_*_agent.py` - Individual agent implementations
   - `test_dairy_agent_controller.py` - Main controller logic
   - `test_error_handling.py` - Error handling and recovery

2. **Integration Tests** - Test component interactions
   - `test_integration_workflow.py` - Complete event processing workflow
   - Tests event flow from detection to diary generation
   - Validates component integration and data flow

3. **Performance Tests** - Test system performance and scalability
   - `test_performance.py` - Concurrent processing, load testing, memory usage
   - Tests system behavior under high load
   - Validates performance requirements and resource usage

4. **Acceptance Tests** - Test real-world scenarios
   - `test_acceptance.py` - Realistic user scenarios and diary quality validation
   - Tests with authentic event data and user interactions
   - Validates diary content quality and appropriateness

5. **End-to-End Tests** - Test complete system integration
   - `test_end_to_end.py` - Full system tests with real components
   - Tests entire system from initialization to cleanup
   - Validates system behavior in production-like environment

### Test Data Generation

- `test_data_generators.py` - Comprehensive test data generators
  - `TestDataGenerator` - Generates realistic test data for all event types
  - `PerformanceTestDataGenerator` - Generates large datasets for performance testing
  - Supports all event types: weather, trending, holiday, friends, interaction, dialogue, neglect

## Running Tests

### Prerequisites

Install test dependencies:
```bash
pip install -r requirements.txt
```

### Running Individual Test Suites

```bash
# Run unit tests
python test_runner.py --suite unit

# Run integration tests  
python test_runner.py --suite integration

# Run performance tests
python test_runner.py --suite performance

# Run acceptance tests
python test_runner.py --suite acceptance

# Run end-to-end tests
python test_runner.py --suite e2e

# Run all tests
python test_runner.py --suite all
```

### Using pytest directly

```bash
# Run all tests
pytest

# Run specific test file
pytest test_integration_workflow.py

# Run with verbose output
pytest -v

# Run tests with specific markers
pytest -m "unit"
pytest -m "integration"
pytest -m "performance"

# Run tests and generate coverage report
pytest --cov=diary_agent --cov-report=html
```

### Test Runner Options

```bash
# Verbose output
python test_runner.py --verbose

# Generate detailed report
python test_runner.py --report test_report.json

# Specify test directory
python test_runner.py --test-dir /path/to/tests
```

## Test Configuration

### pytest.ini

The `pytest.ini` file contains pytest configuration:
- Test discovery patterns
- Output formatting options
- Marker definitions for test categorization
- Asyncio configuration
- Logging settings
- Warning filters

### Test Markers

Tests are categorized using pytest markers:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests  
- `@pytest.mark.performance` - Performance tests
- `@pytest.mark.acceptance` - Acceptance tests
- `@pytest.mark.end_to_end` - End-to-end tests
- `@pytest.mark.slow` - Long-running tests
- `@pytest.mark.asyncio` - Async tests
- `@pytest.mark.database` - Database-dependent tests
- `@pytest.mark.llm` - LLM API-dependent tests

## Test Requirements Coverage

The test suite covers all requirements from the specification:

### Requirement 1.1, 1.2, 1.3 - Event Processing
- ✅ Event detection and routing tests
- ✅ Multi-event processing tests
- ✅ Event type classification tests
- ✅ Error handling for unrecognized events

### Requirements 3.1-3.10 - Specialized Sub-Agents
- ✅ Weather agent tests (3.1, 3.2)
- ✅ Trending agent tests (3.3)
- ✅ Holiday agent tests (3.4)
- ✅ Friends agent tests (3.5)
- ✅ Same frequency agent tests (3.6)
- ✅ Adoption agent tests (3.7)
- ✅ Interactive agent tests (3.8)
- ✅ Dialogue agent tests (3.9)
- ✅ Neglect agent tests (3.10)

## Test Data

### Event Types Covered

1. **Weather Events**
   - `favorite_weather`, `dislike_weather`
   - `favorite_season`, `dislike_season`
   - Weather conditions, temperatures, cities

2. **Trending Events**
   - `celebration`, `disaster`
   - Trending topics, keyword classification

3. **Holiday Events**
   - `approaching_holiday`, `during_holiday`, `holiday_ends`
   - Chinese holidays, celebration activities

4. **Social Events**
   - `made_new_friend`, `friend_deleted`
   - `liked_single`, `liked_3_to_5`, `liked_5_plus`
   - `disliked_single`, `disliked_3_to_5`, `disliked_5_plus`

5. **Interaction Events**
   - `liked_interaction_once`, `liked_interaction_3_to_5_times`
   - `liked_interaction_over_5_times`, `disliked_interaction_once`
   - `disliked_interaction_3_to_5_times`, `neutral_interaction_over_5_times`

6. **Dialogue Events**
   - `positive_emotional_dialogue`, `negative_emotional_dialogue`

7. **Neglect Events**
   - `neglect_1_day_no_dialogue`, `neglect_1_day_no_interaction`
   - `neglect_3_days_no_dialogue`, `neglect_3_days_no_interaction`
   - `neglect_7_days_no_dialogue`, `neglect_7_days_no_interaction`
   - `neglect_15_days_no_interaction`, `neglect_30_days_no_dialogue`
   - `neglect_30_days_no_interaction`

### User Profiles

- Multiple user personalities (clam, lively)
- Various preference configurations
- Different emotional states and contexts

## Performance Benchmarks

### Expected Performance Metrics

- **Throughput**: ≥50 events/second under normal load
- **Concurrent Processing**: ≥10 concurrent events without degradation
- **Response Time**: ≤1 second average processing time per event
- **Memory Usage**: ≤100MB increase under high load
- **Success Rate**: ≥90% successful diary generation
- **Error Rate**: ≤5% system errors

### Load Testing Scenarios

- **Concurrent Events**: 50-1000 events processed simultaneously
- **Multi-User**: 10-50 users with concurrent events
- **Stress Testing**: High-volume event processing
- **Memory Testing**: Long-running processes with memory monitoring
- **Database Load**: Concurrent database operations

## Quality Assurance

### Diary Quality Validation

- **Format Compliance**: Title ≤6 characters, Content ≤35 characters
- **Emotional Consistency**: Emotion tags match content tone
- **Content Appropriateness**: Contextually relevant diary entries
- **Language Quality**: Proper Chinese text formatting
- **Emoji Support**: Correct emoji handling in content

### System Reliability

- **Error Recovery**: Graceful handling of component failures
- **Failover Testing**: LLM provider switching and fallback
- **Data Integrity**: Consistent data throughout processing pipeline
- **Configuration Validation**: Hot-reloading and validation testing

## Continuous Integration

### Automated Testing

The test suite is designed for CI/CD integration:

```bash
# CI test command
python test_runner.py --suite all --report ci_report.json

# Exit codes
# 0 - All tests passed
# 1 - One or more test suites failed
```

### Test Reports

Generated test reports include:
- Test execution summary
- Performance metrics
- Coverage information
- Error details and stack traces
- System health metrics

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure diary_agent package is in Python path
   - Install all test dependencies

2. **Async Test Failures**
   - Check asyncio event loop configuration
   - Verify pytest-asyncio installation

3. **Performance Test Timeouts**
   - Adjust timeout settings in pytest.ini
   - Check system resources during testing

4. **Database Test Failures**
   - Verify database connection configuration
   - Check mock database setup

### Debug Mode

Run tests with debug information:
```bash
pytest -v --tb=long --log-cli-level=DEBUG
```

## Contributing

When adding new tests:

1. Follow existing test patterns and naming conventions
2. Add appropriate pytest markers
3. Include test data generators for new event types
4. Update this README with new test coverage
5. Ensure tests are deterministic and isolated
6. Add performance benchmarks for new features

## Test Coverage Goals

- **Unit Tests**: 100% code coverage for individual components
- **Integration Tests**: All component interaction paths
- **Performance Tests**: All performance-critical operations
- **Acceptance Tests**: All user-facing scenarios
- **End-to-End Tests**: Complete system workflows

The test suite ensures the Diary Agent system meets all functional and non-functional requirements while maintaining high quality and reliability standards.