# Redfish API Generation Makefile
# This file contains all targets for Redfish API specification processing,
# code generation, and validation.

# Redfish API Generation Variables
MAIN_OPENAPI := ../dmtf/openapi.yaml
ARTIFACTS_DIR := ../artifacts
MERGED_OPENAPI := $(ARTIFACTS_DIR)/redfish-openapi.yaml
GENERATED_DIR := $(ARTIFACTS_DIR)/generated
GENERATED_SPEC := $(GENERATED_DIR)/spec.gen.go
GENERATED_TYPES := $(GENERATED_DIR)/types.gen.go
GENERATED_SERVER := $(GENERATED_DIR)/server.gen.go
MERGE_SCRIPT := merge-redfish-openapi.py
INFRA_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
# Console repo path - required: make rf-integration-test CONSOLE_REPO=/path/to/console
CONSOLE_REPO ?=
# Tool versions
OAPI_CODEGEN_VERSION := github.com/oapi-codegen/oapi-codegen/v2/cmd/oapi-codegen@v2.5.1

# Source YAML files in ../dmtf directory
YAML_SOURCES := $(wildcard ../dmtf/*.yaml)

# Required tools for Redfish API generation
REDFISH_REQUIRED_TOOLS := python3 go oapi-codegen swagger-cli
PYTHON_TOOLS := PyYAML

# Tool check functions
define check_tool
$(shell command -v $(1) >/dev/null 2>&1 && echo "✅" || echo "❌")
endef

define check_python_package
$(shell python3 -c "import $(1)" 2>/dev/null && echo "✅" || echo "❌")
endef

# OS check function for Ubuntu
define check_ubuntu
	@if [ ! -f /etc/os-release ]; then \
		echo "❌ Cannot detect OS. /etc/os-release not found."; \
		echo "💡 Redfish API targets are only supported on Ubuntu systems."; \
		exit 1; \
	fi; \
	if ! grep -qi "ubuntu" /etc/os-release; then \
		echo "❌ Redfish API targets are only supported on Ubuntu systems."; \
		echo "🔍 Current OS: $$(grep '^PRETTY_NAME=' /etc/os-release | cut -d'=' -f2 | tr -d '\"' || echo 'Unknown')"; \
		echo "💡 Please use an Ubuntu system to run Redfish API generation targets."; \
		exit 1; \
	fi; \
	echo "✅ Ubuntu detected: $$(grep '^PRETTY_NAME=' /etc/os-release | cut -d'=' -f2 | tr -d '\"')"
endef

# HELP =================================================================================================================
# This will output the help for each task
.PHONY: help

help: ## Display this help screen
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Redfish API Generation

rf-merge: ### Merge YAML files into single OpenAPI specification (local artifacts only)
	$(call check_ubuntu)
	@echo "🔄 Merging YAML files into single OpenAPI specification..."
	python3 $(MERGE_SCRIPT)
	@echo "✅ Merged OpenAPI spec created in artifacts: $(MERGED_OPENAPI)"
.PHONY: rf-merge

$(MERGED_OPENAPI): $(YAML_SOURCES) $(MERGE_SCRIPT)
	@echo "🔄 Merging YAML files into single OpenAPI specification..."
	python3 $(MERGE_SCRIPT)
	@echo "✅ Merged OpenAPI spec created in artifacts: $(MERGED_OPENAPI)"

rf-generate: $(GENERATED_SPEC) $(GENERATED_TYPES) $(GENERATED_SERVER) ### Generate Go server code into local artifacts
	$(call check_ubuntu)
.PHONY: rf-generate

$(GENERATED_SPEC): $(MERGED_OPENAPI)
	$(call check_ubuntu)
	@echo "🔄 Generating OpenAPI spec Go code..."
	@mkdir -p $(GENERATED_DIR)
	oapi-codegen -generate spec -o $(GENERATED_SPEC) -package generated $(MERGED_OPENAPI)
	@echo "✅ Generated spec code: $(GENERATED_SPEC)"

$(GENERATED_TYPES): $(MERGED_OPENAPI)
	$(call check_ubuntu)
	@echo "🔄 Generating types Go code..."
	@mkdir -p $(GENERATED_DIR)
	oapi-codegen -generate types -o $(GENERATED_TYPES) -package generated $(MERGED_OPENAPI)
	@echo "✅ Generated types code: $(GENERATED_TYPES)"

$(GENERATED_SERVER): $(MERGED_OPENAPI)
	$(call check_ubuntu)
	@echo "🔄 Generating server Go code..."
	@mkdir -p $(GENERATED_DIR)
	oapi-codegen -generate gin,strict-server -o $(GENERATED_SERVER) -package generated $(MERGED_OPENAPI)
	@echo "✅ Generated server code: $(GENERATED_SERVER)"

rf-deps: ### Install dependencies and required tools for Redfish API
	$(call check_ubuntu)
	@echo "🔧 Installing and verifying all dependencies..."
	@$(MAKE) rf-install-missing-tools
	@echo "✅ All dependencies installed and verified"
.PHONY: rf-deps

rf-check-tools: ### Check if all required tools are available
	$(call check_ubuntu)
	@echo "🔧 Detailed Tool Status Report"
	@echo "==============================="
	@echo ""
	@echo "Required Tools:"
	@missing_tools=""; \
	for tool in $(REDFISH_REQUIRED_TOOLS); do \
		echo -n "  $$tool: "; \
		if command -v $$tool >/dev/null 2>&1; then \
			case $$tool in \
				python3) echo "✅ $$(python3 --version 2>&1)";; \
				go) echo "✅ $$(go version | cut -d' ' -f3-4)";; \
				oapi-codegen) echo "✅ $$(oapi-codegen -version 2>/dev/null || echo 'installed')";; \
				swagger-cli) echo "✅ $$(swagger-cli --version 2>/dev/null || echo 'installed')";; \
				*) echo "✅ installed";; \
			esac; \
		else \
			echo "❌ Missing"; \
			missing_tools="$$missing_tools $$tool"; \
		fi; \
	done; \
	echo ""; \
	echo "Python Packages:"; \
	echo -n "  PyYAML: "; \
	if python3 -c "import yaml; print('✅ version', yaml.__version__)" 2>/dev/null; then \
		true; \
	else \
		echo "❌ Missing"; \
	fi; \
	echo ""; \
	if [ -n "$$missing_tools" ]; then \
		echo "❌ Missing required tools:$$missing_tools"; \
		echo "💡 Run 'make rf-deps' to install missing dependencies"; \
		exit 1; \
	else \
		echo "✅ All required tools are available!"; \
	fi
.PHONY: rf-check-tools

rf-install-missing-tools: ### Install missing tools automatically
	$(call check_ubuntu)
	@echo "🛠️  Installing missing tools..."

	# Check and install Go
	@if ! command -v go >/dev/null 2>&1; then \
		echo "❌ Go not found. Please install Go first: https://golang.org/doc/install"; \
		exit 1; \
	fi

	# Check and install Python3
	@if ! command -v python3 >/dev/null 2>&1; then \
		echo "Installing Python3..."; \
		if command -v apt-get >/dev/null 2>&1; then \
			sudo apt-get update && sudo apt-get install -y python3 python3-pip; \
		elif command -v yum >/dev/null 2>&1; then \
			sudo yum install -y python3 python3-pip; \
		else \
			echo "❌ Please install Python3 manually"; \
			exit 1; \
		fi; \
	fi

	# Install Python packages
	@if ! python3 -c "import yaml" 2>/dev/null; then \
		echo "Installing PyYAML..."; \
		pip3 install PyYAML --user 2>/dev/null || python3 -m pip install PyYAML --user; \
	fi

	# Install oapi-codegen
	@if ! command -v oapi-codegen >/dev/null 2>&1; then \
		echo "Installing oapi-codegen from $(OAPI_CODEGEN_VERSION)..."; \
		go install $(OAPI_CODEGEN_VERSION); \
	fi

	# Install swagger-cli
	@if ! command -v swagger-cli >/dev/null 2>&1; then \
		echo "Installing swagger-cli..."; \
		if command -v npm >/dev/null 2>&1; then \
			npm install -g @apidevtools/swagger-cli; \
		else \
			echo "❌ npm not found. Please install Node.js and npm first, then run:"; \
			echo "   npm install -g @apidevtools/swagger-cli"; \
			exit 1; \
		fi; \
	fi

	@echo "✅ All required tools installed successfully"
.PHONY: rf-install-missing-tools

rf-validate: $(MERGED_OPENAPI) ### Validate OpenAPI specification
	$(call check_ubuntu)
	@echo "🔄 Validating OpenAPI specification..."
	@if command -v swagger-cli >/dev/null 2>&1; then \
		swagger-cli validate $(MERGED_OPENAPI) && echo "✅ OpenAPI spec is valid"; \
	else \
		echo "⚠️  swagger-cli not found, skipping validation"; \
		echo "💡 Install swagger-cli: npm install -g @apidevtools/swagger-cli"; \
	fi
.PHONY: rf-validate

rf-clean: ### Clean local artifacts
	@echo "🧹 Cleaning generated files..."
	@rm -rf $(ARTIFACTS_DIR)
	@echo "✅ Cleaned local artifacts"
.PHONY: rf-clean

rf-auth: ### Add Basic Auth to OpenAPI spec and regenerate Go code
	@echo "🔐 Adding Basic Authentication to Redfish OpenAPI spec..."
	python3 add-basic-auth.py
	@echo "✅ Basic Authentication added"
.PHONY: rf-auth

rf-all: rf-merge rf-generate rf-validate rf-auth rf-metadata-generate ### Run all Redfish API generation steps
	@echo "✅ All Redfish API generation steps completed"
.PHONY: rf-all

rf-metadata-generate: ### Generate metadata.xml from DMTF schemas (local artifacts only)
	@echo "📥 Generating metadata.xml in artifacts from DMTF schemas..."
	python3 metadata-generate.py
	@echo "✅ Metadata generation completed"
.PHONY: rf-metadata-generate

rf-integration-test: ### Run Redfish API integration tests with Newman
	@echo "🧪 Running Redfish API integration tests..."
	@echo "Console repo: $(CONSOLE_REPO)"
	@if [ -z "$(CONSOLE_REPO)" ]; then \
		echo "❌ CONSOLE_REPO is not set."; \
		echo "💡 Example:"; \
		echo "   make rf-integration-test CONSOLE_REPO=/path/to/console"; \
		exit 1; \
	fi; \
	TEST_RUNNER="$(CONSOLE_REPO)/redfish/tests/run_tests.sh"; \
	if [ -f "$$TEST_RUNNER" ]; then \
		cd "$(CONSOLE_REPO)" && bash redfish/tests/run_tests.sh; \
	else \
		echo "❌ Integration test runner not found at $$TEST_RUNNER"; \
		echo "💡 Set CONSOLE_REPO to your Console checkout:"; \
		echo "   make rf-integration-test CONSOLE_REPO=/path/to/console"; \
		exit 1; \
	fi
.PHONY: rf-integration-test
