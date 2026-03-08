# ADR 001: Initial Agent Architecture

Status: accepted

## Context

The project requires a flexible architecture to implement automation agents for different domains such as trading workflows and theater organization tasks.

The architecture must support:

- testability
- clear responsibilities
- future extension to multiple agents

## Decision

A layered architecture is used:

Agent → Tools → Application → Domain → Infrastructure

Dependency Injection is implemented manually via bootstrap modules.

Agents orchestrate workflows but contain no business logic.

Tools encapsulate single operations and are reusable.

Domain logic is implemented as pure functions whenever possible.

## Consequences

Advantages:

- easy testing
- clear structure
- minimal coupling
- reusable components

Trade-offs:

- more files
- slightly higher initial complexity