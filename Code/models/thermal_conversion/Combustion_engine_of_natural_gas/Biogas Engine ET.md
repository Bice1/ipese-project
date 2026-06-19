---
title: "Combined Biodigestion + Biogas Engine (husk-fired) — Energy Technology Model"
subtitle: "IEA IETS Task XXIV · Subtask 1 · Activity 3.1 (Energy Technologies)"
author: "Daniel Flórez-Orrego, EPFL IPESE research group"
date: ""
---

# Combined biodigestion + biogas engine (husk-fired CHP)

A grey-box, steady-state model of a **combined anaerobic-biodigestion + biogas-fired internal-combustion engine** system designed to valorise an on-site organic residue stream (here, **brewery barley husk**) into electricity and recoverable heat. The unit couples two physical sub-stages within a single utility model:

- a **mesophilic anaerobic digester** (operating at 34–35 °C) that produces a methane-rich biogas from the husk;
- a **biogas-fired internal-combustion engine** that consumes the produced biogas in CHP mode.

The unit exposes a husk feedstock input, a net electricity output, three heat streams (one cold — the digester heating duty, two hot — the engine cylinder cooling water and the engine exhaust gases), and no separate CO₂ accounting in the source data.

> **Source-data note.** This model is provided as a Lua model only (no machine-readable schema file). The card below transcribes what the source file states; fields that the source does not provide are left blank.

## 1. Model card

| Field | Value |
|:------|:------|
| Model identifier | Combined biodigestion + biogas engine (husk-fired CHP) (ET) |
| Authors | Daniel Flórez-Orrego — EPFL IPESE research group |
| Version | 1.0 |
| Description | Combined biodigestion of barley husk and power generation in an internal combustion engine using biogas |
| Main reference | Maréchal, Sachan & Salgueiro (2013), *Handbook of Process Integration* |

## 2. Process description

Brewery barley husk is a high-moisture solid residue produced in large quantities by the malting and brewing industries. Its energy content (LHV ≈ 14.3 MJ/kg dry basis) is too low and its moisture content too high for direct combustion to be efficient; **anaerobic digestion** converts a substantial fraction of its organic matter into a methane-rich biogas, which can in turn be fired in an internal-combustion engine for cogeneration.

The model couples the two stages back-to-back:

- The **biodigester** is operated mesophilically at 35 °C with a specific biogas yield of 75 Nm³ per tonne of husk; the digester heating duty (to raise the slurry from 34 °C to 35 °C and compensate the reaction's heat losses) is approximated as 20 % of the biogas energy output.
- The **biogas engine** burns the produced biogas (LHV ≈ 35.7 MJ/Nm³) with fixed efficiencies $\eta_{el} = 0.41$, $\eta_{th,cw} = 0.22$, $\eta_{th,eg} = 0.20$, representative of a Jenbacher Type-4 reference engine. Cooling-water-jacket waste heat is available at 80–90 °C; exhaust-gas waste heat is available at 150–400 °C (exhaust outlet limited to 150 °C to avoid sulphuric-acid condensation in the funnel).

## 3. Block flow diagram

![Combined biodigestion + biogas engine: brewery husk → digester (35 °C, cold duty for heating) → biogas → ICE engine producing electricity + cooling-water hot stream (90 → 80 °C) + exhaust-gas hot stream (400 → 150 °C).](../Figures/NatgasEngine.svg){width=80%}

## 4. Parameters

### 4.1 Decision

| Parameter | Symbol | Default | Unit |
|:----------|:-------|--------:|:-----|
| Husk waste mass flow | $\dot m_{husk}$ | 2 730 | kg/h |
| Digester inlet / outlet temperature | $T_{dig,in}/T_{dig,out}$ | 34 / 35 | °C |
| Cooling-water inlet / outlet temperature (engine jacket) | $T_{CW,in}/T_{CW,out}$ | 90 / 80 | °C |
| Exhaust-gas inlet / outlet temperature | $T_{EG,in}/T_{EG,out}$ | 400 / 150 | °C |
| Engine electrical efficiency | $\eta_{el}$ | 0.410 | – |
| Engine cooling-water efficiency | $\eta_{th,cw}$ | 0.220 | – |
| Engine exhaust-gas efficiency | $\eta_{th,eg}$ | 0.200 | – |
| Engine specific CAPEX | $c_{eng}$ | 1 300 | EUR/kW |
| $\Delta T_{min}$ — liquid / gas | $\Delta T_{min,liq/gas}$ | 5 / 8 | °C |
| Equipment lifetime | $n$ | 40 | year |
| Interest rate | $i$ | 0.06 | – |

### 4.2 Literature

| Parameter | Symbol | Default | Unit | Source |
|:----------|:-------|--------:|:-----|:-------|
| Husk lower heating value (dry) | $LHV_{husk}$ | 14 300 | kJ/kg | Maréchal *et al.* (2013) |
| Biogas lower heating value | $LHV_{biogas}$ | 35 700 | kJ/Nm³ | Maréchal *et al.* (2013) |
| Specific biogas yield from husk | $y_{biogas}$ | 75 | Nm³/t_husk | Maréchal *et al.* (2013) |
| Specific digester heating duty | $\eta_{Q,dig}$ | 0.20 | kW_th / kW_biogas | Maréchal *et al.* (2013) |

## 5. Derived quantities at the reference operating point

| Quantity | Symbol | Expression | Value | Unit |
|:---------|:-------|:-----------|------:|:-----|
| Biogas volumetric flow | $\dot V_{biogas}$ | $\dot m_{husk}/1000\cdot y_{biogas}$ | 205 | Nm³/h |
| Biogas energy flow | $\dot Q_{biogas}$ | $\dot V_{biogas}\,LHV_{biogas}/3600$ | 2 030 | kW |
| Digester heating duty | $\dot Q_{dig}$ | $\eta_{Q,dig}\,\dot Q_{biogas}$ | 406 | kW |
| Net electricity output | $W_{el}$ | $\eta_{el}\,\dot Q_{biogas}$ | 832 | kW |
| Cooling-water heat recovery | $\dot Q_{CW}$ | $\eta_{th,cw}\,\dot Q_{biogas}$ | 447 | kW |
| Exhaust-gas heat recovery | $\dot Q_{EG}$ | $\eta_{th,eg}\,\dot Q_{biogas}$ | 406 | kW |
| Annualisation factor | $a$ | $i(1+i)^{n}/((1+i)^{n}-1)$ | 0.0665 | – |
| Annualised investment cost | $C_{inv2,eng}$ | $c_{eng}\,W_{el}\,a$ | 71.9 k | EUR/y |

## 6. Interfaces and heat streams

| Interface | Direction / Type | Reference flow | T | Notes |
|:----------|:-----------------|---------------:|:--|:------|
| Husk feedstock | In · Mass | 2 730 kg/h | – | Brewery barley husk |
| Electricity (net) | Out · Electrical | 832 kW | – | Mechanical output via generator |
| Digester heating duty | Cold thermal | 406 kW | 34 °C → 35 °C | $\Delta T_{min}/2 = 4$ °C |
| Cooling-water waste heat | Hot thermal | 447 kW | 90 °C → 80 °C | $\Delta T_{min}/2 = 2.5$ °C; low-grade, suitable for district heating, preheating |
| Exhaust-gas waste heat | Hot thermal | 406 kW | 400 °C → 150 °C | $\Delta T_{min}/2 = 4$ °C; high-grade, suitable for steam generation, drying |

The model deliberately couples the digester (heat sink) and the engine (heat sources) within a single utility, so that on the system heat cascade the engine's waste heat can directly cover the digester's heating duty (here ~406 kW of heating against ~853 kW of recoverable heat, leaving ~450 kW for the surrounding process).

## 7. Equipment and cost

A single asset — the engine — is sized for cost calculation; the digester is included in the model's heat balance but no separate equipment CAPEX is attributed to it in the source.

$$C_{inv2,eng} \;=\; c_{eng}\,W_{el}\,a \quad [\text{EUR/y}], \qquad a \;=\; \dfrac{i(1+i)^{n}}{(1+i)^{n}-1}.$$

| Item | Value |
|:-----|:------|
| Engine specific investment | 1 300 EUR/kWₑₗ |
| Lifetime | 40 years |
| Interest rate | 0.06 |
| Capacity range | 0 × to 10 × reference |
| Fixed operating cost | 0 EUR/y |
| Variable operating cost | 0 EUR/h |

## 8. References

1. Maréchal, F., Sachan, R. & Salgueiro, L. (2013). **Handbook of Process Integration**.

## 9. Cite as

> Flórez-Orrego, D. *Combined biodigestion + biogas engine (husk-fired) — Ex-ante energy-technology model (ET, v1.0).* IEA IETS Task XXIV / Subtask 1, Activity 3.1. EPFL IPESE, Lausanne. Contact: <daniel.florezorrego@epfl.ch>.
