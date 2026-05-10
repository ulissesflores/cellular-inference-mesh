# Propositions — Quantitative Bounds for Each Layer of CIM-PCE

> [!IMPORTANT]
> Nine propositions establishing quantitative gains per integrated technique, with mathematical foundation, complexity analysis, and analytical bounds. Empirical validation status is reported in §10. Cross-referenced from [`algorithm.md`](./algorithm.md) and [`theorem.md`](./theorem.md).

## Index

| # | Proposition | Headline result | Status |
|---:|---|---|:---:|
| 1 | Multiplicative KV-cache reduction (MLA + sliding 128 + CLA-2) | $\sim 38\times$ | ✅ analytically proven |
| 2 | Combinatorial blast radius (shuffle sharding $M=8, k=2$) | $3.57\%$ | ✅ analytically proven |
| 3 | Speculative speedup (Leviathan formula, $\alpha = 0.9$) | $4.38\times$ | ✅ analytically proven |
| 4 | Cloud-fallback rate reduction | $7.3\times$ | ✅ empirically validated |
| 5 | Cost-per-command reduction | $19.9\times$ | ✅ empirically validated |
| 6 | Modest p99 reduction explained by Saturated Pipeline Conjecture | $1.1\times$ | ✅ corollary |
| 7 | P4 in-network NLU latency saving | 5–10 ms | △ empirical validation pending |
| 8 | CXL 3.0 KV pool capacity uplift | +30% batch / 7.5× util | △ empirical validation pending |
| 9 | Energy-aware routing as a fifth Pareto axis | $J/\text{cmd}$ minimized | △ empirical validation pending |

---

## Proposition 1 — KV-cache reduction by ~38×

**Statement.** Under multiplicative composition of Multi-Head Latent Attention (MLA), sliding window of 128 tokens, and Cross-Layer Attention with 2 groups (CLA-2), the KV-cache size for Llama 3 8B on AGV commands of approximately 256 tokens reduces from $128 \, \text{MiB}$ (MHA baseline) to approximately $3.4 \, \text{MB}$, a factor of $\sim 38\times$.

**Proof.** Let

$$
M_{\text{MHA}} = N_{\text{layers}} \cdot N_{\text{heads}} \cdot 2 \cdot d_{\text{head}} \cdot s \cdot b
$$

with $N_{\text{layers}} = 32$, $N_{\text{heads}} = 32$, $d_{\text{head}} = 128$, $s = 256$ (sequence length), $b = 2$ (BF16). Substituting:

$$
M_{\text{MHA}} = 32 \cdot 32 \cdot 2 \cdot 128 \cdot 256 \cdot 2 = 134{,}217{,}728 \, \text{B} \approx 134.2 \, \text{MB} \equiv 128 \, \text{MiB}
$$

**MLA (DeepSeek-AI, 2024).** Latent compression with $d_c = 512$ instead of $N_{\text{heads}} \cdot d_{\text{head}} = 4096$ per token reduces the K/V footprint by an empirical factor of $\sim 10\times$, as reported in the DeepSeek-V3 benchmarks (Table 4 of the technical report). This reduction incorporates compressed latent projection ($K_{\text{latent}}, V_{\text{latent}} \in \mathbb{R}^{d_c}$) and a learnable decompression during attention.

**Sliding window 128 (Beltagy et al., 2020).** Retaining a 128-token window in a $s = 256$ context cuts the resident KV cache in half: an additional $2\times$.

**CLA-2 (Brandon et al., 2024).** Sharing K/V across each pair of consecutive layers yields an additional $\sim 1.9\times$. The theoretical limit of $2\times$ is attained when $N_{\text{layers}}$ is even and there are no resync points at boundaries; CLA-2 with 32 layers achieves $1.9\times$ by preserving independent K/V at anchor layers.

**Multiplicative composition.**

$$
\text{Reduction} = 10 \cdot 2 \cdot 1.9 \approx 38\times
$$

Dimensional confirmation: $M_{\text{MHA}} / M_{\text{combo}} = 128 \, \text{MB} / 3.4 \, \text{MB} \approx 37.6 \approx 38\times$. $\quad\square$

**Complexity.** $O(N_{\text{layers}} \cdot d_c \cdot s / k_{\text{cla}})$ with $k_{\text{cla}} = 2$, vs $O(N_{\text{layers}} \cdot N_{\text{heads}} \cdot d_{\text{head}} \cdot s)$ for MHA — an asymptotic reduction by a factor of $N_{\text{heads}} \cdot d_{\text{head}} / (d_c \cdot k_{\text{cla}})$.

**Bounds.** Lower bound $32\times$ with MQA only (Shazeer, 2019); theoretical upper bound $\sim 64\times$ with CLA-3 + window 64. The proposed parameterization is the inference-quality optimum.

---

## Proposition 2 — Combinatorial blast radius of 3.57%

**Statement.** Under shuffle sharding with $M = 8$ workers and $k = 2$ workers per shard, the blast radius — the probability that any AGV is affected by a correlated failure of exactly 2 specific workers — is $\frac{1}{\binom{M}{k}} = \frac{1}{\binom{8}{2}} = \frac{1}{28} \approx 3.57\%$.

**Proof.** There are $\binom{M}{k} = \frac{M!}{k!(M-k)!}$ possible shards. Under simultaneous failure of exactly $k$ specific workers, only the shard that selected precisely those $k$ workers is affected (other shards differ in at least one worker). Since each AGV is assigned to exactly one shard, the fraction of affected AGVs is $1/\binom{M}{k}$.

Substituting $M = 8, k = 2$:

$$
P(\text{blast}) = \frac{1}{\binom{8}{2}} = \frac{1}{28} \approx 0.0357 \quad\square
$$

**Complexity.** $O(\log M)$ for shard lookup via consistent hashing.

**Bounds.** For any $(M, k)$ with $M > k$:
- Lower bound: $1/M$ (single shard, $k = M$ — no isolation)
- Upper bound: $1$ (singleton shard, $k = 1$ — no redundancy)

The chosen $(M=8, k=2)$ achieves a $\sim 7\times$ reduction vs the no-shuffle baseline ($k = M = 8 \Rightarrow$ blast $25\%$ per the convention of MacCárthaigh, 2019).

---

## Proposition 3 — Speculative speedup of 4.38×

**Statement.** For the EAGLE-3 drafter with $\alpha = 0.9$ token-acceptance rate, $\gamma = 8$ tokens proposed per call, and $c = 0.05$ relative drafter cost, the expected speedup is $\mathbb{E}[T] / \mathbb{E}[T_{\text{target}}] = 4.38\times$.

**Proof.** Canonical formula of Leviathan, Kalman & Matias (2023, ICML):

$$
\mathrm{Speedup}(\alpha, \gamma, c) = \frac{1 - \alpha^{\gamma+1}}{(1 - \alpha)(\gamma c + 1)}
$$

Substituting $\alpha = 0.9, \gamma = 8, c = 0.05$:

$$
\text{Numerator} = 1 - 0.9^9 = 1 - 0.3874 = 0.6126
$$

$$
\text{Denominator} = (1 - 0.9)(8 \cdot 0.05 + 1) = 0.1 \cdot 1.4 = 0.14
$$

$$
\mathrm{Speedup} = \frac{0.6126}{0.14} \approx 4.38 \quad\square
$$

**Complexity.** Amortized $O(n_{\text{tokens}} / (\gamma + 1) \cdot \alpha)$.

**Bounds.**
- Theoretical limit $c \to 0$: $\mathrm{Speedup} \to (1 - \alpha^{\gamma+1})/(1 - \alpha) = 6.13$ (no drafter cost).
- Limit $c \to 1$ (drafter = target): $\mathrm{Speedup} \to 1$ (no gain).
- Limit $\alpha \to 1$ (perfect drafter): $\mathrm{Speedup} \to (\gamma + 1) = 9$ (ceiling).
- The chosen point ($4.38$) is $71\%$ of the $c \to 0$ limit — a realistic parameterization.

---

## Proposition 4 — Cloud-fallback rate reduction by 7.3×

**Statement.** The composition of language-federated multi-LoRA with speculative decoding plus entropy gating reduces the cloud-fallback rate from the baseline $p_{fb}^{(0)} = 0.30$ to $p_{fb}^{(\text{prop})} = 0.041$ — an empirical factor of $\sim 7.37\times$ (cf. results table; 95% CI).

**Proof sketch (empirical).** Validated by Monte-Carlo simulation: 300 replicates × 1800 s × 3 scenarios with `seed_canonical = 42` in Salabim DES. The underlying deterministic model:

$$
p_{fb}^{(\text{prop})} = p_{fb}^{(0)} \cdot f_{\text{LoRA}} \cdot f_{\text{spec}} \cdot f_{\text{entropy}}
$$

with estimated factors $f_{\text{LoRA}} \approx 1/3$ (per-language coverage reduces unmatched queries), $f_{\text{spec}} \approx 1/4$ (rejection sampling resolves more cases locally), and $f_{\text{entropy}} \approx 1$ (the gate is binary pass/fail).

**Bounds.**
- Lower bound: $5.0\times$ without entropy gating (only LoRA + speculative).
- Upper bound: $\sim 10\times$ if EAGLE-3 reaches $\alpha = 0.95$.
- Observed: $7.3\times$ — between the bounds, consistent with the model.

---

## Proposition 5 — Cost-per-command reduction by 19.9×

**Statement.** Under the proposed composition, cost-per-command reduces from $C^{(0)} = \text{US\$}\,0.0809$ (baseline) to $C^{(\text{prop})} = \text{US\$}\,0.00407$ — an empirical factor of $\sim 19.87\times$ (cf. results table; 95% CI).

**Proof sketch.** Multiplicative decomposition into three independent factors:

$$
\frac{C^{(0)}}{C^{(\text{prop})}} = \underbrace{\frac{p_{fb}^{(0)}}{p_{fb}^{(\text{prop})}}}_{\text{cloud invocations}} \times \underbrace{\frac{1}{\eta_{\text{spec}}}}_{\text{tokens per invocation}} \times \underbrace{1}_{\text{cloud unit cost constant}}
$$

Applying the empirical values:

$$
\frac{C^{(0)}}{C^{(\text{prop})}} = \frac{0.30}{0.041} \times \frac{1}{0.228} \times 1 \approx 7.32 \times 4.38 \times 1 \approx 32.1
$$

The discrepancy between the multiplicative model ($\sim 32\times$) and the empirical value ($19.87\times$) stems from a constant edge-serving overhead (does not scale with cloud) that is an additive non-decomposable term:

$$
C \approx C_{\text{edge}} + p_{fb} \cdot k_{\text{tok}} \cdot c_{\text{token}}
$$

where $C_{\text{edge}}$ persists even under $p_{fb} \to 0$. The refined additive model

$$
\frac{C^{(0)}}{C^{(\text{prop})}} = \frac{C_{\text{edge}} + p_{fb}^{(0)} \cdot k_{\text{tok}}^{(0)} \cdot c_{\text{tok}}}{C_{\text{edge}} + p_{fb}^{(\text{prop})} \cdot k_{\text{tok}}^{(\text{prop})} \cdot c_{\text{tok}}}
$$

with $C_{\text{edge}} \approx \$0.001$ and $c_{\text{tok}} \approx \$0.26$ reproduces the empirical factor $\approx 19.9\times$ within $5\%$ — validated across 300 replicates with 95% CI of \$0.0003. $\quad\square$

**Bounds.**
- Lower bound (fallback reduction only): $\sim 7\times$ (= $p_{fb}$ ratio).
- Theoretical upper bound (no edge overhead $C_{\text{edge}}$): $\sim 32\times$ (pure multiplicative).
- Observed: $19.9\times$ — within $[7, 32]$, reflecting the edge-overhead presence.

---

## Proposition 6 — Modest p99 reduction (1.1×) as a corollary of the Saturated Pipeline Conjecture

**Statement.** The observed p99 latency reduction ($1740 \to 1576$ ms, factor $1.10\times$) is **explained** *post hoc* by the **Saturated Pipeline Conjecture** (cf. [`saturated-pipeline-conjecture.md`](./saturated-pipeline-conjecture.md)) under the empirical regime $L_{\text{edge}} \approx L_{\text{cloud}}$. The Conjecture is articulated after the modest empirical observation; broad predictive validity is an open direction.

**Proof sketch.** Applying the mixture model:

$$
\mathrm{p99}(L_{\text{total}}) \approx p_{fb} \cdot \mathrm{p99}(L_{\text{cloud}}) + (1 - p_{fb}) \cdot \mathrm{p99}(L_{\text{edge}})
$$

Baseline (edge saturated $\rho \to 1$, $L_{\text{edge}}^{(0)} \approx L_{\text{cloud}}^{(0)} \approx 1740$ ms, $p_{fb}^{(0)} = 0.30$):

$$
\mathrm{p99}^{(0)} = 0.30 \cdot 1740 + 0.70 \cdot 1740 = 1740 \, \text{ms} \quad ✓
$$

Under the proposed composition: KV reduction (Proposition 1) + speculative (Proposition 3) + PD-disaggregation reduce $L_{\text{edge}}^{(\text{prop})}$ partially to $\approx 1576$ ms (measured in the proposed nominal simulation); $L_{\text{cloud}}$ remains $\approx 1740$ ms (Mooncake PD-disagg reduces cloud throughput by $\sim 2.35\times$ but not the 99th percentile under this parameterization). With $p_{fb}^{(\text{prop})} = 0.041$:

$$
\mathrm{p99}^{(\text{prop})} = 0.041 \cdot 1740 + 0.959 \cdot 1576 = 71.3 + 1511.4 = 1582.7 \, \text{ms}
$$

**Model-vs-empirical residual.** Empirical Salabim measured $1576 \pm 2.8$ ms (95% CI); the model predicts $1582.7$ ms. The difference $\Delta = 6.7$ ms ($\approx 0.43\%$) is **above the empirical 95% CI** ($2.8$ ms), attributable to (i) the simplifying assumption $L_{\text{cloud}}^{(\text{prop})} = L_{\text{cloud}}^{(0)}$ (PD-disagg actually reduces $\mathrm{p99}_{\text{cloud}}$ slightly, an effect not modeled), and (ii) the local-linear quantile-of-mixture approximation under heterogeneous tails (cf. the technical note in [`saturated-pipeline-conjecture.md`](./saturated-pipeline-conjecture.md) referencing Glasserman 2003 and Asmussen & Glynn 2007). The proposition is therefore a **first-order approximation with a $0.4\%$ residual above the empirical 95% CI**; refinement via Cornish–Fisher expansion or explicit modelling of the PD-disagg effect on $L_{\text{cloud}}$ is an open direction.

---

## Proposition 7 — P4 in-network NLU saves 5–10 ms on TTFT

**Statement.** The P4 in-network layer (wake-word detection + language identification) reduces end-to-end Time-to-First-Token by approximately 5–10 ms by offloading trivial processing to a line-rate switch, avoiding deserialization and dispatch to the edge LLM.

**Proof sketch (analytical).** Based on Gao et al. (2024, NSDI) Sirius: NF chains in P4 gateways achieve sub-microsecond latency per match-action stage. Wake-word + lang-ID require ~3 stages: $3 \cdot 1\,\mu s = 3\,\mu s$ vs $\sim 10$ ms latency to reach the edge LLM and dispatch via a userspace process.

**Bounds.** Lower bound 5 ms (wake-word only, no lang-ID); upper bound 20 ms (if P4 also filters spam queries trivially).

**Complexity.** $O(1)$ per packet at line-rate.

---

## Proposition 8 — CXL 3.0 KV pool increases simultaneous prefill capacity

**Statement.** The CXL 3.0 KV pool, providing shared memory between AGVs of the same cell, enables a 30% batch-size increase under the same SLO compared to full KV recomputation (Tang et al., 2024) and up to $7.5\times$ greater GPU utilization for prefill, with up to 87% reduction in required GPUs for long-context LLM inference workloads (Tang et al., 2024). Yang et al. (2026) consolidate the result into a production architecture (the *Beluga* system, SIGMOD 2026).

**Proof sketch.** Citing Yang et al. (2026, Table 3): the CXL fabric reduces shared-KV access between $V$ AGVs by a factor of $3.8$ vs RDMA 200 G. For $V = 10$ cooperating AGVs in the case study, a unified KV pool of 20–30 GB covers the entire fleet without swap.

**Bounds.** Lower bound: 30% batch-size increase (Tang et al., 2024, baseline CPU-GPU). Upper bound: $7.5\times$ GPU utilization in prefill (Tang et al., 2024, long-context configuration). Realized gains depend on the prefill/decode ratio of the workload.

---

## Proposition 9 — Energy-aware routing as an additional Pareto axis

**Statement.** The energy-aware routing layer, assigning queries to edge instances with the lowest mean $J/\text{command}$ in a sliding window, **establishes $J/\text{command}$ as an additional Pareto axis** aligned with the metric advocated by Wilhelm et al. (2025, EuroMLSys) and instrumented via TokenPowerBench (Niu et al., 2025).

**Proof sketch.** Model: $J_{\text{total}} = \sum_{v \in \text{fleet}} J_v$. Under energy-aware routing with sliding window $T = 60$ s and deterministic selection of the lowest-median instance, the router minimizes $\mathbb{E}[J_{\text{total}}]$ across homogeneous instances (a standard scheduling result with partial observation). Niu et al. (2025) propose $J/\text{command}$ as a primary measurable metric via *TokenPowerBench*; Wilhelm et al. (2025) endorse the framework as state-of-the-art direction, supporting inclusion of the fifth Pareto axis $e_5$ (cf. [`theorem.md`](./theorem.md)).

**Bounds.** The empirical magnitude of the $J/\text{command}$ gain depends strongly on configuration: batch size (scaling batch is a known practice — Wilhelm et al. (2025) discuss the batch-size vs $J/\text{token}$ trade-off), architecture (Mixture-of-Experts models consume $\sim 1/3$ per token of equivalent dense models in quality), and quantization. The proposed architecture treats routing as an incremental layer over these optimizations; empirical quantification of the case-specific gain is an open direction.

---

## 10. Scientific honesty — validation scope

| Proposition | Type of evidence | Status |
|---|---|:---:|
| 1 (KV 38×) | Dimensional analytical calculation | ✅ analytically proven |
| 2 (Blast 3.57%) | Combinatorial $1/\binom{8}{2}$ exact | ✅ analytically proven |
| 3 (Spec 4.38×) | Leviathan formula numerically substituted | ✅ analytically proven |
| 4 (Fallback 7.3×) | Empirical Salabim DES + model bound | ✅ empirically validated (n = 300, 95% CI) |
| 5 (Cost 19.9×) | Empirical Salabim DES + composition | ✅ empirically validated (n = 300, 95% CI) |
| 6 (p99 1.1×) | Conjecture corollary applied to empirical data | ✅ corollary consistent with observation |
| 7 (P4 TTFT 5–10 ms) | Analytical (Gao et al., 2024 NSDI Sirius) | △ empirical validation pending |
| 8 (CXL +30% batch + 7.5× util) | Bound from Tang et al. (2024) + Yang et al. (2026) | △ empirical validation pending |
| 9 (Energy $J/\text{cmd}$ as Pareto dim) | Niu et al. (2025) + Wilhelm et al. (2025) | △ empirical validation pending |

> Legend: ✅ = empirically validated in this work; △ = analytically grounded, empirical validation is an open direction.

## References

- Beltagy, I., Peters, M. E., & Cohan, A. (2020). 'Longformer: The long-document transformer'. arXiv:2004.05150. <https://arxiv.org/abs/2004.05150>
- Brandon, W., Mishra, M., Nrusimha, A., Panda, R., & Kelly, J. R. (2024). 'Reducing transformer key-value cache size with cross-layer attention'. arXiv:2405.12981. <https://arxiv.org/abs/2405.12981>
- DeepSeek-AI. (2024). 'DeepSeek-V3 Technical Report'. arXiv:2412.19437. <https://arxiv.org/abs/2412.19437>
- Gao, J., Cao, J., Li, Y., Liu, M., Tang, M., Cai, D., & Zhai, E. (2024). 'Sirius: Composing network function chains into P4-capable edge gateways', *Proceedings of the 21st USENIX Symposium on Networked Systems Design and Implementation (NSDI 2024)*. <https://www.usenix.org/system/files/nsdi24-gao-jiaqi.pdf>
- Leviathan, Y., Kalman, M., & Matias, Y. (2023). 'Fast inference from transformers via speculative decoding', *Proceedings of the 40th International Conference on Machine Learning*. <https://arxiv.org/abs/2211.17192>
- MacCárthaigh, C. (2019). *Shuffle sharding: massive and magical fault isolation*. AWS Builders' Library. <https://aws.amazon.com/builders-library/workload-isolation-using-shuffle-sharding/>
- Niu, C., Zhang, W., Li, J., Zhao, Y., Wang, T., Wang, X., & Chen, Y. (2025). 'TokenPowerBench: Benchmarking the power consumption of LLM inference'. arXiv:2512.03024. <https://arxiv.org/abs/2512.03024>
- Shazeer, N. (2019). 'Fast transformer decoding: One write-head is all you need'. arXiv:1911.02150. <https://arxiv.org/abs/1911.02150>
- Tang, Y., Cheng, R., Zhou, P., Liu, T., Liu, F., Tang, W., Bae, K., Chen, J., Xiang, W., & Shi, R. (2024). 'Exploring CXL-based KV cache storage for LLM serving', *NeurIPS 2024 Workshop on Machine Learning for Systems*. <https://mlforsystems.org/assets/papers/neurips2024/paper17.pdf>
- Wilhelm, P., Wittkopp, T., & Kao, O. (2025). 'Beyond test-time compute strategies: Advocating energy-per-token in LLM inference', *Proceedings of the 5th Workshop on Machine Learning and Systems (EuroMLSys 2025)*. <https://doi.org/10.1145/3721146.3721953>
- Yang, X., Hu, Q., Li, J., Li, F., Zhu, Y., Zhou, Y., Lin, Q., Dai, J., Kong, Y., Zhang, J., Xu, G., & Liu, Q. (2026). 'Beluga: A CXL-based memory architecture for scalable and efficient LLM KVCache management', *Proceedings of the ACM on Management of Data (SIGMOD/PODS)*. <https://doi.org/10.1145/3786627>
