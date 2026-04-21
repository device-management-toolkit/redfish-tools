# Redfish Developer's Guide

## Table of Contents

- [Scope](#scope)
- [System Requirements](#system-requirements)
- [Quick Start](#quick-start)
- [Makefile Reference](#makefile-reference)
- [Development Workflow](#development-workflow)
- [Integration Testing](#integration-testing)
- [Additional Resources](#additional-resources)
- [Developing New Redfish Integration Tests](#developing-new-redfish-integration-tests)
- [Test Organization Best Practices](#test-organization-best-practices)
- [Advanced Testing Techniques](#advanced-testing-techniques)
- [Debugging Tests](#debugging-tests)
- [Continuous Integration](#continuous-integration)
- [Common Pitfalls](#common-pitfalls)
- [Test Maintenance](#test-maintenance)
- [Resources](#resources)
- [Examples](#examples)

## Scope

This repository focuses on Redfish OpenAPI tooling and DMTF schema sources.

- OpenAPI source schemas: `openapi/dmtf`
- Tooling scripts and Make targets: `openapi/infra`
- Local generated outputs (not committed): `openapi/artifacts`

Integration tests require the Console repository. Set `CONSOLE_REPO` to point to your local checkout:

- Example: `/path/to/console/redfish/tests/run_tests.sh`
- Run with: `make -C openapi/infra rf-integration-test CONSOLE_REPO=/path/to/console`

## System Requirements

### Base Requirements

- Operating System: Ubuntu 22.04 or later
- Go: 1.24 or higher

### Code Generation Requirements

- Python 3.x
- PyYAML package

### Integration Testing Requirements

- Node.js 16 or higher
- npm
- Newman (`npm install -g newman`)
- curl

Optional:

- `newman-reporter-htmlextra` (`npm install -g newman-reporter-htmlextra`)

## Quick Start

All commands below should be run from `openapi/infra`:

```bash
cd openapi/infra
```

Equivalent from repository root:

```bash
make -C openapi/infra <target>
```

Check environment and install dependencies:

```bash
make rf-check-tools
make rf-deps
```

Run the complete workflow:

```bash
make rf-all
```

Run integration tests:

```bash
make -C openapi/infra rf-integration-test CONSOLE_REPO=/path/to/console
```

Custom test port example:

```bash
HTTP_PORT=9090 make rf-integration-test CONSOLE_REPO=/path/to/console
```

## Makefile Reference

### Help and Diagnostics

- `make help`: show all available targets
- `make rf-check-tools`: verify required tools

### Dependency Management

- `make rf-deps`: install and verify required dependencies
- `make rf-install-missing-tools`: install only missing dependencies

### OpenAPI Processing

- `make rf-merge`: merge DMTF YAML files into a single OpenAPI spec
- `make rf-validate`: validate merged OpenAPI spec
- `make rf-generate`: generate Go code from merged OpenAPI spec
- `make rf-auth`: add Basic Auth security to OpenAPI spec and regenerate
- `make rf-metadata-generate`: generate metadata.xml from DMTF schemas

### Workflow Commands

- `make rf-all`: full pipeline (merge, generate, validate, auth, metadata)
- `make rf-clean`: remove generated files

### Testing

- `make rf-integration-test`: run Newman integration tests via sibling Console runner

From repository root:

- `make -C openapi/infra rf-integration-test CONSOLE_REPO=/path/to/console`

## Development Workflow

### Standard Development Process

1. Verify environment:

     ```bash
     make rf-check-tools
     ```

2. Install dependencies if needed:

     ```bash
     make rf-deps
     ```

3. Make API/schema changes:

     - Edit YAML in `openapi/dmtf`
     - Keep schema references consistent
     - Follow DMTF Redfish schema format

4. Regenerate local artifacts:

     ```bash
     make rf-all
     ```

5. Run tests:

     ```bash
    make -C openapi/infra rf-integration-test CONSOLE_REPO=/path/to/console
     ```

### Individual Steps (Advanced)

```bash
make rf-merge
make rf-validate
make rf-generate
make rf-auth
make rf-metadata-generate
```

## Integration Testing

### New Test Development Overview

Integration tests provide black-box HTTP API validation for Redfish behavior and regressions using Newman.

### Test Methodology

- Type: Black-box API tests
- Framework: Newman (Postman CLI)
- Test Data: Mock WSMAN repository (in sibling Console project)
- Default Port: 8181 (configurable with `HTTP_PORT`)

### Running New Tests

From this repository:

```bash
make -C openapi/infra rf-integration-test CONSOLE_REPO=/path/to/console
```

From Console repository directly:

```bash
cd /path/to/console
bash redfish/tests/run_tests.sh
```

### What Gets Tested

Endpoint coverage:

- Service Root (`/redfish/v1/`)
- OData Service Document (`/redfish/v1/odata`)
- Metadata Document (`/redfish/v1/$metadata`)
- Systems Collection (`/redfish/v1/Systems`)
- Individual System (`/redfish/v1/Systems/{id}`)
- Power Control Actions

Functional coverage:

- Authentication behavior (public and protected endpoints)
- Power actions (`On`, `ForceOff`, `ForceRestart`, `GracefulShutdown`, `PowerCycle`)
- Error handling (`400`, `401`, `404`, `405`)
- DMTF compliance checks (headers, response structure)
- Edge cases (invalid IDs, malformed payloads)

### Test Execution Flow

1. Build application from source
2. Start test server with mock data
3. Wait for readiness on `/redfish/v1/`
4. Execute Newman collection
5. Generate reports
6. Cleanup server process

### Test Reports

- CLI output: terminal output
- JSON report: `/path/to/console/redfish/tests/postman/results/newman-report.json`
- Server log: `/tmp/redfish_test_server.log`

### Troubleshooting

Server fails to start:

```bash
cat /tmp/redfish_test_server.log
lsof -i :8181
```

Tests fail:

- Verify Newman installation: `newman --version`
- Ensure no process is bound to test port
- Review server logs for startup or auth issues

## Additional Resources

Version checks:

```bash
go version
python3 --version
node --version
newman --version
```

Install Newman:

```bash
npm install -g newman
npm install -g newman-reporter-htmlextra
```

## Developing New Redfish Integration Tests

### Overview

Integration tests use Newman collections in sibling Console repository to validate Redfish API conformance with deterministic mock-backed test data.

### Test Architecture

Primary components (sibling Console repository):

1. Collection: `/path/to/console/redfish/tests/postman/redfish-collection.json`
2. Environment: `/path/to/console/redfish/tests/postman/test-environment.json`
3. Runner script: `/path/to/console/redfish/tests/run_tests.sh`
4. Mock repository: `/path/to/console/redfish/internal/mocks/mock_repo.go`

### Running Tests

Recommended from this repository:

```bash
cd openapi/infra
make rf-integration-test CONSOLE_REPO=/path/to/console
```

Direct Newman execution from sibling Console repository:

```bash
cd /path/to/console
newman run redfish/tests/postman/redfish-collection.json \
    --environment redfish/tests/postman/test-environment.json
```

### Creating New Tests

Step 1: Identify scenario

- New endpoint
- Error handling path
- Authentication behavior
- DMTF compliance behavior

Step 2: Add request in collection

```json
{
    "name": "Get System by ID",
    "event": [
        {
            "listen": "test",
            "script": {
                "type": "text/javascript",
                "exec": [
                    "pm.test('Status code is 200', function () {",
                    "  pm.response.to.have.status(200);",
                    "});"
                ]
            }
        }
    ],
    "request": {
        "method": "GET",
        "auth": {
            "type": "basic"
        },
        "url": "{{base_url}}/redfish/v1/Systems/{{system_id}}"
    }
}
```

Step 3: Add assertions

```javascript
pm.test('OData-Version header is 4.0', function () {
    pm.expect(pm.response.headers.get('OData-Version')).to.equal('4.0');
});

pm.test('Response includes standard odata fields', function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('@odata.id');
    pm.expect(jsonData).to.have.property('@odata.type');
});
```

Step 4: Organize folders

- Public Endpoints
- Protected Endpoints
- Power Control Actions
- Authentication Tests
- Error Handling Tests

Step 5: Update mock data if required

- Modify `/path/to/console/redfish/internal/mocks/mock_repo.go`

Step 6: Test locally

```bash
cd openapi/infra
make rf-integration-test CONSOLE_REPO=/path/to/console
```

Step 7: Update environment variables if needed

- Add new keys to `/path/to/console/redfish/tests/postman/test-environment.json`

## Test Organization Best Practices

### Folder Structure

```text
Redfish API Tests
|-- Public Endpoints (no auth)
|-- Protected Endpoints (Basic Auth)
|-- Power Control Actions
|-- Authentication Tests
`-- Error Handling Tests
```

### Naming Conventions

- Folder names: endpoint/function category
- Request names: Action + Resource
- Test names: precise assertion purpose

### Coverage Checklist

For each endpoint, verify:

- Success path (`200`/`202`)
- Required headers
- Response schema fields
- Unauthorized request behavior (`401`)
- Invalid request behavior (`400`)
- Not found behavior (`404`)
- Method not allowed (`405`)
- Error payload format

## Advanced Testing Techniques

### Collection Variables

```javascript
var jsonData = pm.response.json();
pm.collectionVariables.set('extracted_id', jsonData.Id);
```

### Pre-request Scripts

```javascript
var timestamp = new Date().getTime();
pm.collectionVariables.set('timestamp', timestamp);
```

### Conditional Assertions

```javascript
pm.test('Optional property validation', function () {
    var jsonData = pm.response.json();
    if (jsonData.PowerState === 'On') {
        pm.expect(jsonData).to.have.property('ProcessorSummary');
    }
});
```

### Response Time Check

```javascript
pm.test('Response time under 200ms', function () {
    pm.expect(pm.response.responseTime).to.be.below(200);
});
```

## Debugging Tests

View server logs:

```bash
cat /tmp/redfish_test_server.log
```

Run one folder only:

```bash
cd /path/to/console/redfish/tests/postman
newman run redfish-collection.json --environment test-environment.json --folder "Power Control Actions"
```

Verbose Newman output:

```bash
cd /path/to/console/redfish/tests/postman
newman run redfish-collection.json --environment test-environment.json --verbose
```

## Continuous Integration

Integration tests are designed to run in CI and fail builds if assertions fail.

Typical CI steps:

1. Checkout
2. Setup Go
3. Run test script
4. Upload test results
5. Publish summary

## Common Pitfalls

1. Authentication mismatch between endpoint and auth mode
2. Startup timing and first-request latency
3. JSON structure assumptions without null checks
4. Port conflicts on `8181`
5. Stateful test ordering interactions

## Test Maintenance

Update tests when:

1. New endpoints are added
2. Existing API behavior changes
3. Schema updates introduce or remove properties
4. Regressions are fixed (add regression tests)
5. DMTF updates require additional checks

Keep tests aligned with API spec:

- Paths should match OpenAPI definitions
- Security requirements should match endpoint behavior
- Response checks should match generated types and schema intent
- Status code assertions should include documented outcomes

## Resources

- [Newman documentation](https://learning.postman.com/docs/running-collections/using-newman-cli/command-line-integration-with-newman/)
- [Postman test scripts](https://learning.postman.com/docs/writing-scripts/test-scripts/)
- [DMTF Redfish standard](https://www.dmtf.org/standards/redfish)
- [Chai assertions](https://www.chaijs.com/api/bdd/)

## Examples

### Example 1: GET Endpoint Test

```json
{
    "name": "Get Specific System",
    "event": [
        {
            "listen": "test",
            "script": {
                "exec": [
                    "pm.test('Status code is 200', function () {",
                    "  pm.response.to.have.status(200);",
                    "});",
                    "pm.test('Body has required fields', function () {",
                    "  var body = pm.response.json();",
                    "  pm.expect(body).to.have.property('Id');",
                    "  pm.expect(body).to.have.property('Name');",
                    "});"
                ]
            }
        }
    ],
    "request": {
        "method": "GET",
        "url": "{{base_url}}/redfish/v1/Systems/{{system_id}}"
    }
}
```

### Example 2: POST Action Test

```json
{
    "name": "Reset System - ForceOff",
    "request": {
        "method": "POST",
        "header": [
            {
                "key": "Content-Type",
                "value": "application/json"
            }
        ],
        "body": {
            "mode": "raw",
            "raw": "{\"ResetType\":\"ForceOff\"}"
        },
        "url": "{{base_url}}/redfish/v1/Systems/{{system_id}}/Actions/ComputerSystem.Reset"
    }
}
```

### Example 3: Error Handling Test

```json
{
    "name": "Get System - Invalid ID",
    "request": {
        "method": "GET",
        "url": "{{base_url}}/redfish/v1/Systems/invalid-id-12345"
    },
    "event": [
        {
            "listen": "test",
            "script": {
                "exec": [
                    "pm.test('Status code is 404', function () {",
                    "  pm.response.to.have.status(404);",
                    "});",
                    "pm.test('Redfish error object exists', function () {",
                    "  var body = pm.response.json();",
                    "  pm.expect(body).to.have.property('error');",
                    "  pm.expect(body.error).to.have.property('code');",
                    "  pm.expect(body.error).to.have.property('message');",
                    "});"
                ]
            }
        }
    ]
}
```
