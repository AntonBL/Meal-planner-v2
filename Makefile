.PHONY: help restart logs logs-err logs-out status clean test lint format install

# Default target
help:
	@echo "AI Recipe Planner - Makefile Commands"
	@echo ""
	@echo "Production Operations:"
	@echo "  make restart    - Restart the application and check logs"
	@echo "  make status     - Check application status"
	@echo "  make logs       - View error logs (last 50 lines)"
	@echo "  make logs-err   - View error logs (last 50 lines)"
	@echo "  make logs-out   - View output logs (last 50 lines)"
	@echo "  make logs-tail  - Tail error logs in real-time"
	@echo ""
	@echo "Development:"
	@echo "  make install    - Install dependencies with uv"
	@echo "  make lint       - Run linter (ruff)"
	@echo "  make format     - Format code with ruff"
	@echo "  make test       - Run tests with pytest"
	@echo "  make clean      - Clean Python cache files"
	@echo ""
	@echo "Environment:"
	@echo "  make env-edit   - Edit .env file"
	@echo "  make env-show   - Show current environment variables (sanitized)"

# Production Operations
restart:
	@echo "🔄 Restarting meal-planner service..."
	@supervisorctl restart meal-planner
	@sleep 3
	@echo ""
	@echo "📊 Service Status:"
	@supervisorctl status meal-planner
	@echo ""
	@echo "📋 Recent Error Logs:"
	@tail -30 /var/log/meal-planner.err.log || echo "No error logs"
	@echo ""
	@echo "✅ Checking for errors in output log:"
	@tail -50 /var/log/meal-planner.out.log | grep -i -E "(error|warning|exception|traceback)" || echo "✅ No errors found"

status:
	@supervisorctl status meal-planner

logs:
	@tail -50 /var/log/meal-planner.err.log

logs-err:
	@tail -50 /var/log/meal-planner.err.log

logs-out:
	@tail -50 /var/log/meal-planner.out.log

logs-tail:
	@tail -f /var/log/meal-planner.err.log

# Development
install:
	@echo "📦 Installing dependencies with uv..."
	@uv pip install -r requirements.txt
	@echo "✅ Dependencies installed"

lint:
	@echo "🔍 Running linter..."
	@venv/bin/ruff check lib/ app.py pages/

format:
	@echo "✨ Formatting code..."
	@venv/bin/ruff format lib/ app.py pages/
	@venv/bin/ruff check --fix lib/ app.py pages/

test:
	@echo "🧪 Running tests..."
	@venv/bin/pytest --cov=lib

clean:
	@echo "🧹 Cleaning Python cache files..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleaned"

# Environment
env-edit:
	@nano .env

env-show:
	@echo "Current environment variables (passwords hidden):"
	@cat .env | sed 's/\(PASSWORD=\).*/\1***HIDDEN***/' | sed 's/\(API_KEY=sk-ant-[^-]*-\).*$$/\1***HIDDEN***/'
