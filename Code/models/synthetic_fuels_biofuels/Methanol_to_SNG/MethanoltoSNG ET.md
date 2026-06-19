---
title: "Methanol-to-SNG (reforming + methanation) — Energy Technology Model"
subtitle: "IEA IETS Task XXIV · Subtask 1 · Activity 3.1 (Energy Technologies)"
author: "Daniel Flórez-Orrego, Meire Domingos — EPFL IPESE"
date: "2025-11-13"
---

# Methanol-to-SNG (autothermal reforming + WGS + PSA + methanation)

A grey-box, steady-state model that converts liquid **methanol** into pipeline-grade **synthetic natural gas (SNG)** through a four-stage process: autothermal reforming (ATR) of methanol with steam and oxygen, two-stage water-gas-shift (WGS), pressure-swing adsorption (PSA) to fix the stoichiometric ratio $(\mathrm{H_2-CO_2})/(\mathrm{CO+CO_2}) = 3$, and finally three-stage catalytic methanation. The unit exposes a methanol input, a water input, an oxygen input (from an ASU or an electrolyser), an electricity input, an SNG output, and a CO₂ output (combining the PSA-separated CO₂ and the residual unconverted CO₂ from methanation).

The model couples two physical sub-units:

- **MeOHReform** — methanol autothermal reformer with HT-LT water-gas-shift reactors and PSA;
- **SyngasMethanator** — three-bed adiabatic methanator with interbed cooling and an SNG dryer.

## 1. Model card

| Field | Value |
|:------|:------|
| Model identifier | Methanol-to-SNG (ET) |
| Authors | Daniel Flórez-Orrego, Meire Domingos — EPFL IPESE |
| Contact | daniel.florezorrego@epfl.ch · oktay.boztas@epfl.ch |
| Version · Status | 1 · Maintained |
| Created · Updated | 2025-11-13 · 2025-11-13 |
| Confidentiality · Sharing layer | Open · 1 (fully shareable) |
| Model grade · TRL | Gray-box · 9 |
| Reference capacity | 56 681 kW of produced CH₄ (LHV) ≈ 4.08 t/h |
| Keywords | MeOH · SNG · Methanol reforming · Methanation · Synthetic natural gas |
| Description | Methanol reforming, WGS and PSA to get stoichiometric ratio for SNG production |
| Main publication | Domingos *et al.* — Techno-economic & environmental analysis (see [1]) |

## 2. Process description

Methanol is an attractive liquid hydrogen / carbon carrier: dense, transportable at ambient conditions, and convertible into pipeline-grade **synthetic natural gas (SNG)** through a catalytic chain that closes on the natural-gas grid. The reaction chain used in this model is:

1. **Autothermal reforming (ATR)** — methanol is reacted with steam and a sub-stoichiometric amount of oxygen at 350 °C and 35 bar; the partial-oxidation reaction supplies the heat for the endothermic steam-reforming reaction, so the overall reactor operates adiabatically:
$$\mathrm{CH_3OH + \tfrac{1}{2}\,O_2 \to CO_2 + 2H_2}, \qquad \mathrm{CH_3OH + H_2O \to CO_2 + 3H_2}.$$

2. **Water-gas-shift (WGS)** — a high-temperature followed by a low-temperature WGS reactor pushes the equilibrium toward more H₂ at the expense of CO and additional H₂O:
$$\mathrm{CO + H_2O \rightleftharpoons CO_2 + H_2}.$$

3. **Pressure-swing adsorption (PSA)** — a CO₂-selective PSA unit removes the bulk of the CO₂ at low pressure (1 bar) to bring the gas composition to the **methanation stoichiometric ratio** $(\mathrm{H_2-CO_2})/(\mathrm{CO+CO_2}) = 3$ required by the downstream catalytic methanator.

4. **Catalytic methanation** — three adiabatic fixed-bed methanators in series (with intercooling between beds) convert the conditioned syngas into CH₄ at 35 bar:
$$\mathrm{CO + 3H_2 \to CH_4 + H_2O}, \qquad \mathrm{CO_2 + 4H_2 \to CH_4 + 2H_2O}.$$

The dried product contains > 99 mass% CH₄ at 30 °C and 35 bar, ready for grid injection. The water of methanation is condensed and recovered; a small CO₂ slip from the methanator (~30 kg/h, unconverted) is vented together with the PSA-separated CO₂.

The model is **calibrated** to a fixed Hysys-simulation operating point. All operating temperatures, heat duties, and compressor powers are boundary parameters of the optimisation; the only model-level decisions are the unit's overall capacity multiplier and its position on the system heat cascade.

## 3. Block flow diagram

![Methanol-to-SNG plant: oxygen compression train (1→30 bar), methanol/water pumping and preheating (22→350 °C), ATR + HT-WGS + LT-WGS, PSA CO₂ removal, three-bed methanation at 35 bar with interbed cooling, SNG drying.](../Figures/MeOHtoSNG.svg){width=85%}

## 4. Parameters

All parameters in the source model are **boundary values** (fixed by the Hysys-simulation calibration). The literature parameters are the cost-correlation references and the LHV of methane.

### 4.1 Boundary (operating point)

**Feedstocks and products**

| Parameter | Symbol | Default | Unit |
|:----------|:-------|--------:|:-----|
| Methanol feed (to reformer, 350 °C / 35 bar) | $\dot m_{MeOH}$ | 12 103 | kg/h |
| Water feed (to reformer, 1 → 35 bar) | $\dot m_{H_2O,in}$ | 14 953 | kg/h |
| Water condensate (recovered) | $\dot m_{H_2O,cond}$ | 10 731 | kg/h |
| Oxygen feed (from ASU or electrolyser, 1 → 30 bar) | $\dot m_{O_2}$ | 1 760 | kg/h |
| ATR total feedstock (sum) | $\dot m_{ATR}$ | 28 815 | kg/h |
| Syngas to methanator (after WGS + PSA) | $\dot m_{syn,SNG}$ | 12 709 | kg/h |
| CO₂ separated in PSA (low-pressure vent) | $\dot m_{CO_2,PSA}$ | 5 375 | kg/h |
| CO₂ unconverted (from methanator) | $\dot m_{CO_2,unc}$ | 34 | kg/h |
| CH₄ product flow | $\dot m_{CH_4}$ | 4 081 | kg/h |
| Water of methanation (condensate) | $\dot V_{H_2O,meth}$ | 7.06 | m³/h |

**Reforming-section operating point**

| Step | Temperature in → out | Duty (kW) |
|:-----|:----------------------|----------:|
| O₂ compressor stage 1 intercooling (1 → 3 bar) | 156 → 35 °C | 55 |
| O₂ compressor stage 2 intercooling (3 → 10 bar) | 163 → 35 °C | 59 |
| O₂ compressor stage 3 intercooling (10 → 30 bar) | 163 → 35 °C | 61 |
| O₂ preheating to reactor entry | 50 → 350 °C | 145 |
| MeOH+water mixture preheating — stage 1 | 22 → 131 °C | 3 495 |
| MeOH+water vaporisation | 131 → 241 °C | 13 437 |
| Superheating to 350 °C | 241 → 350 °C | 1 894 |
| Post-WGS high-T cooling | 365 → 179 °C | 3 563 |
| Post-WGS low-T cooling (water condensation) | 179 → 30 °C | 10 022 |

**Methanation-section operating point**

| Step | Temperature in → out | Duty (kW) |
|:-----|:----------------------|----------:|
| Methanator feed preheating | 30 → 250 °C | 2 429 |
| Methanator bed 1 outlet cooling | 610 → 300 °C | 10 200 |
| Methanator bed 2 outlet cooling | 462 → 200 °C | 3 889 |
| Methanator bed 3 outlet cooling | 212 → 30 °C | 6 003 |

**Electricity consumption**

| Item | Symbol | Default | Unit |
|:-----|:-------|--------:|:-----|
| O₂ compressor stages 1 / 2 / 3 / 4 | $W_{O_2,1\dots 4}$ | 57 / 58 / 58 / 7 | kW |
| MeOH pump (1 → 35 bar) | $W_{p,MeOH}$ | 18 | kW |
| Water pump (1 → 35 bar) | $W_{p,H_2O}$ | 21 | kW |
| Total electricity demand | $W_{tot}$ | 219 | kW |

**$\Delta T_{min}$, financial assumptions**

| Parameter | Symbol | Default | Unit |
|:----------|:-------|--------:|:-----|
| $\Delta T_{min}$ for gas / liquid / two-phase | $\Delta T_{min,gas/liq/2ph}$ | 8 / 5 / 2 | °C |
| Equipment lifetime | $n$ | 40 | year |
| Interest rate | $i$ | 0.06 | – |
| CEPCI 2020 | $CEPCI_{2020}$ | 596.2 | – |

### 4.2 Literature

| Parameter | Symbol | Default | Unit | Source |
|:----------|:-------|--------:|:-----|:-------|
| Methane LHV | $LHV_{CH_4}$ | 50 000 | kJ/kg | Domingos *et al.* (see [1]) |
| Reforming-section specific CAPEX (per kg/h of ATR feedstock) | $c_{ref}$ | 1 000 | EUR/(kg/h) | Domingos *et al.* — 350 M EUR for 8 000 t/d ATR feedstock |
| Methanator specific CAPEX | $c_{meth}$ | 300 | EUR/kW | EPFL IPESE research group |

## 5. Derived quantities at the reference operating point

| Quantity | Symbol | Expression | Value | Unit |
|:---------|:-------|:-----------|------:|:-----|
| CH₄ energy flow (LHV) | $\dot Q_{CH_4}$ | $\dot m_{CH_4}\,LHV_{CH_4}/3600$ | 56 681 | kW |
| Annualisation factor | $a$ | $i(1+i)^{n}/((1+i)^{n}-1)$ | 0.0665 | – |
| Annualised CAPEX — reforming section | $C_{inv2,ref}$ | $\dot m_{ATR}\,c_{ref}\,a$ | 1.92 M | EUR/y |
| Annualised CAPEX — methanation section | $C_{inv2,meth}$ | $\dot Q_{CH_4}\,c_{meth}\,a$ | 1.13 M | EUR/y |
| Total annualised CAPEX | $C_{inv2,tot}$ | $C_{inv2,ref}+C_{inv2,meth}$ | 3.05 M | EUR/y |

## 6. Interfaces and heat streams

The plant exchanges six external resources with the surrounding system. Internally, the reforming and methanation sub-units share an intermediate syngas stream.

| Interface | Sub-unit | Direction / Type | Reference flow | T | P | Phase / Composition |
|:----------|:---------|:-----------------|---------------:|:--|:--|:--------------------|
| Methanol feed | Reforming | In · Mass | 12 103 kg/h | 30 °C | 1 bar | Liquid, CH₃OH (100 %) |
| Water feed | Reforming | In · Mass | 4 222 m³/h (≈ 14 953 kg/h) | 30 °C | 1 bar | Liquid, H₂O (100 %) |
| Oxygen feed | Reforming | In · Mass | 1 760 kg/h | 30 °C | 1 bar | Vapour, O₂ (100 %) |
| Electricity | Reforming + methanation | In · Electrical | 219 kW | – | – | – |
| Syngas (intermediate) | Reforming → Methanator | Internal · Mass | 12 709 kg/h | – | 35 bar | Vapour, molar 17.9 % CO₂ / 2.6 % CO / 79.5 % H₂ |
| Water condensate (methanation) | Methanator | Out · Mass | 7.06 m³/h | – | – | Liquid, H₂O |
| CO₂ (PSA + methanation slip) | Reforming + methanator | Out · Mass (emission) | 5 409 kg/h | 30 °C | 1 bar | Vapour, CO₂ (100 %) |
| SNG product | Methanator | Out · Mass | 4 081 kg/h (56 681 kW LHV) | 30 °C | 35 bar | Vapour, CH₄ (99 mass%) |

**Heat streams** (13 total): the reforming section exposes 9 streams (compressor intercoolings + mixture preheating + WGS effluent cooling) and the methanator exposes 4 (feed preheating + three bed-outlet coolings). The two single largest streams are the **mixture vaporisation** (13.4 MW, 131 → 241 °C, **cold** — needs to be heated) and the **first methanator-bed outlet cooling** (10.2 MW, 610 → 300 °C, **hot** — heat available at high grade). Matching these against high-temperature waste heat or steam on the system cascade is the main heat-integration opportunity of the unit.

A full per-stream table is given in §4.1 above.

## 7. Equipment and cost

The plant comprises a multi-stage centrifugal O₂ compressor train, centrifugal feed pumps (MeOH and water), a shell-and-tube heat-exchanger network, an autothermal fixed-bed reformer, a PSA unit, three adiabatic fixed-bed methanators (with their intercooler heat-exchanger network), and a molecular-sieve SNG dryer.

Capital cost is allocated to the two sub-sections:

$$C_{inv2,ref} \;=\; \dot m_{ATR}\,c_{ref}\,a, \qquad C_{inv2,meth} \;=\; \dot Q_{CH_4}\,c_{meth}\,a,$$

with $\dot m_{ATR}$ in kg/h, $\dot Q_{CH_4}$ in kW, and $a$ the discrete-compounding capital-recovery factor.

| Item | Value |
|:-----|:------|
| Reforming-section specific investment | 1 000 EUR/(kg/h) of ATR feedstock |
| Methanator specific investment | 300 EUR/kW of SNG output |
| Lifetime | 40 years |
| Interest rate | 0.06 |
| Capacity range — reforming sub-unit | 0 × to 1 000 × reference |
| Capacity range — methanator sub-unit | 0 × to 1 000 × reference |
| Fixed operating cost | 0 EUR/y |
| Variable operating cost | 0 EUR/h |

Operating costs are zero in the reference model — feedstock, utility, product, and emission flows enter the optimisation through the resource interfaces of §6.

## 8. References

1. Domingos, M. E. G. R. *et al.* *Techno-economic and environmental analysis of methanol and dimethyl ether production from syngas in a kraft pulp process.* <https://www.sciencedirect.com/science/article/pii/S009813542200148X>.
2. *Energy Conversion and Management* (2022). <https://www.sciencedirect.com/science/article/pii/S0196890422000413>.

## 9. Cite as

> Flórez-Orrego, D. & Domingos, M. *Methanol-to-SNG — Ex-ante energy-technology model (ET, v1).* IEA IETS Task XXIV / Subtask 1, Activity 3.1. EPFL IPESE, Lausanne, 2025. Contact: <daniel.florezorrego@epfl.ch>.
