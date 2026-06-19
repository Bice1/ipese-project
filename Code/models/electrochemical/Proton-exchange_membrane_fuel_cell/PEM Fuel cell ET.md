---
title: "PEM Fuel Cell — Energy Technology Model"
subtitle: "IEA IETS Task XXIV · Subtask 1 · Activity 3.1 (Energy Technologies)"
author: "Daniel Flórez-Orrego, Oktay Boztas — EPFL IPESE"
date: "2026-04-24"
---

# Proton-exchange membrane (PEM) fuel cell

A grey-box, steady-state model of a **low-temperature proton-exchange membrane (PEM) fuel cell** that converts gaseous hydrogen and oxygen into electrical power, water, and waste heat. The unit exposes a hydrogen input, an oxygen input, a water output (condensed liquid product), an electricity output, and one hot heat stream (the cooling loop carrying the waste heat away at the cell operating temperature).

## 1. Model card

| Field | Value |
|:------|:------|
| Model identifier | PEM Fuel Cell (ET) |
| Authors | Daniel Flórez-Orrego, Oktay Boztas — EPFL IPESE |
| Contact | daniel.florezorrego@epfl.ch · oktay.boztas@epfl.ch |
| Version · Status | 1.0.1 · Maintained |
| Created · Updated | 2026-04-24 · 2026-04-24 |
| Confidentiality · Sharing layer | Open · 1 (fully shareable) |
| Model grade · TRL | Gray-box · 9 |
| Reference capacity | 144 kW of electricity output |
| Keywords | Fuel Cell · Hydrogen · Oxygen · Electricity · Energy Conversion |
| Main publication | Fuel Cell Systems Explained, Larminie & Dicks (2003), 2nd ed., Wiley — ISBN 0-470-84857-X |

## 2. Process description

A fuel cell converts the chemical energy of a fuel directly into electrical work through electrochemical oxidation, bypassing the thermal cycle and its Carnot bound. The **proton-exchange membrane (PEM) fuel cell** is the most mature low-temperature variant: a polymer membrane that conducts protons separates the anode (where hydrogen is oxidised, $\mathrm{H_2 \to 2H^+ + 2e^-}$) from the cathode (where oxygen is reduced and combined with the protons, $\mathrm{\tfrac{1}{2}O_2 + 2H^+ + 2e^- \to H_2O}$). The overall reaction is

$$\mathrm{H_2 + \tfrac{1}{2}O_2 \;\longrightarrow\; H_2O} \quad \text{(exergonic)},$$

producing one mole of water per mole of hydrogen consumed and releasing electrical work plus heat. Typical PEM operating temperatures lie between 60 °C and 80 °C, low enough to require high-purity hydrogen but high enough to use the by-product water as a thermal stream for low-grade heat integration. As the operating current rises, ohmic, activation, and mass-transport irreversibilities reduce the actual cell voltage below the thermodynamic open-circuit value; this is captured here through a single second-law-like efficiency $\eta_{cell}$ that maps the ideal cell power to the delivered electrical power.

The model uses Faraday's law to relate the molar hydrogen consumption to the cell current,

$$I_{cell} \;=\; \dfrac{2 F\,\dot n_{H_2}}{3600},$$

where $F$ is the Faraday constant, $\dot n_{H_2}$ is in mol/h, and the factor 2 reflects the two electrons exchanged per H₂ molecule. The delivered electric power follows as $P_{cell} = V_{cell}\,I_{cell}\,\eta_{cell}$, and the corresponding waste-heat output as $\dot Q_{cell} = P_{cell}\,(1-\eta_{cell})/\eta_{cell}$. Oxygen and product water flows close the stoichiometric mass balance.

## 3. Block flow diagram

![Low-temperature PEM fuel-cell unit: stack with H₂/O₂ feeds, electrical and water outputs, and a cooling loop carrying the waste heat away at the operating temperature.](../Figures/PEMFuelCell.svg){width=80%}

## 4. Parameters

Parameters are grouped by their role — **Decision** (chosen by the modeller / optimiser), **Boundary** (operating environment, financial assumptions), **Literature** (constants and physical properties).

### 4.1 Decision

| Parameter | Symbol | Default | Min | Max | Unit |
|:----------|:-------|--------:|----:|----:|:-----|
| Hydrogen mass flow | $\dot m_{H_2}$ | 7 | 0.01 | 5 000 | kg/h |
| Cell voltage | $V_{cell}$ | 1.4 | 0.4 | 1.23 | V |
| Cell second-law efficiency | $\eta_{cell}$ | 0.55 | 0 | 1 | – |
| Specific investment cost | $c_{cell}$ | 1 200 | 100 | 10 000 | EUR/kW |
| $\Delta T_{min}$ contribution | $\Delta T_{min}$ | 5 | 1 | 50 | °C |
| Interest rate | $i$ | 0.06 | 0 | 1 | – |
| Equipment lifetime | $n$ | 40 | 2 | 50 | year |

### 4.2 Boundary

| Parameter | Symbol | Default | Min | Max | Unit |
|:----------|:-------|--------:|----:|----:|:-----|
| Cell operating temperature | $T_{cell}$ | 80 | 20 | 200 | °C |
| Cooling return temperature | $T_{rec}$ | 60 | 40 | 180 | °C |

### 4.3 Literature

| Parameter | Symbol | Default | Unit | Source |
|:----------|:-------|--------:|:-----|:-------|
| Molecular weight of H₂ | $M_{H_2}$ | 2 | kg/kmol | EPFL IPESE research group |
| Molecular weight of H₂O | $M_{H_2O}$ | 18 | kg/kmol | EPFL IPESE research group |
| Molecular weight of O₂ | $M_{O_2}$ | 32 | kg/kmol | EPFL IPESE research group |
| Faraday constant | $F$ | 96 485.33 | A·s/mol | EPFL IPESE research group |

## 5. Derived quantities at the reference operating point

Values shown for $\dot m_{H_2}=7$ kg/h, $V_{cell}=1.4$ V, $\eta_{cell}=0.55$, $T_{cell}=80$ °C.

| Quantity | Symbol | Expression | Value | Unit |
|:---------|:-------|:-----------|------:|:-----|
| Hydrogen molar flow | $\dot n_{H_2}$ | $\dot m_{H_2}/M_{H_2}$ | 3.5 | kmol/h |
| Oxygen mass consumption | $\dot m_{O_2}$ | $\tfrac{1}{2}\,\dot n_{H_2}\,M_{O_2}$ | 56 | kg/h |
| Water mass production | $\dot m_{H_2O}$ | $\dot n_{H_2}\,M_{H_2O}$ | 63 | kg/h |
| Cell current | $I_{cell}$ | $2F\,\dot n_{H_2}/3600$ | 187 610 | A |
| Electrical power output | $P_{cell}$ | $V_{cell}\,I_{cell}\,\eta_{cell}$ | 144 | kW |
| Waste-heat output | $\dot Q_{cell}$ | $P_{cell}(1-\eta_{cell})/\eta_{cell}$ | 118 | kW |
| Annualised investment cost | $C_{inv2,cell}$ | $c_{cell}\,P_{cell}\,\dfrac{i(1+i)^{n}}{(1+i)^{n}-1}$ | 11 025 | EUR/y |

## 6. Interfaces and heat streams

The PEM fuel cell exchanges four resources with the surrounding system and produces one hot heat stream from its cooling loop.

| Interface | Direction / Type | Reference flow | T | P | Phase / Composition |
|:----------|:-----------------|---------------:|:--|:--|:--------------------|
| Hydrogen feed | In · Mass | 7 kg/h | 25 °C | 1 bar | Vapour, H₂ (100 %) |
| Oxygen feed | In · Mass | 56 kg/h | 25 °C | 1 bar | Vapour, O₂ (100 %) |
| Electricity (net) | Out · Electrical | 144 kW | – | – | – |
| Water (condensed product) | Out · Mass | 63 kg/h | 25 °C | 1 bar | Liquid, H₂O (100 %) |
| Cooling loop (waste-heat) | Hot thermal | 118 kW | $T_{cell}=80$ °C → $T_{rec}=60$ °C | – | Water; $\Delta T_{min}/2 = 5$ °C |

The cooling-loop heat stream represents the residual reaction enthalpy that is *not* converted to electrical work; it is available at low-temperature ($\le 80$ °C) and can be matched against any process cold stream above $T_{rec}$ on the system heat cascade.

## 7. Equipment and cost

The unit comprises the PEM fuel-cell stack plus its auxiliaries: pumps for the lean air, the oxygen and the water outlet, and heat exchangers for water condensation and air cooling.

Capital cost is taken as a specific-investment correlation in the net electric output:

$$C_{inv2,cell} \;=\; c_{cell}\,P_{cell}\,\dfrac{i\,(1+i)^{n}}{(1+i)^{n}-1} \quad [\text{EUR/y}],$$

with $P_{cell}$ in kW and $c_{cell}$ in EUR/kW.

| Item | Value |
|:-----|:------|
| Equipment subtype | PEM fuel-cell stack |
| Lifetime | 40 years |
| Interest rate | 0.06 |
| Specific investment | 1 200 EUR/kWₑₗ |
| Capacity range | 0 × to 1 × (relative to reference $P_{cell}$) |
| Fixed operating cost | 0 EUR/y |
| Variable operating cost | 0 EUR/h |

Operating costs are zero in the reference model — fuel, oxidant and water flows enter the optimisation through the resource interfaces of §6.

## 8. References

1. Larminie, J. & Dicks, A. (2003). **Fuel Cell Systems Explained**, 2nd ed., John Wiley & Sons. ISBN 0-470-84857-X. <https://onlinelibrary.wiley.com/doi/pdf/10.1002/9781118878330.app2>.

## 9. Cite as

> Flórez-Orrego, D. & Boztas, O. *PEM Fuel Cell — Ex-ante energy-technology model (ET, v1.0.1).* IEA IETS Task XXIV / Subtask 1, Activity 3.1. EPFL IPESE, Lausanne, 2026. Contact: <daniel.florezorrego@epfl.ch>.
