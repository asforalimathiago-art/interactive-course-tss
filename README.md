# Interactive Course with Threshold Secret Sharing (TSS)

An interactive learning platform that combines adaptive questionnaires with threshold secret sharing (TSS) for secure event management.

## Features

- **Adaptive Learning**: Dynamic question selection based on user role and performance
- **Threshold Secret Sharing**: Secure event storage with multi-party reconstruction
- **RESTful API**: FastAPI-based backend with automatic documentation
- **Type-Safe**: Fully typed Python code with Pydantic models
- **Secure**: Hardened crypto implementation with clear error handling

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Running the Server

```bash
uvicorn engine_reference:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`.

## API Endpoints

### Questionnaire Endpoints

- `POST /questionnaire/next` - Get next question for a session
- `POST /questionnaire/submit` - Submit an answer and get feedback

### TSS Endpoints

- `POST /tss/event` - Create a TSS-protected event
- `POST /tss/reconstruct` - Reconstruct a TSS-protected event

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black .
```

### Linting

```bash
flake8 .
```

### Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
```

## Architecture

- **engine_reference.py**: Main application with API endpoints and business logic
- **tss_crypto.py**: Threshold secret sharing and encryption utilities
- **adaptive_rules.yaml**: Rules for adaptive question selection
- **question_bank.csv**: Question database

## Security

This project uses:
- AES-GCM for payload encryption
- Shamir's Secret Sharing for key splitting
- Type-safe interfaces with clear error messages
- Logging for audit trails

## License

See LICENSE file for details.

## Contributing

See CONTRIBUTING.md for guidelines.
