# Development Guidelines

## Architecture Rules

1 Dependencies must point inward.

Agent → Tools → Application → Domain

2 Domain must not depend on infrastructure.

3 Side effects belong to infrastructure.

4 Agents orchestrate but do not contain business logic.

---

## Coding Style

Prefer small functions.

Prefer dataclasses for data structures.

Avoid large utility modules.

Use explicit dependency injection.

---

## Testing

Domain functions should be unit tested.

Infrastructure should be tested using integration tests or fakes.

Agents should be tested using mocked tools.

---

## Naming

Agents: *Agent  
Tools: *Tool  
Use Cases: *UseCase  
Ports: *Gateway or *Store