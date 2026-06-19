---
title: "Biodigestion of MSW with biogas upgrading — Energy Technology Model"
subtitle: "IEA IETS Task XXIV · Subtask 1 · Activity 3.1 (Energy Technologies)"
author: "Daniel Flórez-Orrego, Meire Domingos — EPFL IPESE"
date: "2025-11-13"
---

# Biodigestion of MSW with biogas upgrading

A grey-box, steady-state model of the **anaerobic digestion of the organic fraction of municipal solid waste (MSW)** followed by **water-scrubbing upgrading of the raw biogas** to pipeline-grade biomethane. The model couples two physical sub-units that share one internal stream:

- a **thermophilic anaerobic digester** (Biodigester) operating at 55 °C, converting biowaste into raw biogas (≈ 55 mol% CH₄, ≈ 45 mol% CO₂) and a digestate residue;
- a **biogas upgrading plant** (BiogasPurif) that compresses the biogas and removes CO₂ in a water-scrubbing column, producing biomethane suitable for natural-gas-grid injection.

The combined unit exposes a biomass input, a biomethane (energy) output, a CO₂ output, a digestate output, an electricity input (for the compressor and the scrubber), and a heat duty needed to keep the digester at 55 °C.

## 1. Model card

| Field | Value |
|:------|:------|
| Model identifier | Biodigester of MSW with biogas upgrading (ET) |
| Authors | Daniel Flórez-Orrego, Meire Domingos — EPFL IPESE |
| Contact | daniel.florezorrego@epfl.ch · oktay.boztas@epfl.ch |
| Version · Status | 1.0.1 · Maintained |
| Created · Updated | 2025-11-13 · 2025-11-13 |
| Confidentiality · Sharing layer | Open · 1 (fully shareable) |
| Model grade · TRL | Gray-box · 9 |
| Reference capacity | 154 407 kW of produced biomethane |
| Keywords | Biogas · Biodigestion · Municipal Solid Waste |
| Description | Biodigester of municipal solid waste with biogas purification to natural gas |

## 2. Process description

Anaerobic digestion is a biological process in which organic matter decomposes into biogas in an oxygen-free environment, through the action of microorganisms. The conversion takes place in a **biodigester** vessel that can process a wide range of feedstocks — agricultural residues, municipal organic waste, sewage sludge. Two operating regimes are usually distinguished: **mesophilic** (≈ 35–37 °C, easier to maintain, more stable, slower kinetics) and **thermophilic** (≈ 55–60 °C, faster kinetics, pathogen destruction, higher biogas yields, but higher heating demand). The model implemented here represents the **thermophilic** regime at 55 °C, sustained by an external heat duty.

The biomass feed (mass flow $\dot m_{biomass}$, total solids fraction $TS$, volatile solids fraction $VS$) is converted at a rate set by an exponential degradation kinetics with rate constant $k$ over a retention time $t$. The biogas volumetric yield is approximated by

$$\dot V_{biogas} \;=\; \dfrac{\dot m_{biomass}\, TS\, VS\, BMP\, \bigl(1 - e^{-k\,t}\bigr)}{x_{CH_4,biogas}},$$

where $BMP$ is the **biomethane potential** of the volatile solids and $x_{CH_4,biogas}$ is the methane molar fraction in the raw biogas. The resulting raw biogas (≈ 55 mol% CH₄, ≈ 45 mol% CO₂) carries an energy content $\dot Q_{biogas} = \dot V_{biogas}\,LHV_{biogas}^{vol}$. The non-gaseous residue, the **digestate**, leaves the digester at process temperature and is usually valorised as a fertiliser. The digester itself requires a heating duty $\dot Q_{dig} = q_{dig}\,\dot m_{biomass}$ to maintain its set-point.

In the **upgrading stage**, the raw biogas is compressed isothermally with intercooling from $P_{in}$ to $P_{out}$ — the compressor power is approximated by an ideal-gas isothermal compression with efficiency $\eta_{comp}$,

$$W_{comp} \;=\; \dfrac{\dot m_{biogas}}{\eta_{comp}}\,\dfrac{R_u}{M_{biogas}}\,T_{comp}\,\ln\!\left(\dfrac{P_{out}}{P_{in}}\right),$$

after which CO₂ is absorbed in a counter-current **water-scrubbing column**, leaving a pure CH₄ stream ready for grid injection. The scrubbing column itself consumes a specific electricity duty $q_{scrub}$ per unit of biogas volume processed.

## 3. Block flow diagram

![Biodigestion plant: anaerobic digester (left) producing raw biogas + digestate, followed by compression and water-scrubbing CO₂ removal (right) yielding pipeline-grade biomethane.](../Figures/biodigester.svg){width=85%}

## 4. Parameters

Parameters are grouped by their role — **Decision** (chosen by the modeller / optimiser), **Boundary** (operating environment, financial assumptions), **Literature** (kinetics, gas properties, cost references).

### 4.1 Decision

| Parameter | Symbol | Default | Min | Max | Unit |
|:----------|:-------|--------:|----:|----:|:-----|
| Digester operating temperature (thermophilic) | $T_{dig}$ | 55 | 50 | 65 | °C |
| Biogas compressor efficiency | $\eta_{comp}$ | 0.80 | 0 | 1 | – |
| Intercooler outlet temperature | $T_{comp}$ | 311 | 273.15 | 373.15 | K |
| Compressor inlet pressure | $P_{in}$ | 1 | 0.5 | 5 | bar |
| Compressor outlet pressure | $P_{out}$ | 30 | 1.1 | 250 | bar |
| Water-scrubbing specific power | $q_{scrub}$ | 0.20 | 0.05 | 0.5 | kWh/Nm³_biogas |

### 4.2 Boundary

| Parameter | Symbol | Default | Min | Max | Unit |
|:----------|:-------|--------:|----:|----:|:-----|
| Biomass feed (MSW organic fraction) | $\dot m_{biomass}$ | 270 | 1 | 1 000 | t/h |
| Total solids fraction | $TS$ | 0.30 | 0 | 1 | t/t_waste |
| Volatile solids fraction | $VS$ | 0.70 | 0 | 1 | t/t_TS |
| Methane fraction in biogas (molar) | $x_{CH_4,biogas}$ | 0.553 | 0 | 1 | – |
| $\Delta T_{min}$ for digester heating | $\Delta T_{min,dig}$ | 5 | 1 | 20 | °C |
| Equipment lifetime | $n$ | 40 | 5 | 60 | year |
| Interest rate | $i$ | 0.06 | 0 | 1 | – |
| CEPCI (current / 2008) | $CEPCI_{2020}$ / $CEPCI_{2008}$ | 596.2 / 575.4 | – | – | – |

### 4.3 Literature

| Parameter | Symbol | Default | Unit | Source |
|:----------|:-------|--------:|:-----|:-------|
| Biomethane potential of VS | $BMP$ | 300 | Nm³/tVS | EPFL IPESE research group |
| Exponential degradation coefficient | $k$ | 0.2 | 1/day | EPFL IPESE research group |
| Retention time | $t$ | 30 | day | EPFL IPESE research group |
| Volumetric LHV of methane | $LHV^{vol}_{CH_4}$ | 9.1 | kWh/Nm³ | EPFL IPESE research group |
| Mass LHV of methane | $LHV^{m}_{CH_4}$ | 50 000 | kJ/kg | EPFL IPESE research group |
| Volumetric LHV of raw biogas | $LHV^{vol}_{biogas}$ | 5.0 | kWh/Nm³ | EPFL IPESE research group |
| Specific heating duty of biowaste | $q_{dig}$ | 28.5 | kWh/t_waste | EPFL IPESE research group |
| Molecular weight of CH₄ / CO₂ | $M_{CH_4}$ / $M_{CO_2}$ | 16 / 44 | kg/kmol | EPFL IPESE research group |
| Universal gas constant | $R_u$ | 8.314 | kJ/(kmol·K) | EPFL IPESE research group |
| Digester specific CAPEX | $c_{dig}$ | 1 870 000 | EUR/(t/h)_waste | Remy (2018) [1] |
| Compressor specific CAPEX (linearised) | $c_{comp}$ | 176.47 | EUR/kW | Turton (2008) |
| Water-scrubbing specific CAPEX | $c_{scrub}$ | 1 500 | EUR·h/Nm³ | Bauer *et al.* (2013) [2] |

## 5. Derived quantities at the reference operating point

Values shown for $\dot m_{biomass}=270$ t/h, $TS=0.30$, $VS=0.70$, $BMP=300$ Nm³/tVS, $k=0.2/$d, $t=30$ d, $x_{CH_4,biogas}=0.553$, $T_{dig}=55$ °C, $P_{in}=1$ bar, $P_{out}=30$ bar.

| Quantity | Symbol | Expression | Value | Unit |
|:---------|:-------|:-----------|------:|:-----|
| Degradation factor | – | $1-e^{-k\,t}$ | 0.998 | – |
| Biogas volumetric flow | $\dot V_{biogas}$ | $\dot m_{biomass}\,TS\,VS\,BMP\,(1-e^{-k\,t})/x_{CH_4,biogas}$ | 30 683 | Nm³/h |
| Biogas energy flow | $\dot Q_{biogas}$ | $\dot V_{biogas}\,LHV^{vol}_{biogas}$ | 153 416 | kW |
| Biomethane volumetric flow | $\dot V_{CH_4}$ | $x_{CH_4,biogas}\,\dot V_{biogas}$ | 16 968 | Nm³/h |
| Biomethane energy flow | $\dot Q_{CH_4}$ | $\dot V_{CH_4}\,LHV^{vol}_{CH_4}$ | 154 407 | kW |
| CH₄ mass flow | $\dot m_{CH_4}$ | $\dot Q_{CH_4}/LHV^{m}_{CH_4}\cdot 3600$ | 11 117 | kg/h |
| CH₄ mass fraction in biogas | $w_{CH_4}$ | $(x_{CH_4,biogas}M_{CH_4}) / (x_{CH_4,biogas}M_{CH_4}+(1-x_{CH_4,biogas})M_{CO_2})$ | 0.310 | – |
| Biogas mass flow | $\dot m_{biogas}$ | $\dot m_{CH_4}/w_{CH_4}$ | 35 830 | kg/h |
| CO₂ mass flow | $\dot m_{CO_2}$ | $\dot m_{biogas}-\dot m_{CH_4}$ | 24 712 | kg/h |
| Digestate mass flow | $\dot m_{dig}$ | $\dot m_{biomass}-\dot m_{biogas}/1000$ | 234 | t/h |
| Digester heating duty | $\dot Q_{dig}$ | $q_{dig}\,\dot m_{biomass}$ | 7 695 | kW |
| Biogas compressor duty (isothermal) | $W_{comp}$ | $\dfrac{\dot m_{biogas}}{\eta_{comp}}\dfrac{R_u}{M_{biogas}}T_{comp}\ln(P_{out}/P_{in})$ | 3 837 | kW |
| Water-scrubbing duty | $W_{scrub}$ | $q_{scrub}\,\dot V_{biogas}$ | 6 137 | kW |
| Total electricity demand | $W_{tot}$ | $W_{comp}+W_{scrub}$ | 9 973 | kW |
| Annualisation factor | $a$ | $i(1+i)^{n}/((1+i)^{n}-1)$ | 0.0665 | – |
| Annualised CAPEX — digester | $C_{inv2,dig}$ | $\dot m_{biomass}\,c_{dig}\,(CEPCI_{2020}/CEPCI_{2008})\,a$ | 34.8 M | EUR/y |
| Annualised CAPEX — compressor | $C_{inv2,comp}$ | $W_{comp}\,c_{comp}\,(CEPCI_{2020}/CEPCI_{2008})\,a$ | 47 k | EUR/y |
| Annualised CAPEX — scrubber | $C_{inv2,scrub}$ | $\dot V_{biogas}\,c_{scrub}\,(CEPCI_{2020}/CEPCI_{2008})\,a$ | 3.17 M | EUR/y |

## 6. Interfaces and heat streams

The compound unit exchanges five external resources with the surrounding system, plus one internal biogas stream between the two sub-units, and one heat duty at the digester.

| Interface | Sub-unit | Direction / Type | Reference flow | T | P | Phase / Composition |
|:----------|:---------|:-----------------|---------------:|:--|:--|:--------------------|
| BioMSW (feedstock) | Biodigester | In · Mass | 270 t/h | 25 °C | 1 bar | Solid; digestible organic fraction |
| Biogas (internal) | Biodigester → BiogasPurif | Out → In · Mass | 35 830 kg/h | 55 °C | 1 bar | Vapour; molar CH₄/CO₂ ≈ 0.553/0.447 |
| Digestate | Biodigester | Out · Mass | 234 t/h | 25 °C | 1 bar | Liquid; stabilised organic residue |
| Electricity (auxiliaries) | BiogasPurif | In · Electrical | 9 973 kW | – | – | – |
| Biomethane (CH₄) product | BiogasPurif | Out · Energy | 154 407 kW | 25 °C | 1 bar | Vapour, CH₄ (100 %) |
| CO₂ vent | BiogasPurif | Out · Mass | 24 712 kg/h | 25 °C | 1 bar | Vapour, CO₂ (100 %) |
| Digester heating duty | Biodigester | Hot thermal | 7 695 kW | 55 °C → 55 °C (isothermal) | – | $\Delta T_{min}/2 = 5$ °C |

## 7. Equipment and cost

Two assets are sized for cost calculation:

- **Anaerobic digester vessel** — sized in proportion to the biomass throughput, with a high specific CAPEX reflecting the civil work, mixing system, gas-tight enclosure, and auxiliary heat-exchange surface.
- **Upgrading system** — biogas compressor (linearised cost from a 450–3 000 kW centrifugal-compressor correlation, Turton 2008) and water-scrubbing column (specific cost per Nm³/h of biogas processed, Bauer *et al.* 2013).

Capital costs are annualised over the equipment lifetime via the discrete-compounding capital-recovery factor $a$, and updated from their 2008 reference year through the ratio of CEPCI indices:

$$C_{inv2,j} \;=\; \text{(size}_j\text{)} \cdot c_j \cdot \dfrac{CEPCI_{2020}}{CEPCI_{2008}} \cdot a, \qquad a \;=\; \dfrac{i\,(1+i)^{n}}{(1+i)^{n}-1}.$$

| Item | Value |
|:-----|:------|
| Digester lifetime | 40 years |
| Interest rate | 0.06 |
| Digester specific CAPEX | 1 870 000 EUR/(t/h)_waste |
| Compressor specific CAPEX | 176.47 EUR/kW |
| Water-scrubbing specific CAPEX | 1 500 EUR·h/Nm³ |
| Capacity range — digester | 0 × to 100 × reference |
| Capacity range — upgrading | 0 × to 10 000 × reference |
| Fixed operating cost | 0 EUR/y |
| Variable operating cost | 0 EUR/h |

Operating costs are zero in the reference model — biomass, electricity, and product streams enter the optimisation through the resource interfaces of §6.

## 8. References

1. Remy, F. (2018). *Potential for the anaerobic digestion of municipal solid waste (MSW) in the city of Curitiba, Brazil.*
2. Bauer, F., Hulteberg, C., Persson, T. & Tamm, D. (2013). *Biogas upgrading — Review of commercial technologies.*
3. Hamzah *et al.* (2019). *Comparative start-up between mesophilic and thermophilic for acidified palm oil mill effluent treatment.* **IOP Conf. Ser.: Earth Environ. Sci.** **268** 012028.
4. Wales AD Centre. *Mesophilic and thermophilic systems* (2023). <https://www.walesadcentre.org.uk/ad-information/technologies/mesophilic-and-thermophilic-systems/>.

## 9. Cite as

> Flórez-Orrego, D. & Domingos, M. *Biodigestion of MSW with biogas upgrading — Ex-ante energy-technology model (ET, v1.0.1).* IEA IETS Task XXIV / Subtask 1, Activity 3.1. EPFL IPESE, Lausanne, 2025. Contact: <daniel.florezorrego@epfl.ch>.
