---
title: "Gas Turbine — Energy Technology Model"
subtitle: "IEA IETS Task XXIV · Subtask 1 · Activity 3.1 (Energy Technologies)"
author: "Daniel Flórez-Orrego, Meire Domingos — EPFL IPESE"
date: "2025-11-12"
---

# Gas Turbine

A grey-box, steady-state model of an **open-cycle gas turbine** with **internal recuperation**, producing net electrical power from a gaseous fuel (natural gas in the reference case) and rejecting a residual hot exhaust stream to the environment. The unit exposes a fuel input (natural gas), a net electricity output, a CO₂-in-flue-gas output, and two heat streams that together represent the recuperator (turbine exhaust → compressed-air preheating).

## 1. Model card

| Field | Value |
|:------|:------|
| Model identifier | Gas Turbine (ET) |
| Authors | Daniel Flórez-Orrego, Meire Domingos — EPFL IPESE |
| Contact | daniel.florezorrego@epfl.ch · oktay.boztas@epfl.ch |
| Version · Status | 1.0.1 · Maintained |
| Created · Updated | 2025-11-12 · 2025-11-12 |
| Confidentiality · Sharing layer | Open · 1 (fully shareable) |
| Model grade · TRL | Gray-box · 9 |
| Reference capacity | 929 kWₑₗ (net) |
| Keywords | Gas Turbine · Natural Gas · Electricity |
| Description | Gas turbine unit model including a recuperator for waste heat recovery |

## 2. Process description

Gas turbines play a key role in electricity generation, propulsion, and cogeneration in modern industrial processes. They start up quickly, have few moving parts, and offer high reliability and low maintenance. They can drive compressors, pumps, and generators directly, or — in combined-cycle configurations — supply a steam bottoming cycle from the exhaust to lift the overall efficiency. They run on a wide variety of fuels (natural gas, diesel, biofuels, syngas from biomass gasification).

The unit modelled here is an **open-cycle gas turbine with recuperator**. Fresh air at ambient temperature $T_1$ and pressure $P_1$ enters the **compressor**, where its temperature and pressure are raised to $T_2$ and $P_2 = PR\cdot P_1$ at the cost of a shaft work $W_{1\to 2}$. The high-pressure air is then **preheated** in the recuperator up to $T_{2a}$ by recovering heat from the turbine exhaust. It enters the **combustion chamber**, where the fuel is burned at nearly constant pressure; the resulting hot gases enter the **turbine** at $T_3$ and expand back to $P_1$, producing shaft work $W_{3\to 4}$. The exhaust gases leaving the turbine at $T_4$ are first cooled in the recuperator (releasing heat $Q_4$ to the preheating side) before being released to the stack at $T_{stack}$.

The net electric output is the difference between the turbine and the compressor work: $W_{el,net} = W_{3\to 4} - W_{1\to 2}$. The fuel demand follows from the air-to-fuel mass ratio $f$ and the lower heating value $LHV$: $\dot Q_{fuel} = \dot m_{air}/f \cdot LHV$. CO₂ emissions are computed stoichiometrically from the natural-gas consumption assuming pure methane (44/16 kg of CO₂ per kg of CH₄). Air-to-fuel ratios of 50 or higher are typical: the excess air also serves as a coolant for the turbine blades.

A gas turbine, like any thermal cycle, is bounded by the Carnot efficiency $1 - T_o/T_{chamber}$; commercial standalone gas turbines operate at 20–40 % thermal efficiency, the rest of the energy leaving as exhaust heat $Q_4$ that the recuperator (and in combined-cycle configurations, a steam bottoming cycle) recovers.

## 3. Block flow diagram

![Open-cycle gas turbine with recuperator: compressor (1→2), air preheater (2→2a), combustion chamber (2a→3), turbine (3→4), recuperator exhaust side (4→stack).](../Figures/GasTurbine.svg){width=80%}

## 4. Parameters

Parameters are grouped by their role — **Decision** (chosen by the modeller / optimiser), **Boundary** (operating environment, $\Delta T_{min}$ contributions, financial assumptions), **Literature** (thermodynamic constants, cost indices).

### 4.1 Decision

| Parameter | Symbol | Default | Min | Max | Unit |
|:----------|:-------|--------:|----:|----:|:-----|
| Compressor isentropic efficiency | $\eta_{comp}$ | 0.80 | 0.60 | 0.95 | – |
| Turbine isentropic efficiency | $\eta_{turb}$ | 0.80 | 0.60 | 0.95 | – |
| Air inlet temperature | $T_1$ | 298 | 233.15 | 323.15 | K |
| Preheated-air temperature (after recuperator) | $T_{2a}$ | 873 | 300 | 1 100 | K |
| Compressor pressure ratio | $PR$ | 15 | 1.1 | 60 | – |
| Air-to-fuel mass ratio | $f$ | 60 | 30 | 150 | kg/kg |
| Air mass flow | $\dot m_{air}$ | 4 | 0.1 | 1 500 | kg/s |
| Stack temperature (after recuperator) | $T_{stack}$ | 423 | 353.15 | 800 | K |

### 4.2 Boundary

| Parameter | Symbol | Default | Min | Max | Unit |
|:----------|:-------|--------:|----:|----:|:-----|
| Equipment lifetime | $n$ | 40 | 5 | 60 | year |
| Interest rate | $i$ | 0.06 | 0.01 | 0.25 | – |
| $\Delta T_{min}$ for the recuperator | $\Delta T_{min}$ | 5 | 1 | 100 | K |

### 4.3 Literature

| Parameter | Symbol | Default | Unit | Source |
|:----------|:-------|--------:|:-----|:-------|
| Air specific-heat ratio | $\gamma_{air}$ | 1.40 | – | EPFL IPESE research group |
| Flue-gas specific-heat ratio | $\gamma_{gas}$ | 1.33 | – | EPFL IPESE research group |
| Air specific heat capacity | $c_{p,air}$ | 1.006 | kJ/(kg·K) | EPFL IPESE research group |
| Flue-gas specific heat capacity | $c_{p,gas}$ | 1.151 | kJ/(kg·K) | EPFL IPESE research group |
| Lower heating value of fuel | $LHV$ | 50 000 | kJ/kg | EPFL IPESE research group |
| CEPCI (current / 2008) | $CEPCI_{2020}$ / $CEPCI_{2008}$ | 596.2 / 575.4 | – | EPFL IPESE research group |

## 5. Derived quantities at the reference operating point

Values shown for $\dot m_{air}=4$ kg/s, $PR=15$, $T_1=298$ K, $T_{2a}=873$ K, $T_{stack}=423$ K, $f=60$, $\eta_{comp}=\eta_{turb}=0.80$, $LHV=50$ MJ/kg.

| Quantity | Symbol | Expression | Value | Unit |
|:---------|:-------|:-----------|------:|:-----|
| Air thermodynamic ratio | $\gamma_a$ | $(\gamma_{air}-1)/\gamma_{air}$ | 0.286 | – |
| Gas thermodynamic ratio | $\gamma_g$ | $(\gamma_{gas}-1)/\gamma_{gas}$ | 0.248 | – |
| Compressor pressure-ratio factor | $R_{pa}$ | $(PR^{\gamma_a}-1)/\eta_{comp}$ | 1.46 | – |
| Turbine pressure-ratio factor | $R_{pg}$ | $1 - 1/PR^{\gamma_g}$ | 0.489 | – |
| Compressor discharge temperature | $T_2$ | $T_1\,(1+R_{pa})$ | 733 | K |
| Turbine inlet temperature | $T_3$ | $\dfrac{\dot m_{air}\,c_{p,air}\,T_{2a}+\dot m_{air}/f\cdot LHV}{(1+1/f)\,\dot m_{air}\,c_{p,gas}}$ | 1 463 | K |
| Turbine outlet temperature | $T_4$ | $T_3(1-\eta_{turb}\,R_{pg})$ | 890 | K |
| Compressor work | $W_{1\to 2}$ | $\dot m_{air}\,c_{p,air}\,T_1\,R_{pa}$ | 1 751 | kW |
| Turbine work | $W_{3\to 4}$ | $\dot m_{air}\,(1+1/f)\,c_{p,gas}\,T_3\,R_{pg}\,\eta_{turb}$ | 2 680 | kW |
| Recuperator duty (preheating) | $Q_{2a}$ | $\dot m_{air}\,c_{p,air}\,(T_{2a}-T_2)$ | 563 | kW |
| Recoverable waste heat (turbine → stack) | $Q_4$ | $\dot m_{air}\,(1+1/f)\,c_{p,gas}\,(T_4-T_{stack})$ | 2 187 | kW |
| Fuel demand | $\dot Q_{fuel}$ | $\dot m_{air}/f \cdot LHV$ | 3 333 | kW |
| CO₂ emissions (from CH₄) | $\dot m_{CO_2}$ | $\dot Q_{fuel}/LHV \cdot 3600 \cdot 44/16$ | 660 | kg/h |
| Net electric output | $W_{el,net}$ | $W_{3\to 4} - W_{1\to 2}$ | 929 | kW |
| Annualisation factor | $a$ | $i(1+i)^{n}/((1+i)^{n}-1)$ | 0.0665 | – |
| Annualised investment cost | $C_{inv2,GT}$ | see §7 | 30 880 | EUR/y |

## 6. Interfaces and heat streams

The gas turbine exchanges three external resources and two internal heat streams (the recuperator's hot and cold sides).

| Interface | Direction / Type | Reference flow | T | P | Phase / Composition |
|:----------|:-----------------|---------------:|:--|:--|:--------------------|
| Natural gas | In · Energy/Mass | 3 333 kW | 25 °C | 1 bar | Vapour, CH₄ (100 %) |
| Electricity (net) | Out · Electrical | 929 kW | – | – | – |
| CO₂ in flue gas | Out · Mass (emission) | 660 kg/h | 25 °C | 1 bar | Vapour, CO₂ (100 %) |
| Waste-heat stream (turbine exhaust → stack) | Hot thermal | 2 187 kW | 617 °C → 150 °C | – | Flue gas; $\Delta T_{min}/2 = 5$ K, $\alpha = 0.06$ |
| Recuperator preheating (compressor discharge → combustion chamber) | Cold thermal | 563 kW | 460 °C → 600 °C | – | Air; $\Delta T_{min}/2 = 5$ K, $\alpha = 0.06$ |

The hot and cold heat streams together represent the recuperator: the cold stream (compressed air preheated from $T_2$ to $T_{2a}$) draws its duty from the hot stream (exhaust gases cooled from $T_4$ to $T_{stack}$). In an optimisation problem they are placed on the system heat cascade and may be matched against process streams, allowing combined-heat-and-power studies.

## 7. Equipment and cost

A single mechanical assembly comprising the axial compressor, the combustion chamber, and the power turbine, with shaft-coupled electrical generator and a recuperator.

Capital cost is taken as a specific-investment correlation in the net electric output:

$$C_{inv2,GT} \;=\; 500 \cdot W_{el,net} \cdot a \quad [\text{EUR/y}],$$

with $W_{el,net}$ in kW. The 500 EUR/kW basis is in 2008 EUR; the JSON-stored value is annualised over $n$ via $a = i(1+i)^{n}/((1+i)^{n}-1)$.

| Item | Value |
|:-----|:------|
| Equipment subtype | Gas turbine with recuperator |
| Lifetime | 40 years |
| Interest rate | 0.06 |
| Specific investment | 500 EUR/kWₑₗ |
| Capacity range | 0 × to 10 × (relative to reference $W_{el,net}$) |
| Fixed operating cost | 0 EUR/y |
| Variable operating cost | 0 EUR/h |

Operating costs are zero in the reference model — fuel and emission flows enter the optimisation through the resource interfaces of §6.

## 8. References

1. Cengel, Y. and Boles, M. (2010). **Thermodynamics: An Engineering Approach** (with Student Resources DVD).
2. Rahman, M. M., Ibrahim, T. K. and Abdalla, A. N. (2011). *Thermodynamic performance analysis of gas-turbine power-plant.* **International Journal of the Physical Sciences** **6** (14), 3539–3550.

## 9. Cite as

> Flórez-Orrego, D. & Domingos, M. *Gas Turbine — Ex-ante energy-technology model (ET, v1.0.1).* IEA IETS Task XXIV / Subtask 1, Activity 3.1. EPFL IPESE, Lausanne, 2025. Contact: <daniel.florezorrego@epfl.ch>.
