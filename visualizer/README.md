# State Space Visualizer v0.1

STATUS: OPERATIONAL

Part of the Freedeon Engine project.

---

## Purpose

The State Space Visualizer provides an observable representation of:

* Connectivity
* Reachability
* Discoverability

as defined by Freedeon Engine v0.1.

The Visualizer does not define ontology.

The Engine remains the single source of truth.

---

## Core Principle

The UI represents.

The Engine decides.

---

## Engine Concepts

### Connectivity

Question:

Does a path exist between two states?

Engine Function:

exists_path()

Depends on:

* States
* Transitions

Does not depend on:

* Observer
* Knowledge
* Capabilities

---

### Reachability

Question:

Can a specific EON physically traverse a path?

Engine Function:

can_reach()

Depends on:

* States
* Transitions
* Capabilities

---

### Discoverability

Question:

Can a specific EON infer the existence of a path?

Engine Function:

can_discover()

Depends on:

* Information
* Known Information
* Inference Rules

Does not depend on:

exists_path()

---

## Visual Categories

### Reachable

The destination can be reached by the selected EON.

### Discoverable

The destination can be inferred by the selected EON.

### Connected

A path exists but is neither reachable nor discoverable.

### Abyss

No path exists.

---

## Limitations

The Visualizer is an observational tool.

It does not prove ontology.

It visualizes the output of Engine v0.1.

Differences between Engine State and Visual Representation may exist and should be treated as observations rather than ontology changes.

---

## Visual Tests

### VISUAL TEST 001

STATUS: PASSED

Validated operational separation between:

Reachability

and

Discoverability.

---

### VISUAL TEST 002

STATUS: PASSED

Validated that Information affects Discoverability when Topology and Capability remain constant.

---

## Known Observation

PSO-16C-002

The Engine distinguishes:

Reachable + Discoverable

from

Reachable + Not Discoverable

but the current Visualizer renders both as:

Reachable

when can_reach = True.

This observation is under analysis.

---

## Status

Visualizer v0.1

Operational.

No ontology is implemented here.

Ontology lives in the Engine.
