---
title: "Organic Rankine Cycle — Energy Technology Model"
subtitle: "IEA IETS Task XXIV · Subtask 1 · Activity 3.1 (Energy Technologies)"
author: "Daniel Flórez-Orrego, EPFL IPESE research group"
date: "2026-04-16"
---

# Organic Rankine Cycle (ORC)

A grey-box, steady-state model of a **two-stage Organic Rankine Cycle** for waste-heat recovery and electricity generation. The reference configuration documented here uses **toluene** as the working fluid, with two evaporation pressures, two expansion stages, and a single low-temperature condenser. The unit exposes one electrical output and seven thermal streams that, together, represent the cycle's full heat-cascade footprint on the surrounding system (preheating + two-stage evaporation + intermediate cooling + condensation + regenerative recovery).

**Variants.** Four working-fluid / configuration variants exist for this unit (organic fluid; supercritical CO₂; transcritical CO₂; and a superstructure-based configuration covering several fluids and pressures). The cycle topology, the parameter groups, and the interfaces are the same across variants; only the working fluid, the saturation temperatures, and the heat duties differ. This document describes the organic-fluid (toluene) reference; the same template applies to the other variants.

## 1. Model card

| Field | Value |
|:------|:------|
| Model identifier | Organic Rankine Cycle (ET) |
| Authors | Daniel Flórez-Orrego — EPFL IPESE research group |
| Contact | daniel.florezorrego@epfl.ch · oktay.boztas@epfl.ch |
| Version · Status | 1.0.1 · Maintained |
| Created · Updated | 2026-04-16 · 2026-04-16 |
| Confidentiality · Sharing layer | Open · 1 (fully shareable) |
| Model grade · TRL | Gray-box · 9 |
| Reference capacity | 34 kW of net electrical output |
| Reference working fluid | Toluene |
| Keywords | Rankine Cycle · Waste-heat recovery · Power generation · Organic fluid · Electricity |
| Description | Organic Rankine Cycle for waste-heat recovery and electricity generation |

## 2. Process description

The **Organic Rankine Cycle (ORC)** is a Rankine power cycle that uses an organic, high-molecular-mass working fluid (toluene, hexamethyldisiloxane, R245fa, hydrocarbons or refrigerants more generally) instead of water/steam. The fluid's lower boiling temperature and lower critical temperature are exactly what allow the cycle to recover work from **low-grade heat sources** — biomass combustion, industrial waste heat, geothermal — where a water-steam Rankine cycle would be impractical (impossibly large turbines, sub-atmospheric condensers, freezing risk in low-temperature condensation).

Like the water Rankine cycle, the ORC closes on **four canonical processes**:

- 1 → 2: **isentropic compression** of the saturated liquid in a pump;
- 2 → 3: **constant-pressure heat addition** (preheating + evaporation) in the boiler;
- 3 → 4: **isentropic expansion** of the saturated vapour through a turbine (or screw / scroll expander), producing shaft work;
- 4 → 1: **constant-pressure heat rejection** (condensation) at the low-temperature sink, closing the cycle.

Real cycles depart from these idealised four steps in two physically distinct ways. **(i) Expander irreversibilities** — only part of the available enthalpy drop is converted into useful shaft work; the rest is dissipated as heat. This is captured in the model through an *isentropic efficiency* applied to each turbine stage. **(ii) Heat-exchanger irreversibilities** — pressure drops along the long, sinuous fluid path through the evaporator and condenser, plus exergy destruction associated with the finite temperature difference between the working fluid and the heat source/sink. These set the practical lower bound on the achievable temperature lift between the heat sources and the working fluid.

The reference configuration documented here is a **two-stage refinement** of the four-process Rankine cycle, with two evaporation pressures: the liquid working fluid is first pumped and preheated to the upper saturation temperature, evaporated, and expanded in a **first turbine** down to an intermediate pressure; the partially-expanded vapour is then re-heated (typically by a recuperator using turbine-outlet sensible heat) and re-evaporated at the intermediate saturation temperature, before being expanded in a **second turbine** to the condenser pressure. The vapour is condensed at the low-temperature heat sink, and the cycle is closed by two pumping stages back up to the evaporation pressures.

The net electrical output is the difference between the two turbine outputs and the two pumping powers,

$$W_{net} \;=\; W_{T_1} + W_{T_2} - W_{P_1} - W_{P_2}.$$

The model is **calibrated** to a fixed operating point (working fluid, saturation temperatures, intermediate pressure, and corresponding heat duties), reported below. The cycle's external interface is a single electrical output; its **internal** heat streams are exposed to the surrounding heat cascade so that the system optimisation can match the cycle's heat demands (preheating, evaporation, reheat) against available waste-heat sources, and the cycle's cooling duty (condenser) against available cold utilities.

## 3. Block flow diagram

![Two-stage Organic Rankine Cycle: working fluid is pumped, preheated, evaporated, expanded in a first turbine, reheated/re-evaporated, expanded in a second turbine, and condensed against a low-temperature sink.](../Figures/OrgRC.svg){width=80%}

## 4. Parameters

The reference operating point is fixed by the process-simulation calibration of the working fluid (toluene); all temperatures and duties are **boundary** parameters in the model. The only literature parameter is the working-fluid specific heat capacity, used in the heat-balance closure.

### 4.1 Boundary (working-fluid operating point)

| Parameter | Symbol | Default | Unit | Stage |
|:----------|:-------|--------:|:-----|:------|
| HX1 inlet / outlet (preheater) | $T_{HX1,in}$ / $T_{HX1,out}$ | 115.7 / 241.4 | °C | Liquid preheating to upper saturation |
| HX1 duty | $Q_{HX1}$ | 81.13 | kW | – |
| HX2 saturation T | $T_{HX2}$ | 241.2 | °C | Upper-pressure evaporation |
| HX2 duty | $Q_{HX2}$ | 69.2 | kW | – |
| First-turbine power | $W_{T_1}$ | 22.11 | kW | High-pressure expansion |
| HX3 inlet / outlet | $T_{HX3,in}$ / $T_{HX3,out}$ | 178.3 / 115 | °C | Recuperative inter-stage cooling |
| HX3 duty | $Q_{HX3}$ | 12.62 | kW | – |
| HX4 saturation T | $T_{HX4}$ | 115 | °C | Intermediate-pressure re-evaporation |
| HX4 duty | $Q_{HX4}$ | 45.36 | kW | – |
| Second-turbine power | $W_{T_2}$ | 12.57 | kW | Intermediate-pressure expansion |
| HX5 inlet / outlet | $T_{HX5,in}$ / $T_{HX5,out}$ | 125.3 / 34.18 | °C | Post-expansion desuperheating |
| HX5 duty | $Q_{HX5}$ | 18.67 | kW | – |
| HX6 condenser T | $T_{HX6}$ | 34.18 | °C | Low-pressure condensation |
| HX6 duty | $Q_{HX6}$ | 62.15 | kW | – |
| HX7 inlet / outlet | $T_{HX7,in}$ / $T_{HX7,out}$ | 34.22 / 115 | °C | Regenerative preheating |
| HX7 duty | $Q_{HX7}$ | 22.51 | kW | – |
| Pump powers | $W_{P_1}$ / $W_{P_2}$ | 0.620 / 0.026 | kW | Two pumping stages |
| $\Delta T_{min}$ for two-phase streams | $\Delta T_{min,2ph}$ | 2 | °C | – |
| Equipment lifetime | $n$ | 40 | year | – |
| Interest rate | $i$ | 0.06 | – | – |
| CEPCI (current / 2008) | $CEPCI_{2020}$ / $CEPCI_{2008}$ | 596.2 / 575.4 | – | – |

### 4.2 Literature

| Parameter | Symbol | Default | Unit | Source |
|:----------|:-------|--------:|:-----|:-------|
| Working-fluid specific heat (toluene at 150 °C) | $c_{p,fluid}$ | 2.2 | kJ/(kg·K) | Garg, Orosz & Kumar (2016) — see §8 |

## 5. Derived quantities at the reference operating point

| Quantity | Symbol | Expression | Value | Unit |
|:---------|:-------|:-----------|------:|:-----|
| Net electrical output | $W_{net}$ | $W_{T_1}+W_{T_2}-W_{P_1}-W_{P_2}$ | 34.03 | kW |
| Total CAPEX (specific = 1 000 EUR/kW) | $C_{inv,ORC}$ | $1000\,W_{net}$ | 34 034 | EUR |
| Annualisation factor | $a$ | $i(1+i)^{n}/((1+i)^{n}-1)$ | 0.0665 | – |
| Annualised investment cost | $C_{inv2,ORC}$ | $C_{inv,ORC}\,a$ | 2 344 | EUR/y |

The total CAPEX is implemented as a flat specific-investment correlation in the net electrical output, $C_{inv,ORC} \;=\; 1\,000 \cdot W_{net}$ EUR (with $W_{net}$ in kW). The reference value 34 034 EUR corresponds directly to $W_{net} = 34.034$ kW.

## 6. Interfaces and heat streams

The ORC exposes a single external interface — its net electrical output — and seven internal thermal streams that participate in the system heat cascade.

| Interface | Direction / Type | Reference flow | Notes |
|:----------|:-----------------|---------------:|:------|
| Net electricity output | Out · Electrical | 34.03 kW | Two turbines minus two pumps |

**Heat streams** — the cycle's working-fluid path exposes seven thermal segments (preheating, two evaporations, two expansions' post-cooling, the condenser, and a regenerative preheat). Source-data labels (Hot / Cold) and duties are reproduced as given.

| Name | Source label | Temperature range | Duty (kW) | Role in the cycle |
|:-----|:-------------|:------------------|----------:|:------------------|
| hex1 | Hot | 115.7 °C → 241.4 °C | 81.13 | Liquid preheating to upper saturation |
| hex2 | Hot | 241.2 °C (isothermal) | 69.20 | Upper-pressure evaporation |
| hex3 | Cold | 178.3 °C → 115 °C | 12.62 | Inter-stage cooling between the two turbines |
| hex4 | Cold | 115 °C (isothermal) | 45.36 | Intermediate-pressure re-evaporation |
| hex5 | Cold | 125.3 °C → 34.18 °C | 18.67 | Post-expansion desuperheating |
| hex6 | Cold | 34.18 °C (isothermal) | 62.15 | Condensation at the low-pressure sink |
| hex7 | Hot | 34.22 °C → 115 °C | 22.51 | Regenerative preheating |

All streams use $\Delta T_{min}/2 = 2$ °C for the two-phase segments. The cycle's heating demand (preheat + evaporations) and its rejection demand (desuperheat + condensation) together establish the cycle's footprint on the system heat cascade.

## 7. Equipment and cost

A single composite asset — the Rankine-cycle skid: two pumps, two evaporator heat exchangers, two turbines, one or more regenerative heat exchangers, and one condenser.

Capital cost is taken as a flat specific-investment correlation in the net electrical output:

$$C_{inv,ORC} \;=\; 1\,000 \cdot W_{net} \quad [\text{EUR}], \qquad C_{inv2,ORC} \;=\; C_{inv,ORC}\,\dfrac{i(1+i)^{n}}{(1+i)^{n}-1}.$$

| Item | Value |
|:-----|:------|
| Equipment subtype | Organic Rankine Cycle (turbines + pumps + heat exchangers + condenser) |
| Lifetime | 40 years |
| Interest rate | 0.06 |
| Specific investment | 1 000 EUR/kWₑₗ |
| Capacity range | 0 × to 100 000 × reference |
| Fixed operating cost | 0 EUR/y |
| Variable operating cost | 0 EUR/h |

Operating costs are zero in the reference model — the only resource exchanged through external interfaces is electricity (output).

## 8. References

1. Garg, P., Orosz, M. S. & Kumar, P. (2016). *Thermo-economic evaluation of ORCs for various working fluids.* **Applied Thermal Engineering** **109** B, 841–853. DOI: <https://doi.org/10.1016/j.applthermaleng.2016.06.083>.
2. Turton, R. *et al.* (2012). **Analysis, Synthesis, and Design of Chemical Processes** (4th ed.), Prentice Hall.
3. Bruno, J. C. *et al.* (1998). — generic ORC techno-economic correlation.

## 9. Cite as

> Flórez-Orrego, D. *Organic Rankine Cycle — Ex-ante energy-technology model (ET, v1.0.1).* IEA IETS Task XXIV / Subtask 1, Activity 3.1. EPFL IPESE, Lausanne, 2026. Contact: <daniel.florezorrego@epfl.ch>.
