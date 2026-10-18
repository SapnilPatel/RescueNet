"""City-scale delivery simulation: % of SOS that reach responders within an
hour vs. % of phones carrying the RescueNet relay SDK.

Model (1-minute steps, 60 minutes):
  * 4 km x 4 km dead zone (16 km^2), no cell signal inside.
  * A 300 m populated band around it HAS signal: any relay phone there is a gateway.
  * Population 2000/km^2; a fraction `adoption` of phones run our SDK (relays).
  * 300 trapped victims, uniform, stationary. They need no app: their SOS
    enters any relay or beacon within Wi-Fi range (80 m) via the SOS-HELP page.
  * Relays within 80 m of each other exchange messages (flooding within a
    connected cluster happens inside one minute).
  * Beacons (optional): LoRa boards on a 1 km grid (~1 per school); they talk
    to each other at 1.5 km and the edge beacons reach a LoRa gateway outside.
    Phones/victims reach a beacon over Wi-Fi at 80 m.
  * Cars (optional): 40% of relay phones evacuate by car at ~15 km/h toward
    the nearest edge, carrying everything they picked up (store-and-forward).

A message counts as delivered once any node holding it is in coverage.

Usage:  python sim/simulate.py [--seeds 2]
Writes: sim/out/delivery_vs_adoption.png and sim/out/results.csv
"""
import argparse
import csv
import os

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

SIDE = 4000.0          # m
BAND = 300.0           # m populated band with signal outside the dead zone
DENSITY = 2000 / 1e6   # people per m^2
WIFI = 80.0            # m phone/beacon Wi-Fi range
LORA = 1500.0          # m beacon-to-beacon
GRID = 1000.0          # m beacon spacing
VICTIMS = 300
MINUTES = 60
CAR_FRACTION = 0.40
CAR_SPEED = 15000 / 60  # m per minute
ADOPTION = [0.005, 0.01, 0.02, 0.05, 0.10, 0.20]
SCENARIOS = [("phones", "Phones only"), ("beacons", "+ LoRa beacons"), ("cars", "+ evacuating cars")]


def in_coverage(p):
    return (p[:, 0] < 0) | (p[:, 0] > SIDE) | (p[:, 1] < 0) | (p[:, 1] > SIDE)


def place_relays(rng, adoption):
    outer = SIDE + 2 * BAND
    n = rng.poisson(DENSITY * adoption * outer * outer)
    return rng.uniform(-BAND, SIDE + BAND, size=(n, 2))


def edge_target(p):
    """Nearest exit point just outside the dead zone, for each position."""
    t = p.copy()
    d = np.stack([p[:, 0], SIDE - p[:, 0], p[:, 1], SIDE - p[:, 1]], axis=1)
    side = d.argmin(axis=1)
    t[side == 0, 0] = -1
    t[side == 1, 0] = SIDE + 1
    t[side == 2, 1] = -1
    t[side == 3, 1] = SIDE + 1
    return t


def run(adoption, scenario, seed):
    rng = np.random.default_rng(seed)
    relays = place_relays(rng, adoption)
    victims = rng.uniform(0, SIDE, size=(VICTIMS, 2))

    nodes = relays
    n_relay = len(relays)
    beacon_idx = np.array([], dtype=int)
    if scenario in ("beacons", "cars"):
        g = np.arange(GRID / 2, SIDE, GRID)
        beacons = np.array([(x, y) for x in g for y in g])
        beacon_idx = np.arange(n_relay, n_relay + len(beacons))
        nodes = np.vstack([relays, beacons])
    n = len(nodes)

    moving = np.zeros(n, dtype=bool)
    if scenario == "cars":
        inside = ~in_coverage(relays)
        moving[:n_relay] = inside & (rng.random(n_relay) < CAR_FRACTION)
    target = edge_target(nodes)

    holds = np.zeros((VICTIMS, n), dtype=bool)
    delivered = np.zeros(VICTIMS, dtype=bool)
    vtree = cKDTree(victims)
    steps = MINUTES if scenario == "cars" else 1  # static network: one step is enough
    pos = nodes.copy()

    for _ in range(steps):
        # Victims hand their SOS to any relay/beacon in Wi-Fi range (no app needed).
        for node, vs in enumerate(vtree.query_ball_point(pos, WIFI)):
            if vs:
                holds[vs, node] = True

        # Contact graph: Wi-Fi between all nodes, LoRa between beacons.
        pairs = cKDTree(pos).query_pairs(WIFI, output_type="ndarray")
        if len(beacon_idx):
            bp = cKDTree(pos[beacon_idx]).query_pairs(LORA, output_type="ndarray")
            pairs = np.vstack([pairs, beacon_idx[bp]]) if len(bp) else pairs
        adj = coo_matrix((np.ones(len(pairs)), (pairs[:, 0], pairs[:, 1])), shape=(n, n)) if len(pairs) else coo_matrix((n, n))
        n_comp, label = connected_components(adj, directed=False)

        covered = in_coverage(pos)
        if len(beacon_idx):
            # Edge beacons reach a LoRa gateway outside the zone.
            b = pos[beacon_idx]
            edge_dist = np.minimum.reduce([b[:, 0], SIDE - b[:, 0], b[:, 1], SIDE - b[:, 1]])
            covered[beacon_idx[edge_dist <= LORA]] = True

        # Flood messages within each connected cluster.
        comp_has = np.zeros((VICTIMS, n_comp), dtype=bool)
        vi, ni = np.nonzero(holds)
        comp_has[vi, label[ni]] = True
        holds = comp_has[:, label]
        delivered |= holds[:, covered].any(axis=1)

        if moving.any():
            d = target[moving] - pos[moving]
            dist = np.linalg.norm(d, axis=1, keepdims=True)
            step = np.minimum(dist, CAR_SPEED)
            pos[moving] += d / np.maximum(dist, 1e-9) * step

    return delivered.mean()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=2)
    args = ap.parse_args()
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
    os.makedirs(out_dir, exist_ok=True)

    results = {}
    for key, _ in SCENARIOS:
        for a in ADOPTION:
            results[key, a] = float(np.mean([run(a, key, seed) for seed in range(args.seeds)]))

    with open(os.path.join(out_dir, "results.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["adoption"] + [label for _, label in SCENARIOS])
        for a in ADOPTION:
            w.writerow([a] + [round(results[k, a], 4) for k, _ in SCENARIOS])

    print("| Adoption | " + " | ".join(label for _, label in SCENARIOS) + " |")
    print("|---|" + "---|" * len(SCENARIOS))
    for a in ADOPTION:
        print("| %g%% | " % (a * 100) + " | ".join("%.1f%%" % (results[k, a] * 100) for k, _ in SCENARIOS) + " |")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    colors = {"phones": "#9aa3b2", "beacons": "#4f8cff", "cars": "#e53935"}
    fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
    xs = [a * 100 for a in ADOPTION]
    for key, label in SCENARIOS:
        ys = [results[key, a] * 100 for a in ADOPTION]
        ax.plot(xs, ys, marker="o", lw=2.5, color=colors[key], label=label)
    ax.set_xscale("log")
    ax.set_xticks(xs)
    ax.set_xticklabels(["%g%%" % x for x in xs])
    ax.set_ylim(0, 102)
    ax.set_xlabel("Phones carrying the RescueNet relay SDK")
    ax.set_ylabel("SOS reaching responders within 60 min (%)")
    ax.set_title("16 km² dead zone · 300 trapped victims · victims need no app", fontsize=11)
    ax.grid(alpha=0.3)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="upper left")
    fig.tight_layout()
    path = os.path.join(out_dir, "delivery_vs_adoption.png")
    fig.savefig(path)
    print("wrote", path)


if __name__ == "__main__":
    main()
