---
title: "Reverse Water-Gas Shift reactor with recycle — Energy Technology Model"
subtitle: "IEA IETS Task XXIV · Subtask 1 · Activity 3.1 (Energy Technologies)"
author: "Daniel Flórez-Orrego, EPFL IPESE research group"
date: "2026-04-21"
---

# Reverse Water-Gas Shift (rWGS) reactor with recycle

A grey-box, steady-state model of a **reverse water-gas shift (rWGS) reactor with feed recycle**, converting CO₂ and H₂ into a syngas (CO + H₂) suitable for downstream Fischer–Tropsch or methanol synthesis. The unit exposes a CO₂ input, a hydrogen input, an electricity input (for the multi-stage compression of the reactants and the recycle), a water-condensate output, and a syngas output. Its heat content is represented by ten thermal streams capturing the compressor intercoolings (eight hot streams) and the high-temperature reactor preheating + endothermic duty (two cold streams).

## 1. Model card

| Field | Value |
|:------|:------|
| Model identifier | Reverse WGS reactor with recycle (ET) |
| Authors | Daniel Flórez-Orrego — EPFL IPESE research group |
| Contact | daniel.florezorrego@epfl.ch · oktay.boztas@epfl.ch |
| Version · Status | 1.0.1 · Maintained |
| Created · Updated | 2026-04-21 · 2026-04-21 |
| Confidentiality · Sharing layer | Open · 1 (fully shareable) |
| Model grade · TRL | Gray-box · 9 |
| Reference capacity | 46 069 kg/h of produced syngas (≈ 321 MW LHV) |
| Keywords | Syngas · CO₂ · Hydrogen |
| Description | Reverse WGS reactor with recycle |

## 2. Process description

The **reverse water-gas shift** reaction is the back-conversion of CO₂ and H₂ to CO and H₂O:

$$\mathrm{CO_2 + H_2 \;\rightleftharpoons\; CO + H_2O}, \qquad \Delta H^\circ_{rxn} \approx +41\ \mathrm{kJ/mol}\ \text{(endothermic)}.$$

The reaction is mildly endothermic and equilibrium-limited at low temperature, so it is conducted in a high-temperature reactor (here at 750 °C) over a Ni- or Pt-based catalyst, where the equilibrium shifts strongly to the right. The water produced is condensed at the reactor outlet and removed from the syngas; the unconverted CO₂ and H₂ are compressed and recycled back into the reactor feed. The product, after water knock-out, is a CO/H₂-rich syngas with a small CH₄ slip (reference composition ≈ 63 mol% H₂, 32 mol% CO, 4 mol% CH₄, 1 mol% H₂O), ready to be further compressed to the operating pressure of a downstream Fischer–Tropsch (≈ 41 bar) or methanol (≈ 35 bar) plant.

The model represents the rWGS reactor together with its **upstream compression train** (two-stage compression of H₂ and CO₂ from 1 bar to the reactor pressure of 5 bar), the **recycle compressor**, and the **product cooling and water knock-out** train. Operating temperatures, heat duties, and compressor powers are taken from a process simulation (Hysys) at the reference operating point and treated as fixed boundary conditions in the optimisation model; the only model-level decisions are the unit's capacity multiplier and the overall mass flow.

The reactor's preheating and endothermic duty are matched by the system heat cascade against the high-temperature heat sources available in the wider system (electrified heating, recovered heat from a high-temperature electrolyser or a downstream Fischer–Tropsch reactor, etc.).

## 3. Block flow diagram

![rWGS reactor with recycle: H₂ and CO₂ are multi-stage compressed to 5 bar (intercoolings q_hot1…4), preheated and reacted at 750 °C (q_cold1–2), then cooled and depressurised; water is knocked out, unconverted reactants are recycled.](../Figures/ReverseWGS.svg){width=85%}

## 4. Parameters

All parameters in the source model are **boundary values** (operating point fixed by a process simulation). There are no internal optimiser decisions beyond the unit's capacity multiplier; the literature parameters are the equipment cost references and the financial / index assumptions.

### 4.1 Boundary

| Parameter | Symbol | Default | Unit |
|:----------|:-------|--------:|:-----|
| CO₂ input mass flow | $\dot m_{CO_2}$ | 66 014 | kg/h |
| H₂ input mass flow | $\dot m_{H_2}$ | 9 421 | kg/h |
| Syngas output mass flow | $\dot m_{syngas}$ | 46 069 | kg/h |
| Water condensate output | $\dot V_{H_2O}$ | 29.36 | m³/h |
| Syngas LHV | $LHV_{syngas}$ | 25 094 | kJ/kg |
| Reactor inlet / outlet temperatures | $T_{rxn,in}$ / $T_{rxn,out}$ | 700 / 750 | °C |
| Reactor preheating duty (28.9 °C → 700 °C) | $Q_{cold,1}$ | 48 387 | kW |
| Reactor endothermic duty (700 °C → 750 °C) | $Q_{cold,2}$ | 7 606 | kW |
| Product cooling — 750 °C → 99 °C | $Q_{hot,5}$ | 48 387 | kW |
| Product subcooling — 99 °C → 30 °C | $Q_{hot,6}$ | 20 310 | kW |
| H₂ compressor intercooling — 1st / 2nd stage | $Q_{hot,1}$ / $Q_{hot,2}$ | 5 029 / 2 880 | kW |
| CO₂ compressor intercooling — 1st / 2nd stage | $Q_{hot,3}$ / $Q_{hot,4}$ | 1 435 / 1 053 | kW |
| Recycle compressor intercooling — 1st / 2nd stage | $Q_{hot,7}$ / $Q_{hot,8}$ | 747 / 1 065 | kW |
| H₂ compression power (1→5 bar, two-stage) | $W_{H_2}$ | 7 909 | kW |
| CO₂ compression power (1→5 bar, two-stage) | $W_{CO_2}$ | 2 420 | kW |
| Recycle compression power (two-stage) | $W_{rec}$ | 1 745 | kW |
| $\Delta T_{min}$ for gas streams | $\Delta T_{min,gas}$ | 8 | °C |
| $\Delta T_{min}$ for two-phase streams | $\Delta T_{min,2ph}$ | 2 | °C |
| Equipment lifetime | $n$ | 25 | year |
| Interest rate | $i$ | 0.06 | – |
| CEPCI (current / 2008) | $CEPCI_{2020}$ / $CEPCI_{2008}$ | 596.2 / 575.4 | – |

### 4.2 Literature

| Parameter | Symbol | Default | Unit | Source |
|:----------|:-------|--------:|:-----|:-------|
| rWGS specific CAPEX (per kW of reactor heat duty) | $c_{rWGS}$ | 200 | EUR/kW_th | Adelung *et al.* (2021) — see §8 |

## 5. Derived quantities at the reference operating point

| Quantity | Symbol | Expression | Value | Unit |
|:---------|:-------|:-----------|------:|:-----|
| Syngas energy flow (LHV) | $\dot Q_{syngas}$ | $\dot m_{syngas}\,LHV_{syngas}/3600$ | 321 126 | kW |
| Total compression power (rWGS reactants + recycle) | $W_{rWGS}$ | $W_{H_2}+W_{CO_2}+W_{rec}$ | 12 074 | kW |
| Reactor cost-basis heat duty (high-T fraction) | $Q_{cost}$ | $0.4\,Q_{cold,1}+Q_{cold,2}$ | 26 961 | kW_th |
| Annualisation factor | $a$ | $i(1+i)^{n}/((1+i)^{n}-1)$ | 0.0782 | – |
| Annualised investment cost | $C_{inv2,rWGS}$ | $c_{rWGS}\,Q_{cost}\,(CEPCI_{2020}/CEPCI_{2008})\,a$ | 437 059 | EUR/y |

The cost-basis duty $Q_{cost}$ takes only 40 % of the low-temperature preheating duty (since the temperature lift 450 → 750 °C corresponds to ~40 % of the full 30 → 750 °C lift in the reactor's heat balance), plus the full endothermic duty $Q_{cold,2}$. Two additional downstream-compression duties are exposed for the case studies feeding either a Fischer–Tropsch plant (syngas compression to 41 bar, $W_{FT}=9\ 442$ kW) or a methanol plant (compression to 35 bar, $W_{MeOH}=8\ 692$ kW); these are not part of the rWGS unit itself.

## 6. Interfaces and heat streams

The rWGS reactor exchanges five resources with the surrounding system and exposes ten thermal streams on the heat cascade.

| Interface | Direction / Type | Reference flow | T | P | Phase / Composition |
|:----------|:-----------------|---------------:|:--|:--|:--------------------|
| CO₂ feed | In · Mass | 66 014 kg/h | 30 °C | 1 bar | Vapour, CO₂ (100 %) |
| H₂ feed | In · Mass | 9 421 kg/h | 30 °C | 1 bar | Vapour, H₂ (100 %) |
| Electricity (compressors) | In · Electrical | 12 074 kW | – | – | – |
| Water condensate | Out · Mass | 29.36 m³/h | 25 °C | 1 bar | Liquid, H₂O |
| Syngas product | Out · Mass | 46 069 kg/h | 30 °C | 1 bar | Vapour, molar CH₄/H₂O/CO/H₂ ≈ 4.2 / 1.1 / 31.6 / 63.1 % |

**Heat streams** ($\Delta T_{min}/2 = 4$ °C for gases, 1 °C for two-phase).

| Name | Type | Inlet T → Outlet T | Duty | Description |
|:-----|:-----|:--------------------|-----:|:------------|
| q_rWGS_cold1 | Cold | 28.9 °C → 700 °C | 48 387 kW | Reactor feed preheating |
| q_rWGS_cold2 | Cold | 700 °C → 750 °C | 7 606 kW | rWGS endothermic reactor duty |
| q_rWGS_hot5 | Hot | 750 °C → 99 °C | 48 387 kW | Reactor product cooling |
| q_rWGS_hot6 | Hot | 99 °C → 30 °C | 20 310 kW | Reactor product subcooling (water condensation) |
| q_rWGS_hot1 | Hot | 165 °C → 30 °C | 5 029 kW | H₂ compressor — 1st-stage intercooling |
| q_rWGS_hot2 | Hot | 108 °C → 30 °C | 2 880 kW | H₂ compressor — 2nd-stage intercooling |
| q_rWGS_hot3 | Hot | 116 °C → 30 °C | 1 435 kW | CO₂ compressor — 1st-stage intercooling |
| q_rWGS_hot4 | Hot | 93 °C → 30 °C | 1 053 kW | CO₂ compressor — 2nd-stage intercooling |
| q_rWGS_hot7 | Hot | 91.5 °C → 30 °C | 747 kW | Recycle compressor — 1st-stage intercooling |
| q_rWGS_hot8 | Hot | 116 °C → 30 °C | 1 065 kW | Recycle compressor — 2nd-stage intercooling |

The high-temperature cold streams ($q_{cold,1}$ and $q_{cold,2}$) are the dominant driver of the integration with the rest of the system: they must be matched by hot streams above 700 °C (e.g. high-temperature electrified heating, hot exhaust from a downstream Fischer–Tropsch reactor, or a high-temperature solid-oxide electrolyser).

## 7. Equipment and cost

A single reactor asset (refractory reactor for the high-temperature endothermic step) plus the compression train. Capital cost is taken as a specific-investment correlation in the reactor's effective heat duty $Q_{cost}$ (high-temperature fraction of the preheating duty plus the endothermic duty):

$$C_{inv2,rWGS} \;=\; c_{rWGS}\,Q_{cost}\,\dfrac{CEPCI_{2020}}{CEPCI_{2008}}\,a \quad [\text{EUR/y}],$$

with $c_{rWGS}=200$ EUR/kW_th and $Q_{cost}=0.4\,Q_{cold,1}+Q_{cold,2}$.

| Item | Value |
|:-----|:------|
| Equipment subtype | Refractory reactor (rWGS) |
| Lifetime | 25 years |
| Interest rate | 0.06 |
| Specific investment | 200 EUR/kW_th |
| Capacity range | 0 × to 100 × reference |
| Fixed operating cost | 0 EUR/y |
| Variable operating cost | 0 EUR/h |

Operating costs are zero in the reference model — feedstocks (CO₂, H₂) and electricity enter the optimisation through the resource interfaces of §6.

## 8. References

1. Hysys process-simulation model (internal); calibrated against Adelung & Meurer (see [2] and below).
2. Adelung, S., Maier, S. & Dietrich, R.-U. (2021). *Impact of the reverse water-gas shift operating conditions on the Power-to-Liquid process efficiency.* **Sustainable Energy Technologies and Assessments** **43**, 100897.
3. Samimi, F., Hamedi, N. & Rahimpour, M. R. (2019). *Green methanol production process from indirect CO₂ conversion: RWGS reactor versus RWGS membrane reactor.* **Journal of Environmental Chemical Engineering** **7** (1), 102813.

## 9. Cite as

> Flórez-Orrego, D. *Reverse WGS reactor with recycle — Ex-ante energy-technology model (ET, v1.0.1).* IEA IETS Task XXIV / Subtask 1, Activity 3.1. EPFL IPESE, Lausanne, 2026. Contact: <daniel.florezorrego@epfl.ch>.
