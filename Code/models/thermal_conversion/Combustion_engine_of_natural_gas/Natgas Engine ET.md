---
title: "Natural-Gas Internal Combustion Engine (cogeneration) — Energy Technology Model"
subtitle: "IEA IETS Task XXIV · Subtask 1 · Activity 3.1 (Energy Technologies)"
author: "Daniel Flórez-Orrego, EPFL IPESE research group"
date: "2026-04-21"
---

# Natural-Gas Engine (cogeneration)

A grey-box, steady-state model of a **stationary internal-combustion engine (ICE)** burning **natural gas** in a combined-heat-and-power (CHP) configuration. The unit exposes a fuel input (natural gas), a net electricity output, a CO₂-in-flue-gas output, and two hot heat streams that together capture the engine's recoverable waste heat: a **high-grade** flue-gas stream (400 → 150 °C) and a **low-grade** engine-cooling-water stream (90 → 40 °C). The model is a fixed-efficiency representation calibrated on a Jenbacher Type-4 reference engine.

**Variants.** A companion model exists in the source set for a **raw-biogas-fired engine** (`RawBiogasEngine_ET`) with the same structure but a different fuel composition and different reference efficiencies. That variant is documented separately (see *Biogas Engine ET*).

## 1. Model card

| Field | Value |
|:------|:------|
| Model identifier | Natural-Gas Engine (ET) |
| Authors | Daniel Flórez-Orrego — EPFL IPESE research group |
| Contact | daniel.florezorrego@epfl.ch · oktay.boztas@epfl.ch |
| Version · Status | 1.0.1 · Maintained |
| Created · Updated | 2026-04-21 · 2026-04-21 |
| Confidentiality · Sharing layer | Open · 1 (fully shareable) |
| Model grade · TRL | Gray-box · 9 |
| Reference capacity | 1 000 kW of natural-gas consumption (≈ 433 kWₑₗ electrical output) |
| Keywords | Natural Gas · Cogeneration · Engine · Electricity |
| Description | Combustion engine of natural gas with cogeneration |

## 2. Process description

A natural-gas-fired internal-combustion engine is the workhorse of small-to-medium-scale cogeneration: burn the fuel in the engine cylinders, take shaft work out via a generator, and recover the remaining energy from the exhaust gases and the engine cooling jacket. Compared with a gas turbine, an ICE-CHP has lower upfront capex per kW, higher part-load flexibility, and a slightly higher electrical efficiency at small scale, at the cost of more frequent maintenance and a noisier installation.

The model represents the engine with a **fixed-efficiency** energy balance: a fraction $\eta_{el}$ of the fuel LHV is converted into shaft power (electrical output), a fraction $\eta_{th,fg}$ leaves at high temperature in the flue gases, and a fraction $\eta_{th,cw}$ leaves at low temperature in the engine cooling water. The remainder (~12 %, the gap to unity) is lost as radiative/convective losses to the surroundings and is not modelled as a recoverable stream. CO₂ emissions are computed stoichiometrically from the fuel consumption, assuming pure methane (44/16 kg of CO₂ per kg of CH₄).

The two waste-heat streams are exposed on the system heat cascade so that the optimisation can match them against any process heat demand in the surrounding system — typical use cases are district-heating networks, drying processes, low-pressure steam generation, or feed-water preheating.

## 3. Block flow diagram

![Natural-gas internal combustion engine in cogeneration: fuel input, electrical output via the generator, flue-gas hot stream (400 → 150 °C, high-grade) and cooling-water hot stream (90 → 40 °C, low-grade).](../Figures/NatgasEngine.svg){width=80%}

## 4. Parameters

All operating-point parameters in the source model are **boundary values** taken from the manufacturer reference and treated as fixed in the optimisation. The only literature parameter is the LHV of the fuel.

### 4.1 Boundary (operating point)

| Parameter | Symbol | Default | Unit |
|:----------|:-------|--------:|:-----|
| Reference fuel consumption | $\dot Q_{fuel,ref}$ | 1 000 | kW |
| Electrical efficiency | $\eta_{el}$ | 0.433 | – |
| Thermal efficiency, flue-gas (high-grade) | $\eta_{th,fg}$ | 0.21 | – |
| Thermal efficiency, cooling water (low-grade) | $\eta_{th,cw}$ | 0.236 | – |
| Flue-gas inlet / outlet temperature | $T_{fg,in}/T_{fg,out}$ | 400 / 150 | °C |
| Cooling-water inlet / outlet temperature | $T_{cw,in}/T_{cw,out}$ | 90 / 40 | °C |
| Reference CO₂ emission | $\dot m_{CO_2,ref}$ | 198 | kg/h |
| Engine specific CAPEX | $c_{eng}$ | 1 200 | EUR/kWₑₗ |
| $\Delta T_{min}$ — gas / liquid | $\Delta T_{min,gas/liq}$ | 8 / 5 | K |
| Equipment lifetime | $n$ | 40 | year |
| Interest rate | $i$ | 0.06 | – |
| CEPCI (current / 2008) | $CEPCI_{2020}$ / $CEPCI_{2008}$ | 596.2 / 575.4 | – |

### 4.2 Literature

| Parameter | Symbol | Default | Unit | Source |
|:----------|:-------|--------:|:-----|:-------|
| Lower heating value of fuel | $LHV_{fuel}$ | 50 000 | kJ/kg | Cengel & Boles (2010) — see [1] |

## 5. Derived quantities at the reference operating point

| Quantity | Symbol | Expression | Value | Unit |
|:---------|:-------|:-----------|------:|:-----|
| Net electrical output | $W_{el}$ | $\eta_{el}\,\dot Q_{fuel,ref}$ | 433 | kW |
| Flue-gas recoverable heat | $\dot Q_{fg}$ | $\eta_{th,fg}\,\dot Q_{fuel,ref}$ | 210 | kW |
| Cooling-water recoverable heat | $\dot Q_{cw}$ | $\eta_{th,cw}\,\dot Q_{fuel,ref}$ | 236 | kW |
| Annualisation factor | $a$ | $i(1+i)^{n}/((1+i)^{n}-1)$ | 0.0665 | – |
| Annualised investment cost | $C_{inv2,eng}$ | $c_{eng}\,W_{el}\,a\,(CEPCI_{2020}/CEPCI_{2008})$ | 35 782 | EUR/y |

The unrecovered fraction $1-\eta_{el}-\eta_{th,fg}-\eta_{th,cw} \approx 0.12$ corresponds to radiative and convective losses to the engine room.

## 6. Interfaces and heat streams

The natural-gas engine exchanges three external resources with the surrounding system and exposes two recoverable thermal streams.

| Interface | Direction / Type | Reference flow | T | P | Phase / Composition |
|:----------|:-----------------|---------------:|:--|:--|:--------------------|
| Natural-gas fuel | In · Energy | 1 000 kW | 25 °C | 1 bar | Vapour, CH₄ (100 %) |
| Electricity (net) | Out · Electrical | 433 kW | – | – | – |
| CO₂ in flue gas | Out · Mass (emission) | 198 kg/h | 25 °C | 1 bar | Vapour, CO₂ (100 %) |
| Flue-gas waste heat | Hot thermal | 210 kW | 400 °C → 150 °C | – | Flue gas; $\Delta T_{min}/2 = 4$ K |
| Cooling-water waste heat | Hot thermal | 236 kW | 90 °C → 40 °C | – | Water; $\Delta T_{min}/2 = 2.5$ K |

The two heat streams are complementary: the flue-gas duty is **high-grade** (suitable for steam generation, process heating, or absorption chilling), while the cooling-water duty is **low-grade** (typical match against district heating, low-temperature drying, or feed-water preheating).

## 7. Equipment and cost

A single asset — the natural-gas engine — is sized for cost calculation. Capital cost is taken as a flat specific-investment correlation in the net electrical output:

$$C_{inv2,eng} \;=\; c_{eng}\,W_{el}\,\dfrac{CEPCI_{2020}}{CEPCI_{2008}}\,a \quad [\text{EUR/y}],$$

with $W_{el}$ in kW and $a$ the discrete-compounding capital-recovery factor.

| Item | Value |
|:-----|:------|
| Equipment subtype | Natural-gas engine (Jenbacher Type 4 reference) |
| Lifetime | 40 years |
| Interest rate | 0.06 |
| Specific investment | 1 200 EUR/kWₑₗ |
| Capacity range | 0 × to 100 × reference |
| Fixed operating cost | 0 EUR/y |
| Variable operating cost | 0 EUR/h |

Operating costs are zero in the reference model — fuel and emission flows enter the optimisation through the resource interfaces of §6.

## 8. References

1. Cengel, Y. & Boles, M. (2010). **Thermodynamics: An Engineering Approach**.
2. INNIO Jenbacher. *Jenbacher Type 4 — gas engines.* <https://www.jenbacher.com/en/gas-engines/type-4> (accessed 2023-08-28).
3. European Biogas Association. *National biomethane potentials* (2022). <https://www.europeanbiogas.eu/wp-content/uploads/2022/07/GfC_national-biomethane-potentials_070722.pdf>.
4. Maréchal, F., Sachan, R. & Salgueiro, L. (2013). **Handbook of Process Integration**.

## 9. Cite as

> Flórez-Orrego, D. *Natural-Gas Engine — Ex-ante energy-technology model (ET, v1.0.1).* IEA IETS Task XXIV / Subtask 1, Activity 3.1. EPFL IPESE, Lausanne, 2026. Contact: <daniel.florezorrego@epfl.ch>.
