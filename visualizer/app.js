/* ===========================================================
   State Space Visualizer v0.1 — app.js

   ARCHITECTURAL RULE: The UI represents. The Engine decides.
   SINGLE SOURCE OF TRUTH: engine.py exists in exactly one place
   on disk. This file does not contain a copy of it. It fetches
   the real file at runtime and executes it as-is in Pyodide.

   This file never reimplements exists_path / can_reach / can_discover.
   If you find yourself writing a graph traversal in this file to
   "decide" something — stop. That decision belongs in engine.py.

   RUNTIME REQUIREMENT: this fetch only works when the page is
   served over http(s) (e.g. `python3 -m http.server`). Opening
   index.html directly as a file:// URL will fail due to browser
   CORS restrictions on local file fetches — this is a browser
   security constraint, not a Freedeon limitation.
   =========================================================== */

const ENGINE_PATH = "./engine.py";

async function loadEngineSource() {
  const response = await fetch(ENGINE_PATH);
  if (!response.ok) {
    throw new Error(
      `Could not fetch ${ENGINE_PATH} (status ${response.status}). ` +
      `If you opened this file directly (file://), serve it over http instead, ` +
      `e.g.: python3 -m http.server, then open http://localhost:8000/`
    );
  }
  return await response.text();
}

// Rendering-only helper. Not part of the ontology: it does not decide
// exists_path, can_reach, or can_discover. It is appended after the
// real engine.py is loaded, and only describes a path already known
// to exist (used to draw the "traversed" line). If engine.py grows
// its own path-reconstruction helper, this should be deleted in
// favor of importing that instead of keeping a second one here.
const RENDER_HELPER_SOURCE = `
def shortest_path_nodes(transitions, a, b):
    if a == b:
        return [a]
    adjacency = {}
    for t in transitions:
        adjacency.setdefault(t.from_state, set()).add(t.to_state)

    from collections import deque
    prev = {a: None}
    queue = deque([a])
    while queue:
        current = queue.popleft()
        if current == b:
            break
        for neighbor in adjacency.get(current, ()):
            if neighbor not in prev:
                prev[neighbor] = current
                queue.append(neighbor)
    if b not in prev:
        return []
    path = []
    node = b
    while node is not None:
        path.append(node)
        node = prev[node]
    path.reverse()
    return path
`;

// ---------------------------------------------------------------
// 2. Demo scenario: Test Visual 001
//    Graph: A - B - C | D   (D disconnected => Abyss)
//    Lives in scenario.py, not here, for the same reason engine.py
//    is fetched rather than embedded: one definition, one place.
// ---------------------------------------------------------------

const SCENARIO_PATH = "./scenario.py";

async function loadScenarioSource() {
  const response = await fetch(SCENARIO_PATH);
  if (!response.ok) {
    throw new Error(`Could not fetch ${SCENARIO_PATH} (status ${response.status}).`);
  }
  return await response.text();
}

// ---------------------------------------------------------------
// 3. Pyodide bootstrap
// ---------------------------------------------------------------

let pyodide = null;
let STATE_IDS = [];
let EON_NAMES = [];

const statusDot = document.getElementById("status-dot");
const statusText = document.getElementById("status-text");

async function boot() {
  try {
    pyodide = await loadPyodide();

    const engineSource = await loadEngineSource();
    const scenarioSource = await loadScenarioSource();

    await pyodide.runPythonAsync(engineSource);       // engine.py, fetched as-is
    await pyodide.runPythonAsync(RENDER_HELPER_SOURCE); // rendering-only, not ontology
    await pyodide.runPythonAsync(scenarioSource);      // scenario.py, fetched as-is

    STATE_IDS = pyodide.globals.get("state_ids").toJs();
    EON_NAMES = Array.from(pyodide.globals.get("eons").toJs().keys());

    const transitionPairsRaw = pyodide.runPython(`
import json
json.dumps([[t.from_state, t.to_state] for t in transitions])
    `);
    TRANSITION_PAIRS = JSON.parse(transitionPairsRaw);
    LAYOUT = computeLayout(STATE_IDS, TRANSITION_PAIRS);

    populateSelect("select-eon", EON_NAMES);
    populateSelect("select-origin", STATE_IDS);
    populateSelect("select-destination", STATE_IDS, STATE_IDS[2]); // default C

    statusDot.classList.add("is-ready");
    statusText.textContent = "engine.py loaded (fetched, not embedded)";

    attachListeners();
    renderGraph();
    evaluateSelection();
  } catch (err) {
    statusDot.classList.add("is-error");
    statusText.textContent = "engine failed to load — see console";
    console.error(err);
  }
}

function populateSelect(id, options, defaultValue) {
  const el = document.getElementById(id);
  el.innerHTML = "";
  for (const opt of options) {
    const o = document.createElement("option");
    o.value = opt;
    o.textContent = opt;
    if (defaultValue && opt === defaultValue) o.selected = true;
    el.appendChild(o);
  }
}

function attachListeners() {
  document.getElementById("select-eon").addEventListener("change", evaluateSelection);
  document.getElementById("select-origin").addEventListener("change", evaluateSelection);
  document.getElementById("select-destination").addEventListener("change", evaluateSelection);
}

// ---------------------------------------------------------------
// 4. Ask the engine. Never decide here.
// ---------------------------------------------------------------

function evaluateSelection() {
  if (!pyodide) return;

  const eonName = document.getElementById("select-eon").value;
  const origin = document.getElementById("select-origin").value;
  const destination = document.getElementById("select-destination").value;

  pyodide.globals.set("_eon_name", eonName);
  pyodide.globals.set("_a", origin);
  pyodide.globals.set("_b", destination);

  const result = pyodide.runPython(`
import json
_eon = eons[_eon_name]
_connectivity = exists_path(transitions, _a, _b)
_reachability = can_reach(_eon, transitions, _a, _b)
_discoverability = can_discover(_eon, information_set, _a, _b)
_traversed = shortest_path_nodes(transitions, _a, _b) if _connectivity else []
json.dumps({
    "exists_path": _connectivity,
    "can_reach": _reachability,
    "can_discover": _discoverability,
    "traversed": _traversed,
})
  `);

  const data = JSON.parse(result);
  renderResult(data, origin, destination);
  renderGraph(data, origin, destination);
}

// ---------------------------------------------------------------
// 5. Category derivation — display logic only, mirrors the
//    spec's labels for what the engine already returned. This
//    does not compute connectivity/reachability/discoverability;
//    it only names the combination that came back from Python.
// ---------------------------------------------------------------

function categoryFor(connectivity, reachability, discoverability) {
  if (!connectivity) return "abyss";
  if (reachability) return "reachable";
  if (discoverability) return "discoverable";
  return "connected";
}

const CATEGORY_LABEL = {
  reachable: "Reachable",
  discoverable: "Discoverable only",
  connected: "Connected only",
  abyss: "Abyss",
};

function renderResult(data, origin, destination) {
  setBool("r-exists_path", data.exists_path);
  setBool("r-can_reach", data.can_reach);
  setBool("r-can_discover", data.can_discover);

  const cat = categoryFor(data.exists_path, data.can_reach, data.can_discover);
  const catEl = document.getElementById("r-category");
  catEl.textContent = `${destination} — ${CATEGORY_LABEL[cat]}`;
  catEl.style.color = `var(--c-${cat === "discoverable" ? "discoverable" : cat})`;
}

function setBool(id, value) {
  const el = document.getElementById(id);
  el.textContent = value ? "True" : "False";
  el.classList.toggle("is-true", value);
  el.classList.toggle("is-false", !value);
}

// ---------------------------------------------------------------
// 6. Rendering. Pure presentation. Graph topology (which states,
//    which transitions) is read from Python — never hardcoded here
//    — so this file has no independent opinion about what the
//    state space looks like. Only pixel layout (where to place a
//    state visually) is computed in JS, because layout is a
//    presentation concern, not an ontological one.
// ---------------------------------------------------------------

let TRANSITION_PAIRS = []; // [from, to] pairs, read from scenario.py's transitions
let LAYOUT = {};
const NODE_R = 28;
const SVG_W = 760;
const SVG_H = 480;

function computeLayout(stateIds, transitionPairs) {
  // Identify states with no transition touching them at all (isolated
  // in this graph) so they can be placed off the main line, purely
  // for legibility. This reads the real topology; it does not decide
  // connectivity, reachability, or discoverability.
  const touched = new Set();
  for (const [from, to] of transitionPairs) {
    touched.add(from);
    touched.add(to);
  }
  const connectedChain = stateIds.filter((id) => touched.has(id));
  const isolated = stateIds.filter((id) => !touched.has(id));

  const layout = {};
  const margin = 110;
  const usableWidth = SVG_W - margin * 2;
  const mainY = SVG_H / 2;

  connectedChain.forEach((id, i) => {
    const x = connectedChain.length > 1
      ? margin + (usableWidth * i) / (connectedChain.length - 1)
      : SVG_W / 2;
    layout[id] = { x, y: mainY };
  });

  isolated.forEach((id, i) => {
    const x = margin + (usableWidth * (i + 0.5)) / Math.max(isolated.length, 1);
    layout[id] = { x, y: mainY - 140 };
  });

  return layout;
}

function renderGraph(data, origin, destination) {
  const svg = document.getElementById("graph-svg");
  svg.innerHTML = "";

  const edgesGroup = document.createElementNS(svg.namespaceURI, "g");
  const nodesGroup = document.createElementNS(svg.namespaceURI, "g");
  svg.appendChild(edgesGroup);
  svg.appendChild(nodesGroup);

  const traversedSet = new Set();
  if (data && data.traversed) {
    for (let i = 0; i < data.traversed.length - 1; i++) {
      traversedSet.add(data.traversed[i] + "->" + data.traversed[i + 1]);
    }
  }
  const selectedPair = origin && destination ? `${origin}->${destination}` : null;

  for (const [from, to] of TRANSITION_PAIRS) {
    const p1 = LAYOUT[from];
    const p2 = LAYOUT[to];
    if (!p1 || !p2) continue;
    const isTraversed = traversedSet.has(`${from}->${to}`) || traversedSet.has(`${to}->${from}`);
    const isDirectSelected = selectedPair === `${from}->${to}` || selectedPair === `${to}->${from}`;

    const line = document.createElementNS(svg.namespaceURI, "line");
    line.setAttribute("x1", p1.x);
    line.setAttribute("y1", p1.y);
    line.setAttribute("x2", p2.x);
    line.setAttribute("y2", p2.y);
    line.setAttribute("class", "gedge" + (isTraversed ? " is-traversed" : isDirectSelected ? " is-selected" : ""));
    edgesGroup.appendChild(line);
  }

  for (const id of STATE_IDS) {
    const pos = LAYOUT[id];
    if (!pos) continue;
    const g = document.createElementNS(svg.namespaceURI, "g");
    g.setAttribute("class", "gnode");

    const circle = document.createElementNS(svg.namespaceURI, "circle");
    circle.setAttribute("cx", pos.x);
    circle.setAttribute("cy", pos.y);
    circle.setAttribute("r", NODE_R);

    // Category for the currently selected destination comes straight
    // from the engine's result. States that are neither origin nor
    // destination, and have no transitions touching them at all, are
    // shown as Abyss relative to the current origin (no path can
    // exist from origin to an island with zero edges); everything
    // else not selected stays neutral until selected.
    let catClass = "cat-neutral";
    if (data && id === destination) {
      const cat = categoryFor(data.exists_path, data.can_reach, data.can_discover);
      catClass = "cat-" + cat;
    } else if (id !== origin && isIsolated(id)) {
      catClass = "cat-abyss";
    }
    circle.setAttribute("class", `gnode__circle ${catClass}` +
      (id === origin ? " is-origin" : "") +
      (id === destination ? " is-destination" : ""));

    if (catClass === "cat-abyss") {
      const title = document.createElementNS(svg.namespaceURI, "title");
      title.textContent = "No path from origin";
      circle.appendChild(title);
    }

    const label = document.createElementNS(svg.namespaceURI, "text");
    label.setAttribute("x", pos.x);
    label.setAttribute("y", pos.y + 5);
    label.setAttribute("class", "gnode__label");
    label.textContent = id;

    g.appendChild(circle);
    g.appendChild(label);
    nodesGroup.appendChild(g);
  }
}

function isIsolated(stateId) {
  return !TRANSITION_PAIRS.some(([from, to]) => from === stateId || to === stateId);
}

// ---------------------------------------------------------------
boot();