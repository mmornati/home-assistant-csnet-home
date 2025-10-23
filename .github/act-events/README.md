# Act Event Payloads

This directory contains test event payloads for use with [act](https://github.com/nektos/act) to test workflows locally.

## Usage

### Test Pull Request Workflow
```bash
act pull_request -W .github/workflows/validate.yaml -e .github/act-events/pull_request.json
```

### Test Workflow Dispatch (Release)
```bash
act workflow_dispatch -W .github/workflows/release.yaml -e .github/act-events/workflow_dispatch.json
```

### Test Push Workflow
```bash
act push -W .github/workflows/validate.yaml -e .github/act-events/push.json
```

## Event Files

- **pull_request.json**: Simulates a pull request event
- **workflow_dispatch.json**: Simulates manual workflow trigger with version input
- **push.json**: Simulates a push to main branch

## Customization

You can modify these JSON files to test different scenarios:
- Change PR numbers and titles
- Modify version inputs
- Test different branches

## Full GitHub Event Structure

For complete event structures, see:
- https://docs.github.com/en/webhooks/webhook-events-and-payloads
- https://github.com/nektos/act#example-event-payloads

