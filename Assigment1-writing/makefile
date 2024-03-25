.PHONY: all

all: install_pyplot make_scripts_executable


install_pyplot:
	@echo "Installing pyplot..."
	pip install matplotlib

make_scripts_executable:
	@echo "Making scripts executable..."
	chmod +x disk-benchmark-background.sh
	chmod +x network-test.sh

