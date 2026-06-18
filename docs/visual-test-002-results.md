# VISUAL TEST 002 — Results

STATUS: PASSED

Date: 2026-06-18

## Experimental Question

Does Information affect Discoverability when Topology and Capability remain constant?

## Observed Results

| EON   | exists_path | can_reach | can_discover | visual_category |
| ----- | ----------- | --------- | ------------ | --------------- |
| ALPHA | True        | True      | False        | Reachable       |
| BETA  | True        | True      | True         | Reachable       |
| GAMMA | True        | True      | False        | Reachable       |

## Critical Comparison

BETA and GAMMA share:

* Same topology
* Same capabilities
* Same inference rule

Difference:

BETA:
known_information = {claims_path:A:F}

GAMMA:
known_information = {}

Observed:

BETA:
can_discover(A,F) = True

GAMMA:
can_discover(A,F) = False

## Conclusion

Under Engine v0.1:

Discoverability depends on:

Information + Inference Rules

The Null Hypothesis:

"Knowledge does not affect Discoverability"

was not supported by the observed results.

## Secondary Observation

The Engine distinguishes:

Reachable + Discoverable

from

Reachable + Not Discoverable

but the current Visualizer renders both as:

Reachable

when can_reach = True.

This is a visualization observation, not an ontology observation.

## Status

VISUAL TEST 002 PASSED
