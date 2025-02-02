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

## Local tests

To test your changes locally, without working in your real HomeAssistant environment, you can start a HA instance in a docker container.

```
docker run --rm -d --name home-assistant -v /Users/mmornati/hassio-config:/config -p 8080:8123 homeassistant/home-assistant
```

* within the `/Users/mmornati/hassio-config` (change it accordingly to your setup) HA will create all the necessary base configuration files
* access to Home Assistant using the `http://localhost:8080` URL. After the first startup (with the configuration folder empty) you need to go through the first HomeAssistant configuration.


## License

By contributing, you agree that your contributions will be licensed under its Apache v2 [License](LICENSE).