# PSO-16C-002 Analysis

STATUS: OPEN

Origin:

VISUAL TEST 002

Observation:

The Engine distinguishes:

Reachable + Discoverable

from

Reachable + Not Discoverable

but the current Visualizer renders both as:

Reachable

when can_reach = True.

Question:

How can visual representation preserve the distinction between:

Reachable + Discoverable

and

Reachable + Not Discoverable

without changing the ontology or the Engine?

Constraints:

* No changes to Engine v0.1
* No ontology changes
* No Discoverability changes
* Visualization layer only

Status:

Open design question.

No implementation authorized.
