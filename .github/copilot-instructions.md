# Asterisk Home Assistant Integration

This is a Home Assistant custom integration that connects to Asterisk PBX systems via AMI (Asterisk Manager Interface) to provide device state monitoring, DTMF detection, and telephony event tracking. The integration creates binary sensors and sensors for SIP/PJSIP devices discovered through AMI.

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

### Bootstrap and Setup
- **Python Version**: Requires Python 3.10.6+ (confirmed working with Python 3.12.3)
- **Environment Setup**:
  ```bash
  python -m pip install --upgrade pip
  pip install -r dev-requirements.txt
  ```
  - **Install time**: ~1 minute. NEVER CANCEL. Use timeout of 10+ minutes.
  - **Dependencies include**: asterisk-ami, pytest-homeassistant-custom-component, pre-commit, Home Assistant core
  - **Network issues**: May fail with timeout errors to PyPI due to firewall/network limitations. Retry or use local package cache.

### Development Workflow
- **Install pre-commit hooks** (required for clean commits):
  ```bash
  pre-commit install
  ```
  - **Install time**: ~1 second
- **Format code before committing**:
  ```bash
  black custom_components tests
  isort custom_components tests
  ```
  - **Format time**: ~1 second each. Always run both commands.
  - **Warning**: isort shows deprecation warnings about config options but works correctly.
- **Run tests**:
  ```bash
  pytest -v
  ```
  - **Test time**: ~4 seconds. NEVER CANCEL. Use timeout of 30+ seconds.
  - **Coverage**: Tests cover config flow only. Most sensor tests are commented out.
- **Lint code**:
  ```bash
  flake8 custom_components tests
  ```
  - **Lint time**: ~1 second
  - **Known issue**: tests/test_sensors.py has unused imports (all tests are commented out)

### Validation Requirements
- **ALWAYS run formatting and linting before commits**:
  ```bash
  black custom_components tests && isort custom_components tests && flake8 custom_components tests
  ```
- **ALWAYS run tests after code changes**:
  ```bash
  pytest -v
  ```
- **CI Requirements**: Code must pass hassfest validation (Home Assistant manifest validator) and pytest on Python 3.10.11 and 3.11.3

## Manual Testing Scenarios

Since this integration connects to external Asterisk PBX systems, manual testing requires:

1. **Config Flow Testing**: Verify the integration can be added through Home Assistant UI
   - Test with valid AMI credentials (host, port 5038, username, password)
   - Test with invalid credentials to ensure proper error handling
   
2. **Device Discovery**: After successful AMI connection, verify that:
   - SIP devices are discovered and added as entities
   - PJSIP devices are discovered and added as entities
   - Device states are properly mapped (NOT_INUSE → "Not in use", etc.)

3. **Real-time Updates**: Monitor that device state changes from Asterisk are reflected in Home Assistant:
   - Device state changes (available, busy, ringing, etc.)
   - DTMF digit detection (sent/received)
   - Connected line information updates

**Note**: Manual testing requires a running Asterisk PBX with AMI enabled. Mock testing is available through MockAMIClient in tests.

## Project Structure

### Key Directories
- `custom_components/asterisk/`: Main integration code
  - `__init__.py`: Entry point, device discovery, AMI connection setup
  - `config_flow.py`: UI configuration flow for adding integration
  - `const.py`: Constants, device states, icons mapping
  - `base.py`: Base entity class for Asterisk devices
  - `sensor.py`: Sensor entities (device state, DTMF, connected line)
  - `binary_sensor.py`: Binary sensor entities (AMI connection, device registration)
  - `manifest.json`: Integration metadata (version 1.0.4, requires asterisk-ami==0.1.6)

### Test Structure
- `tests/`: Test suite using pytest-homeassistant-custom-component
  - `conftest.py`: Test fixtures and configuration
  - `test_config_flow.py`: Config flow integration test (1 passing test)
  - `test_sensors.py`: Sensor tests (currently all commented out)
  - `mock_ami_client.py`: Mock AMI client for testing

### Configuration Files
- `setup.cfg`: pytest, coverage, flake8, isort, mypy configuration
- `.pre-commit-config.yaml`: Code quality hooks (black, isort, flake8)
- `dev-requirements.txt`: Development dependencies
- `.python-version`: Python 3.10.6 (pyenv configuration)

## Common Tasks

### Adding New Sensors
1. Add sensor class to `sensor.py` or `binary_sensor.py`
2. Inherit from `AsteriskDeviceEntity` and appropriate sensor base class
3. Register AMI event listeners in `__init__` method
4. Implement `handle_event` method for real-time updates
5. Add entity to setup function in platform file

### Modifying Device Discovery
- Edit `async_setup_entry` function in `__init__.py`
- Modify `create_PJSIP_device` or `create_SIP_device` event handlers
- Update device completion logic in `devices_complete` function

### Configuration Changes
- Update `manifest.json` for version bumps or dependency changes
- Modify `config_flow.py` for new configuration parameters
- Update `const.py` for new constants or state mappings

## Troubleshooting

### Common Issues
- **Import errors**: Ensure `pip install -r dev-requirements.txt` completed successfully
- **AMI connection failures**: Verify Asterisk AMI is enabled and credentials are correct
- **Device not discovered**: Check Asterisk SIP/PJSIP configuration and module loading
- **Pre-commit failures**: May fail due to network timeouts during hook installation
- **Flake8 unused imports**: Known issue in test_sensors.py (tests are commented out)

### Development Notes
- This integration polls Asterisk AMI for device states
- Real-time updates use AMI event listeners
- Device registration requires both SIP and PJSIP modules to be loaded in Asterisk
- Integration supports authentication and automatic reconnection to AMI

### CI Pipeline
- **hassfest.yml**: Validates Home Assistant integration manifest
- **tests.yaml**: Runs pytest on multiple Python versions (3.10.11, 3.11.3)
- Both workflows trigger on push and pull requests

## Installation for End Users
This integration is distributed through HACS (Home Assistant Community Store):
1. Add custom repository URL to HACS
2. Install through HACS interface
3. Restart Home Assistant
4. Add integration through Integrations page with AMI connection details