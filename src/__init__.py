"""Cellular Inference Mesh — Salabim discrete-event simulation.

Models multilingual AGV edge-cloud LLM inference under PACELC (Abadi, 2012)
and Tail at Scale (Dean & Barroso, 2013), with parametric variation per
replicate over realistic operational ranges.

Empirically validates: Little's Law, Pollaczek–Khinchine (M/G/1),
Roofline performance ceiling, and the Leviathan speculative-decoding
speedup formula.
"""

__version__ = "0.3.2"
__author__ = "Carlos Ulisses Flores"
__email__ = "c.ulisses@gmail.com"
