ifeq ($(OS),Windows_NT)
PYTHON ?= python
else
PYTHON ?= python3
endif

.DEFAULT_GOAL := help
.NOTPARALLEL:
.PHONY: help setup build test check fetch status baseline ports doctor clean menuconfig flash monitor flash-monitor full dev port

help setup build test check fetch status baseline ports doctor clean menuconfig flash monitor flash-monitor full:
	$(PYTHON) TOOLCONF/dev.py $@

dev:
	$(PYTHON) TOOLCONF/dev.py dev "$(MODULE)"

port:
	$(PYTHON) TOOLCONF/dev.py port "$(PORT)"
