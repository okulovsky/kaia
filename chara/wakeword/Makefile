PYTHON ?= python
BRAINBOX_URL ?= http://127.0.0.1:8090
CONFIG ?= learn-settings.json
OUTPUT ?= ../../temp/wakeword/smoke-host-001

TRAIN_CONFIG ?= $(CONFIG)
SCOPE ?= full
DATASET ?=

.PHONY: check setup run generate train report
check setup run generate train report:
	"$(PYTHON)" scripts/manage.py $@ --brainbox-url "$(BRAINBOX_URL)" --config "$(CONFIG)" --output "$(OUTPUT)" --training-config "$(TRAIN_CONFIG)" --scope "$(SCOPE)" $(if $(strip $(DATASET)),--dataset "$(DATASET)",)
