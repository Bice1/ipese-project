---
title: "Cooling Tower — Energy Technology Model"
subtitle: "IEA IETS Task XXIV · Subtask 1 · Activity 3.1 (Energy Technologies)"
author: "Daniel Flórez-Orrego, EPFL IPESE research group"
date: "2026-03-24"
---

# Cooling Tower

A grey-box, steady-state model of a **wet evaporative cooling tower** acting as a cold utility for process integration studies. The unit exposes one hot heat stream (the cooling-water loop), an electricity input (recirculation pumps and fans), and a makeup-water input. It is intended for high-level optimisation problems in which the size and the existence of the cold utility are decision variables; only wet evaporative cooling is in scope.

## 1. Model card

| Field | Value |
|:------|:------|
| Model identifier | Cooling Tower (ET) |
| Authors | Daniel Flórez-Orrego, EPFL IPESE research group |
| Contact | daniel.florezorrego@epfl.ch · oktay.boztas@epfl.ch |
| Version · Status | 1.0.1 · Maintained |
| Created · Updated | 2025-06-01 · 2026-03-24 |
| Confidentiality · Sharing layer | Open · 1 (fully shareable) |
| Model grade · TRL | Grey box · 9 |
| Reference capacity | 100 000 kW of cooling duty |
| Keywords | Cold utility · Cooling water · Electricity · Evaporation |
| Main publication | <https://www.sciencedirect.com/science/article/pii/S0959652619335176> |

## 2. Process description

Industrial processes typically reject a large amount of waste heat that cannot be further integrated with other process streams. When that excess heat must be removed by water-based cooling, a cooling tower is the standard cold utility: circulating water collects heat from the process and is then sprayed in counter-flow with ambient air, lowering its temperature by evaporative cooling before being pumped back to the process.

The cooling tower can reach temperatures below the dry-bulb air temperature thanks to evaporation; the achievable cold-side temperature is bounded from below by the **wet-bulb temperature** $T_{wb}$, computed here from $T_{db}$ and the relative humidity $\varphi$ via the Stull (2011) correlation. The difference $\Delta T_{approach} = T_{Cool,in} - T_{wb}$ is the main design lever and the dominant driver of capital cost. The temperature difference between return and supply (the *range* $\Delta T_{range}$) together with the heat capacity of water sets the circulating mass flow via the steady-state energy balance $Q_{Cool,max} = \dot m_{water}\,c_{p,water}\,\Delta T_{range}$.

In addition to the heat stream the tower consumes auxiliary **electricity** for pumps and fans (~0.021 kWₑ/kWₜₕ) and a small flow of **makeup water** to compensate evaporation, drift, and blowdown losses (modelled by a single empirical correlation, see §4).

## 3. Block flow diagram

![Wet evaporative cooling tower: cold water leaves at $T_{Cool,in}$ and returns warm at $T_{Cool,out}$, with auxiliary electricity for fans/pumps and a makeup-water input.](../Figures/CoolTower.svg){width=75%}

## 4. Parameters

Parameters are grouped by their role — **Decision** (chosen by the modeller / optimiser), **Boundary** (operating environment, $\Delta T_{min}$ contributions, financial assumptions), **Literature** (from published correlations or handbooks). Bounds give the range over which the model is considered applicable.

### 4.1 Decision

| Parameter | Symbol | Default | Min | Max | Unit |
|:----------|:-------|--------:|----:|----:|:-----|
| Cooling-tower supply temperature | $T_{Cool,in}$ | 13 | 5 | 20 | °C |

### 4.2 Boundary

| Parameter | Symbol | Default | Min | Max | Unit |
|:----------|:-------|--------:|----:|----:|:-----|
| Return temperature | $T_{Cool,out}$ | 30 | 25 | 40 | °C |
| Dry-bulb temperature | $T_{db}$ | 20 | −10 | 45 | °C |
| Relative humidity | $\varphi$ | 40 | 10 | 100 | % |
| Wet-bulb temperature (Stull 2011) | $T_{wb}$ | 12.32 | −15 | 30 | °C |
| $\Delta T_{min}$ — gas / liquid / 2-phase | $\Delta T_{min,gas/liq/2ph}$ | 8 / 5 / 2 | – | – | °C |
| Lifetime · interest rate | $n$ · $i$ | 40 · 0.06 | – | – | year · – |
| CEPCI (current / 2008) | $CEPCI_{2020}$ / $CEPCI_{2008}$ | 596.2 / 575.4 | – | – | – |

### 4.3 Literature

| Parameter | Symbol | Default | Unit | Source |
|:----------|:-------|--------:|:-----|:-------|
| Specific heat capacity of water | $c_{p,water}$ | 4.2 | kJ/(kg·K) | Perry's Handbook |
| Reference cooling duty | $Q_{Cool,max}$ | 100 000 | kW | Florez-Orrego et al., ECOS 2105 |
| Auxiliary electricity ratio | $\eta_{el/th}$ | 0.021 | kWₑ/kWₜₕ | MARLEY |

## 5. Derived quantities at the reference operating point

Values shown for $Q_{Cool,max}=100$ MW, $T_{db}=20$ °C, $\varphi=40$ %, $T_{Cool,in}=13$ °C, $T_{Cool,out}=30$ °C — useful as a sanity-check anchor for re-implementations.

| Quantity | Symbol | Expression | Value | Unit |
|:---------|:-------|:-----------|------:|:-----|
| Auxiliary electricity | $E_{ref,CT}$ | $\eta_{el/th}\,Q_{Cool,max}$ | 2 100 | kW |
| Range | $\Delta T_{range}$ | $T_{Cool,out} - T_{Cool,in}$ | 17 | K |
| Approach | $\Delta T_{approach}$ | $T_{Cool,in} - T_{wb}$ | 0.68 | K |
| Circulating water flow | $\dot m_{water}$ | $Q_{Cool,max}/(c_{p,water}\,\Delta T_{range})\cdot 3.6$ | 5 042 | t/h |
| Makeup-water flow | $\dot V_{water,mu}$ | $0.00085\cdot 1.8\cdot (\dot m_{water}/\rho_{water})\cdot \Delta T_{range}$, with $\rho_{water}\approx 1$ t/m³ | 131 | m³/h |
| Annualisation factor | $a$ | $i(1+i)^{n}/((1+i)^{n}-1)$ | 0.0665 | – |
| Total investment cost | $C_{T,cost}$ | see §7 | 25.5 M | EUR (2008) |
| Annualised investment cost | $C_{inv2,CT}$ | $C_{T,cost}\cdot(CEPCI_{2020}/CEPCI_{2008})\cdot a$ | 1.75 M | EUR/y |

## 6. Interfaces and heat stream

| Interface | Direction | Type | Reference flow | T | P | Phase / Composition |
|:----------|:----------|:-----|---------------:|:--|:--|:--------------------|
| Auxiliary electricity | In | Electrical | 2 100 kW | – | – | – |
| Makeup water | In | Mass | 131 m³/h | 25 °C | 1 bar | Liquid H₂O |
| Cooling-water heat stream | Hot | Thermal | 100 000 kW | 13 °C → 30 °C | – | Liquid water; $\Delta T_{min}/2 = 5$ °C; reference stream |

The cooling-water stream is the **hot side** of a heat-exchange interaction from the optimisation's point of view (heat is rejected from the process into the cooling water).

## 7. Equipment and cost

Capital cost is taken from the empirical correlation reported in *Int. J. Environ. Sci. Tech.* **5**(2), 251–262 (2008), with EUR 2008 basis:

$$C_{T,cost} \;=\; \tfrac{746.49}{0.066}\;\dot m_{water}^{\,0.79}\,\Delta T_{range}^{\,0.57}\,\Delta T_{approach}^{-0.9924}\,(0.022\,T_{wb}+0.39)^{2.447} \quad[\text{EUR}_{2008}].$$

Updated to the cost-evaluation year via $CEPCI_{target}/CEPCI_{2008}$ and annualised over $n$ via $a$. Capacity range: 0 × to 100 × $Q_{Cool,max}$, intended for single-tower duties of roughly 10 MW – 500 MW. Fixed and variable operating costs are deliberately zero — consumables (electricity, makeup water) enter through the resource interfaces of §6, not as lumped operating costs.

## 8. References

1. *Int. J. Environ. Sci. Tech.* **5** (2), 251–262 (2008) — cost correlation.
2. Florez-Orrego, D. *et al.*, ECOS 2105 — reference operating parameters.
3. Stull, R. *Wet-Bulb Temperature from Relative Humidity and Air Temperature*, **2011**. DOI: [10.1175/JAMC-D-11-0143.1](https://doi.org/10.1175/JAMC-D-11-0143.1).
4. *Perry's Chemical Engineers' Handbook* — water properties.
5. SPX Cooling Technologies — <https://spxcooling.com/coolingtowers>.
6. MARLEY. *Cooling Tower energy and its management* — auxiliary-electricity ratio.

## 9. Cite as

> Flórez-Orrego, D. *Cooling Tower — Ex-ante energy-technology model (ET, v1.0.1).* IEA IETS Task XXIV / Subtask 1, Activity 3.1. EPFL IPESE, Lausanne, 2026. Contact: <daniel.florezorrego@epfl.ch>.
