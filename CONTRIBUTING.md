# Contribution guidelines

Contributing to this project should be as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features

## Github is used for everything

Github is used to host code, to track issues and feature requests, as well as accept pull requests.

Pull requests are the best way to propose changes to the codebase.

1. Fork the repo and create your branch from `main`.
2. If you've changed something, update the documentation.
3. Make sure your code lints (using black).
4. Issue that pull request!

## Report bugs using Github's [issues](https://github.com/mmornati/home-assistant-csnet-home/issues)

GitHub issues are used to track public bugs.  
Report a bug by [opening a new issue](https://github.com/mmornati/home-assistant-csnet-home/issues/new/choose); it's that easy!

## Write bug reports with detail, background, and sample code

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can.
- Show logs
  - Ideally enable debug logging in Home Assistant
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

## Enable debug logging in Home Assistant

To enable, add this or modify the logging section of your Home Assistant configuration.yaml:
```yaml
logger:
  default: warning
  logs:
    custom_components.csnet_home: debug
```

## Development Environment Setup

To setup your development environment you can follow the documentation available in this [README](tests/README.md) file

## Local Testing

### Integration Testing (Recommended)

The easiest way to test your changes locally is using our automated integration testing setup:

```bash
# Start Home Assistant with your changes
./scripts/integration-test.sh start

# View logs
./scripts/integration-test.sh logs

# Stop when done
./scripts/integration-test.sh stop
```

This will:
- Start a Home Assistant instance in Docker
- Automatically mount your custom component
- Provide a clean test environment
- Allow you to test the full user experience

**Benefits:**
- ✅ One command to start testing
- ✅ Isolated from your production setup
- ✅ Hot-reload on restart
- ✅ Pre-configured environment
- ✅ Easy cleanup

📖 **Full documentation:** See [INTEGRATION_TESTING.md](INTEGRATION_TESTING.md) for the complete guide.

### Unit Tests

Always run unit tests before submitting a PR:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=custom_components/csnet_home --cov-report=html

# Or using Make
make test-unit
```

### Manual Docker Setup (Alternative)

If you prefer manual setup:

```bash
docker run --rm -d --name home-assistant \
  -v $(pwd)/custom_components/csnet_home:/config/custom_components/csnet_home \
  -v ./test_config:/config \
  -p 8123:8123 \
  homeassistant/home-assistant
```

Access Home Assistant at http://localhost:8123


## License

By contributing, you agree that your contributions will be licensed under its Apache v2 [License](LICENSE).